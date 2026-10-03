import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

export const HEX = /^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;
const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const color = value => typeof value === 'string' && HEX.test(value);
const fontStyle = value => typeof value === 'string' && /^(?:(?:italic|bold|underline|strikethrough)(?:\s+|$))*$/.test(value);
const selector = /^(?:\*|[\w-]+)(?:\.[\w-]+)*(?::[\w+-]+)?$/;

export function readInputs(args = process.argv.slice(2)) {
  const { values } = parseArgs({ args, options: {
    json: { type: 'boolean', default: false },
    'theme-dir': { type: 'string', default: fileURLToPath(new URL('../themes/', import.meta.url)) },
    registry: { type: 'string', default: fileURLToPath(new URL('../data/registry.json', import.meta.url)) },
  } });
  const snapshot = JSON.parse(readFileSync(resolve(values.registry), 'utf8'));
  if (!record(snapshot.colors) || !Object.keys(snapshot.colors).length || !snapshot.source?.version ||
      !/^[a-f0-9]{40}$/.test(snapshot.source.commit ?? '') || !/^[a-f0-9]{64}$/.test(snapshot.source.bundleSha256 ?? '')) {
    throw new Error('注册表快照缺失颜色键或来源信息；不能跳过校验');
  }
  const themes = Object.fromEntries(['dark', 'light'].map(kind => [kind,
    JSON.parse(readFileSync(resolve(values['theme-dir'], `sakura-macaron-${kind}.json`), 'utf8')),
  ]));
  return { asJson: values.json, registry: new Set(Object.keys(snapshot.colors)), source: snapshot.source, themes };
}

export function checkColors(themes, registry) {
  const report = { registrySize: registry.size };
  for (const [kind, theme] of Object.entries(themes)) {
    const colors = record(theme?.colors) ? theme.colors : {};
    report[kind] = {
      keys: Object.keys(colors).length,
      missing: [...registry].filter(key => !Object.hasOwn(colors, key)).sort(),
      invalid: Object.keys(colors).filter(key => !registry.has(key)).sort(),
      values: Object.entries(colors).filter(([, value]) => !color(value)).map(([key, value]) => `${key} = ${JSON.stringify(value)}`),
    };
  }
  const darkKeys = Object.keys(record(themes.dark?.colors) ? themes.dark.colors : {});
  const lightKeys = Object.keys(record(themes.light?.colors) ? themes.light.colors : {});
  report.darkOnly = darkKeys.filter(key => !lightKeys.includes(key));
  report.lightOnly = lightKeys.filter(key => !darkKeys.includes(key));
  report.errors = [];
  for (const kind of ['dark', 'light']) {
    for (const key of report[kind].missing) report.errors.push(`${kind}: 缺失颜色 ${key}`);
    for (const key of report[kind].invalid) report.errors.push(`${kind}: 未注册颜色 ${key}`);
    for (const value of report[kind].values) report.errors.push(`${kind}: 非法色值 ${value}`);
  }
  if (report.darkOnly.length || report.lightOnly.length) report.errors.push('深浅颜色键集不一致');
  return report;
}

