# Sakura Macaron 主题要素差距调研报告

> 基准：本机安装的 VS Code 颜色注册表（`out/vs/workbench/workbench.desktop.main.js` 中全部 `registerColor` 调用 + workbench CSS 里的 `--vscode-*` 变量），共 **1079** 个颜色 id。

> 对照物：官方 GitHub Dark/Light（183–245 色）、One Dark Pro（222 色 / 275 条 token 规则）、VS Code 2026 默认主题（291/298 色）。

## 0. 总览

| 指标 | Sakura Dark | Sakura Light | 参考（成熟主题） |
|---|---|---|---|
| 已定义 `colors` | 528 | 527 | 222–298 |
| 缺失颜色 id | 613 | 614 | ~0–30 |
| `tokenColors` 规则数 | 15 | 15 | 45（GitHub）/ 275（One Dark Pro） |
| token 覆盖 scope 数 | 57 | 57 | 73（GitHub）/ 303（One Dark Pro） |
| `semanticTokenColors` | 32 | 32 | 10–60+ |

结论：**工作台"骨架"配色齐全，但缺少 2026 新版界面的整族键、AI/Chat 整族键、以及大量细节键**，这些位置会回落到 VS Code 默认蓝灰色，是"看起来不统一"的根因。

## 1. 缺失的颜色 id（按模块）

### 1. Modern UI (2026 新界面) — 缺 37 项

```
actionBar.toggledBackground
contrastActiveBorder
contrastBorder
modernActivityBar.activeBackground
modernActivityBar.activeForeground
modernActivityBar.background
modernActivityBar.border
modernActivityBar.hoverBackground
modernActivityBar.hoverForeground
modernActivityBar.inactiveBackground
modernActivityBarItem.activeBackground
modernActivityBarItem.activeForeground
modernActivityBarItem.hoverBackground
modernActivityBarItem.hoverForeground
modernEditorTab.activeActionBackground
modernEditorTab.activeBackground
modernEditorTab.activeForeground
modernEditorTab.activeHoverActionBackground
modernEditorTab.activeHoverBackground
modernEditorTab.hoverActionBackground
modernEditorTab.hoverBackground
modernEditorTab.hoverForeground
modernEditorTab.inactiveBackground
modernEditorTab.selectedActionBackground
modernPanel.border
modernSash.gripForeground
modernTab.activeBackground
modernTab.activeForeground
modernTab.hoverBackground
modernTab.hoverForeground
modernUI.inactiveShellBackground
modernUI.shellBackground
surface.background
surface.border
surface.foreground
window.activeBorder
window.inactiveBorder
```

### 10. 列表 / 设置 / 面板 — 缺 35 项

```
banner.background
banner.foreground
banner.iconForeground
keybindingTable.headerBackground
keybindingTable.rowsBackground
list.deemphasizedForeground
list.dropBetweenBackground
list.filterMatchBackground
list.filterMatchBorder
list.focusAndSelectionOutline
list.focusHighlightForeground
list.inactiveFocusBackground
list.inactiveFocusOutline
menu.selectionBorder
menubar.selectionBorder
notificationCenterHeader.foreground
notificationLink.foreground
panelSectionHeader.background
panelSectionHeader.border
panelSectionHeader.foreground
panelTitle.border
panelTitleBadge.background
panelTitleBadge.foreground
quickInput.list.focusBackground
quickInputList.focusHighlightForeground
search.resultsInfoForeground
searchEditor.findMatchBackground
searchEditor.findMatchBorder
searchEditor.textInputBorder
settings.dropdownListBorder
settings.headerBorder
settings.sashBorder
settings.settingsHeaderHoverForeground
sideBarTitle.background
sideBarTitle.border
```

### 11. 富文本 / 表单 / 状态栏 / 活动栏 — 缺 61 项

