# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

- **Windows 与最低版本兼容性实测**：在 Windows 11 上用独立用户/扩展目录安装 VSIX，分别在 VS Code **1.80.2**（manifest 声明的最低版本）和 **1.140.0** 下确认两套主题注册、深浅色渲染正常、渲染日志无主题相关告警；同时验证 `npm run verify` 与 `npm run package` 在本机通过。按 1.80.2 源码的 669 个注册色对账：本主题 992 键中 660 个生效、332 个为该版本尚未注册的键（静默忽略），另有 9 个 1.80 注册而 1.140 已移除的旧键取编辑器默认值，实测仅 `scm.providerBorder` 与 `statusBar.offlineBackground`/`Foreground` 有肉眼可见差异。README 的“最低版本尚未实测”声明已替换为上述结论。
- **统一 UTF-8 控制台输出**：Python 脚本入口调用新增的 `scripts/utf8_console.py`，Node 校验入口调用新增的 `scripts/utf8-console.mjs`，在 Windows 上先把控制台输出代码页切到 65001 并在进程退出后还原原代码页。修复英文区域设置下控制台代码页为 cp1252 时 `check_contrast.py` 打印中文抛 `UnicodeEncodeError`，以及代码页 936 下 Node 与 Python 输出编码不一致造成的乱码；CI 中显式设置的 `PYTHONIOENCODING=utf-8` 由此从必需项降级为冗余保险，故保留不动。
- **注册表提取适配旧版 bundle**：`extract_registry.py` 原先只认模块内 `wrapper("id", …)` 直接调用，旧版压缩产物把同一函数导出为别名并以 `(0, MOD.ALIAS)("id", …)` 跨模块调用，导致 1.80.2 上只识别出 228 个注册色（该版本源码实际有 669 个）却仍正常写出快照。现在两种调用形状都识别；导出别名只取函数体闭合括号后紧邻的绑定，避免压缩短名在其它模块被复用时把 `div`、`span`、`caret` 一类无关调用当成注册；参数扫描加 4000 字符上限，无关同名调用不再把解析拖到文件末尾。
- **快照写出前加合理性断言**：注册色数量低于量级下限（600，1.80 实际有 669 个）时直接失败而不是写出半套基准，探索性低产出可用新增的 `--allow-low-yield` 显式放行；提取结果同时报告 `registration` 与 `css-reference` 分项数量。1.140.0 基准重新提取后与已提交快照逐字节一致。

## [0.2.3] - 2026-10-04

- 更换真实重截的深/浅主题截图，文件更名为 `images/dark.png`、`images/light.png`，README 与维护指南链接同步。
- 删除历史遗留文档 `docs/theme-gap-report.md` 及其在维护指南中的引用；主题与配色无变化。

## [0.2.2] - 2026-10-04

- **浅色语法再鲜艳**：类型紫提彩至 `#6A37B0`；中性色家族整体去灰——正文 `#6F4C7A`、标题/选中档 `#7C4380`、悬停档 `#8E5076`、注释 `#775874`、标点 `#755A72`、属性 `#735675`；强调色（树莓/芒果/抹茶/琥珀/樱桃）已贴 4.5:1 审计下限，保持不变。
- **修复 Markdown 预览代码块底色**：浅色 `textCodeBlock.background` 由此前误继承的深色缺省 `#00000066` 改为 `#F7E6EE`，全部语法前景在其上 ≥4.97:1。
- **修复调试态与阴影的同类跨侧继承**：`commandCenter.debuggingBackground` 浅色改浅玫瑰粉 `#F4CAD5`（此前前景对比仅 1.31:1）、深色按官方锚点复合改为 `#54374A`（此前 2.17:1）；浅色 `diffEditor.unchangedRegionShadow` 恢复 light+ 官方半透明灰 `#737373BF`。
- 对比度审计新增 4 组 UI 前景对（Markdown 代码块、命令中心常态/调试态/调试悬停），每套主题 74→78 组，两套均 0 失败。

## [0.2.1] - 2026-10-04

- **Light 多彩马卡龙重设计**：浅色正文由此前单一深棕（约 120 个 UI 键与全部语法色同值、区分度不足）拆分为角色分档——灰紫默认 `#665568`、梅紫标题/选中 `#75456F`、兰紫悬停 `#86506D`、玫瑰强调 `#8F4059`，并按语义接入莓红错误、陶土警告、鼠尾草信息。语法色板整体重设：玫红关键字 `#A13F5A`、陶土函数 `#8F4B2F`、橄榄字符串 `#496334`、暗金数字 `#775A18`、藤梅类型 `#75456F`、肉桂常量 `#875A28`，六级括号同步展开为独立色相。修复重设引入的三处低对比（查找命中前景、选中/无线电前景），两套主题对比审计 0 失败、0 未测；界面背景不变，`screenshot-light.png` 待重截。
- 修复 Windows CI：Runner 控制台默认 cp1252 编码导致构建/校验脚本打印中文时 `UnicodeEncodeError`，工作流为全部步骤设置 `PYTHONIOENCODING=utf-8`（与测试内既有约定一致）。

