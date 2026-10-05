#!/usr/bin/env python3
"""从本机 VS Code bundle 注册调用和过滤后的 CSS 引用抽取候选颜色快照。

默认输出 data/registry.json，包含 source 元数据和带 provenance 的 colors。
单独探索时应显式指定 --output；维护固定基准请使用 update_registry.py。
"""
import json
import os
import re
import sys
import argparse
import hashlib
from pathlib import Path
from utf8_console import use_utf8_console

BUNDLE_CANDIDATES = [
    os.environ.get("VSCODE_PATH", "") + "/out/vs/workbench/workbench.desktop.main.js",
    "/usr/share/code/resources/app/out/vs/workbench/workbench.desktop.main.js",
    "/usr/lib/code/resources/app/out/vs/workbench/workbench.desktop.main.js",
    "/opt/visual-studio-code/resources/app/out/vs/workbench/workbench.desktop.main.js",
    "/Applications/Visual Studio Code.app/Contents/Resources/app/out/vs/workbench/workbench.desktop.main.js",
]


def find_bundle(root=None) -> str:
    explicit = root or os.environ.get("VSCODE_PATH")
    candidates = [str(Path(explicit) / "out/vs/workbench/workbench.desktop.main.js")] if explicit else BUNDLE_CANDIDATES[1:]
    if not explicit:
        for variable in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            if os.environ.get(variable):
                base = Path(os.environ[variable])
                for suffix in ("Programs/Microsoft VS Code/resources/app", "Microsoft VS Code/resources/app"):
                    candidates.append(str(base / suffix / "out/vs/workbench/workbench.desktop.main.js"))
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    sys.exit("找不到 VS Code bundle，请设置 $VSCODE_PATH")


def split_args(src: str, start: int) -> list[str]:
    """从 start 开始按顶层逗号切分参数（正确处理括号/引号）。"""
    args, depth, cur, i, n = [], 0, [], start, len(src)
    quote = None
    while i < n:
        ch = src[i]
        if quote:
            cur.append(ch)
            if ch == "\\":
                if i + 1 < n:
                    cur.append(src[i + 1])
                    i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            if depth == 0:
                break
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    tail = "".join(cur).strip()
    if tail:
        args.append(tail)
    return args


def parse_obj(expr: str) -> dict:
    """把 {dark: X, light: Y, ...} 解析成 key -> 表达式原文。"""
    assert expr.startswith("{")
    inner = expr[1:-1] if expr.endswith("}") else expr[1:]
    out = {}
    for part in split_args(inner, 0):
        m = re.match(r"^(\w+)\s*:\s*(.*)$", part, re.S)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


HELPER_RE = re.compile(r"function ([\w$]+)\([^)]*\)\{return [\w$]+\.registerColor\(")

# 各版本的压缩器对同一个 registerColor 会留下不同形状的调用点：
# 本模块内直接 `wrapper("id", ...)`，跨模块则走导出别名 `(0, MOD.ALIAS)("id", ...)`。
# 只扫前者会在旧版 bundle 上静默漏掉大半注册，因此两种形状都要认。
CALL_FORMS_TMPL = [
    r"(?<![\w$])(?:[\w$]+=)?{name}\(",
    r"(?<![\w$])(?:[\w$]+=)?\(0,\s*[\w$]+\.{name}\)\(",
]

# 1.80 已有 669 个注册色；低于此量级说明调用点形状没认全，而不是 VS Code 真的少了键
MIN_REGISTRATION_IDS = 600

# 真实注册的参数总量很小；给扫描设上限，既避免无关同名调用把参数扫到文件末尾，
# 也让"扫不到闭合括号"的调用自然落选
ARGUMENT_SCAN_LIMIT = 4000

# 只在包装函数体结束处取紧跟其后的导出绑定（`…}e.$Yu=g;`）：压缩后的短名会在其它模块里
# 被反复复用，按名字或按窗口搜别名会把无关函数当成别名，既拖慢扫描又注入垃圾键
ALIAS_PROXIMITY = 80


def export_aliases(src: str, body_end: int, helper: str) -> list[str]:
    """包装函数定义之后紧跟的导出名；没有导出绑定时返回空。"""
    match = re.match(r"[\w$]+\.([\w$]+)\s*=\s*" + re.escape(helper) + r"(?![\w$(=])",
                     src[body_end:body_end + ALIAS_PROXIMITY])
    return [match.group(1)] if match else []


def is_registration_call(raw: str) -> bool:
    """把真实注册和同名压缩函数的无关调用分开。

    默认值可以是 `{dark:…}` 对象、压缩后的变量名，也可以是 `"#00000000"` 这样的
    字面量，所以这里只排除明显不是颜色注册的空参数调用。
    """
    return raw not in ("", "void 0", "undefined")


def call_pattern(names: list[str]) -> re.Pattern:
    """把各调用形状合成一个模式；分支必须整体括起来，否则后缀只绑到最后一个分支。"""
    branches = "|".join(
        tmpl.format(name=re.escape(n)) for n in names for tmpl in CALL_FORMS_TMPL)
    return re.compile(r"(" + branches + r")\s*\"([a-zA-Z][a-zA-Z0-9_.]*)\"\s*,")