```
activeSessionView.background
activeSessionView.foreground
activityBarBadge.background
activityBarBadge.foreground
activityBarTop.dropBorder
activityErrorBadge.background
activityErrorBadge.foreground
activityWarningBadge.background
activityWarningBadge.foreground
browser.border
button.border
button.secondaryBorder
button.separator
checkbox.disabled.background
checkbox.disabled.foreground
checkbox.selectBackground
checkbox.selectBorder
extensionBadge.remoteBackground
extensionBadge.remoteForeground
extensionButton.background
extensionButton.border
extensionButton.foreground
extensionButton.hoverBackground
extensionButton.separator
extensionIcon.preReleaseForeground
extensionIcon.privateForeground
extensionIcon.sponsorForeground
extensionIcon.starForeground
extensionIcon.verifiedForeground
inactiveSessionView.background
inactiveSessionView.foreground
markdownAlert.caution.foreground
markdownAlert.important.foreground
markdownAlert.note.foreground
markdownAlert.tip.foreground
markdownAlert.warning.foreground
radio.activeBackground
radio.activeBorder
radio.activeForeground
radio.inactiveBackground
radio.inactiveBorder
radio.inactiveForeground
radio.inactiveHoverBackground
statusBar.inactiveBackground
statusBarItem.offlineBackground
statusBarItem.offlineForeground
statusBarItem.offlineHoverBackground
statusBarItem.offlineHoverForeground
statusBarItem.remoteHoverBackground
statusBarItem.remoteHoverForeground
text
textBlockQuote.background
textBlockQuote.border
textCodeBlock.background
textLink.activeForeground
textLink.foreground
textPreformat.background
textPreformat.border
textPreformat.foreground
textSeparator.foreground
walkthrough.stepTitle.foreground
```

### 12. 其它 — 缺 118 项

```
action.item.auto.timeout
bodyFontSize
bodyFontSize.small
bodyFontSize.xSmall
chart.axis
chart.guide
chart.line
codiconFontSize
codiconFontSize.compact
colorPicker.colorDecoratorMargin
colorPicker.colorDecoratorWidth
commandCenter.debuggingBackground
commandCenter.inactiveForeground
commentsView.resolvedIcon
commentsView.unresolvedIcon
cornerRadius.circle
cornerRadius.large
cornerRadius.medium
cornerRadius.small
cornerRadius.xLarge
cornerRadius.xSmall
editor.border
editor.dictation.widget.height
editor.dictation.widget.width
editorActiveLineNumber.foreground
editorCursor.background
editorError.background
editorError.border
editorGroup.dropIntoPromptBackground
editorGroup.dropIntoPromptBorder
editorGroup.dropIntoPromptForeground
editorGroup.focusedEmptyBorder
editorGroupHeader.connectedTabsBackground
editorHint.border
editorInfo.background
editorInfo.border
editorUnicodeHighlight.background
editorUnicodeHighlight.border
editorUnnecessaryCode.border
editorWarning.background
editorWarning.border
editorWidget.resizeBorder
explorer.align.offset.margin.left
hover.maxWidth
hover.sourceWhiteSpace
hover.whiteSpace
icon.chevron.down.content
icon.chevron.down.font.family
icon.chevron.right.content
icon.chevron.right.font.family
icon.circle.filled.content
icon.circle.filled.font.family
icon.close.content
icon.close.font.family
icon.comment.add.content
icon.comment.add.font.family
icon.comment.draft.content
icon.comment.draft.font.family
icon.comment.unresolved.content
icon.comment.unresolved.font.family
icon.debug.stackframe.dot.content
icon.debug.stackframe.dot.font.family
icon.debug.stop.content
icon.debug.stop.font.family
icon.menu.content
icon.menu.font.family
icon.mic.filled.content
icon.mic.filled.font.family
icon.pinned.content
icon.pinned.dirty.content
icon.pinned.dirty.font.family
icon.pinned.font.family
icon.plus.content
icon.plus.font.family
icon.pulse.content
icon.pulse.font.family
icon.x.content
icon.x.font.family
inline.chat.affordance.height
interactive.result.editor.background.color
interactive.session.foreground
merge.border
outputView.background
outputViewStickyScroll.background
parameterHintsWidget.editorFontFamily
parameterHintsWidget.editorFontFamilyDefault
peekViewEditorStickyScroll.background
peekViewEditorStickyScrollGutter.background
profiles.sashBorder
repl.font.family
repl.font.size
repl.font.size.for.twistie
repl.line.height
sash.hover.size
sash.size
scrollbar.background
shadow.active.tab
shadow.depth.x
shadow.depth.y
shadow.lg
shadow.md
shadow.sm
shadow.xl
sideBySideEditor.horizontalBorder
sideBySideEditor.verticalBorder
simpleFindWidget.sashBorder
strokeThickness
strongForeground
symbolIcon.constructorForeground
symbolIcon.enumeratorMemberForeground
symbolIcon.folderForeground
symbolIcon.functionForeground
symbolIcon.keywordForeground
symbolIcon.referenceForeground
symbolIcon.snippetForeground
toolbar.action.min.width
toolbar.hoverOutline
tree.inactiveIndentGuidesStroke
```