## [0.2.0] - 2026-10-03

- **夜樱护眼化（马卡龙低饱和）**：深色表面整体提亮（编辑器 `#3C2D3C`、侧栏 `#352737`），正文压至 `#EBC4D7`，正文对比由 13.2:1 降到约 8.2:1；全部界面与语法色降饱和约 18%，语法前景亮度封顶 87%，Diff/选区叠加同步压淡，恢复旧版灰蓝主题的护眼体感。状态栏重新设计为浅藕紫 `#AD7F96` 配深梅文字，noFolder/debugging/inactive 与 active/compactHover 项同步改为浅底深字。
- **Light 文字马卡龙暖色化**：语法角色由青绿/绿/紫等冷色整体换为暖色家族——陶土函数、橄榄字符串、梅紫类型、暗金数字、玫红关键字；正文由近黑提亮为暖棕 `#6B5346`，各角色在柔和亮度上小幅提升饱和度；六级括号同步暖色六档。角色色相与明度双重分档以保证区分度，Diff 文字叠加压淡至 `0x12`、列表/菜单选中底色提亮为 `#F2C3D2`，保住全部表面 4.5:1。界面背景不变。
- 新增护眼设计回归：正文对比限定 6–9:1、深色语法前景亮度上限、浅色语法前景暖色判定与括号六级可见性；深色选区叠加与状态栏错误悬停按新基准微调。

- **重设计 Dark 为「夜樱」**：整体替换灰蓝界面，使用樱紫黑编辑器、深梅色侧栏、玫瑰色状态栏与樱粉强调色，同步覆盖 Modern UI、选区、悬停及失焦状态；Light 配色不变。
- 重做 Dark 语法色：樱粉关键字、花瓣粉函数、藤紫类型、鼠尾草绿字符串和奶油金数字；Diff 保留绿/莓红角色，减轻叠加底色。
- 恢复深色六级括号的可见颜色，终端蓝/青/绿保持独立角色；增加界面层级一致性、括号、终端与交互态文字的设计回归检查，并更新真实 Dark 截图。

- 统一两套校验入口：使用带版本、commit、文件哈希与来源标记的固定颜色快照；缺少快照或两套主题同时缺键均失败，不再依赖本机 VS Code 才能检查。
- 将人工界面色迁入 `src/`，区分深浅色默认锚点；离线重建全部主题与语法色，支持逐字节产物一致性检查。
- 扩展对比度检查至每主题 74 组 UI、480 组 TextMate、564 组语义色组合；修复语法、行号、幽灵文本、按钮、状态栏及 Markdown 引用等低对比度配色。
- 调整浅色删除角色为莓红，与修改角色的橙棕区分；保留透明度，并按 Diff 行底色叠加文字高亮后审计。
- 增加回归测试与 Ubuntu/Windows CI；打包前执行完整验证，快照更新先暂存并验证，避免解析失败污染已提交基准。
- 添加真实深浅色 VS Code 截图、预览样例及维护指南；明确静态对比度检查不等同于完整 WCAG 认证，最低声明版本尚未实测。

以下已发布版本记录保留历史描述；当前覆盖数与验证边界以 README 和维护指南为准。

## [0.1.1] — 2026-10-03

一次面向「与当前 VS Code 同步」的大修：以本机 VS Code 的颜色注册表为基准，
补齐所有缺失键、清理所有失效键，并大幅扩展语法与语义高亮覆盖。

### 修复

- **修复窗口失焦时的渲染异常**（用户实测反馈）：
  - `modernActivityBar.inactiveBackground` 错误地派生自 `activityBar.inactiveBackground`，
    链条最终落到 `editor.foreground`，导致**失焦时整个活动栏变成正文色近黑**。
    官方定义为 `modernActivityBar.background`，已修正。
  - `modernUI.inactiveShellBackground` 派生自 `editorGroupHeader.tabsBackground`，
    官方定义为 `titleBar.inactiveBackground`，已修正。
  - `titleBar.inactive*` 按官方语义改为「active 色 × 60% 透明度」，并让
    `modernUI.shellBackground` 与 `titleBar.activeBackground` 同源，失焦时整体平滑变淡。
- **修复状态栏失焦时文字不可见**：`statusBar.inactiveBackground` 官方默认为 `null`
  （回退到 `statusBar.background`），此前被派生为浅粉色，导致近白文字对比度跌到 1.22:1，已修正。
- **修复失焦态前景对比度不足**：`activityBar.inactiveForeground` 与
  `activityBarTop.inactiveForeground` 在浅粉底上仅 1.73:1，已压深至 3.74:1。
- **修复浅色主题可读性问题**：浅色下沿用深色取值的键（活动栏图标、终端 ANSI 亮白）
  会导致「白字画在浅底上」，已改为深色取值。
