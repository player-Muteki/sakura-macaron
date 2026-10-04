#!/usr/bin/env python3
"""对比度审计：找出「前景色画在自己背景上」看不清的组合。

按 VS Code 实际绘制的界面层级列出 (前景键, 背景键) 配对，计算 WCAG 对比度，
低于阈值时报告出来。用于人工复核自动补色是否产生可读性问题。

用法：python scripts/check_contrast.py [--threshold 4.5] [--strict] [--json]
"""
import json
import os
import sys
import argparse
from pathlib import Path

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES = os.path.join(HERE, "themes")

# (说明, 前景键, 背景键)
PAIRS = [
    ("活动栏图标", "activityBar.foreground", "activityBar.background"),
    ("活动栏激活项", "activityBar.foreground", "activityBar.activeBackground"),
    ("侧边栏条目", "sideBar.foreground", "sideBar.background"),
    ("侧边栏标题", "sideBarTitle.foreground", "sideBarTitle.background"),
    ("树选中项", "tree.inactiveIndentGuidesStroke", "sideBar.background"),
    ("列表选中文字", "list.activeSelectionForeground", "list.activeSelectionBackground"),
    ("列表悬停文字", "list.hoverForeground", "list.hoverBackground"),
    ("列表过滤命中", "list.highlightForeground", "list.focusBackground"),
    ("编辑器正文", "editor.foreground", "editor.background"),
    ("当前行行号", "editorLineNumber.activeForeground", "editor.background"),
    ("行号", "editorLineNumber.foreground", "editor.background"),
    ("选区文字", "editor.selectionForeground", "editor.selectionBackground"),
    ("查找命中", "editor.findMatchForeground", "editor.findMatchBackground"),
    ("查找命中高亮", "editor.findMatchHighlightForeground", "editor.findMatchHighlightBackground"),
    ("单词高亮", "editor.foreground", "editor.wordHighlightStrongBackground"),
    ("光标", "editorCursor.foreground", "editor.background"),
    ("当前行", "editor.foreground", "editor.lineHighlightBackground"),
    ("括号匹配", "editorBracketMatch.foreground", "editorBracketMatch.background"),
    ("折叠占位符", "editor.foldPlaceholderForeground", "editor.background"),
    ("代码透镜", "editorCodeLens.foreground", "editor.background"),
    ("内联提示", "editorInlayHint.foreground", "editorInlayHint.background"),
    ("占位符文字", "editorGhostText.foreground", "editor.background"),
    ("建议框", "editorSuggestWidget.foreground", "editorSuggestWidget.background"),
    ("悬浮提示", "editorHoverWidget.foreground", "editorHoverWidget.background"),
    ("消息", "notifications.foreground", "notifications.background"),
    ("消息链接", "textLink.foreground", "notifications.background"),
    ("问题面板", "problemsErrorIcon.foreground", "panel.background"),
    ("输出正文", "editor.foreground", "editor.background"),
    ("调试控制台", "debugConsole.sourceForeground", "panel.background"),
    ("终端文字", "terminal.foreground", "terminal.background"),
    ("终端选区", "terminal.selectionForeground", "terminal.selectionBackground"),
    ("状态栏", "statusBar.foreground", "statusBar.background"),
    ("状态栏失焦", "statusBar.foreground", "statusBar.inactiveBackground"),
    ("状态栏调试项", "statusBar.debuggingForeground", "statusBar.debuggingBackground"),
    ("状态栏无文件夹", "statusBar.noFolderForeground", "statusBar.noFolderBackground"),
    ("状态栏离线项", "statusBarItem.offlineForeground", "statusBarItem.offlineBackground"),
    ("活动栏失焦图标", "activityBar.inactiveForeground", "activityBar.background"),
    ("活动栏顶失焦", "activityBarTop.inactiveForeground", "activityBarTop.background"),
    ("输入校验错误", "inputValidation.errorForeground", "inputValidation.errorBackground"),
    ("输入校验警告", "inputValidation.warningForeground", "inputValidation.warningBackground"),
    ("标签页激活", "tab.activeForeground", "tab.activeBackground"),
    ("标签页未激活", "tab.inactiveForeground", "tab.inactiveBackground"),
    ("标签栏底色", "tab.unfocusedActiveForeground", "tab.unfocusedActiveBackground"),
    ("面包屑", "breadcrumb.foreground", "breadcrumb.background"),
    ("标题栏", "titleBar.activeForeground", "titleBar.activeBackground"),
    ("菜单", "menu.foreground", "menu.background"),
    ("菜单选中", "menu.selectionForeground", "menu.selectionBackground"),
    ("快速输入", "input.foreground", "quickInput.background"),
    ("快速输入标题", "quickInput.foreground", "quickInputTitle.background"),
    ("快速输入列表选中", "list.activeSelectionForeground", "quickInput.list.focusBackground"),
    ("下拉框", "dropdown.foreground", "dropdown.background"),
    ("输入框", "input.foreground", "input.background"),
    ("按钮", "button.foreground", "button.background"),
    ("次要按钮", "button.secondaryForeground", "button.secondaryBackground"),
    ("复选框", "checkbox.foreground", "checkbox.background"),
    ("单选框", "radio.activeForeground", "radio.activeBackground"),
    ("徽章", "badge.foreground", "badge.background"),
    ("扩展按钮", "extensionButton.foreground", "extensionButton.background"),
    ("Git 图", "scmGraph.foreground1", "sideBar.background"),
    ("测试通过图标", "testing.iconPassed", "panel.background"),
    ("测试失败图标", "testing.iconFailed.retired", "panel.background"),
    ("Notebook 单元格", "editor.foreground", "notebook.cellEditorBackground"),
    ("Peek 视图", "peekViewResult.lineForeground", "peekViewResult.background"),
    ("Peek 视图标题", "peekViewTitleLabel.foreground", "peekViewTitle.background"),
    ("Chat 输入继承", "input.foreground", "input.background"),
    ("设置项标题", "settings.headerForeground", "editor.background"),
    ("富文本正文", "foreground", "textBlockQuote.background"),
    ("行内代码", "textPreformat.foreground", "textPreformat.background"),
    ("链接", "textLink.foreground", "editor.background"),
    ("Diff 新增", "editor.foreground", "diffEditor.insertedTextBackground"),
    ("Diff 删除", "editor.foreground", "diffEditor.removedTextBackground"),
    ("合并冲突", "mergeEditor.conflict.unhandledFocused.border", "mergeEditor.conflictingLines.background"),
    ("符号图标", "symbolIcon.classForeground", "sideBar.background"),
    ("树形缩进参考线", "tree.indentGuidesStroke", "sideBar.background"),
    ("Markdown 代码块", "editor.foreground", "textCodeBlock.background"),
    ("命令中心", "commandCenter.foreground", "commandCenter.background"),
    ("命令中心调试态", "commandCenter.foreground", "commandCenter.debuggingBackground"),
    ("命令中心调试悬停", "commandCenter.activeForeground", "commandCenter.debuggingBackground"),
]


