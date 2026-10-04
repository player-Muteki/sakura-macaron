# Sakura Macaron

樱花马卡龙配色主题：Dark 夜樱、Light 樱粉，两套独立的 VS Code 主题，不依赖其他主题或运行时代码。马卡龙主张低饱和护眼：深色控制正文对比在 8:1 左右、语法色不超过柔和亮度；浅色文字按角色分档，语法使用易于区分的暖色系。

## 截图

### Sakura Macaron Dark

**夜樱**：暗梅紫的编辑器、深李色侧栏与浅藕紫状态栏（深梅字），搭配柔和粉雾正文与马卡龙低饱和强调色。关键字樱玫、函数杏橙、类型藤紫、字符串鼠尾草绿、数字奶油金、操作符兰紫——色相分散、区分清晰；表面提亮、正文压柔，长时间编码不刺眼。

![Sakura Macaron Dark](images/screenshot-dark.png)

### Sakura Macaron Light

**樱粉**：界面维持暖粉白底，文字按角色分四档——灰紫正文、梅紫标题/选中、兰紫悬停、玫瑰强调；语法改设暖色多档——玫红关键字、陶土函数、橄榄字符串、暗金数字、藤梅类型、肉桂常量，配莓红删除与鼠尾草新增，靠色相与明度双重差保持可区分。

![Sakura Macaron Light](images/screenshot-light.png)

截图来自 VS Code 1.140.0 的独立扩展开发窗口，使用仓库内 `examples/preview.ts`，不是概念渲染图。

## 特性与覆盖

- 两套主题各包含 **992 个工作台颜色键**，键集一致，覆盖编辑器、终端、Git/Diff、调试、测试、Notebook、Chat 等界面。
- **80 条 TextMate 规则、232 个 scope 条目、94 项语义高亮规则**，包含关键字、函数、类型、Markdown、正则、转义与 Diff 等分类。
- 新增、修改、删除采用不同角色色；浅色删除色为莓红，与修改色的橙棕区分。
- 自带固定快照、生成器、结构校验、静态对比度审计及回归测试，生成主题无需安装 VS Code。

**覆盖边界：** 992 项是 VS Code **1.140.0 固定样本**的候选颜色基准：966 项来自 bundle 中识别出的注册调用，26 项来自过滤后的 CSS 引用。快照逐项记录来源；CSS 引用不等同于已证明的正式注册。这里不承诺覆盖未来版本或所有第三方扩展。

## 安装与使用

在 VS Code 扩展市场搜索 **Sakura Macaron**，或通过“Extensions: Install from VSIX...”安装本地包。

1. 在命令面板运行 **Preferences: Color Theme**；Windows/Linux 也可依次按 `Ctrl+K`、`Ctrl+T`。
2. 选择 **Sakura Macaron Dark** 或 **Sakura Macaron Light**。
3. 如需跟随系统切换，添加设置：

```json
{
  "window.autoDetectColorScheme": true,
  "workbench.preferredDarkColorTheme": "Sakura Macaron Dark",
  "workbench.preferredLightColorTheme": "Sakura Macaron Light"
}
```

主题不包含文件图标主题。

## 配色一览

### 界面

| 角色 | Dark | Light |
|---|---|---|
| 编辑器背景 | `#3C2D3C` | `#FFF6F8` |
| 侧边栏 | `#352737` | `#FDE7EE` |
| 活动栏 | `#281F2B` | `#F0C2D4` |
| 面板 | `#372737` | `#F9DBE5` |
| 状态栏 | `#AD7F96` | `#AF4258` |
| 编辑器正文 | `#EBC4D7` | `#665568` |
| 行号 | `#BC9DB0` | `#816B74` |

### 语法

| 角色 | Dark | Light |
|---|---|---|
| 关键字 | `#F3A4B8` | `#A13F5A` |
| 函数 | `#F3B795` | `#8F4B2F` |
| 字符串 | `#ACD39A` | `#496334` |
| 数字 | `#EAD3A0` | `#775A18` |
| 类型 / 类 | `#CCB0F0` | `#75456F` |
| 常量 | `#E2B48D` | `#875A28` |
| 注释 | `#BBA9BA` | `#6B5963` |

界面色来源为 `src/*.json`，语法色来源为 `scripts/build_tokens.py` 的 `PALETTE`；语言服务可能选择不同语义规则。

## 对比度检查范围

每套主题静态检查 **74 组 UI、480 组 TextMate、564 组语义色组合**。默认文字阈值为 **4.5:1**，图标等非文字阈值为 **3:1**。语法色分别检查编辑器、新增行、新增文本、删除行、删除文本和选区六种背景；半透明 Diff 文本背景叠加于对应行背景后计算。

当前基准下两套主题均 **0 失败、0 未测项**。Dark 有 2 项、Light 有 3 项低对比度装饰豁免，仅涉及树缩进线和冲突边框，报告会显示理由；行号和幽灵文本不豁免。

**这不是完整 WCAG 认证。** 静态模型不能覆盖所有 UI 状态、语言规则优先级、用户覆盖色、第三方扩展、Markdown 网页或屏幕显示条件。真实截图仅验证样例编辑器外观，不能替代这些场景的人工检查。

## 兼容性

- manifest 声明最低 VS Code **1.80.0**，但本次仅在 **1.140.0** 实测主题渲染，尚未完成最低版本兼容性测试。
- 固定快照对应 commit `07f806f999227108933c2e30515b26eecc1fda74`，并保存 bundle/CSS 哈希；不宣称该版本为最新版本。
- 不同 VS Code 版本的界面与颜色支持可能不同；新增颜色需要显式更新基准和审查，不会随本机编辑器升级自动改变构建结果。

## 开发与验证

需要 **Node.js 22+**、**Python 3.10+**，并保证 `python` 命令指向 Python 3。Python 脚本仅用标准库；常规构建和校验不需要本机 VS Code 或网络，首次安装 npm 开发依赖需要网络。

```bash
npm ci --ignore-scripts
npm run build
npm run verify
npm run package
```

| 命令 | 用途 |
|---|---|
| `npm run build` | 从 `src/`、固定快照及语法色板生成两套完整主题 |
| `npm run check` | 固定键集、色值、主题结构、TextMate 与语义样式检查 |
| `npm run check:generated` | 检测手改产物、过期产物或缺失产物，不写文件 |
| `npm run check:contrast` | 严格对比度检查；失败或缺少必测颜色时返回非零 |
| `npm test` | Node 与 Python 回归测试 |
| `npm run verify` | 顺序执行全部检查与测试 |
| `npm run package` | 先验证，再生成不携带开发依赖的 VSIX |

修改配色时编辑 `src/dark.json`、`src/light.json` 或 `scripts/build_tokens.py`，再运行构建；不要直接修改生成的 `themes/*.json`。

升级 VS Code 快照需要本机编辑器和人工审查，使用 `npm run registry:update -- --vscode-path <resources/app>`。当前锚点解析器仅允许已验证的 commit，不支持的新版本会拒绝更新，且解析失败不改变 `data/`。详见 [维护指南](docs/maintenance.md)。

## 问题反馈

请在项目仓库提交 Issue，并附上 VS Code 版本、主题名称、语言/扩展、相关设置和截图。

## License

[MIT](LICENSE)
