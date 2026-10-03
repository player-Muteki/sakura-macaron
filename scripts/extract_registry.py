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


def main() -> None:
    parser = argparse.ArgumentParser(description="显式更新固定版本的注册表快照；日常构建不需要 VS Code")
    parser.add_argument("--vscode-path")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data/registry.json")
    options = parser.parse_args()
    bundle = find_bundle(options.vscode_path)
    src = open(bundle, encoding="utf8", errors="ignore").read()
    match = re.search(r"function ([\w$]+)\([^)]*\)\{return [\w$]+\.registerColor\(", src)
    if not match:
        sys.exit("无法识别 registerColor 包装函数；请更新解析器，未写入快照")
    helper = match.group(1)

    registry = {}
    # 有的注册没有赋值给局部变量；变量名可能含 `$`，因此用 [\w$]+
    for m in re.finditer(r"(?<![\w$])(?:([\w$]+)=)?" + re.escape(helper) + r'\("([a-zA-Z0-9_.]+)",', src):
        var, cid = m.group(1), m.group(2)
        args = split_args(src, m.end())
        if not args:
            continue
        raw = args[0]
        entry = {"var": var, "raw": raw, "provenance": "registration"}
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
        registry[cid] = {"var": None, "raw": None, "dark": None, "light": None, "provenance": "css-reference"}

    if not registry:
        sys.exit("注册表为空；未写入快照")
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
    print(f"注册表 {len(registry)} 个颜色 id -> {out}")


if __name__ == "__main__":
    main()