- **修复查找命中 / 括号匹配前景色**：此前前景色被推导成与高亮底色相同，导致文字不可见。
- **修复 `inputValidation.*Foreground`**：此前派生为正文色，丢失错误/警告/信息语义，
  改为跟随对应 `*Border` 色。
- **清理失效颜色键**（写在主题里但当前 VS Code 已不再注册、值不生效）：
  - `tabs.*`（17 个，VS Code 1.5x 旧命名）→ 迁移到现代等价键 `tab.*` / `tab.activeBorderTop`
  - `merge.*` / `merge.editorOverview.*`（16 个）→ 直接移除。现代 `mergeEditor.*` 键
    按自身语义重新推导，避免把旧 UI 的边框色搬进背景槽位
  - 单点笔误：`symbolIcon.constructorsForeground` → `symbolIcon.constructorForeground`、
    `tab.activeBorderBottom` → `tab.activeBorderTop`
  - 其余旧名（`quickInputSelection.*`、`problems*Decoration.rangeBackground`、
    `ports.iconRaiiProcessForeground` 等）→ 迁移或移除
- **两套主题键集对齐**：不会出现「某个界面只在浅色下不对」。

### 新增

- **补齐 464 个缺失的工作台颜色键**，覆盖此前完全回落默认蓝灰的区域：
  - Modern UI（`modernUI.*`、`modernActivityBar*`、`modernEditorTab*`、`modernTab.*`、`surface.*`、`window.*`）
  - AI / Chat / Agents（`chat.*`、`inlineEdit.*`、`agent*`、`agents*`、`interactive.*`、`mcpIcon.*`）
  - 编辑器细节（括号配对引导、缩进参考线 2–6、Inlay Hint、建议框、multi-cursor、ghost text）
  - 编辑器状态高亮（查找命中、word/symbol highlight、snippet tabstop、range highlight）
  - 概览标尺 / 缩略图（`editorOverviewRuler.*` 20 项、`minimap.*Highlight`）
  - 测试 / 调试 / 终端（`terminalSymbolIcon.*` 19 项、`testing.*` 30 项、`debugTokenExpression.*`、`debugView.*`）
  - Notebook / Git 图 / 多 Diff / 合并（`notebook.*`、`scmGraph.*`、`multiDiffEditor.*`、`mergeEditor.*`）
  - 列表 / 设置 / 面板、富文本 / 表单 / 状态栏等
- **`tokenColors` 从 15 条规则 / 57 个 scope 扩展到 80 条规则 / 232 个 scope**：
  补齐 Markdown（标题、粗斜体、删除线、引用、列表、链接、diff 标记）、
  正则与转义、diff 元信息、meta/JSX/embedded、常量与占位符、括号配对高亮、
  非法/弃用 token、label/lifetime、log.*-token 等。
- **`semanticTokenColors` 从 32 项扩展到 94 项**：补齐全部官方 `.defaultLibrary` 组合，
  八类 modifier（declaration / documentation / static / readonly / deprecated /
  modification / abstract / async），以及官方扩展通过 `semanticTokenTypes` 注册的自定义类型
  （TypeScript 的 `selfKeyword`/`newKeyword` 等、Pylance 的 `intrinsic`/`builtinConstant`、
  rust-analyzer 的 `builtinType`/`lifetime`、cpptools 的 `referenceType` 等）。
- **移除无效语义键**：`tag` 不是已注册的 token 类型，`variable.definition` 的
  `definition` 不是已注册 modifier —— 二者都不会生效，已删除。

### 工程

- 新增可复现的补色流水线（`scripts/`）：
  - `extract_registry.py` — 从 VS Code bundle 抽取 992 个颜色 id 及默认值表达式
  - `derive_colors.py` — 把默认值表达式归约为「颜色 id 引用」或「hex」
  - `build_themes.py` — 失效键迁移、兄弟键派生、语义族映射、色相加权重映射
  - `build_tokens.py` — 生成 token 与 semantic 配色
  - `check-theme.mjs` — 键集与注册表校验
  - `check-schema.mjs` — **官方接口适配性校验**（色值格式、`tokenColors` 字段、
    semantic token 类型与 modifier 是否已注册、两套主题键集一致性）
  - `check_contrast.py` — WCAG 对比度审计（覆盖深浅两套，含失焦态）
- GitHub Actions CI：运行键集 / schema / 对比度校验。
- README 增加覆盖率与兼容性说明。

### 指标变化

| 指标 | 0.1.0 | 0.1.1 |
|---|---|---|
| `colors` 键数（深/浅） | 528 / 527 | **992 / 992** |
| 未注册（失效）键 | 62 | **0** |
| 缺失注册键 | 613 | **0** |
| `tokenColors` | 15 规则 / 57 scope | **80 规则 / 232 scope** |
| `semanticTokenColors` | 32 | **94** |
| WCAG 对比度异常 | — | **0** |

## [0.1.0]

- 初始版本：Dark / Light 两套主题，编辑器、侧边栏、面板、状态栏、Git、终端、Diff、调试配色。
