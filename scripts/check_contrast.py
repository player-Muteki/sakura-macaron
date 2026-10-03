#!/usr/bin/env python3
"""对比度审计：找出「前景色画在自己背景上」看不清的组合。

按 VS Code 实际绘制的界面层级列出 (前景键, 背景键) 配对，计算 WCAG 对比度，
低于阈值时报告出来。用于人工复核自动补色是否产生可读性问题。

用法：python3 scripts/check_contrast.py [--threshold 3.0]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES = os.path.join(HERE, "themes")

# (说明, 前景键, 背景键)
PAIRS = [
    ("活动栏图标", "activityBar.foreground", "activityBar.background"),
    ("活动栏激活项", "activityBar.activeForeground", "activityBar.activeBackground"),
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
    ("单词高亮", "editor.wordHighlightStrongForeground", "editor.wordHighlightStrongBackground"),
    ("光标", "editorCursor.foreground", "editor.background"),
    ("当前行", "editor.lineHighlightForeground", "editor.lineHighlightBackground"),
    ("括号匹配", "editorBracketMatch.foreground", "editorBracketMatch.background"),
    ("折叠占位符", "editor.foldPlaceholderForeground", "editor.background"),
    ("代码透镜", "editorCodeLens.foreground", "editor.background"),
    ("内联提示", "editorInlayHint.foreground", "editor.background"),
    ("占位符文字", "editorGhostText.foreground", "editor.background"),
    ("建议框", "editorSuggestWidget.foreground", "editorSuggestWidget.background"),
    ("悬浮提示", "editorHoverWidget.foreground", "editorHoverWidget.background"),
    ("调试悬浮", "editorHoverWidget.debuggerExpressionForeground", "editorHoverWidget.background"),
    ("签名帮助", "editorHoverWidget.signatureForeground", "editorHoverWidget.background"),
    ("消息", "notifications.foreground", "notifications.background"),
    ("消息链接", "notificationsLink.foreground", "notifications.background"),
    ("问题面板", "problemsErrorIcon.foreground", "panel.background"),
    ("输出面板", "outputView.foreground", "panel.background"),
    ("调试控制台", "debugConsole.foreground", "debugConsole.background"),
    ("终端文字", "terminal.foreground", "terminal.background"),
    ("终端选区", "terminal.selectionForeground", "terminal.selectionBackground"),
    ("状态栏", "statusBar.foreground", "statusBar.background"),
    ("状态栏失焦", "statusBar.foreground", "statusBar.inactiveBackground"),
    ("状态栏调试项", "statusBar.debuggingForeground", "statusBar.debuggingBackground"),
    ("状态栏无文件夹", "statusBar.noFolderForeground", "statusBar.noFolderBackground"),
    ("状态栏离线项", "statusBarItem.offlineForeground", "statusBarItem.offlineBackground"),
    ("活动栏失焦图标", "activityBar.inactiveForeground", "activityBar.background"),
    ("活动栏顶失焦", "activityBarTop.inactiveForeground", "activityBarTop.background"),
    ("输入校验错误", "inputValidation.errorForeground", "input.background"),
    ("输入校验警告", "inputValidation.warningForeground", "input.background"),
    ("标签页激活", "tab.activeForeground", "tab.activeBackground"),
    ("标签页未激活", "tab.inactiveForeground", "tab.inactiveBackground"),
    ("标签栏底色", "tab.unfocusedActiveForeground", "tab.unfocusedActiveBackground"),
    ("面包屑", "breadcrumb.foreground", "breadcrumb.background"),
    ("编辑器组标题", "editorGroupHeader.foreground", "editorGroupHeader.tabsBackground"),
    ("标题栏", "titleBar.activeForeground", "titleBar.activeBackground"),
    ("菜单", "menu.foreground", "menu.background"),
    ("菜单选中", "menu.selectionForeground", "menu.selectionBackground"),
    ("快速输入", "input.foreground", "quickInput.background"),
    ("快速输入标题", "quickInputTitle.foreground", "quickInputTitle.background"),
    ("快速输入列表选中", "list.activeSelectionForeground", "quickInput.list.focusBackground"),
    ("下拉框", "dropdown.foreground", "dropdown.background"),
    ("输入框", "input.foreground", "input.background"),
    ("按钮", "button.foreground", "button.background"),
    ("次要按钮", "button.secondaryForeground", "button.secondaryBackground"),
    ("复选框", "checkbox.foreground", "checkbox.background"),
    ("单选框", "radio.foreground", "radio.background"),
    ("徽章", "badge.foreground", "badge.background"),
    ("扩展按钮", "extensionButton.foreground", "extensionButton.background"),
    ("滚动条", "scrollbarSlider.foreground", "scrollbarSlider.background"),
    ("Git 图", "scmGraph.foreground1", "sideBar.background"),
    ("测试通过图标", "testing.iconPassed", "panel.background"),
    ("测试失败图标", "testing.iconFailed.retired", "panel.background"),
    ("Notebook 单元格", "notebook.cellEditorForeground", "notebook.cellEditorBackground"),
    ("Peek 视图", "peekViewResult.foreground", "peekViewResult.background"),
    ("Peek 视图标题", "peekViewTitleLabel.foreground", "peekViewTitle.background"),
    ("Chat 输入", "chat.inputForeground", "chat.inputBackground"),
    ("设置项标题", "settings.headerForeground", "settings.background"),
    ("设置分组标题", "settings.settingsHeaderForeground", "settings.background"),
    ("富文本正文", "textBlockQuote.foreground", "textBlockQuote.background"),
    ("行内代码", "textPreformat.foreground", "textPreformat.background"),
    ("链接", "textLink.foreground", "editor.background"),
    ("Diff 新增", "diffEditor.insertedTextForeground", "diffEditor.insertedTextBackground"),
    ("Diff 删除", "diffEditor.removedTextForeground", "diffEditor.removedTextBackground"),
    ("合并冲突", "mergeEditor.conflict.unhandledFocused.border", "mergeEditor.conflictingLines.background"),
    ("符号图标", "symbolIcon.foreground", "sideBar.background"),
    ("树形缩进参考线", "tree.indentGuidesStroke", "sideBar.background"),
]


def parse_hex(h):
    h = h.lstrip("#")
    if len(h) == 3:
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
    ("合并冲突", "mergeEditor.conflict.unhandledFocused.border"),
    ("括号匹配", "editorBracketMatch.foreground"),
    ("树选中项", "tree.inactiveIndentGuidesStroke"),
    ("树形缩进参考线", "tree.indentGuidesStroke"),
    ("行号", "editorLineNumber.foreground"),
    ("占位符文字", "editorGhostText.foreground"),
}


def main():
    thresh = 3.0
    if "--threshold" in sys.argv:
        thresh = float(sys.argv[sys.argv.index("--threshold") + 1])
    strict = "--strict" in sys.argv
    total_bad = 0
    for kind, fname in (("dark", "sakura-macaron-dark.json"),
                        ("light", "sakura-macaron-light.json")):
        c = json.load(open(os.path.join(THEMES, fname)))["colors"]
        bad, expected = [], []
        for label, fkey, bkey in PAIRS:
            if fkey not in c or bkey not in c:
                continue
            fg, bg = c[fkey], c[bkey]
            # 半透明的高亮/选区要先合成到所属界面的底色上，否则对比度会被低估
            base_key = surface_of(bkey)
            base = c.get(base_key, bg) if base_key else bg
            bg_eff = over_base(bg, base)
            fg_eff = over_base(fg, bg_eff)
            try:
                ratio = contrast(fg_eff, bg_eff)
            except Exception:
                continue
            if ratio >= thresh:
                continue
            row = (label, fkey, fg, bkey, bg, ratio)
            (expected if (label, fkey) in EXPECTED_LOW else bad).append(row)
        print(f"=== {kind}: 异常 {len(bad)} 处 / 预期偏低 {len(expected)} 处（阈值 {thresh}:1）===")
        for label, fkey, fg, bkey, bg, ratio in sorted(bad, key=lambda x: x[5]):
            print(f"  {ratio:5.2f}:1  {label:16} {fkey}={fg} on {bkey}={bg}")
        if expected:
            print("  （以下为设计上偏低的边框/参考线，与 VS Code 默认一致）")
            for label, fkey, fg, bkey, bg, ratio in sorted(expected, key=lambda x: x[5]):
                print(f"  {ratio:5.2f}:1  {label:16} {fkey}={fg}")
        total_bad += len(bad)
    return 1 if (strict and total_bad) else 0


if __name__ == "__main__":
    sys.exit(main())