def parse_hex(h):
    h = h.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "FF"
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)


def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_lum(hexcolor):
    r, g, b, _ = parse_hex(hexcolor)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def composite(fg, bg):
    """把带 alpha 的前景合成到背景上（简单 source-over）"""
    fr, fg_, fb, fa = parse_hex(fg)
    br, bg_, bb, _ = parse_hex(bg)
    a = fa / 255.0
    return "#%02X%02X%02X" % (round(fr * a + br * (1 - a)),
                              round(fg_ * a + bg_ * (1 - a)),
                              round(fb * a + bb * (1 - a)))


def contrast(fg, bg):
    l1, l2 = rel_lum(fg), rel_lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def over_base(hexcolor, base):
    """半透明背景需要先合成到底色上，再算对比度；不透明则原样返回。"""
    if parse_hex(hexcolor)[3] >= 255:
        return hexcolor
    return composite(hexcolor, base)


# 这些界面的底色（用于把半透明高亮合成成实色后再算对比度）
SURFACE_BASE = {
    "editor": "editor.background",
    "terminal": "terminal.background",
    "sideBar": "sideBar.background",
    "panel": "panel.background",
}


def surface_of(bkey):
    head = bkey.split(".")[0]
    return SURFACE_BASE.get(head, "editor.background")


# 刻意保持低对比度的元素（这些不是文字，而是边框/参考线/背景高亮，
# VS Code 官方默认也是同样处理，不应报警）
EXPECTED_LOW = {
    "mergeEditor.conflict.unhandledFocused.border": "装饰性冲突边框；冲突文字另有前景色",
    "tree.inactiveIndentGuidesStroke": "装饰性树缩进线，不承载文字",
    "tree.indentGuidesStroke": "装饰性树缩进线，不承载文字",
}

NON_TEXT = {
    "activityBar.foreground", "activityBar.inactiveForeground", "activityBarTop.inactiveForeground",
    "editorCursor.foreground", "problemsErrorIcon.foreground", "scmGraph.foreground1",
    "testing.iconPassed", "testing.iconFailed.retired", "symbolIcon.classForeground",
    *EXPECTED_LOW,
}


