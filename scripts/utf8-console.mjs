// 把 Windows 控制台输出代码页临时切到 UTF-8，让 Node 写出的中文和 Python 侧一致可读。
// Node 的 stdout 永远按 UTF-8 编码，在 GBK 代码页的控制台里必然乱码；Python 侧由
// utf8_console.py 做同样的事，两边必须用同一套编码，否则一次 npm run verify 输出两半乱码。
import { spawnSync } from 'node:child_process';

const UTF8_CODE_PAGE = 65001;

function codePage() {
  const result = spawnSync('chcp', [], { encoding: 'utf8', shell: true });
  if (result.error || !result.stdout) return 0;
  const match = /:\s*(\d+)/.exec(result.stdout) || /\b(\d{3,6})\b/.exec(result.stdout);
  return match ? Number(match[1]) : 0;
}

function setCodePage(page) {
  spawnSync(`chcp ${page} >nul`, [], { shell: true, stdio: 'ignore' });
}

export function useUtf8Console() {
  if (process.platform !== 'win32') return;
  const before = codePage();
  if (!before || before === UTF8_CODE_PAGE) return;
  setCodePage(UTF8_CODE_PAGE);
  process.on('exit', () => {
    try { setCodePage(before); } catch { /* 退出时尽力还原 */ }
  });
}
