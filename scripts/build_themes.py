#!/usr/bin/env python3
"""Sakura Macaron 主题生成器。

流程：
  1. 读取 VS Code 颜色注册表（scripts/extract_registry.py 产出）与默认表达式锚点
     （scripts/derive_colors.py 产出）。
  2. 对每个注册的颜色 id 求出主题色值，优先级：
       a. 主题中已显式定义的值            （尊重人工设计）
       b. 失效键迁移表 MIGRATE            （tabs.* -> tab.* 等）
       c. 兄弟键派生表 SIBLING            （默认值为 null 的键）
       d. 默认表达式的 id 引用            （语义 100% 保持）
       e. 默认表达式的 hex -> Lab 最近邻映射到本主题调色板
       f. 人工覆盖表 OVERRIDE            （少量需要手调的键）
  3. 保证深浅两套主题键集完全一致（单侧独有的键自动派生）。
  4. 校验所有色值为合法 hex，输出到 themes/。

用法：python3 scripts/build_themes.py [--check]
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES = os.path.join(HERE, "themes")
BUILD = os.path.join(HERE, "build")

REG = json.load(open(os.path.join(BUILD, "registry.json")))
ANCH = json.load(open(os.path.join(BUILD, "anchors.json")))
DARK_PATH = os.path.join(THEMES, "sakura-macaron-dark.json")
LIGHT_PATH = os.path.join(THEMES, "sakura-macaron-light.json")

# --------------------------------------------------------------------------
# 颜色工具
# --------------------------------------------------------------------------

def parse_hex(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h += "FF"
    if len(h) != 8:
        raise ValueError(h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)


def to_hex(r, g, b, a):
    return "#%02X%02X%02X%02X" % (r, g, b, a)


def with_alpha(h, factor):
    r, g, b, a = parse_hex(h)
    return to_hex(r, g, b, max(0, min(255, round(a * factor))))


def mix(h1, h2, t):
    r1, g1, b1, a1 = parse_hex(h1)
    r2, g2, b2, a2 = parse_hex(h2)
    return to_hex(round(r1 + (r2 - r1) * t), round(g1 + (g2 - g1) * t),
                  round(b1 + (b2 - b1) * t), round(a1 + (a2 - a1) * t))


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb_to_hsl(r, g, b):
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == rf:
        h = ((gf - bf) / d) % 6
    elif mx == gf:
        h = (bf - rf) / d + 2
    else:
        h = (rf - gf) / d + 4
    return h * 60.0, s, l


def _hue_dist(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


class Palette:
    """把颜色映射到主题调色板中最接近的色值。

    以色相为主、明度/饱和度为辅：这样 VS Code 默认的纯红/纯绿/纯紫会被映射到
    主题里「同色相」的颜色，而不是被明度接近的灰色抢走（纯 Lab 距离会出现这种漂移）。
    无彩色（灰）锚点则只按明度匹配。
    """

    HUE_W = 12.0
    SAT_W = 1.5
    LIGHT_W = 1.0
    GRAY_SAT = 0.18

    def __init__(self, colors):
        seen, items = set(), []
        for h in colors:
            if not isinstance(h, str) or not h.startswith("#"):
                continue
            key = h.upper()
            if key in seen:
                continue
            seen.add(key)
            r, g, b, a = parse_hex(h)
            if a == 0:
                continue
            hh, ss, ll = _rgb_to_hsl(r, g, b)
            items.append((h, hh, ss, ll))
        self.items = items

    def nearest(self, hexcolor):
        r, g, b, a = parse_hex(hexcolor)
        th, ts, tl = _rgb_to_hsl(r, g, b)
        gray_anchor = ts < self.GRAY_SAT
        best, bestscore = None, None
        for h, hh, ss, ll in self.items:
            if gray_anchor:
                # 锚点本身是灰阶：只比明度
                score = self.LIGHT_W * (ll - tl) ** 2
            else:
                # 锚点有彩色：色相必须占主导，灰候选要为此付出高额代价，
                # 否则任何灰色都会因为明度接近而抢走本该属于蓝/绿/紫的锚点。
                hd = _hue_dist(th, hh) / 180.0
                sd = (ss - ts) / max(ts, 1e-6)
                if ss < self.GRAY_SAT:
                    hd = max(hd, 1.0)          # 灰候选色相无意义，视为最大偏差
                    sd = max(sd, 1.0)
                score = (self.HUE_W * hd ** 2
                         + self.SAT_W * min(sd, 2.0) ** 2
                         + self.LIGHT_W * (ll - tl) ** 2)
            if bestscore is None or score < bestscore:
                best, bestscore = h, score
        return best


# --------------------------------------------------------------------------
# 失效键迁移：老名字 -> 现代等价键（值为老键已设计的色值）
# --------------------------------------------------------------------------
MIGRATE = {
    # tabs.* (VS Code 1.5x) -> tab.* / modernTab.*
    "tabs.activeBackground": "tab.activeBackground",
    "tabs.activeBorder": "tab.activeBorder",
    "tabs.activeForeground": "tab.activeForeground",
    "tabs.border": "tab.border",
    "tabs.hoverBackground": "tab.hoverBackground",
    "tabs.hoverBorder": "tab.hoverBorder",
    "tabs.hoverForeground": "tab.hoverForeground",
    "tabs.inactiveBackground": "tab.inactiveBackground",
    "tabs.inactiveForeground": "tab.inactiveForeground",
    "tabs.topActiveBorder": "tab.activeBorderTop",
    "tabs.topBorder": "tab.border",
    "tabs.unfocusedActiveBackground": "tab.unfocusedActiveBackground",
    "tabs.unfocusedActiveBorder": "tab.unfocusedActiveBorder",
    "tabs.unfocusedActiveForeground": "tab.unfocusedActiveForeground",
    "tabs.unfocusedHoverBackground": "tab.unfocusedHoverBackground",
    "tabs.unfocusedInactiveBackground": "tab.unfocusedInactiveBackground",
    "tabs.unfocusedInactiveForeground": "tab.unfocusedInactiveForeground",
    # 单点笔误 / 旧名
    "symbolIcon.constructorsForeground": "symbolIcon.constructorForeground",
    "tab.activeBorderBottom": "tab.activeBorderTop",
    "debugConsoleInputBorder.foreground": "debugConsoleInputBorder",
    "debugConsole.background": "debugConsole",
    "editorHoverWidget.statusBarBorder": "editorHoverWidget.statusBarBackground",
    "quickInputSelection.background": "quickInput.list.focusBackground",
    "problemsErrorDecoration.rangeBackground": "problemsErrorDecoration",
    "problemsWarningDecoration.rangeBackground": "problemsWarningDecoration",
    "problemsInfoDecoration.rangeBackground": "problemsInfoDecoration",
    "process.border": "process",
    "ports.iconRaiiProcessForeground": "ports.iconRunningProcessForeground",
    "ports.iconUnrunningProcessForeground": "ports.iconStoppedProcessForeground",
    "testing.errorForeground": "list.errorForeground",
    "diffEditorOverview.border": "diffEditorOverview.border",
    "gitLFSDeletedResourceForeground": "gitDecoration.deletedResourceForeground",
    "gitLFSModifiedResourceForeground": "gitDecoration.modifiedResourceForeground",
    "statusBarItem.activeForeground": "statusBarItem.hoverForeground",
    # merge.* / merge.editorOverview.* 只删除不迁移：老的 merge 配色是按 2020 年的
    # merge UI 设计的，颜色类型（border/header/content）与现代 mergeEditor.* 不对应，
    # 直接搬会把边框色塞进背景槽位。现代键交给默认值锚点推导（会自动得到正确的淡色底色）。
    # gitDecoration 老式 hover 背景同理（现代用 foreground 表达）
    "agentsGradient.tintColor": "agents.background",
}

# --------------------------------------------------------------------------
# 语义族映射：Diff/Merge/Git/Testing 这类“有语义”的颜色不按色相最近邻，
# 而是直接对齐主题已有的 diff 调色板，保证 新增=绿 / 删除=红 与侧边栏一致。
# --------------------------------------------------------------------------
SEMANTIC = {
    # 新增 / 插入（对齐 diffEditor.insertedLine*，这类键不会自身落入前缀规则）
    "inserted": ("diffEditor.insertedLineBackground", "diffEditor.insertedTextBorder"),
    # 删除 / 移除
    "removed": ("diffEditor.removedLineBackground", "diffEditor.removedTextBorder"),
    # 修改 / 变更
    "modified": ("editorGutter.modifiedBackground", "editorGutter.modifiedBackground"),
}

# 需要按语义对齐的键前缀 -> 族
SEMANTIC_PREFIX = {
    "mergeEditor.change.": "inserted",
    "mergeEditor.changeBase.": "modified",
    "mergeEditor.conflict.input1.": "modified",
    "mergeEditor.conflict.input2.": "modified",
    "diffEditorOverview.inserted": "inserted",
    "diffEditorOverview.removed": "removed",
    "diffEditorOverview.modified": "modified",
    "diffEditorGutter.inserted": "inserted",
    "diffEditorGutter.removed": "removed",
    "testing.covered": "inserted",
    "testing.message.error": "removed",
    "testing.iconErrored": "removed",
    "testing.iconFailed": "removed",
    "scmGraph.historyItemHoverAdditions": "inserted",
    "scmGraph.historyItemHoverDeletions": "removed",
    "agentsMobileDiff.added": "inserted",
    "agentsMobileDiff.deleted": "removed",
    "agentsMobileDiff.modified": "modified",
}


def semantic_family(key):
    for pfx, fam in SEMANTIC_PREFIX.items():
        if key.startswith(pfx):
            return fam
    return None

# --------------------------------------------------------------------------
# 兄弟键派生：默认值为 null 的键从哪个已存在的键派生
#   (源键, alpha 系数)
# --------------------------------------------------------------------------
def _sib(src, alpha=1.0):
    return (src, alpha)


SIBLING = {
    # --- 活动栏 / 标题栏 ---
    "activityBar.activeBackground": ("list.activeSelectionBackground", 1.0),
    "activityBar.activeFocusBorder": ("focusBorder", 0.0),
    "activityBar.border": ("editorWidget.border", 1.0),
    "activityBarTop.activeBackground": ("activityBar.activeBackground", 1.0),
    "activityBarTop.background": ("activityBar.background", 1.0),
    "titleBar.border": ("editorWidget.border", 1.0),
    "statusBar.border": ("editorWidget.border", 1.0),
    # 官方默认 null（回退到 statusBar.background）。若改成浅色，聚焦时是深粉底配
    # 近白字（3.78:1），失焦变浅粉底后文字对比度只剩 1.22:1 几乎不可见。
    "statusBar.inactiveBackground": ("statusBar.background", 1.0),
    "window.activeBorder": ("focusBorder", 0.55),
    "window.inactiveBorder": ("editorWidget.border", 0.0),
    "contrastBorder": ("editorWidget.border", 1.0),
    "contrastActiveBorder": ("focusBorder", 1.0),
    "surface.border": ("editorWidget.border", 1.0),
    "surface.background": ("editor.background", 1.0),
    "surface.foreground": ("foreground", 1.0),
    # --- 编辑器基础 ---
    "editor.border": ("editorWidget.border", 0.0),
    "editorCursor.background": ("editor.foreground", 1.0),
    "editorGroup.emptyBackground": ("editor.background", 1.0),
    "editorGroup.border": ("editorGroupHeader.tabsBackground", 1.0),
    "editorGroup.focusedEmptyBorder": ("focusBorder", 0.4),
    "editorGroupHeader.border": ("editorWidget.border", 1.0),
    "editorGroupHeader.tabsBorder": ("tab.border", 1.0),
    "editorStickyScroll.border": ("editorWidget.border", 1.0),
    "editorWidget.resizeBorder": ("editorWidget.border", 1.0),
    "editorOverviewRuler.border": ("editorOverviewRuler.border", 1.0),
    "editorOverviewRuler.background": ("editor.background", 0.0),
    "editorLineNumber.dimmedForeground": ("editorLineNumber.foreground", 0.6),
    "editorBracketMatch.foreground": ("editor.foreground", 1.0),
    "editorGhostText.background": ("editor.background", 0.0),
    "editorGhostText.border": ("editorWidget.border", 0.0),
    "editorUnnecessaryCode.border": ("editorWidget.border", 0.0),
    "editorGroup.dropIntoPromptBorder": ("focusBorder", 0.0),
    "widget.border": ("editorWidget.border", 1.0),
    # --- 查找 / 高亮 ---
    # 注意：foreground 类应指向正文色（高亮靠 background 上色），
    # 若指向 background 会让文字与底色同色而“看不见”。
    "editor.findMatchBorder": ("editor.findMatchBackground", 1.0),
    "editor.findMatchForeground": ("editor.foreground", 1.0),
    "editor.findMatchHighlightBorder": ("editor.findMatchHighlightBackground", 1.0),
    "editor.findMatchHighlightForeground": ("editor.foreground", 1.0),
    "editor.findRangeHighlightBorder": ("editor.findMatchBackground", 1.0),
    "editor.rangeHighlightBorder": ("editor.rangeHighlightBackground", 0.0),
    "editor.lineHighlightBackground": ("editor.lineHighlightBackground", 1.0),
    # --- 选区 ---
    # 不强制改选区内的文字色：VS Code 默认在选区里保持正常前景色，
    # 强制设成 selectionForeground 会降低可读性。这里指向正文色。
    "editor.selectionForeground": ("editor.foreground", 1.0),
    "editor.selectionHighlightBorder": ("editor.selectionBackground", 1.0),
    "editor.wordHighlightBorder": ("editor.wordHighlightBackground", 0.0),
    "editor.wordHighlightStrongBorder": ("editor.wordHighlightStrongBackground", 0.0),
    "editor.symbolHighlightBorder": ("editor.symbolHighlightBackground", 0.0),
    "editor.snippetTabstopHighlightBorder": ("editor.snippetTabstopHighlightBackground", 1.0),
    "editor.snippetFinalTabstopHighlightBorder": ("editor.snippetFinalTabstopHighlightBackground", 1.0),
    "peekViewEditor.matchHighlightBorder": ("editor.findMatchBackground", 1.0),
    # --- squiggle / 提示 ---
    "editorError.border": ("editorError.foreground", 0.55),
    "editorWarning.border": ("editorWarning.foreground", 0.55),
    "editorInfo.border": ("editorInfo.foreground", 0.55),
    "editorHint.border": ("editorHint.foreground", 0.55),
    "editorUnnecessaryCode.opacity": ("editorUnnecessaryCode.opacity", 1.0),
    # --- 列表 / 菜单 ---
    "list.focusAndSelectionOutline": ("focusBorder", 1.0),
    "list.inactiveFocusBackground": ("list.inactiveSelectionBackground", 1.0),
    "list.inactiveFocusOutline": ("list.focusOutline", 0.6),
    "list.activeSelectionIconForeground": ("list.activeSelectionForeground", 1.0),
    "list.inactiveSelectionForeground": ("list.activeSelectionForeground", 0.7),
    "list.inactiveSelectionIconForeground": ("list.inactiveSelectionForeground", 1.0),
    "menu.border": ("editorWidget.border", 1.0),
    "menu.selectionBorder": ("focusBorder", 0.0),
    "menubar.selectionBorder": ("focusBorder", 0.0),
    "listFilterWidget.outline": ("focusBorder", 0.0),
    "quickInput.list.focusBackground": ("list.activeSelectionBackground", 1.0),
    "dropdown.listBackground": ("dropdown.background", 1.0),
    "pickerGroup.border": ("editorWidget.border", 1.0),
    # --- 面板 / 侧栏 ---
    "sideBar.border": ("editorWidget.border", 1.0),
    "sideBar.foreground": ("foreground", 1.0),
    "sideBarStickyScroll.border": ("editorWidget.border", 1.0),
    "sideBarTitle.border": ("sideBarSectionHeader.border", 1.0),
    "panelSectionHeader.foreground": ("panelSectionHeader.border", 1.0),
    "panelStickyScroll.border": ("panel.border", 1.0),
    "panelTitle.border": ("panel.border", 1.0),
    "titleBar.activeForeground": ("titleBar.activeBackground", 1.0),
    "outputView.background": ("panel.background", 1.0),
    "debugToolBar.border": ("editorWidget.border", 1.0),
    "debugConsole": ("editorWidget.background", 1.0),
    "debugConsoleInputBorder": ("input.border", 1.0),    # --- 输入控件 ---
    "input.border": ("inputOption.activeBorder", 1.0),
    "checkbox.disabled.background": ("checkbox.background", 1.0),
    "checkbox.disabled.foreground": ("checkbox.foreground", 0.5),
    "radio.inactiveBackground": ("checkbox.background", 1.0),
    "radio.inactiveForeground": ("radio.foreground", 0.7),
    "radio.activeBorder": ("radio.border", 1.0),
    "radio.inactiveBorder": ("radio.border", 1.0),
    "checkbox.selectBorder": ("checkbox.border", 1.0),
    "checkbox.selectBackground": ("checkbox.background", 1.0),
    # 官方默认均为 null（回退）；前景跟随对应边框色，而不是正文色
    "inputValidation.errorForeground": ("inputValidation.errorBorder", 1.0),
    "inputValidation.warningForeground": ("inputValidation.warningBorder", 1.0),
    "inputValidation.infoForeground": ("inputValidation.infoBorder", 1.0),
    "textPreformat.border": ("textPreformat.background", 1.0),
    "button.border": ("button.secondaryBackground", 1.0),
    # --- 标签页 ---
    "tab.activeBorder": ("focusBorder", 0.9),
    "tab.activeBorderTop": ("focusBorder", 0.9),
    "tab.hoverBackground": ("tab.inactiveBackground", 1.0),
    "tab.hoverBorder": ("tab.border", 1.0),
    "tab.hoverForeground": ("tab.activeForeground", 1.0),
    # --- 终端 ---
    "terminal.background": ("editor.background", 1.0),
    "terminal.selectionForeground": ("terminal.foreground", 1.0),
    "terminal.findMatchBorder": ("terminal.findMatchBackground", 1.0),
    "terminal.findMatchHighlightBorder": ("terminal.findMatchHighlightBackground", 1.0),
    "terminalCursor.background": ("terminal.foreground", 1.0),
    "terminalCursor.foreground": ("terminal.background", 1.0),
    "terminalStickyScroll.background": ("editor.background", 1.0),
    "terminalStickyScroll.border": ("editorWidget.border", 1.0),
    "terminalSymbolIcon.inlineSuggestionForeground": ("terminal.ansiBlue", 1.0),
    # --- Diff / Merge ---
    "diffEditor.border": ("editorWidget.border", 0.0),
    "diffEditor.insertedTextBorder": ("diffEditor.insertedTextBackground", 1.0),
    "diffEditor.removedTextBorder": ("diffEditor.removedTextBackground", 1.0),
    "diffEditorGutter.insertedLineBackground": ("diffEditor.insertedLineBackground", 1.0),
    "diffEditorGutter.removedLineBackground": ("diffEditor.removedLineBackground", 1.0),
    "diffEditorOverview.insertedForeground": ("gitDecoration.addedResourceForeground", 1.0),
    "diffEditorOverview.removedForeground": ("gitDecoration.deletedResourceForeground", 1.0),
    "diffEditorOverview.border": ("editorWidget.border", 0.0),
    "merge.border": ("mergeEditor.change.background", 0.0),
    "merge.currentHeaderBackground": ("mergeEditor.change.background", 1.0),
    "merge.commonHeaderBackground": ("mergeEditor.changeBase.background", 1.0),
    "merge.incomingHeaderBackground": ("mergeEditor.conflict.input1.background", 1.0),
    # --- Notebook ---
    "notebook.focusedCellBackground": ("notebook.cellEditorBackground", 1.0),
    "notebook.inactiveSelectedCellBorder": ("notebook.selectedCellBorder", 0.5),
    "notebook.outputContainerBackgroundColor": ("editor.background", 1.0),
    "notebook.outputContainerBorderColor": ("notebook.cellBorderColor", 1.0),
    # --- 标记导航 / 测试 ---
    "editorMarkerNavigationError.background": ("editorOverviewRuler.errorForeground", 1.0),
    "editorMarkerNavigationWarning.background": ("editorOverviewRuler.warningForeground", 1.0),
    "editorMarkerNavigationInfo.background": ("editorOverviewRuler.infoForeground", 1.0),
    "testing.message.error.lineBackground": ("editorError.background", 0.4),
    "testing.message.info.lineBackground": ("editorInfo.background", 0.4),
    # 提示底色（注册表默认 null，按前景色淡化）
    "editorError.background": ("editorError.foreground", 0.18),
    "editorWarning.background": ("editorWarning.foreground", 0.18),
    "editorInfo.background": ("editorInfo.foreground", 0.18),
    "editor.snippetFinalTabstopHighlightBackground": ("editor.snippetTabstopHighlightBackground", 1.0),
    "list.hoverOutline": ("list.hoverBackground", 1.0),
    # --- 通知 / 滚动条 / 杂项 ---
    "notificationCenterHeader.foreground": ("foreground", 1.0),
    "toolbar.hoverOutline": ("focusBorder", 0.0),
    "scrollbar.background": ("editor.background", 0.0),
    "minimap.background": ("editor.background", 0.0),
    "minimap.foregroundOpacity": ("minimap.foreground", 0.0),
    "welcomePage.background": ("editor.background", 1.0),
    "selection.background": ("editor.selectionBackground", 1.0),
    "progressBar.background": ("statusBar.background", 1.0),
    "chart.axis": ("charts.foreground", 0.0),
    "chart.guide": ("charts.foreground", 0.35),
    "chart.line": ("charts.blue", 1.0),
    "agents.background": ("editor.background", 1.0),
    "agentsPanel.background": ("sideBar.background", 1.0),
    "agentsDetail.background": ("editor.background", 1.0),
    "agentsChatInput.background": ("editorWidget.background", 1.0),
    # --- Modern UI ---
    "modernActivityBar.activeBackground": ("list.activeSelectionBackground", 1.0),
    "modernActivityBar.activeForeground": ("list.activeSelectionForeground", 1.0),
    "modernActivityBar.hoverBackground": ("list.hoverBackground", 1.0),
    "modernActivityBar.hoverForeground": ("list.hoverForeground", 1.0),
    "modernActivityBar.background": ("activityBar.background", 1.0),
    # inactive* 键必须严格按官方定义的来源，否则失焦时会错位。
    # 官方(见 workbench.desktop.main.js):
    #   modernActivityBar.inactiveBackground = modernActivityBar.background
    "modernActivityBar.inactiveBackground": ("modernActivityBar.background", 1.0),
    "modernActivityBar.border": ("activityBar.border", 1.0),
    "modernActivityBarItem.activeBackground": ("activityBar.activeBackground", 1.0),
    "modernActivityBarItem.activeForeground": ("list.activeSelectionForeground", 1.0),
    "modernActivityBarItem.hoverBackground": ("list.hoverBackground", 1.0),
    "modernActivityBarItem.hoverForeground": ("list.hoverForeground", 1.0),
    "modernTab.activeBackground": ("tab.activeBackground", 1.0),
    "modernTab.activeForeground": ("tab.activeForeground", 1.0),
    "modernTab.hoverBackground": ("tab.hoverBackground", 1.0),
    "modernTab.hoverForeground": ("tab.hoverForeground", 1.0),
    "modernEditorTab.inactiveBackground": ("tab.inactiveBackground", 1.0),
    "modernPanel.border": ("panel.border", 1.0),
    "modernSash.gripForeground": ("sash.hoverBorder", 1.0),
    "modernUI.shellBackground": ("sideBar.background", 1.0),
    "modernUI.inactiveShellBackground": ("titleBar.inactiveBackground", 1.0),
    "diffEditor.unchangedRegionForeground": ("foreground", 1.0),
    "chat.voiceListeningGlow": ("editorInfo.foreground", 0.45),
    "chat.voiceSpeakingGlow": ("charts.purple", 0.45),
    # --- Chat / Agents / Interactive 扩展界面 ---
    "chat.list.background": ("sideBar.background", 1.0),
    "agentsMobileDiff.addedForeground": ("gitDecoration.addedResourceForeground", 1.0),
    "agentsMobileDiff.deletedForeground": ("gitDecoration.deletedResourceForeground", 1.0),
    "agentsMobileDiff.modifiedForeground": ("gitDecoration.modifiedResourceForeground", 1.0),
    "inlineChat.regionHighlight": ("inlineChatInput.background", 1.0),
    "interactive.session.foreground": ("foreground", 1.0),
    "interactive.result.editor.background.color": ("editor.background", 1.0),
}

# --------------------------------------------------------------------------
# 人工覆盖（需要手调的少量键；支持 {dark: ..., light: ...}）
# --------------------------------------------------------------------------
OVERRIDE = {
    # --- 窗口聚焦 / 失焦 ---
    # VS Code 的失焦切换逻辑（workbench.desktop.main.js）：
    #   root.backgroundColor = titleBar.activeBackground : titleBar.inactiveBackground
    #   --modern-ui-shell-background = modernUI.shellBackground : modernUI.inactiveShellBackground
    #                       （失焦时取不到 inactive 则回退到 active）
    # 官方默认是 inactive = Ci(active, .6)，靠 60% 透明度叠在 root 底色上自然变淡。
    # 如果把 inactive 设成不透明色，失焦时不但不会变淡，还会让外壳与根容器出现色阶断层。
    # 因此这里严格遵循官方语义：inactive 用 active 的 60% 透明度。
    # 官方默认里 modernUI.shellBackground 与 titleBar.activeBackground 同源，
    # 统一为同一个值，失焦时 root 与外壳一起变淡，不会出现分层割裂。
    "titleBar.activeBackground": {"dark": "#2A2C31", "light": "#F9DBE5"},
    "titleBar.inactiveBackground": {"dark": "#2A2C3199", "light": "#F9DBE599"},
    "titleBar.inactiveForeground": {"dark": "#8A8A8ACC", "light": "#C99AA8CC"},
    "modernUI.shellBackground": {"dark": "#2A2C31", "light": "#F9DBE5"},
    # modernUI.inactiveShellBackground 不在这里覆盖，由 SIBLING 跟随
    # titleBar.inactiveBackground（官方定义的来源），避免两处真相。
    "window.inactiveBorder": {"dark": "#00000000", "light": "#00000000"},
    # 半透明浮层统一为樱粉调
    "surface.background": {"dark": "#2F3136", "light": "#FDE7EE"},
    # 浅色下这些键沿用深色的取值会导致「白字画在浅底上」不可读
    "window.activeBorder": {"dark": "#A3B1D6", "light": "#F4CDDB"},
    "activityBar.foreground": {"dark": "#FFFFFF", "light": "#6B3A48"},
    "terminal.ansiWhite": {"dark": "#CCCCCC", "light": "#5C4A50"},
    "terminal.ansiBrightWhite": {"dark": "#FFFFFF", "light": "#7A626A"},
    "terminal.ansiBrightBlack": {"dark": "#6B7280", "light": "#4A3A40"},
    # 浅色下对比度不足的键（check_contrast.py 审计得出）
    # 失焦态：VS Code 默认是 active 前景 × 0.6，对浅粉底只剩 1.7:1，这里手动压深
    "activityBar.inactiveForeground": {"dark": "#8A8A8A", "light": "#8A5566"},
    "activityBarTop.inactiveForeground": {"dark": "#8A8A8A", "light": "#8A5566"},
    "tab.inactiveForeground": {"dark": "#8A8A8A", "light": "#7E6270"},
    "tab.unfocusedActiveForeground": {"dark": "#8A8A8A", "light": "#7E6270"},
    "breadcrumb.foreground": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "editorCodeLens.foreground": {"dark": "#D6A461", "light": "#4F7A52"},
    "scmGraph.foreground1": {"dark": "#F2D199", "light": "#B5651F"},
    "scmGraph.foreground2": {"dark": "#C45A6D", "light": "#C05A6D"},
    "scmGraph.foreground3": {"dark": "#BD8A48", "light": "#A8632A"},
    "scmGraph.foreground4": {"dark": "#85B59A", "light": "#4F7A45"},
    "scmGraph.foreground5": {"dark": "#87A3D6", "light": "#3F6E9B"},
    "testing.iconPassed": {"dark": "#85B59A", "light": "#4F7A45"},
    "testing.iconSkipped": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "testing.iconUnset": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "testing.iconErrored": {"dark": "#E27E7E", "light": "#B0413F"},
    "testing.iconQueued": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "editorLineNumber.foreground": {"dark": "#6B7A8D", "light": "#A88B96"},
    "editorGhostText.foreground": {"dark": "#6B7A8D", "light": "#A88B96"},
    "tree.indentGuidesStroke": {"dark": "#59677A", "light": "#D9A2B7"},
    "tree.inactiveIndentGuidesStroke": {"dark": "#4A5566", "light": "#E4B6C6"},
    "list.highlightForeground": {"dark": "#E0C48A", "light": "#8E2F3F"},
    "textPreformat.foreground": {"dark": "#E0B87A", "light": "#8A5220"},
    "testing.iconFailed.retired": {"dark": "#E27E7E", "light": "#A85E1E"},
    "testing.iconErrored.retired": {"dark": "#E27E7E", "light": "#B0413F"},
    "testing.iconQueued.retired": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "testing.iconUnset.retired": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "testing.iconSkipped.retired": {"dark": "#8A8A8A", "light": "#8A6B76"},
    "testing.iconPassed.retired": {"dark": "#85B59A", "light": "#4F7A45"},
}

# --------------------------------------------------------------------------
# 求解
# --------------------------------------------------------------------------


class Resolver:
    def __init__(self, explicit: dict, fallback_bg: str, fallback_fg: str, kind: str = "dark"):
        self.explicit = explicit          # 主题已定义的键（含迁移进来的）
        self.kind = kind
        self.cache = {}
        self.palette = Palette(explicit.values())
        self.fallback_bg = fallback_bg
        self.fallback_fg = fallback_fg

    def get(self, key, _stack=None):
        if key in self.explicit:
            return self.explicit[key]
        if key not in REG and key not in OVERRIDE:
            return None                      # 非注册表的键不应被引入
        if key in self.cache:
            return self.cache[key]
        _stack = _stack or set()
        if key in _stack:                 # 循环引用保护
            return self.fallback_fg
        _stack = _stack | {key}

        val = None
        if key in OVERRIDE:
            ov = OVERRIDE[key]
            if isinstance(ov, str):
                val = ov
            else:
                val = ov.get(self.kind)
        if val is None and key in SIBLING:
            src, factor = SIBLING[key]
            base = self.get(src, _stack) or self.fallback_fg
            val = with_alpha(base, factor) if factor != 1.0 else base
        if val is None and key in ANCH:
            a = ANCH[key]
            fam = semantic_family(key)
            if fam and a["type"] == "hex":
                # 语义色：对齐主题自己的 diff 调色板，而不是按色相最近邻
                bg_key, border_key = SEMANTIC[fam]
                base = self.get(bg_key, _stack) or self.fallback_fg
                alpha = round(a["value"][3] * 255)
                # background 类语义键作为底色使用，过高的不透明度会过于刺眼
                if key.endswith(".background") or key.endswith("LineBackground"):
                    alpha = min(alpha, 0x33)
                r, g, b, _ = parse_hex(base)
                val = to_hex(r, g, b, alpha)
            elif a["type"] == "id" and a["value"] != key:
                val = self.get(a["value"], _stack) or self.fallback_fg
            elif a["type"] == "hex":
                r, g, b, alpha = a["value"]
                near = self.palette.nearest(to_hex(r, g, b, 255))
                nr, ng, nb, na = parse_hex(near)
                val = to_hex(nr, ng, nb, round(alpha * 255))
        if val is None:
            val = self.fallback_fg
            self.unresolved = getattr(self, "unresolved", set())
            self.unresolved.add(key)
        self.cache[key] = val
        return val


def build(theme_path, other_path, is_dark):
    kind = "dark" if is_dark else "light"
    theme = json.load(open(theme_path))
    colors = dict(theme["colors"])

    # 1) 失效键迁移：把老键的色值搬到现代键（现代键未被显式定义时才搬）
    migrated = 0
    for old, new in MIGRATE.items():
        if old in colors:
            if new not in colors and new in REG:
                colors[new] = colors[old]
                migrated += 1
            del colors[old]

    # 1b) 人工覆盖优先级最高（修正深浅取值不一致、可读性问题）
    for key, ov in OVERRIDE.items():
        if not isinstance(ov, str) and key in REG:
            val = ov.get(kind)
            if val:
                colors[key] = val

    base_bg = colors.get("editor.background", "#1E1E1E")
    base_fg = colors.get("editor.foreground", "#CCCCCC")
    r = Resolver(colors, base_bg, base_fg, kind)

    # 2) 补齐注册表中所有缺失的键
    added = []
    for key in sorted(REG):
        if key not in r.explicit and key not in r.cache:
            r.get(key)
            added.append(key)

    # 3) 丢弃不在注册表里的键（除迁移目标外）
    dropped = [k for k in r.explicit if k not in REG]
    for k in dropped:
        r.explicit.pop(k, None)

    # 4) 组装：保持原有顺序，新增键按字典序追加
    final = {}
    for k in theme["colors"]:
        if k in REG:
            final[k] = colors.get(k, r.get(k))
    for k in sorted(set(REG)):
        if k not in final:
            final[k] = r.get(k)

    return theme, final, {"migrated": migrated, "added": len(added), "dropped": dropped,
                          "unresolved": sorted(getattr(r, "unresolved", set()))}


def main():
    check_only = "--check" in sys.argv
    dt, dc, dmeta = build(DARK_PATH, LIGHT_PATH, True)
    lt, lc, lmeta = build(LIGHT_PATH, DARK_PATH, False)

    # 5) 深浅键集对齐
    only_d = sorted(set(dc) - set(lc))
    only_l = sorted(set(lc) - set(dc))
    for k in only_d:
        lc[k] = dc[k]
    for k in only_l:
        dc[k] = lc[k]
    for k in only_d + only_l:
        # 放回有序位置
        if k not in dc:
            dc[k] = lc[k]
        if k not in lc:
            lc[k] = dc[k]

    # 6) 校验
    HEX = re.compile(r"^#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
    problems = []
    for name, c in (("dark", dc), ("light", lc)):
        for k, v in c.items():
            if not HEX.match(v):
                problems.append(f"{name}.{k} = {v}")
    if set(dc) != set(lc):
        problems.append("深浅键集仍不一致")
    for meta, name in ((dmeta, "dark"), (lmeta, "light")):
        if meta["unresolved"]:
            problems.append(f"{name} 未能求解: {meta['unresolved']}")

    if problems:
        print("校验失败：")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    print(f"dark : 定义 {len(dc)} 键（迁移 {dmeta['migrated']}，新增 {dmeta['added']}，"
          f"清理失效 {len(dmeta['dropped'])}）")
    print(f"light: 定义 {len(lc)} 键（迁移 {lmeta['migrated']}，新增 {lmeta['added']}，"
          f"清理失效 {len(lmeta['dropped'])}）")

    if check_only:
        return

    dt["colors"] = dc
    lt["colors"] = lc
    for path, data in ((DARK_PATH, dt), (LIGHT_PATH, lt)):
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("写入", os.path.relpath(path, HERE))


if __name__ == "__main__":
    main()
