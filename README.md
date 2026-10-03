# Sakura Macaron

[![Visual Studio Marketplace](https://img.shields.io/badge/-Sakura%20Macaron-C45A6D?style=for-the-badge&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=player-muteki.sakura-macaron)

樱花马卡龙配色主题 — 一套完整、自包含的 VSCode 主题，不依赖任何其它主题。

- 🌙 **Dark** — 灰蓝色调，暗色环境下的柔和护眼配色
- ☀️ **Light** — 樱粉色调，柔和不刺眼的浅色界面

## 特性

- **完全独立**：不基于 GitHub Dark/Light 或任何其它主题，全部配色内建于主题文件
- **覆盖面完整**：编辑器、侧边栏、标签页、面板、状态栏、命令中心、标题栏
- **语法高亮**：TextMate + 语义高亮双套 token 规则，深浅色各一套
- **Git 与 Diff**：文件装饰、增删改色、合并冲突、差异视图全部定制
- **终端**：16 色 ANSI 配色表与背景一致
- **调试 / 测试**：断点图标、堆栈高亮、测试状态
- **Modern UI 与 Agents**：适配新版界面、粘性滚动、Chat 气泡、Agents 面板
- **状态栏优化**：修复默认半透明叠加在自定义底色上发灰的问题

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

| | Dark | Light |
|---|---|---|
| 编辑器背景 | `#36393F` | `#FFF6F8` |
| 侧边栏 | `#2F3136` | `#FDE7EE` |
| 活动栏 | `#26282C` | `#F0C2D4` |
| 面板 | `#2C2E33` | `#F9DBE5` |
| 状态栏 | `#87A3D6` | `#C45A6D` |
| 关键字 | `#87A3D6` | `#C84B5D` |
| 字符串 | `#85B59A` | `#6B965C` |
| 数字 | `#F2D299` | `#D8823B` |
| 类型 | `#E27E7E` | `#875C96` |
| 注释 | `#9B8A9E` | `#6A8A76` |

## 问题反馈

如发现配色问题或想要调整，欢迎在仓库提 Issue：
https://github.com/player-Muteki/sakura-macaron/issues

## License

[MIT](LICENSE)