"""统一运行 My Cursor 项目的自动化回归测试。"""

import unittest


def main():
    """发现并运行当前 tests 目录下的测试。"""
    suite = unittest.defaultTestLoader.discover(
        start_dir="tests",
        pattern="test_*.py",
        top_level_dir=".",
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