### 2. AI / Chat / Agents — 缺 70 项

```
agentFeedbackEditorWidget.background
agentFeedbackEditorWidget.border
agentFeedbackInputWidget.border
agentSessionSelectedBadge.border
agentSessionSelectedUnfocusedBadge.border
agentsDetail.background
agentsMobileDiff.addedForeground
agentsMobileDiff.deletedForeground
agentsMobileDiff.modifiedForeground
agentsUpdateButton.downloadedBackground
agentsUpdateButton.downloadingBackground
agentsVoice.speakingBackground
agentsVoice.speakingForeground
chat.checkpointSeparator
chat.dictationActiveMicGlow
chat.editedFileForeground
chat.findMatchBackground
chat.findMatchHighlightBackground
chat.font.family
chat.font.size.body.l
chat.font.size.body.m
chat.font.size.body.s
chat.font.size.body.xl
chat.font.size.body.xs
chat.font.size.body.xxl
chat.inputWorkingBorderColor1
chat.inputWorkingBorderColor2
chat.inputWorkingBorderColor3
chat.linesAddedForeground
chat.linesRemovedForeground
chat.list.background
chat.mcpCompatibilityWarningForeground
chat.persistent.content.height
chat.sessionStateIndicator.inProgressBorder
chat.sessionStateIndicator.needsInputBorder
chat.sessionStateIndicator.unvisitedBorder
chat.slashCommandBackground
chat.slashCommandForeground
chat.statusBackground
chat.voiceGlowBaseColor
chat.voiceListeningGlow
chat.voiceSpeakingGlow
chat.workingProgressInsidersIconForeground
chat.workingProgressStableIconForeground
inlineChat.foreground
inlineChat.regionHighlight
inlineChat.shadow
inlineChatDiff.inserted
inlineChatDiff.removed
inlineEdit.gutterIndicator.background
inlineEdit.gutterIndicator.primaryBackground
inlineEdit.gutterIndicator.primaryBorder
inlineEdit.gutterIndicator.primaryForeground
inlineEdit.gutterIndicator.secondaryBackground
inlineEdit.gutterIndicator.secondaryBorder
inlineEdit.gutterIndicator.secondaryForeground
inlineEdit.gutterIndicator.successfulBackground
inlineEdit.gutterIndicator.successfulBorder
inlineEdit.gutterIndicator.successfulForeground
inlineEdit.modifiedBackground
inlineEdit.modifiedBorder
inlineEdit.modifiedChangedLineBackground
inlineEdit.modifiedChangedTextBackground
inlineEdit.originalBackground
inlineEdit.originalBorder
inlineEdit.originalChangedLineBackground
inlineEdit.originalChangedTextBackground
inlineEdit.tabWillAcceptModifiedBorder
inlineEdit.tabWillAcceptOriginalBorder
mcpIcon.starForeground
```

### 3. Tabs — 缺 16 项

```
tab.activeBorder
tab.activeModifiedBorder
tab.dragAndDropBorder
tab.hoverBorder
tab.inactiveModifiedBorder
tab.lastPinnedBorder
tab.selectedBackground
tab.selectedBorderTop
tab.selectedForeground
tab.unfocusedActiveBorder
tab.unfocusedActiveBorderTop
tab.unfocusedActiveModifiedBorder
tab.unfocusedHoverBorder
tab.unfocusedHoverForeground
tab.unfocusedInactiveModifiedBorder
terminal.tab.activeBorder
```

### 4. Editor 细节控件 — 缺 68 项