def syntax_surfaces(colors):
    base = colors["editor.background"]
    surfaces = {"editor": base}
    for kind in ("inserted", "removed"):
        line = over_base(colors[f"diffEditor.{kind}LineBackground"], base)
        surfaces[f"diff.{kind}.line"] = line
        surfaces[f"diff.{kind}.text"] = over_base(colors[f"diffEditor.{kind}TextBackground"], line)
    surfaces["selection"] = over_base(colors["editor.selectionBackground"], base)
    return surfaces


def audit(theme, threshold=4.5):
    colors = theme["colors"]
    report = {"checked": {"ui": 0, "textmate": 0, "semantic": 0}, "failures": [], "exemptions": [], "skipped": []}

    def measure(category, label, foreground, background, minimum, exemption=None):
        effective = over_base(foreground, background)
        ratio = contrast(effective, background)
        report["checked"][category] += 1
        if ratio < minimum:
            row = {"category": category, "label": label, "foreground": foreground,
                   "background": background, "ratio": round(ratio, 4), "minimum": minimum}
            if exemption:
                row["reason"] = exemption
                report["exemptions"].append(row)
            else:
                report["failures"].append(row)

    for label, foreground, background in PAIRS:
        base_key = surface_of(background)
        missing = list(dict.fromkeys(key for key in (foreground, background, base_key) if key not in colors))
        if missing:
            report["skipped"].append({"label": label, "missing": missing})
            continue
        base = colors[base_key]
        minimum = 3.0 if foreground in NON_TEXT else threshold
        measure("ui", f"{label}: {foreground}", colors[foreground], over_base(colors[background], base), minimum, EXPECTED_LOW.get(foreground))

    required = ["editor.background", "editor.foreground", "editor.selectionBackground",
                "diffEditor.insertedLineBackground", "diffEditor.insertedTextBackground",
                "diffEditor.removedLineBackground", "diffEditor.removedTextBackground"]
    missing = [key for key in required if key not in colors]
    if missing:
        report["skipped"].append({"label": "语法背景", "missing": missing})
        return report
    surfaces = syntax_surfaces(colors)
    for category, rules in (("textmate", theme["tokenColors"]), ("semantic", theme["semanticTokenColors"].items())):
        for index, rule in enumerate(rules):
            if category == "textmate":
                settings = rule["settings"]
                label = f"{index}: {rule['scope']}"
            else:
                label, value = rule
                settings = {"foreground": value} if isinstance(value, str) else value
            if "foreground" not in settings:
                report["skipped"].append({"label": f"{category}.{label}", "reason": "仅含字体样式，实际前景取决于语言与其它规则"})
                continue
            for surface, background in surfaces.items():
                foreground = settings["foreground"]
                if "background" in settings:
                    background = over_base(settings["background"], background)
                if surface == "selection":
                    foreground = colors.get("editor.selectionForeground", foreground)
                measure(category, f"{label} on {surface}", foreground, background, threshold)
    return report


def main():
    parser = argparse.ArgumentParser(description="静态对比度审计：正文 4.5:1、图标 3:1；不是完整 WCAG 认证")
    parser.add_argument("--threshold", type=float, default=4.5)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--theme-dir", type=Path, default=Path(THEMES))
    options = parser.parse_args()
    if not 1 <= options.threshold <= 21:
        parser.error("threshold 必须在 1 到 21 之间")
    reports = {}
    for kind, fname in (("dark", "sakura-macaron-dark.json"),
                        ("light", "sakura-macaron-light.json")):
        theme = json.loads((options.theme_dir / fname).read_text(encoding="utf-8"))
        reports[kind] = audit(theme, options.threshold)
    if options.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for kind, report in reports.items():
            print(f"=== {kind}: 检查 {report['checked']}；失败 {len(report['failures'])}；装饰豁免 {len(report['exemptions'])}；未测 {len(report['skipped'])} ===")
            for row in report["failures"]:
                print(f"  {row['ratio']:.2f}:1 < {row['minimum']}:1  {row['label']}")
            for row in report["skipped"]:
                print(f"  未测: {row}")
            for row in report["exemptions"]:
                print(f"  豁免: {row['label']} — {row['reason']}")
    missing = any(row.get("missing") for report in reports.values() for row in report["skipped"])
    return int(options.strict and (missing or any(report["failures"] for report in reports.values())))


if __name__ == "__main__":
    sys.exit(main())
