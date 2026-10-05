#!/usr/bin/env python3
"""先在临时目录验证注册表与锚点，再更新固定快照。"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
from utf8_console import use_utf8_console


SCRIPTS = Path(__file__).resolve().parent


def update(vscode_path=None, output_dir=SCRIPTS.parent / "data"):
    with tempfile.TemporaryDirectory(prefix="sakura-registry-") as temporary:
        staging = Path(temporary)
        registry = staging / "registry.json"
        anchors = staging / "anchors.json"
        source = ["--vscode-path", str(vscode_path)] if vscode_path else []
        subprocess.run([sys.executable, str(SCRIPTS / "extract_registry.py"),
                        *source, "--output", str(registry)], check=True)
        subprocess.run([sys.executable, str(SCRIPTS / "derive_colors.py"),
                        *source, "--registry", str(registry), "--output", str(anchors)], check=True)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for snapshot in (registry, anchors):
            (output_dir / snapshot.name).write_bytes(snapshot.read_bytes())


def main():
    use_utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vscode-path", type=Path)
    options = parser.parse_args()
    try:
        update(options.vscode_path)
    except subprocess.CalledProcessError as error:
        print("快照提取或解析失败，data/ 保持不变", file=sys.stderr)
        return error.returncode
    print("注册表和锚点已更新；请复核差异并运行 npm run verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