```
editorActionList.background
editorActionList.focusBackground
editorActionList.focusForeground
editorActionList.foreground
editorBracketHighlight.foreground1
editorBracketHighlight.foreground2
editorBracketHighlight.foreground3
editorBracketHighlight.foreground4
editorBracketHighlight.foreground5
editorBracketHighlight.foreground6
editorBracketHighlight.unexpectedBracket.foreground
editorBracketMatch.foreground
editorBracketPairGuide.activeBackground1
editorBracketPairGuide.activeBackground2
editorBracketPairGuide.activeBackground3
editorBracketPairGuide.activeBackground4
editorBracketPairGuide.activeBackground5
editorBracketPairGuide.activeBackground6
editorBracketPairGuide.background1
editorBracketPairGuide.background2
editorBracketPairGuide.background3
editorBracketPairGuide.background4
editorBracketPairGuide.background5
editorBracketPairGuide.background6
editorCodeLens.fontFamily
editorCodeLens.fontFamilyDefault
editorCodeLens.fontFeatureSettings
editorCodeLens.fontSize
editorCodeLens.foreground
editorCodeLens.lineHeight
editorCommentsWidget.rangeActiveBackground
editorCommentsWidget.rangeBackground
editorCommentsWidget.replyInputBackground
editorCommentsWidget.resolvedBorder
editorCommentsWidget.unresolvedBorder
editorGhostText.background
editorGhostText.border
editorHoverWidget.highlightForeground
editorIndentGuide.activeBackground
editorIndentGuide.activeBackground2
editorIndentGuide.activeBackground3
editorIndentGuide.activeBackground4
editorIndentGuide.activeBackground5
editorIndentGuide.activeBackground6
editorIndentGuide.background
editorIndentGuide.background2
editorIndentGuide.background3
editorIndentGuide.background4
editorIndentGuide.background5
editorIndentGuide.background6
editorInlayHint.parameterBackground
editorInlayHint.parameterForeground
editorInlayHint.typeBackground
editorInlayHint.typeForeground
editorLightBulb.foreground
editorLightBulbAi.foreground
editorLightBulbAutoFix.foreground
editorMinimap.inlineChatInserted
editorMultiCursor.primary.background
editorMultiCursor.primary.foreground
editorMultiCursor.secondary.background
editorMultiCursor.secondary.foreground
editorStickyScroll.foldingOpacityTransition
editorStickyScroll.scrollableWidth
editorSuggestWidget.focusOutline
editorSuggestWidget.selectedForeground
editorSuggestWidget.selectedIconForeground
editorSuggestWidgetStatus.foreground
```

### 5. Editor 高亮状态 — 缺 26 项

```
editor.compositionBorder
editor.findMatchBorder
editor.findMatchForeground
editor.findMatchHighlightBorder
editor.findMatchHighlightForeground
editor.findRangeHighlightBorder
editor.foldBackground
editor.foldPlaceholderForeground
editor.inactiveLineHighlightBackground
editor.inlineValuesBackground
editor.inlineValuesForeground
editor.linkedEditingBackground
editor.placeholder.foreground
editor.rangeHighlightBorder
editor.selectionForeground
editor.selectionHighlightBorder
editor.snippetFinalTabstopHighlightBackground
editor.snippetFinalTabstopHighlightBorder
editor.snippetTabstopHighlightBackground
editor.snippetTabstopHighlightBorder
editor.symbolHighlightBackground
editor.symbolHighlightBorder
editor.wordHighlightBorder
editor.wordHighlightStrongBorder
editor.wordHighlightTextBackground
editor.wordHighlightTextBorder
```

### 6. 概览标尺 / 缩略图 / 行号 — 缺 42 项

```
editorGutter.addedSecondaryBackground
editorGutter.commentDraftGlyphForeground
editorGutter.commentGlyphForeground
editorGutter.commentRangeForeground
editorGutter.commentUnresolvedGlyphForeground
editorGutter.deletedSecondaryBackground
editorGutter.foldingControlForeground
editorGutter.itemBackground
editorGutter.itemGlyphForeground
editorGutter.modifiedSecondaryBackground
editorLineNumber.dimmedForeground
editorMarkerNavigation.background
editorMarkerNavigationError.background
editorMarkerNavigationError.headerBackground
editorMarkerNavigationInfo.background
editorMarkerNavigationInfo.headerBackground
editorMarkerNavigationWarning.background
editorMarkerNavigationWarning.headerBackground
editorOverviewRuler.addedForeground
editorOverviewRuler.background
editorOverviewRuler.bracketMatchForeground
editorOverviewRuler.commentDraftForeground
editorOverviewRuler.commentForeground
editorOverviewRuler.commentUnresolvedForeground
editorOverviewRuler.commonContentForeground
editorOverviewRuler.currentContentForeground
editorOverviewRuler.deletedForeground
editorOverviewRuler.errorForeground
editorOverviewRuler.incomingContentForeground
editorOverviewRuler.infoForeground
editorOverviewRuler.inlineChatInserted
editorOverviewRuler.inlineChatRemoved
editorOverviewRuler.modifiedForeground
editorOverviewRuler.selectionHighlightForeground
editorOverviewRuler.warningForeground
editorOverviewRuler.wordHighlightForeground
editorOverviewRuler.wordHighlightStrongForeground
editorOverviewRuler.wordHighlightTextForeground
editorRuler.foreground
minimap.chatEditHighlight
minimap.infoHighlight
minimap.selectionOccurrenceHighlight
```