export function checkStructure(theme, kind) {
  const errors = [];
  const reject = message => errors.push(`${kind}: ${message}`);
  if (!record(theme)) return [`${kind}: 主题必须是对象`];
  if (theme.$schema !== 'vscode://schemas/color-theme') reject('$schema 不正确');
  if (typeof theme.name !== 'string' || !theme.name.trim()) reject('name 必须是非空字符串');
  if (theme.type !== kind) reject(`type 应为 ${kind}`);
  if (theme.semanticHighlighting !== true) reject('semanticHighlighting 必须开启');
  if ('include' in theme) reject('独立主题不允许 include');
  if (!record(theme.colors)) reject('colors 必须是对象');
  if (!Array.isArray(theme.tokenColors) || !theme.tokenColors.length) {
    reject('tokenColors 必须是非空数组');
  } else {
    theme.tokenColors.forEach((rule, index) => {
      const label = `tokenColors[${index}]`;
      if (!record(rule)) return reject(`${label} 必须是对象`);
      const scopes = Array.isArray(rule.scope) ? rule.scope : [rule.scope];
      if (!scopes.length || scopes.some(scope => typeof scope !== 'string' || !scope.trim())) reject(`${label}.scope 必须是非空字符串或字符串数组`);
      if (!record(rule.settings)) return reject(`${label}.settings 必须是对象`);
      for (const [key, value] of Object.entries(rule.settings)) {
        if (!['foreground', 'background', 'fontStyle'].includes(key)) reject(`${label}.settings.${key} 不支持`);
        else if (key === 'fontStyle' ? !fontStyle(value) : !color(value)) reject(`${label}.settings.${key} 值非法`);
      }
    });
  }
  if (!record(theme.semanticTokenColors) || !Object.keys(theme.semanticTokenColors).length) {
    reject('semanticTokenColors 必须是非空对象');
  } else {
    for (const [key, value] of Object.entries(theme.semanticTokenColors)) {
      const label = `semanticTokenColors.${key}`;
      if (!selector.test(key)) reject(`${label} selector 格式非法`);
      if (typeof value === 'string') {
        if (!color(value)) reject(`${label} 非法色值`);
      } else if (record(value) && Object.keys(value).length) {
        for (const [setting, entry] of Object.entries(value)) {
          if (setting === 'foreground') { if (!color(entry)) reject(`${label}.foreground 非法色值`); }
          else if (setting === 'fontStyle') { if (!fontStyle(entry)) reject(`${label}.fontStyle 值非法`); }
          else if (['bold', 'italic', 'underline', 'strikethrough'].includes(setting)) {
            if (typeof entry !== 'boolean') reject(`${label}.${setting} 必须是 boolean`);
          } else reject(`${label}.${setting} 不支持`);
        }
      } else reject(`${label} 必须是颜色或非空样式对象`);
    }
  }
  return errors;
}

export function statistics(theme) {
  return {
    colors: record(theme?.colors) ? Object.keys(theme.colors).length : 0,
    tokenRules: Array.isArray(theme?.tokenColors) ? theme.tokenColors.length : 0,
    tokenScopes: Array.isArray(theme?.tokenColors) ? theme.tokenColors.reduce((sum, rule) => sum + (Array.isArray(rule?.scope) ? rule.scope.length : typeof rule?.scope === 'string' ? 1 : 0), 0) : 0,
    semantic: record(theme?.semanticTokenColors) ? Object.keys(theme.semanticTokenColors).length : 0,
  };
}

export function runCheck(structure = false) {
  try {
    const { asJson, registry, source, themes } = readInputs();
    const report = { ...checkColors(themes, registry), source };
    if (structure) {
      for (const kind of ['dark', 'light']) report.errors.push(...checkStructure(themes[kind], kind));
      report.statistics = Object.fromEntries(Object.entries(themes).map(([kind, theme]) => [kind, statistics(theme)]));
    }
    if (asJson) console.log(JSON.stringify(report, null, 2));
    else {
      console.log(`固定基准 VS Code ${source.version}: ${registry.size} 个颜色键`);
      for (const kind of ['dark', 'light']) console.log(`${kind}: ${report[kind].keys} colors · 缺失 ${report[kind].missing.length} · 未注册 ${report[kind].invalid.length} · 非法色值 ${report[kind].values.length}`);
      for (const error of report.errors) console.error(error);
      console.log(report.errors.length ? `失败：${report.errors.length} 项` : '全部通过（未跳过注册表检查）');
    }
    process.exitCode = report.errors.length ? 1 : 0;
  } catch (error) {
    if (process.argv.includes('--json')) console.log(JSON.stringify({ errors: [error.message] }));
    else console.error(`校验失败：${error.message}`);
    process.exitCode = 1;
  }
}
