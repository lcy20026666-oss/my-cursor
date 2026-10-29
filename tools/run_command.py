from pathlib import Path
import subprocess

ALLOWED_COMMANDS = {"python", "py", "git"}

GIT_READONLY_ALLOWLIST = {
    ("git", "status", "--short"),
    ("git", "diff"),
    ("git", "diff", "--cached"),
    ("git", "log", "-5", "--oneline"),
    ("git", "branch", "--show-current"),
}


def _format_result(result) -> str:
    return (
        f"退出码：{result.returncode}\n"
        f"标准输出：\n{result.stdout or '(空)'}\n"
        f"标准错误：\n{result.stderr or '(空)'}"
    )


def _resolve_python_command(root: Path, command: list[str]):
    """只允许查询 Python 版本，或运行工作区内的单个 .py 脚本。"""
    if len(command) == 2 and command[1] == "--version":
        return command

    if len(command) != 2:
        raise ValueError(
            "Python 命令仅允许查询版本，或运行一个工作区内的 .py 脚本。"
        )

    script_arg = command[1]

    if not isinstance(script_arg, str) or not script_arg.strip():
        raise ValueError("脚本路径必须是非空字符串。")

    if script_arg.startswith("-"):
        raise ValueError("不允许使用 Python 解释器选项，只允许运行 .py 脚本。")

    workspace = root.resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("工作区路径不是目录。")

    script = (workspace / script_arg).resolve(strict=True)

    if script.suffix.lower() != ".py":
        raise ValueError("只允许运行 .py 文件。")

    if not script.is_file():
        raise ValueError("脚本路径不是普通文件。")

    if workspace not in script.parents:
        raise ValueError("拒绝运行工作区之外的脚本。")

    return [command[0], str(script)]


def _is_git_command_allowed(command: list[str]) -> bool:
    """只允许与 Git 只读白名单完全匹配的命令。"""
    if not all(isinstance(arg, str) for arg in command):
        return False

    return tuple(command) in GIT_READONLY_ALLOWLIST


def run_command(root: Path, command: list[str], timeout: int = 15) -> str:
    """运行受限命令；Python 使用脚本限制，Git 使用只读白名单。"""
    try:
        if not isinstance(command, list) or not command:
            return "拒绝执行：命令必须是非空列表。"

        if not all(isinstance(arg, str) for arg in command):
            return "拒绝执行：命令参数必须全部是字符串。"

        executable = command[0].lower()

        if executable not in ALLOWED_COMMANDS:
            return "拒绝执行：目前只允许 python、py、git 命令。"

        workspace = Path(root).resolve(strict=True)
        if not workspace.is_dir():
            return "拒绝执行：工作区路径不是有效目录。"

        if executable in {"python", "py"}:
            command = _resolve_python_command(workspace, command)

        elif executable == "git":
            if not _is_git_command_allowed(command):
                return "拒绝执行：Git 命令不在只读白名单中。"

        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
            return "拒绝执行：超时时间必须是正数。"

        if timeout <= 0 or timeout > 60:
            return "拒绝执行：超时时间必须大于 0 且不超过 60 秒。"

        result = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return _format_result(result)

    except subprocess.TimeoutExpired:
        return f"执行超时：超过 {timeout} 秒，命令已停止等待。"
    except (ValueError, FileNotFoundError, OSError) as exc:
        return f"执行失败：{type(exc).__name__}: {exc}"
    except Exception as exc:
        return f"执行失败：{type(exc).__name__}: {exc}"
