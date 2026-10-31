"""统一运行 My Cursor 项目的自动化回归测试。"""

import unittest
from pathlib import Path


def main():
    """从项目根目录发现并运行所有自动化测试。"""

    # 根据当前脚本的位置确定项目根目录
    project_root = Path(__file__).resolve().parent.parent

    # 使用绝对路径发现测试，避免依赖当前工作目录
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(project_root / "tests"),
        pattern="test_*.py",
        top_level_dir=str(project_root),
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
