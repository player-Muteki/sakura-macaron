#!/usr/bin/env node
/**
 * 主题适配性校验：对照 VS Code 官方接口检查主题文件是否合规。
 *
 * 检查项：
 *  1. 顶层字段与 $schema
 *  2. colors 键是否都在 VS Code 注册表内（未注册键会被静默忽略，属于无效配置）
 *  3. 色值是否为合法 hex（VS Code schema 为 format: color-hex）
 *  4. tokenColors 结构与 settings 字段合法性
 *  5. semanticTokenColors 的 token 类型与 modifier 是否已注册
 *     （标准类型 + 官方扩展通过 semanticTokenTypes/semanticTokenModifiers 注册的自定义项）
 *  6. 深浅两套主题键集是否一致
 *
 * 用法：node scripts/check-schema.mjs
 * 退出码非 0 表示存在不合规项。
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const THEMES = new URL('../themes/', import.meta.url).pathname;
const asJson = process.argv.includes('--json');

/** VS Code 内置的标准 semantic token 类型 */
const STD_TYPES = new Set([
  'comment', 'string', 'keyword', 'number', 'regexp', 'operator', 'namespace', 'type',
  'struct', 'class', 'interface', 'enum', 'typeParameter', 'function', 'member', 'method',
  'macro', 'variable', 'parameter', 'property', 'enumMember', 'event', 'decorator', 'label',
]);

/** VS Code 内置的标准 semantic token modifier */
const STD_MODS = new Set([
  'declaration', 'documentation', 'static', 'abstract', 'deprecated', 'modification',
  'async', 'readonly',
]);

/**
 * 官方扩展通过 semanticTokenTypes / semanticTokenModifiers 扩展点注册的自定义项。
 * 这些键是合法的（TypeScript / Pylance / rust-analyzer / cpptools 等都会注册），
 * 未列出的自定义键则不会被任何语言发出，属于无效配置。
 */
const EXT_TYPES = new Set([
  // TypeScript / JavaScript
  'selfKeyword', 'newKeyword', 'controlKeyword', 'otherKeyword',
  // Python (Pylance)
  'intrinsic', 'magicFunction', 'builtinConstant', 'selfParameter', 'clsParameter',
  'typeHint', 'typeHintComment', 'parenthesis', 'bracket', 'curlybrace', 'colon',
  'semicolon', 'arrow', 'module', 'escapeCharacter', 'invalid', 'library', 'decorator',
  'overridden', 'callable', 'classMember', 'keywordArgument', 'builtin',
  // Rust (rust-analyzer)
  'selfTypeKeyword', 'builtinType', 'builtinAttribute', 'lifetime', 'toolModule',
  'macroBang', 'formatSpecifier', 'invalidEscapeSequence', 'procMacro', 'trait',
  'typeAlias', 'union', 'unresolvedReference', 'crateRoot', 'injected', 'intraDocLink',
  'consuming', 'mutable', 'public', 'reference', 'unsafe', 'constant', 'attribute',
  'escapeSequence', 'constParameter', 'derive', 'deriveHelper', 'bitwise', 'boolean',
  'comparison', 'logical', 'punctuation', 'comma', 'operator', 'label', 'angle',
  'arithmetic',
  // C / C++ (cpptools)
  'referenceType', 'cliProperty', 'genericType', 'valueType', 'templateFunction',
  'templateType', 'operatorOverload', 'memberOperatorOverload', 'newOperator',
  'customLiteral', 'numberLiteral', 'stringLiteral',
]);

const HEX = /^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;

/** 定位 VS Code 安装目录 */
function findVSCode() {
  const candidates = [
    process.env.VSCODE_PATH,
    '/usr/share/code/resources/app',
    '/usr/lib/code/resources/app',
    '/opt/visual-studio-code/resources/app',
    '/Applications/Visual Studio Code.app/Contents/Resources/app',
  ].filter(Boolean);
  for (const base of candidates) {
    if (existsSync(join(base, 'out/vs/workbench/workbench.desktop.main.js'))) return base;
  }
  return null;
}

/** 收集 VS Code 注册的颜色 id */
function collectRegistry() {
  const root = findVSCode();
  if (!root) return null;
  const bundle = join(root, 'out/vs/workbench/workbench.desktop.main.js');
  const src = readFileSync(bundle, 'utf8');
  const helper = src.match(/function (\w+)\([^)]*\)\{return \w+\.registerColor\(/);
  const ids = new Set();
  if (helper) {
    for (const m of src.matchAll(new RegExp(`\\b${helper[1]}\\("([a-zA-Z0-9_.]{3,80})"`, 'g'))) {
      ids.add(m[1]);
    }
  }
  // CSS 里引用的 --vscode-* 变量补充（gitDecoration.* / terminal.ansi* 等）
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.css')) {
        const css = readFileSync(p, 'utf8');
        for (const m of css.matchAll(/--vscode-([a-zA-Z0-9_.-]+)/g)) ids.add(m[1].replace(/-/g, '.'));
      }
    }
  };
  const cssRoot = join(root, 'out/vs');
  if (existsSync(cssRoot)) walk(cssRoot);
  return ids;
}

