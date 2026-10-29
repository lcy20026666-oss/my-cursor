from pathlib import Path
import subprocess
import sys

def run_tests(root: Path, timeout: int = 30) -> str:
    """使用当前 Python 解释器运行 tests 目录中的 unittest 测试。"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=Path(root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, shell=False
        )
        return (
            f"测试退出码：{result.returncode}\n"
            f"标准输出：\n{result.stdout or '(空)'}\n"
            f"标准错误：\n{result.stderr or '(空)'}"
        )
    except subprocess.TimeoutExpired:
        return f"测试超时：超过 {timeout} 秒。"
    except Exception as exc:
        return f"测试失败：{type(exc).__name__}: {exc}"
