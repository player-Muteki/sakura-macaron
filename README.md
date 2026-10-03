# Sakura Macaron

[![Visual Studio Marketplace](https://img.shields.io/badge/-Sakura%20Macaron-C45A6D?style=for-the-badge&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=player-muteki.sakura-macaron)
[![Version](https://img.shields.io/badge/version-0.1.1-C45A6D)](https://marketplace.visualstudio.com/items?itemName=player-muteki.sakura-macaron)

樱花马卡龙配色主题 — 一套完整、自包含的 VS Code 主题，不依赖任何其它主题。

- 🌙 **Dark** — 灰蓝色调，暗色环境下的柔和护眼配色
- ☀️ **Light** — 樱粉色调，柔和不刺眼的浅色界面

## 截图

<!-- 截图占位：把图片放到 images/ 目录后，取消下面两行的注释即可 -->

<!-- ![Sakura Macaron Dark](images/screenshot-dark.png) -->
<!-- ![Sakura Macaron Light](images/screenshot-light.png) -->

## 特性

- **完全独立**：不基于 GitHub Dark/Light 或任何其它主题，全部配色内建于主题文件
- **键集零遗漏**：两套主题各定义当前 VS Code 注册表中全部 **992** 个颜色键，
  无失效键、无缺失键（含 Modern UI、AI Chat / Agents、Git 图、Notebook、多文件 Diff、合并编辑器）
- **语法高亮**：**80** 条 TextMate 规则覆盖 **232** 个 scope —— 覆盖 Markdown、正则与转义、
  diff 元信息、meta/JSX/embedded、括号配对高亮、非法/弃用 token 等
- **语义高亮**：**94** 项，含全部官方 `.defaultLibrary` 组合与八类 modifier
  （declaration / documentation / static / readonly / deprecated / modification / abstract / async），
  并支持官方扩展注册的自定义 token 类型（TypeScript / Pylance / rust-analyzer / cpptools）
- **色觉友好**：语义色按「新增 / 修改 / 删除」三个明确角色分配，色相间距足够大，
  不依赖红绿单一维度传递信息
- **两套主题键集完全对齐**：不会出现「某个界面只在浅色下不对」
- **Git 与 Diff**：文件装饰、增删改色、合并冲突、三方合并视图全部定制
- **终端**：16 色 ANSI 配色表、命令标记、命令指引线、粘性滚动
- **调试 / 测试**：断点图标、变量类型着色、堆栈高亮、覆盖率着色
- **可访问性**：前景/背景对比度经 WCAG 审计，半透明高亮会先合成底色再计算

## 安装

在 VSCode 扩展市场搜索 **Sakura Macaron** 并安装，或手动安装 `.vsix`。

### 使用

1. `Ctrl+Shift+K` `Ctrl+T` 选择 **Sakura Macaron Dark** / **Sakura Macaron Light**
2. 如需跟随系统自动切换深浅色，在设置中开启：

```json
{
  "window.autoDetectColorScheme": true,
  "workbench.preferredDarkColorTheme": "Sakura Macaron Dark",
  "workbench.preferredLightColorTheme": "Sakura Macaron Light"
}
```

### 推荐搭配

主题不含图标，若喜欢图标可另装 [vscode-icons](https://marketplace.visualstudio.com/items?itemName=vscode-icons-team.vscode-icons)。

## 配色一览

### 界面

| | Dark | Light |
|---|---|---|
| 编辑器背景 | `#36393F` | `#FFF6F8` |
| 侧边栏 | `#2F3136` | `#FDE7EE` |
| 活动栏 | `#26282C` | `#F0C2D4` |
| 面板 | `#2C2E33` | `#F9DBE5` |
| 状态栏 | `#87A3D6` | `#C45A6D` |
| 标签页（激活 / 未激活） | `#36393F` / `#2E3137` | `#FFFFFF` / `#FBE0E9` |
| 列表选中 | `#40444B` | `#EFB8CB` |
| 焦点边框 | `#A3B1D6` | `#F4CDDB` |
| 正文 | `#CCCCCC` | `#3A3132` |
| 行号 | `#6B7A8D` | `#A88B96` |

### 语法

| | Dark | Light |
|---|---|---|
| 关键字 | `#87A3D6` | `#C84B5D` |
| 函数 | `#CBA8B9` | `#327A85` |
| 字符串 | `#85B59A` | `#6B965C` |
| 数字 | `#F2D199` | `#D8823B` |
| 类型 / 类 | `#E27E7E` | `#875C96` |
| 常量 | `#D6A461` | `#C07A3A` |
| 注释 | `#9B8A9E` | `#6A8A76` |

### 状态色

| | Dark | Light |
|---|---|---|
| 新增 | `#85B59A` | `#6B965C` |
| 修改 | `#D6A461` | `#C07A3A` |
| 删除 | `#E27E7E` | `#C07A3A` |
| 错误 | `#C25B5B` | `#7E2A3C` |
| 警告 | `#D6A461` | `#C07A3A` |

## 兼容性

- 要求 VS Code **1.80.0** 及以上（`engines.vscode: ^1.80.0`）
- 主题使用了 **202 个** VS Code 1.90+ 才引入的颜色键（`chat.*`、`modernUI.*`、
  `inlineEdit.*`、`terminalSymbolIcon.*` 等）。在旧版 VS Code 上这些键会被**静默忽略**
  （VS Code 对未注册的颜色 id 返回 undefined，不报错也不崩溃），界面依然可用，
  只是这些新界面的装饰色会回落到默认配色。想要完整效果请用较新的 VS Code。

## 开发

主题的补色不是手写堆出来的，而是从 VS Code 自身的颜色注册表推导：

```bash
python3 scripts/extract_registry.py   # 抽取 992 个颜色 id 及默认值表达式
python3 scripts/derive_colors.py      # 把默认值归约为「颜色 id 引用」或「hex」
python3 scripts/build_themes.py       # 迁移 / 兄弟派生 / 语义族 / 色相映射 → 主题
python3 scripts/build_tokens.py       # 生成 token 与 semantic 配色

npm run check              # 键集 / 注册表 / schema 校验
npm run check:contrast     # WCAG 对比度审计
```

补色遵循的规则：

1. 默认值若指向另一个颜色 id → 直接取本主题该键的值，语义 100% 保持
2. 默认值若是 hex → 按**色相优先**的最近邻映射到本主题调色板
3. 默认值为 `null` → 从语义上正确的兄弟键派生（**必须严格遵循官方定义的来源键**）
4. Diff / Merge / Git / Testing 这类有语义的键走语义族映射，保证「新增=绿、删除=红」

`scripts/check-schema.mjs` 会校验主题是否符合官方接口：键是否在注册表内、
色值是否为合法 hex、`tokenColors` 字段是否合法、`semanticTokenColors` 的
token 类型与 modifier 是否已注册（含官方扩展注册的自定义类型）、两套主题键集是否一致。

## 问题反馈

如发现配色问题或想要调整，欢迎在仓库提 Issue：
https://github.com/player-Muteki/sakura-macaron/issues

## License

[MIT](LICENSE)