### 7. 测试 / 调试 / 问题 — 缺 46 项

```
debugExceptionWidget.background
debugExceptionWidget.border
debugIcon.breakpointUnverifiedForeground
debugTokenExpression.boolean
debugTokenExpression.error
debugTokenExpression.name
debugTokenExpression.number
debugTokenExpression.string
debugTokenExpression.type
debugTokenExpression.value
debugView.exceptionLabelBackground
debugView.exceptionLabelForeground
debugView.stateLabelBackground
debugView.stateLabelForeground
debugView.valueChangedHighlight
testing.coverCountBadgeBackground
testing.coverCountBadgeForeground
testing.coverage.lineHeight
testing.coveredBackground
testing.coveredBorder
testing.coveredGutterBackground
testing.coveredMinimapBackground
testing.iconErrored
testing.iconErrored.retired
testing.iconFailed.retired
testing.iconPassed.retired
testing.iconQueued
testing.iconQueued.retired
testing.iconSkipped
testing.iconSkipped.retired
testing.iconUnset
testing.iconUnset.retired
testing.message.error.badgeBackground
testing.message.error.badgeBorder
testing.message.error.badgeForeground
testing.message.error.lineBackground
testing.message.info.lineBackground
testing.messagePeekBorder
testing.messagePeekHeaderBackground
testing.peekBorder
testing.peekHeaderBackground
testing.uncoveredBackground
testing.uncoveredBorder
testing.uncoveredBranchBackground
testing.uncoveredGutterBackground
testing.uncoveredMinimapBackground
```

### 8. 终端 — 缺 35 项

```
terminal.findMatchBorder
terminal.findMatchHighlightBorder
terminal.hoverHighlightBackground
terminal.inactiveSelectionBackground
terminal.initialHintForeground
terminal.selectionForeground
terminalCommandDecoration.defaultBackground
terminalCommandDecoration.errorBackground
terminalCommandDecoration.successBackground
terminalCommandGuide.foreground
terminalOverviewRuler.border
terminalOverviewRuler.cursorForeground
terminalOverviewRuler.findMatchForeground
terminalStickyScroll.background
terminalStickyScroll.border
terminalStickyScrollHover.background
terminalSymbolIcon.aliasForeground
terminalSymbolIcon.argumentForeground
terminalSymbolIcon.branchForeground
terminalSymbolIcon.commitForeground
terminalSymbolIcon.fileForeground
terminalSymbolIcon.flagForeground
terminalSymbolIcon.folderForeground
terminalSymbolIcon.inlineSuggestionForeground
terminalSymbolIcon.methodForeground
terminalSymbolIcon.optionForeground
terminalSymbolIcon.optionValueForeground
terminalSymbolIcon.pullRequestDoneForeground
terminalSymbolIcon.pullRequestForeground
terminalSymbolIcon.remoteForeground
terminalSymbolIcon.stashForeground
terminalSymbolIcon.symbolText
terminalSymbolIcon.symbolicLinkFileForeground
terminalSymbolIcon.symbolicLinkFolderForeground
terminalSymbolIcon.tagForeground
```

### 9. Notebook / Git 图 / 多 Diff / 合并 — 缺 59 项