def parse_registrations(src: str) -> dict | None:
    """扫描 bundle 里所有 registerColor 调用点，返回 cid -> 注册条目。"""
    definitions = list(HELPER_RE.finditer(src))
    if not definitions:
        return None
    names: list[str] = []
    for definition in definitions:
        helper = definition.group(1)
        if helper not in names:
            names.append(helper)
        brace = src.find("}", definition.start())
        if brace < 0:
            continue
        for alias in export_aliases(src, brace + 1, helper):
            if alias not in names:
                names.append(alias)
    call_re = call_pattern(names)

    registry: dict[str, dict] = {}
    # 有的注册没有赋值给局部变量；变量名可能含 `$`，因此用 [\w$]+
    for m in call_re.finditer(src):
        var = re.match(r"([\w$]+)=", m.group(1))
        cid = m.group(2)
        args = split_args(src[m.end():m.end() + ARGUMENT_SCAN_LIMIT], 0)
        if not args or not is_registration_call(args[0]):
            continue
        raw = args[0]
        entry = {"var": var.group(1) if var else None, "raw": raw, "provenance": "registration"}
        if raw.startswith("{"):
            obj = parse_obj(raw)
            entry["dark"] = obj.get("dark") or obj.get("light") or obj.get("hcDark") or ""
            entry["light"] = obj.get("light") or obj.get("dark") or obj.get("hcLight") or ""
            entry["dark_hc"] = obj.get("hcDark", "")
            entry["light_hc"] = obj.get("hcLight", "")
        else:
            entry["dark"] = raw
            entry["light"] = raw
        registry[cid] = entry
    return registry


def main() -> None:
    use_utf8_console()
    parser = argparse.ArgumentParser(description="显式更新固定版本的注册表快照；日常构建不需要 VS Code")
    parser.add_argument("--vscode-path")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data/registry.json")
    parser.add_argument("--allow-low-yield", action="store_true",
                        help="即使注册色数量异常偏低也写出快照，仅供探索，不要用于固定基准")
    options = parser.parse_args()
    bundle = find_bundle(options.vscode_path)
    src = open(bundle, encoding="utf8", errors="ignore").read()
    registry = parse_registrations(src)
    if registry is None:
        sys.exit("无法识别 registerColor 包装函数；请更新解析器，未写入快照")

    # workbench CSS 里引用的 --vscode-* 变量（补充注册表未覆盖到的键）
    css_ids = set()
    out_dir = os.path.dirname(os.path.dirname(bundle))   # .../out/vs
    for root, _dirs, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".css"):
                css = open(os.path.join(root, f), encoding="utf8", errors="ignore").read()
                for mm in re.finditer(r"--vscode-([a-zA-Z0-9_.-]+)", css):
                    css_ids.add(mm.group(1).replace("-", "."))

    # 以下是 CSS 变量里的非颜色 token（字号/圆角/阴影/图标字体/布局尺寸），
    # 它们通过 configurationDefaults 或图标字体设置，不属于 colors 键集
    non_color = [
        r"^(spacing|fontSize|fontWeight|bodyFontSize|codiconFontSize|agents\.(fontSize|fontWeight|layout|gradient))\.",
        r"\.font\.(family|size)", r"\.fontFamily", r"\.fontSize", r"\.lineHeight$",
        r"\.fontFeatureSettings$", r"^(cornerRadius|shadow)\.",
        r"^chat\.font\.", r"^chat\.persistent\.",
        r"^hover\.(maxWidth|sourceWhiteSpace|whiteSpace)$",
        r"^icon\..*\.content$", r"^icon\..*\.font\.family$",
        r"\.(height|width)$", r"\.margin\.left$", r"\.scrollableWidth$",
        r"\.foldingOpacityTransition$", r"\.auto\.timeout$", r"\.min\.width$",
        r"\.for\.twistie$", r"\.colorDecorator(Margin|Width)$",
        r"^inline\.chat\.affordance\.height$",
        r"\.editorFontFamily(Default)?$", r"^sash\.(hover\.)?size$",
    ]
    css_ids = {c for c in css_ids
               if "." in c and not any(re.search(p, c) for p in non_color)}

    for cid in sorted(css_ids - set(registry)):
        registry[cid] = {"var": None, "raw": None, "dark": None, "light": None, "provenance": "css-reference"}

    if not registry:
        sys.exit("注册表为空；未写入快照")
    counted = sum(1 for e in registry.values() if e["provenance"] == "registration")
    if counted < MIN_REGISTRATION_IDS and not options.allow_low_yield:
        sys.exit(f"只识别出 {counted} 个注册色，低于 {MIN_REGISTRATION_IDS} 的量级下限；"
                 f"该版本 bundle 的调用形状很可能没认全，未写入快照。"
                 f"确认无误后用 --allow-low-yield 显式放行（仅供探索）")
    app = Path(bundle).parents[3]
    package = json.loads((app / "package.json").read_text(encoding="utf-8"))
    product = json.loads((app / "product.json").read_text(encoding="utf-8"))
    css_hash = hashlib.sha256()
    for css in sorted((app / "out/vs").rglob("*.css")):
        css_hash.update(css.relative_to(app).as_posix().encode())
        css_hash.update(css.read_bytes())
    snapshot = {"source": {
        "version": package["version"], "commit": product["commit"],
        "bundleSha256": hashlib.sha256(Path(bundle).read_bytes()).hexdigest(),
        "cssSha256": css_hash.hexdigest(),
        "method": "registerColor calls plus filtered CSS color references",
    }, "colors": dict(sorted(registry.items()))}
    out = options.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"注册表 {len(registry)} 个颜色 id"
          f"（registration {counted}，css-reference {len(registry) - counted}）-> {out}")


if __name__ == "__main__":
    main()
