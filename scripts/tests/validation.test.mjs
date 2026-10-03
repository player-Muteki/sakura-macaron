import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = fileURLToPath(new URL('../../', import.meta.url));

function checkWithThemes(script, mutate) {
  const directory = mkdtempSync(join(tmpdir(), 'sakura theme 空格 '));
  try {
    for (const kind of ['dark', 'light']) {
      const filename = `sakura-macaron-${kind}.json`;
      const theme = JSON.parse(readFileSync(join(root, 'themes', filename), 'utf8'));
      mutate(theme, kind);
      writeFileSync(join(directory, filename), JSON.stringify(theme));
    }
    const result = spawnSync(process.execPath, [join(root, 'scripts', script), '--theme-dir', directory, '--json'], {
      encoding: 'utf8',
      env: { ...process.env, VSCODE_PATH: join(directory, 'not-installed') },
    });
    assert.ifError(result.error);
    return result;
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test('both validators reject the same missing color in both themes', () => {
  for (const script of ['check-theme.mjs', 'check-schema.mjs']) {
    const result = checkWithThemes(script, theme => { delete theme.colors['editor.background']; });
    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(result.stdout, /editor\.background/);
  }
});

test('valid themes pass without an installed editor, including paths with spaces', () => {
  const result = checkWithThemes('check-schema.mjs', () => {});
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(JSON.parse(result.stdout).registrySize, 992);
});

test('unknown keys and invalid hex values fail', () => {
  for (const script of ['check-theme.mjs', 'check-schema.mjs']) {
    const result = checkWithThemes(script, theme => {
      theme.colors['notAColor.invalid'] = '#xyz';
    });
    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(result.stdout, /notAColor\.invalid/);
  }
});

test('semantic colors and boolean styles are validated', () => {
  for (const value of ['red', { foreground: '#gggggg' }, { bold: 'yes' }, { background: '#ffffff' }, null]) {
    const result = checkWithThemes('check-schema.mjs', theme => { theme.semanticTokenColors.variable = value; });
    assert.equal(result.status, 1, result.stdout + result.stderr);
    assert.match(result.stdout, /semanticTokenColors\.variable/);
  }
});

test('custom semantic types, wildcard modifiers and language selectors remain legal', () => {
  const result = checkWithThemes('check-schema.mjs', theme => {
    theme.semanticTokenColors['*.readonly:typescript'] = { foreground: '#aabbcc', bold: true };
    theme.semanticTokenColors['extensionType.customModifier'] = '#abc';
  });
  assert.equal(result.status, 0, result.stdout + result.stderr);
});

test('malformed TextMate settings and top-level fields fail', () => {
  for (const mutate of [
    theme => { theme.tokenColors[0].settings.fontStyle = 'blinking'; },
    theme => { theme.tokenColors[0].scope = [42]; },
    theme => { theme.semanticHighlighting = false; },
    theme => { theme.type = 'hc'; },
    theme => { theme.colors = []; },
  ]) {
    const result = checkWithThemes('check-schema.mjs', mutate);
    assert.equal(result.status, 1, result.stdout + result.stderr);
  }
});

test('a missing registry is a hard failure, not a skipped check', () => {
  const result = spawnSync(process.execPath, [join(root, 'scripts/check-theme.mjs'), '--registry', join(root, 'not-present.json'), '--json'], { encoding: 'utf8' });
  assert.ifError(result.error);
  assert.equal(result.status, 1, result.stdout + result.stderr);
  assert.match(result.stdout, /not-present/);
});