```
diffEditor.move.border
diffEditor.moveActive.border
diffEditor.unchangedCodeBackground
diffEditor.unchangedRegionBackground
diffEditor.unchangedRegionForeground
diffEditor.unchangedRegionShadow
mergeEditor.change.background
mergeEditor.change.word.background
mergeEditor.changeBase.background
mergeEditor.changeBase.word.background
mergeEditor.conflict.handled.minimapOverViewRuler
mergeEditor.conflict.handledFocused.border
mergeEditor.conflict.handledUnfocused.border
mergeEditor.conflict.input1.background
mergeEditor.conflict.input2.background
mergeEditor.conflict.unhandled.minimapOverViewRuler
mergeEditor.conflict.unhandledFocused.border
mergeEditor.conflict.unhandledUnfocused.border
mergeEditor.conflictingLines.background
multiDiffEditor.background
multiDiffEditor.border
multiDiffEditor.headerBackground
notebook.cellBorderColor
notebook.cellEditorBackground
notebook.cellHoverBackground
notebook.cellInsertionIndicator
notebook.cellStatusBarItemHoverBackground
notebook.cellToolbarSeparator
notebook.editorBackground
notebook.focusedCellBackground
notebook.focusedCellBorder
notebook.focusedEditorBorder
notebook.inactiveFocusedCellBorder
notebook.inactiveSelectedCellBorder
notebook.outputContainerBackgroundColor
notebook.outputContainerBorderColor
notebook.selectedCellBackground
notebook.selectedCellBorder
notebook.symbolHighlightBackground
notebookEditorOverviewRuler.runningCellForeground
notebookScrollbarSlider.activeBackground
notebookScrollbarSlider.background
notebookScrollbarSlider.hoverBackground
notebookStatusErrorIcon.foreground
notebookStatusRunningIcon.foreground
notebookStatusSuccessIcon.foreground
scmGraph.foreground1
scmGraph.foreground2
scmGraph.foreground3
scmGraph.foreground4
scmGraph.foreground5
scmGraph.historyItemBaseRefColor
scmGraph.historyItemHoverAdditionsForeground
scmGraph.historyItemHoverDefaultLabelBackground
scmGraph.historyItemHoverDefaultLabelForeground
scmGraph.historyItemHoverDeletionsForeground
scmGraph.historyItemHoverLabelForeground
scmGraph.historyItemRefColor
scmGraph.historyItemRemoteRefColor
```

## 2. 语法高亮（TextMate tokenColors）覆盖不足

- 当前仅 **15 条规则 / 57 个 scope**，而 One Dark Pro 为 275 条规则 / 303 个 scope，GitHub 官方主题 45 条 / 73 个 scope。
- 建议补齐的高价值 scope（GitHub/ODP 都有、本主题缺失）：

```
markup.bold / markup.italic / markup.heading / markup.inline.raw / markup.quote
markup.inserted / markup.deleted / markup.changed / markup.underline / markup.untracked / markup.ignored
markup.strikethrough
constant / constant.character / constant.other.placeholder / constant.other.reference.link
entity.name / entity.name.constant
invalid.broken / invalid.deprecated / invalid.unimplemented
meta.diff.header / meta.diff.header.from-file / meta.diff.header.to-file / meta.diff.range
meta.embedded.expression / meta.object.member / meta.property-name / meta.separator / meta.export.default
message.error
storage.modifier.import / storage.modifier.package
string.regexp / string.regexp.character-class / string.other.link / source.regexp
support.variable / support.class.component / support.type.property-name.json
variable.other.constant / variable.other.enummember / variable.parameter.function
punctuation.definition.inserted / punctuation.definition.deleted / punctuation.definition.changed
brackethighlighter.angle / .curly / .quote / .round / .square / .tag / .unmatched
```

## 3. 语义高亮（semanticTokenColors）覆盖不足

当前 32 条，缺少以下**官方注册**的标准 token 组合（会回落到默认色）：

```
property.readonly
type.defaultLibrary
class.defaultLibrary
interface.defaultLibrary
variable.defaultLibrary.readonly
property.defaultLibrary
property.defaultLibrary.readonly
member.defaultLibrary
```

同时缺少修饰符（modifier）组合，成熟主题一般会定义 `x.declaration` / `x.documentation` / `x.static` / `x.readonly` / `x.deprecated` / `x.abstract` / `x.async` / `x.modification`：
当前仅定义了 `property.static` 一条。可补：

