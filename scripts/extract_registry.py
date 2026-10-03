#!/usr/bin/env python3
"""从 VS Code 的 workbench bundle 中抽取颜色注册表。

输出 build/registry.json：
{
  "<color.id>": {
     "var": "ae",                    # 注册时用的局部变量名
     "dark": "<表达式原文>",
     "light": "<表达式原文>",
     "raw": "<完整默认值参数原文>"
  }
支持三种默认值形态：
  1. {dark: ..., light: ..., hcDark: ..., hcLight: ...}
  2. "sideBar.background"          —— 引用另一个颜色 id
  3. Ci(Po,.15) / DR(x,.2) / t9    —— 变量或表达式
"""
import json
import os
import re
import sys

BUNDLE_CANDIDATES = [
    os.environ.get("VSCODE_PATH", "") + "/out/vs/workbench/workbench.desktop.main.js",
    "/usr/share/code/resources/app/out/vs/workbench/workbench.desktop.main.js",
    "/usr/lib/code/resources/app/out/vs/workbench/workbench.desktop.main.js",
    "/opt/visual-studio-code/resources/app/out/vs/workbench/workbench.desktop.main.js",
    "/Applications/Visual Studio Code.app/Contents/Resources/app/out/vs/workbench/workbench.desktop.main.js",
]


def find_bundle() -> str:
    for c in BUNDLE_CANDIDATES:
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


def main() -> None:
    bundle = find_bundle()
    src = open(bundle, encoding="utf8", errors="ignore").read()
    helper = re.search(r"function (\w+)\([^)]*\)\{return \w+\.registerColor\(", src).group(1)

    registry = {}
    # 有的注册没有赋值给局部变量；变量名可能含 `$`，因此用 [\w$]+
    for m in re.finditer(r"(?:([\w$]+)=)?" + helper + r'\("([a-zA-Z0-9_.]+)",', src):
        var, cid = m.group(1), m.group(2)
        args = split_args(src, m.end())
        if not args:
            continue
        raw = args[0]
        entry = {"var": var, "raw": raw}
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
        registry[cid] = {"var": None, "raw": None, "dark": None, "light": None}

    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "registry.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(registry, open(out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print(f"注册表 {len(registry)} 个颜色 id -> {out}")


if __name__ == "__main__":
    main()
