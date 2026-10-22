#!/usr/bin/env python3
"""Platform entry point. Default is read-only; never runs cleanup on import."""
import runpy
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    if sys.platform == "darwin":
        script = root / "vendor/mac_cleanup/claude_cleanup.py"
    elif sys.platform == "win32":
        script = root / "cleanup_windows.py"
    else:
        print("清理 Skill 当前仅支持 macOS 和 Windows。", file=sys.stderr)
        return 2
    if len(sys.argv) == 1:
        sys.argv.append("--audit")
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
