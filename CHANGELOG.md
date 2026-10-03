# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

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
