#!/usr/bin/env python3
"""Sakura Macaron 补色引擎（第一部分：锚点解析）。

给定 VS Code 注册表和现有主题，为每个未定义的 color id 推导一个主题一致的色值：
  1. 若默认表达式能归约为「另一个 color id」→ 直接取该 id 在本主题中的值（最可靠，语义 100% 保持）
  2. 若能归约为 hex → 用 Lab 空间最近邻映射到本主题调色板（保留红/绿/蓝等语义色系）
  3. 保留 alpha（透明度）信息

输出 build/anchors.json: {id: {"type":"id"|"hex", "value":..., "alpha":float?}}
"""
import json
import os
import re
import colorsys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = None
for c in [
    os.environ.get("VSCODE_PATH", "") + "/out/vs/workbench/workbench.desktop.main.js",
    "/usr/share/code/resources/app/out/vs/workbench/workbench.desktop.main.js",
]:
    if c and os.path.isfile(c):
        BUNDLE = c
        break

REG = json.load(open(os.path.join(HERE, "build/registry.json")))
SRC = open(BUNDLE, encoding="utf8", errors="ignore").read()

# ---- 变量环境 ----------------------------------------------------------
# ae() 注册的 color id
VAR2ID = {v["var"]: cid for cid, v in REG.items() if v.get("var")}
# 形如 `X=.4` 的数值（透明度因子）
NUM = {}
for m in re.finditer(r"[,;{}(\s]([\w$]+)=(\.\d+|0|1)\b", SRC):
    NUM[m.group(1)] = float(m.group(2))
# Color 类常量（$e = Colors class）
COLORS = {
    "white": (255, 255, 255, 1.0), "black": (0, 0, 0, 1.0),
    "red": (255, 0, 0, 1.0), "blue": (0, 0, 255, 1.0),
    "green": (0, 255, 0, 1.0), "cyan": (0, 255, 255, 1.0),
    "magenta": (255, 0, 255, 1.0), "yellow": (255, 255, 0, 1.0),
}
# `new $e(new fi(r,g,b,a))` 形式的颜色常量
RGBA_VAR = {}
for m in re.finditer(r"([\w$]+)=new \$e\(new fi\(([\d.]+),([\d.]+),([\d.]+)(?:,([\d.]+))?\)\)", SRC):
    r, g, b = int(float(m.group(2))), int(float(m.group(3))), int(float(m.group(4)))
    a = float(m.group(5)) if m.group(5) else 1.0
    RGBA_VAR[m.group(1)] = (r, g, b, a)


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
    out, d, cur, q = [], 0, [], None
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur.append(ch)
        elif ch in "([{":
            d += 1
            cur.append(ch)
        elif ch in ")]}":
            d -= 1
            cur.append(ch)
        elif ch == "," and d == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur).strip())
    return out


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
            f = NUM.get(arg, float(arg))
        except ValueError:
            f = 1.0
        if op == "transparent" and base[0] == "hex":
            r, g, b, a = base[1]
            return ("hex", (r, g, b, a * f))
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
    if is_color_id(e):
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
                if fn == "Ci" and rr[0] == "hex" and len(args) > 1:
                    f = NUM.get(split_args(args[1].strip())[0] if args[1].strip() not in NUM else args[1].strip(), None)
                    if f is None:
                        try:
                            f = NUM.get(args[1].strip(), float(args[1].strip()))
                        except ValueError:
                            f = None
                    if f is not None:
                        r, g, b, al = rr[1]
                        return ("hex", (r, g, b, al * f))
                return rr
        return None
    return None


def build_anchors():
    anchors = {}
    for cid, v in REG.items():
        d = resolve(v.get("dark"))
        if d is None:
            d = resolve(v.get("light"))
        if d is not None:
            anchors[cid] = {"type": d[0], "value": d[1]}
    return anchors


if __name__ == "__main__":
    anchors = build_anchors()
    json.dump(anchors, open(os.path.join(HERE, "build/anchors.json"), "w"), indent=1)
    n_id = sum(1 for a in anchors.values() if a["type"] == "id")
    n_hex = sum(1 for a in anchors.values() if a["type"] == "hex")
    print(f"锚点解析成功 {len(anchors)}/{len(REG)}  (id 引用 {n_id}, hex {n_hex})")
    unresolved = sorted(set(REG) - set(anchors))
    print(f"未解析 {len(unresolved)}:")
    for u in unresolved[:200]:
        print("   ", u, "=", REG[u].get("dark"))
