# 维护与验证指南

## 文件职责

| 路径 | 职责 |
|---|---|
| `src/dark.json`、`src/light.json` | 人工界面色和主题元数据；是输入而非生成物 |
| `scripts/build_tokens.py` | 语法色板、TextMate 和语义规则的源定义 |
| `data/registry.json` | 固定颜色候选集合、表达式、逐项来源与版本哈希 |
| `data/anchors.json` | 分开的深浅默认锚点，以及各自未能解析的键 |
| `themes/*.json` | 供 VS Code 加载的最终生成主题 |
| `scripts/theme-validation.mjs` | 两个 Node 校验入口共用的实现 |
| `scripts/check_contrast.py` | UI 配对、透明叠加模型、六种语法背景和豁免理由 |
| `scripts/tests/` | 校验 CLI、表达式解析、快照更新、构建和对比度回归测试 |
| `examples/`、`images/` | 可复现的截图样例和实际截图 |

## 日常改色

1. 修改设计源，不直接修改 `themes/`。现有显式界面色优先，不会被补色规则强制覆盖。
2. 运行 `npm run build`。生成器读取固定快照、分别使用 Dark/Light 锚点，并一次生成 UI、TextMate、semantic 全部内容。
3. 运行 `npm run verify`。`--check` 比较 UTF-8/LF 的确切产物字节；仅检查候选内容合法并不足以证明产物同步。
4. 在独立 VS Code 配置中人工检查，尤其是 Diff/选区、失焦、调试、终端和第三方语言扩展。
5. 更新截图或 README 色板、CHANGELOG，最后 `npm run package`。不要把“全部检查通过”写成“所有界面可访问性均已认证”。

补色仅用于新增或缺失键：先应用已知旧键迁移，再依次考虑显式源值、覆盖表、兄弟键、对应深浅默认锚点及色相映射。未解决键或未知源键会使构建失败。该过程是设计辅助，不证明推导值在所有上下文语义正确。

## 固定快照与升级

当前固定基准：VS Code 1.140.0，commit `07f806f999227108933c2e30515b26eecc1fda74`。

- 注册表共 992 项：966 项 `registration`、26 项 `css-reference`。后者是已过滤 CSS 引用候选，不等于正式注册清单，升级时需要人工复核。
- Dark 锚点解析 837 项，Light 836 项；未解析项记录在 `unresolved` 中，由显式颜色或补色规则处理。这不表示当前主题缺键。
- 两个快照的来源元数据必须一致。常规构建完全读取仓库快照，不扫描本机编辑器，也不访问网络。
- 默认表达式仍依赖已验证 bundle 的压缩符号，所以锚点解析器对 commit 设置了硬限制；不能简单删除限制来“支持最新版”。

```bash
npm run registry:update -- --vscode-path "/path/to/VS Code/resources/app"
```

此路径应包含 `package.json`、`product.json`、`out/`，不是 `code` 可执行文件。也可以用 `VSCODE_PATH` 指定。包装脚本先在临时目录执行提取和锚点解析，两者成功后才写入 `data/`；提取、解析或版本不匹配不会留下半套新快照。写回是两个文件顺序写入，不是文件系统跨文件事务；意外断电后应检查两份来源是否一致。

升级到不同 commit 时：先在 `build/` 等临时输出目录试提取，检查新增/删除项和 CSS 误判，审查压缩函数及变量映射，补解析器回归用例，然后才扩展版本支持、更新快照及设计源。独立调用 `extract_registry.py` / `derive_colors.py` 时务必显式设置 `--output`，避免跳过包装脚本的失败保护。

## 校验边界与报告

```bash
node scripts/check-schema.mjs --json
python scripts/check_contrast.py --strict --json
python scripts/build_themes.py --output-dir build/preview
python scripts/build_themes.py --output-dir build/preview --check
```

Node 校验器检查固定集合的缺失/未知键、合法 hex、两主题键集对齐、独立主题结构及样式字段。语义 selector 校验语法，允许扩展自定义类型、modifier、通配符和语言后缀；不会虚构一个封闭的“所有已注册语言 token”清单。它是项目约束检查器，而不是 VS Code 全部 JSON Schema 的通用实现。

每主题检查 UI 74 组、TextMate 80 × 6 = 480 组、semantic 94 × 6 = 564 组。六个背景为普通编辑器、新增行、新增文本叠加新增行、删除行、删除文本叠加删除行、选区；选区前景覆盖也纳入计算。文字阈值 4.5:1，非文字图标 3:1。纯字体样式而无显式前景的规则会标为未测，不伪造对比度；缺少必要键或低于阈值的非豁免组合使严格命令失败。

本次主题：两套均 0 失败、0 未测；Dark 装饰豁免 2 项、Light 3 项。豁免限于树缩进线和冲突边框，逐项保留理由。模型不是完整浏览器绘制树，也未穷举所有扩展、交互状态或 scope 匹配；实际显示仍需人工检查。

## 截图复现

现有图片使用 VS Code 1.140.0 的扩展开发窗口，视口 1440 × 960，字体 16px、行高 26px，打开 `examples/preview.ts`，开启语义高亮和括号配对着色，关闭文件图标主题和右侧 Chat 栏。

使用独立临时用户目录和扩展目录启动，避免改变日常编辑器配置：

```bash
code --user-data-dir /tmp/sakura-preview-user --extensions-dir /tmp/sakura-preview-extensions --extensionDevelopmentPath . --new-window examples examples/preview.ts
```

Windows 请将临时目录替换为自己的临时路径。依次选择两套 Sakura Macaron 主题，保持相同窗口尺寸和滚动位置，保存为 `images/screenshot-dark.png` 和 `images/screenshot-light.png`。截图证明样例的真实渲染，不代表全部 UI 的验收。

## CI 与发布

CI 配置 Ubuntu/Windows、Node.js 22、Python 3.12，执行安装、完整验证、离线重建及产物差异检查；Linux 额外打包并上传 VSIX。配置矩阵不等于本地已经执行过 Windows CI。

打包前置钩子自动运行 `npm run verify`。`.vscodeignore` 排除 `src/`、`data/`、`scripts/`、`docs/` 和 `examples/`；README 引用的两张截图随包保留。发布前检查 VSIX 内容、版本号、最低版本兼容性，并人工批准发布。

此次改动保留 package 版本 0.1.1，记录在 `CHANGELOG.md` 的 Unreleased；没有自动发布或打标签。`theme-gap-report.md` 是历史材料，不应用于当前覆盖率判定。
