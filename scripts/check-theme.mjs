#!/usr/bin/env node
/**
 * 主题自检脚本：
 *  1. 校验所有颜色值都是合法 hex
 *  2. 校验深/浅两套主题的键集一致
 *  3. 对照本机 VS Code 的颜色注册表，列出缺失 / 失效的颜色 id
 *
 * 用法：node scripts/check-theme.mjs [--json]
 * 依赖：已安装的 VS Code（默认 /usr/share/code，可用 $VSCODE_PATH 覆盖）
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const THEME_DIR = new URL('../themes/', import.meta.url).pathname;
const asJson = process.argv.includes('--json');

/** 定位 VS Code 安装目录（不同发行版打包路径不同） */
function findVSCode() {
  const candidates = [
    process.env.VSCODE_PATH,
    '/usr/share/code/resources/app',
    '/usr/lib/code/resources/app',
    '/opt/visual-studio-code/resources/app',
    '/Applications/Visual Studio Code.app/Contents/Resources/app',
    join(process.env.HOME ?? '', '.vscode-server/bin'),
  ].filter(Boolean);
  for (const base of candidates) {
    if (existsSync(join(base, 'out/vs/workbench/workbench.desktop.main.js'))) return base;
  }
  return null;
}

const DARK = join(THEME_DIR, 'sakura-macaron-dark.json');
const LIGHT = join(THEME_DIR, 'sakura-macaron-light.json');

/** 收集 VS Code 注册表中的颜色 id：registerColor 调用 + CSS 中引用的 --vscode-* 变量 */
function collectRegistry() {
  const root = findVSCode();
  const ids = new Set();
  if (!root) return ids;
  const bundle = join(root, 'out/vs/workbench/workbench.desktop.main.js');
  const src = readFileSync(bundle, 'utf8');
  // 压缩后 registerColor 被包成 `function XX(s,o,...){return Y.registerColor(s,o,...)}`，
  // 不同版本符号名不同，这里动态探测，避免把普通配置键误当成颜色 id。
  const helper = src.match(/function (\w+)\([^)]*\)\{return \w+\.registerColor\(/);
  if (helper) {
    const re = new RegExp(`\\b${helper[1]}\\("([a-zA-Z0-9_.]{3,80})"`, 'g');
    for (const m of src.matchAll(re)) ids.add(m[1]);
  }
  const cssDir = join(root, 'out/vs');
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.css')) {
        const src = readFileSync(p, 'utf8');
        for (const m of src.matchAll(/--vscode-([a-zA-Z0-9_.-]+)/g)) ids.add(m[1].replace(/-/g, '.'));
      }
    }
  };
  walk(cssDir);
  // 排版/间距/圆角/阴影/图标字体等 token 不是颜色，不能写在 colors 里
  const nonColor = [
    /^(spacing|fontSize|fontWeight|bodyFontSize|codiconFontSize|agents\.(fontSize|fontWeight|layout|gradient))\./,
    /\.font\.(family|size)/, /\.fontFamily/, /\.fontSize/, /\.lineHeight$/, /\.fontFeatureSettings$/,
    /^(cornerRadius|shadow)\./, /^chat\.font\./, /^chat\.persistent\./,
    /^(bodyFontSize|codiconFontSize|strokeThickness)(\.|$)/,
    /^hover\.(maxWidth|sourceWhiteSpace|whiteSpace)$/,
    /^icon\..*\.(content|font\.family)$/,
    /\.(height|width)$/, /\.margin\.left$/, /\.scrollableWidth$/,
    /\.foldingOpacityTransition$/, /\.auto\.timeout$/, /\.min\.width$/, /\.for\.twistie$/,
    /\.colorDecorator(Margin|Width)$/, /^inline\.chat\.affordance\.height$/,
    /\.editorFontFamily(Default)?$/, /^sash\.(hover\.)?size$/,
  ];
  return new Set([...ids].filter((id) => !nonColor.some((re) => re.test(id))));
}

const HEX = /^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;
const load = (p) => JSON.parse(readFileSync(p, 'utf8'));

const registry = collectRegistry();
const dark = load(DARK);
const light = load(LIGHT);

const report = {
  registrySize: registry.size,
  dark: { keys: Object.keys(dark.colors).length, missing: [], invalid: [], values: [] },
  light: { keys: Object.keys(light.colors).length, missing: [], invalid: [], values: [] },
  darkOnly: [],
  lightOnly: [],
};

for (const [name, theme] of [['dark', dark], ['light', light]]) {
  for (const [key, value] of Object.entries(theme.colors)) {
    if (!HEX.test(value)) report[name].values.push(`${key} = ${value}`);
    if (!registry.has(key)) report[name].invalid.push(key);
  }
  report[name].missing = [...registry].filter((k) => !(k in theme.colors)).sort();
}

const dk = new Set(Object.keys(dark.colors));
const lk = new Set(Object.keys(light.colors));
report.darkOnly = [...dk].filter((k) => !lk.has(k)).sort();
report.lightOnly = [...lk].filter((k) => !dk.has(k)).sort();

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log(`VS Code 注册表颜色 id：${registry.size}${registry.size ? '' : '（未找到 VS Code 安装，跳过比对）'}`);
  for (const name of ['dark', 'light']) {
    const r = report[name];
    console.log(`\n[${name}] 已定义 ${r.keys} · 缺失 ${r.missing.length} · 未注册键 ${r.invalid.length} · 非法色值 ${r.values.length}`);
    if (r.values.length) console.log('  非法色值:\n   ' + r.values.join('\n   '));
    if (r.invalid.length) console.log('  未注册键:\n   ' + r.invalid.join('\n   '));
  }
  if (report.darkOnly.length || report.lightOnly.length) {
    console.log(`\n深浅键集不一致：dark 独有 ${report.darkOnly.length}，light 独有 ${report.lightOnly.length}`);
    if (report.darkOnly.length) console.log('  dark 独有:\n   ' + report.darkOnly.join('\n   '));
    if (report.lightOnly.length) console.log('  light 独有:\n   ' + report.lightOnly.join('\n   '));
  } else {
    console.log('\n深浅键集一致 ✓');
  }
}

const failed =
  report.dark.values.length || report.light.values.length || report.darkOnly.length || report.lightOnly.length;
process.exit(failed ? 1 : 0);