const registry = collectRegistry();
const themes = ['sakura-macaron-dark.json', 'sakura-macaron-light.json'].map((f) => ({
  file: f,
  data: JSON.parse(readFileSync(join(THEMES, f), 'utf8')),
}));

const errors = [];
const warnings = [];

if (!registry) {
  warnings.push('未找到 VS Code 安装，跳过 colors 键名校验');
}

for (const { file, data } of themes) {
  const tag = file.replace('sakura-macaron-', '').replace('.json', '');

  // 1. 顶层字段
  if (data.$schema !== 'vscode://schemas/color-theme') {
    errors.push(`${tag}: $schema 应为 vscode://schemas/color-theme，实际 ${data.$schema}`);
  }
  if (!data.name) errors.push(`${tag}: 缺少 name`);
  if (!['light', 'dark'].includes(data.type)) errors.push(`${tag}: type 应为 light 或 dark`);
  // 2/3. colors
  for (const [k, v] of Object.entries(data.colors ?? {})) {
    if (registry && !registry.has(k)) errors.push(`${tag}.colors.${k} 不在 VS Code 注册表内（不会生效）`);
    if (typeof v !== 'string' || !HEX.test(v)) errors.push(`${tag}.colors.${k} = ${v} 不是合法 hex`);
  }

  // 4. tokenColors
  for (const [i, rule] of (data.tokenColors ?? []).entries()) {
    if (!rule.scope) errors.push(`${tag}.tokenColors[${i}] 缺少 scope`);
    if (!rule.settings) errors.push(`${tag}.tokenColors[${i}] 缺少 settings`);
    for (const key of Object.keys(rule.settings ?? {})) {
      if (!['foreground', 'background', 'fontStyle'].includes(key)) {
        errors.push(`${tag}.tokenColors[${i}].settings.${key} 不是合法字段`);
      }
    }
    for (const key of ['foreground', 'background']) {
      const v = rule.settings?.[key];
      if (v !== undefined && !HEX.test(v) && v !== 'transparent') {
        errors.push(`${tag}.tokenColors[${i}].settings.${key} = ${v} 不是合法 hex`);
      }
    }
  }

  // 5. semanticTokenColors
  for (const key of Object.keys(data.semanticTokenColors ?? {})) {
    const parts = key.split('.');
    if (!STD_TYPES.has(parts[0]) && !EXT_TYPES.has(parts[0])) {
      errors.push(`${tag}.semanticTokenColors.${key} 的基类型 "${parts[0]}" 未注册（不会生效）`);
    }
    for (const mod of parts.slice(1)) {
      if (mod === 'defaultLibrary' || mod === 'readonly') continue;
      if (!STD_MODS.has(mod)) {
        errors.push(`${tag}.semanticTokenColors.${key} 的 modifier "${mod}" 未注册（不会生效）`);
      }
    }
  }
}

// 6. 深浅键集一致
const [d, l] = themes;
const dk = new Set(Object.keys(d.data.colors ?? {}));
const lk = new Set(Object.keys(l.data.colors ?? {}));
for (const k of dk) if (!lk.has(k)) errors.push(`深浅键集不一致：仅 dark 有 ${k}`);
for (const k of lk) if (!dk.has(k)) errors.push(`深浅键集不一致：仅 light 有 ${k}`);

const stat = (t) => ({
  colors: Object.keys(t.data.colors ?? {}).length,
  tokenRules: t.data.tokenColors?.length ?? 0,
  tokenScopes: (t.data.tokenColors ?? []).reduce((n, r) => n + (Array.isArray(r.scope) ? r.scope.length : 1), 0),
  semantic: Object.keys(t.data.semanticTokenColors ?? {}).length,
});

const report = {
  registrySize: registry ? registry.size : null,
  dark: stat(d),
  light: stat(l),
  keyParity: dk.size === lk.size && [...dk].every((k) => lk.has(k)),
  errors,
  warnings,
};

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log(`VS Code 注册表：${report.registrySize ?? '未找到'} 个颜色 id`);
  for (const kind of ['dark', 'light']) {
    const t = report[kind];
    console.log(`[${kind}] colors ${t.colors} · tokenColors ${t.tokenRules} 规则/${t.tokenScopes} scope · semanticTokenColors ${t.semantic}`);
  }
  console.log(`深浅键集一致：${report.keyParity ? '是 ✓' : '否 ✗'}`);
  for (const w of report.warnings) console.log(`⚠️  ${w}`);
  if (report.errors.length) {
    console.log(`\n发现 ${report.errors.length} 处不合规：`);
    for (const e of report.errors) console.log(`  ✗ ${e}`);
  } else {
    console.log('\n适配性校验全部通过 ✓');
  }
}

process.exit(report.errors.length ? 1 : 0);
