#!/usr/bin/env python3
"""解析固定 VS Code bundle 的深浅默认表达式，分别生成颜色引用或 RGBA 锚点。

默认输出 data/anchors.json，包含 source、themes.dark/light 和 unresolved。
保留引用透明度；版本或 bundle 哈希不匹配时拒绝写入。
维护固定基准请使用 update_registry.py；此脚本不负责主题调色板映射。
"""
import json
import os
import re
import colorsys
import argparse
import hashlib
from pathlib import Path
from extract_registry import find_bundle, split_args as parse_arguments
from utf8_console import use_utf8_console

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = {}

# ---- 变量环境 ----------------------------------------------------------
# ae() 注册的 color id
VAR2ID = {}
# 形如 `X=.4` 的数值（透明度因子）
NUM = {}
# Color 类常量（$e = Colors class）
COLORS = {
    "white": (255, 255, 255, 1.0), "black": (0, 0, 0, 1.0),
    "red": (255, 0, 0, 1.0), "blue": (0, 0, 255, 1.0),
    "green": (0, 255, 0, 1.0), "cyan": (0, 255, 255, 1.0),
    "magenta": (255, 0, 255, 1.0), "yellow": (255, 255, 0, 1.0),
}
# `new $e(new fi(r,g,b,a))` 形式的颜色常量
RGBA_VAR = {}


