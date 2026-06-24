#!/usr/bin/env python3
"""
自动化数据预处理工具 — 入口
默认启动 GUI；传参则进入 CLI 模式
"""
from __future__ import annotations

import sys


def main():
    if len(sys.argv) > 1:
        # CLI 模式
        from cli import main as cli_main
        return cli_main()
    else:
        # GUI 模式
        from gui.app import launch_gui
        launch_gui()
        return 0


if __name__ == "__main__":
    sys.exit(main())