```
variable.declaration / variable.readonly / variable.deprecated / variable.documentation
parameter.declaration / property.declaration / property.readonly / property.static
function.declaration / function.defaultLibrary / function.deprecated
class.declaration / class.defaultLibrary / interface.defaultLibrary / type.defaultLibrary
typeParameter.declaration / enum.declaration / enumMember.declaration / struct.declaration
namespace.declaration / macro.declaration / decorator.declaration / label.declaration
member.declaration / method.declaration / event.declaration
```

## 4. 已失效 / 过时的键（dead keys，建议清理或补现代替键）

主题里设置了 **68** 个当前 VS Code 注册表中**不存在**的颜色 id —— 这些值完全不生效：

```
agentsGradient.tintColor
debugConsole.background
debugConsoleInputBorder.foreground
descriptionForeground
diffEditorOverview.border
disabledForeground
editorHoverWidget.statusBarBorder
errorForeground
focusBorder
foreground
gitDecoration.conflictingResourceForeground
gitDecoration.conflictingResourceHoverBackground
gitDecoration.deletedResourceHoverBackground
gitDecoration.ignoredResourceForeground
gitDecoration.ignoredResourceHoverBackground
gitDecoration.modifiedResourceHoverBackground
gitDecoration.renamedResourceForeground
gitDecoration.renamedResourceHoverBackground
gitDecoration.stageDeletedResourceForeground
gitDecoration.stageModifiedResourceForeground
gitDecoration.submoduleResourceForeground
gitDecoration.untrackedResourceForeground
gitDecoration.untrackedResourceHoverBackground
gitLFSDeletedResourceForeground
gitLFSModifiedResourceForeground
merge.commonBorder
merge.conflictHandledBorder
merge.conflictHandledContentBackground
merge.conflictHandledHeaderBackground
merge.conflictUnhandledBorder
merge.conflictUnhandledContentBackground
merge.conflictUnhandledHeaderBackground
merge.currentBorder
merge.editorOverview.deletedTextBackground
merge.editorOverview.deletedTextBorder
merge.editorOverview.insertedTextBackground
merge.editorOverview.insertedTextBorder
merge.editorOverview.modifiedTextBackground
merge.editorOverview.modifiedTextBorder
merge.incomingBorder
ports.iconRaiiProcessForeground
ports.iconUnrunningProcessForeground
problemsErrorDecoration.rangeBackground
problemsInfoDecoration.rangeBackground
problemsWarningDecoration.rangeBackground
process.border
quickInputSelection.background
statusBarItem.activeForeground
symbolIcon.constructorsForeground
tab.activeBorderBottom
tabs.activeBackground
tabs.activeBorder
tabs.activeForeground
tabs.border
tabs.hoverBackground
tabs.hoverBorder
tabs.hoverForeground
tabs.inactiveBackground
tabs.inactiveForeground
tabs.topActiveBorder
tabs.topBorder
tabs.unfocusedActiveBackground
tabs.unfocusedActiveBorder
tabs.unfocusedActiveForeground
tabs.unfocusedHoverBackground
tabs.unfocusedInactiveBackground
tabs.unfocusedInactiveForeground
testing.errorForeground
```

其中最典型、最需要修的两组：

| 失效键（数量） | 现代替代键 |
|---|---|
| `tabs.*`（17 个） | `tab.*` / `modernTab.*` / `modernEditorTab.*` |
| `merge.*`（15 个） | `mergeEditor.*` / `diffEditor.*` |

其它单点修正：
- `symbolIcon.constructorsForeground` → 应为 `symbolIcon.constructorForeground`
- `tab.activeBorderBottom` → 应为 `tab.activeBorderTop`
- `statusBarItem.activeForeground` → 已由 `statusBarItem.hoverForeground` 等承接
- `quickInputSelection.background` → 已由 `quickInput.list.focusBackground` / `list.focusHighlightForeground` 承接
- `ports.iconRaiiProcessForeground` / `ports.iconUnrunningProcessForeground` → 已被 `ports.iconRunningProcessForeground` 取代
- `problems*Decoration.rangeBackground` → 已由 `problems*Decoration`/`editorError.*` 系列取代

## 5. 工程与市场层面缺失要素