def hex_rgba(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "FF"
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255.0


def is_color_id(tok):
    return bool(re.fullmatch(r"[a-zA-Z][\w]*(\.[\w]+)+", tok))


def split_args(s):
    return parse_arguments(s, 0)


def number(expression):
    return NUM[expression] if expression in NUM else float(expression)


def transparent(base, factor):
    if base[0] == "id":
        return ("id", base[1], (base[2] if len(base) > 2 else 1.0) * factor)
    red, green, blue, alpha = base[1]
    return ("hex", (red, green, blue, alpha * factor))


def resolve(expr, depth=0):
    """归约为 ('id', id) 或 ('hex', (r,g,b,a)) 或 None。alpha 反映 transparent 操作。"""
    if depth > 8 or not expr:
        return None
    e = expr.strip()
    while e.startswith('"') and e.endswith('"') and len(e) >= 2:
        e = e[1:-1].strip()
    if e in ("", "null", "undefined"):
        return None
    # 方法链：取基色并叠加透明/明暗（此处只记录 alpha，明暗交给映射阶段）
    m = re.match(r"^(.*?)\.(transparent|lighten|darken)\(([^)]*)\)$", e, re.S)
    if m:
        base = resolve(m.group(1), depth + 1)
        if base is None:
            return None
        op, arg = m.group(2), m.group(3).strip()
        try:
            f = number(arg)
        except ValueError:
            return None
        if op == "transparent":
            return transparent(base, f)
        return base
    # 颜色常量 $e.white.transparent(.1) / $e.fromHex("#xxx")
    m = re.fullmatch(r"\$e\.([a-zA-Z]+)", e)
    if m and m.group(1) in COLORS:
        r, g, b, a = COLORS[m.group(1)]
        return ("hex", (r, g, b, a))
    m = re.fullmatch(r"\$e\.fromHex\(\"?#?([0-9A-Fa-f]{6,8})\"?\)", e)
    if m:
        return ("hex", hex_rgba("#" + m.group(1)))
    m = re.fullmatch(r"\$e\.transparent\(\s*([\d.]*)\s*\)", e)
    if m:
        f = float(m.group(1)) if m.group(1) else 1.0
        return ("hex", (0, 0, 0, f))
    # new $e(new fi(r,g,b,a))
    m = re.fullmatch(r"new \$e\(new fi\(([\d.]+),([\d.]+),([\d.]+)(?:,([\d.]+))?\)\)", e)
    if m:
        r, g, b = int(float(m.group(1))), int(float(m.group(2))), int(float(m.group(3)))
        a = float(m.group(4)) if m.group(4) else 1.0
        return ("hex", (r, g, b, a))
    # 裸 hex（可能无 #，可能 3/4/6/8 位）
    for pat, base in ((r"#?([0-9A-Fa-f]{8})\b", 8), (r"#?([0-9A-Fa-f]{6})\b", 6)):
        m = re.fullmatch(pat, e)
        if m:
            return ("hex", hex_rgba("#" + m.group(1)))
    m = re.fullmatch(r"#([0-9A-Fa-f]{4})\b", e)   # RGBA 短写法 #000a / #000f
    if m:
        h = "#" + "".join(c * 2 for c in m.group(1))
        return ("hex", hex_rgba(h))
    m = re.fullmatch(r"#([0-9A-Fa-f]{3})\b", e)
    if m:
        return ("hex", hex_rgba(e))
    # 变量：color id / 数字 / rgba 常量
    if e in VAR2ID:
        return ("id", VAR2ID[e])
    if e in RGBA_VAR:
        return ("hex", RGBA_VAR[e])
    if e in ("foreground",):        # 基础前景色（无点号的 base token）
        return ("id", "foreground")
    if e in REG:
        return ("id", e)
    # 函数调用：递归解析第一个能解析出颜色的参数
    m = re.fullmatch(r"([\w$.]+)\((.*)\)$", e, re.S)
    if m:
        fn, args = m.group(1), split_args(m.group(2))
        # op/pv/Ci/DR/DN/D0i 是颜色运算；取其主色参数
        for a in args:
            aa = a.strip()
            # DN(a, b, ...) = 取第一个可用的；try each
            rr = resolve(aa, depth + 1)
            if rr:
                # Ci(x, f) / op / pv 等带因子：若因子是透明度语义则乘 alpha
                if fn == "Ci" and len(args) > 1:
                    try:
                        return transparent(rr, number(args[1].strip()))
                    except ValueError:
                        return None
                return rr
        return None
    return None


def build_anchors(kind):
    anchors = {}
    for cid, v in REG.items():
        d = resolve(v.get(kind))
        if d is not None:
            anchors[cid] = {"type": d[0], "value": d[1]}
            if len(d) > 2:
                anchors[cid]["alpha"] = d[2]
    return anchors


def main():
    use_utf8_console()
    global REG, VAR2ID, NUM, RGBA_VAR
    parser = argparse.ArgumentParser(description="为固定注册表生成深浅色锚点；压缩符号仅支持已验证版本")
    parser.add_argument("--vscode-path")
    parser.add_argument("--registry", type=Path, default=Path(HERE) / "data/registry.json")
    parser.add_argument("--output", type=Path, default=Path(HERE) / "data/anchors.json")
    options = parser.parse_args()
    snapshot = json.loads(options.registry.read_text(encoding="utf-8"))
    source = snapshot["source"]
    if source["commit"] != "07f806f999227108933c2e30515b26eecc1fda74":
        parser.error("锚点解析器仅验证过 VS Code 1.140.0 的固定 commit；请先审查新版本压缩符号和回归用例")
    bundle = Path(find_bundle(options.vscode_path)).read_bytes()
    if hashlib.sha256(bundle).hexdigest() != source["bundleSha256"]:
        parser.error("本机 bundle 与注册表快照不匹配，未写入锚点")
    text = bundle.decode("utf-8")
    REG = snapshot["colors"]
    VAR2ID = {value["var"]: key for key, value in REG.items() if value.get("var")}
    NUM = {match.group(1): float(match.group(2)) for match in re.finditer(r"[,;{}(\s]([\w$]+)=(\.\d+|0|1)\b", text)}
    RGBA_VAR = {match.group(1): (int(float(match.group(2))), int(float(match.group(3))), int(float(match.group(4))), float(match.group(5) or 1))
                for match in re.finditer(r"([\w$]+)=new \$e\(new fi\(([\d.]+),([\d.]+),([\d.]+)(?:,([\d.]+))?\)\)", text)}
    themes = {kind: build_anchors(kind) for kind in ("dark", "light")}
    unresolved = {kind: sorted(set(REG) - set(anchors)) for kind, anchors in themes.items()}
    output = {"source": source, "themes": themes, "unresolved": unresolved}
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for kind, anchors in themes.items():
        print(f"{kind}: 解析 {len(anchors)}/{len(REG)}；其余 {len(unresolved[kind])} 项需显式颜色或派生规则")


if __name__ == "__main__":
    main()
