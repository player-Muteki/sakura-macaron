"""把脚本输出统一到 UTF-8。

Windows 上 Python 默认按控制台代码页编码输出：中文系统是 GBK，英文系统是 cp1252，
后者遇到中文直接 UnicodeEncodeError 崩溃。同时 Node 侧永远写 UTF-8，于是同一个终端里
两种语言的输出必然有一半是乱码。这里统一按 UTF-8 写，并在 Windows 控制台把输出代码页
临时切到 65001，进程退出时还原，避免污染用户后续的 shell 状态。
"""
import atexit
import sys

UTF8_CODE_PAGE = 65001


def _reconfigure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def _switch_console_code_page() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        before = int(kernel32.GetConsoleOutputCP())
    except (AttributeError, OSError, ValueError):
        return
    if before in (0, UTF8_CODE_PAGE):
        return
    try:
        kernel32.SetConsoleOutputCP(UTF8_CODE_PAGE)
    except OSError:
        return
    atexit.register(lambda: kernel32.SetConsoleOutputCP(before))


def use_utf8_console() -> None:
    _reconfigure_streams()
    _switch_console_code_page()