| 项 | 现状 | 成熟主题做法 |
|---|---|---|
| README 截图 | **无**（纯文字） | 主题是视觉商品，README 顶部 2–4 张 Dark/Light 实拍图是安装转化的第一要素 |
| `CHANGELOG.md` | **无** | 主题迭代频繁，变更记录是标配 |
| CI / 校验脚本 | **无**（`.github/` 不存在） | 用脚本自动校验：所有 hex 合法、键名在注册表内、深浅两套键集一致 |
| 深浅色键集一致性 | Dark 528 / Light 527，**不一致** | 成熟主题两套键完全对齐（键名集合 diff = 0） |
| 高对比度变体 | 无 | GitHub / VS Code 均提供 HC 版本，无障碍需求真实存在 |
| 变体数量 | 2（Dark/Light） | One Dark Pro 5 个变体、Catppuccin 16 个 —— 覆盖不同对比度/色温偏好 |
| `configurationDefaults` | 未使用 | 可声明默认字体/字号/LHC（`editor.fontLigatures`）等，主题类扩展的常见增强 |
| 失效键清理 | 62 个 | 保持键集干净，避免"改了没效果"的维护陷阱 |
| 版本号策略 | 0.1.0 | 每次补色应升 minor，并同步 CHANGELOG |
| `keywords` | 偏少 | 补 `japanese?` 否；应补 `macaron`、`pastel`、`sakura`、`soft`、`护眼`、`vscode-theme` 等长尾搜索词 |

## 6. 建议的补齐优先级

1. **P0 —— 修失效键**：`tabs.*` → `tab.*`/`modernTab.*`，`merge.*` → `mergeEditor.*`（当前 38 处配色白写）。
2. **P0 —— Modern UI 族（36 项）**：`modernUI.shellBackground`、`modernActivityBar.*`、`modernEditorTab.*`、`modernTab.*`、`surface.*`：不改这些，新版 VS Code（1.10x 默认 Modern）界面就是默认蓝灰，与主题整体割裂。
3. **P1 —— AI/Chat/Agents（70 项）**：2026 版 VS Code 的主界面就是 Chat/Agents，未定义 = 樱粉主题在主战场不生效。
4. **P1 —— Editor 细节（67）+ 高亮状态（26）**：括号配对引导、缩进参考线、inlay hint、建议框、查找高亮、word highlight、snippet tabstop、multi-cursor。
5. **P2 —— 测试/调试/终端细节（81）**：`terminalSymbolIcon.*`（22）、`testing.*`（27）、`debugTokenExpression.*`、`debugView.*`。
6. **P2 —— Notebook/Git 图/多 Diff/合并（59）**：装了 Python/Notebook/Git Graph 用户才会看到。
7. **P3 —— tokenColors 扩到 80+ scope、semanticTokenColors 补全 defaultLibrary 与 modifier 组合**。
8. **P3 —— 补截图、CHANGELOG、CI 校验脚本、键集一致性检查**。

## 7. 深浅两套主题的一致性问题（`node scripts/check-theme.mjs` 可复现）

- **键集不对齐**：Dark 有 `minimap.foregroundOpacity`（`#000000C0`），Light 没有 —— 深色下的透明度蒙版不能直接照搬到浅色。
- **12 个键在深浅两套里是同一个色值**，多数应当不同（否则浅色主题会出现"发灰/看不清"）：

```
activityBar.foreground            tab.activeBorderBottom        tabs.topBorder
commandCenter.inactiveBorder      editor.lineHighlightBorder     editorGroupHeader.tabsBorder
diffEditor.insertedTextBorder     diffEditor.removedTextBorder   editorUnnecessaryCode.opacity
scrollbar.shadow                  statusBar.debuggingForeground  terminal.ansiBrightWhite
```

  其中 `tab.activeBorderBottom`、`tabs.topBorder`、`editorGroupHeader.tabsBorder` 还是失效键（见第 4 节）。
- 515 个键的深浅取值不同（正常）。

## 8. 复现方式

```bash
node scripts/check-theme.mjs        # 人类可读报告，键集不一致时 exit 1
node scripts/check-theme.mjs --json # 机器可读，接入 CI
```

脚本会自动定位本机 VS Code 安装（`$VSCODE_PATH` 或常见发行版路径），动态探测压缩后的
`registerColor` 包装函数名，抽取注册表颜色 id，再校验：色值合法性、深浅键集一致性、
未注册（失效）键、缺失键。
