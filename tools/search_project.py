"""My Cursor 项目关键词搜索工具：只读，不修改文件。"""

import os
from pathlib import Path


# 仅搜索明确允许的文本文件类型
ALLOWED_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".toml",
    ".yaml", ".yml", ".ini",
}

# 排除缓存、虚拟环境、版本库和备份目录
BLOCKED_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", "build", "dist",
}

BLOCKED_FILES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519", "credentials.json",
    "secrets.json", "secret.json", "credentials",
    "service-account.json", "token.json",
}

MAX_QUERY_LENGTH = 200
MAX_RESULTS_LIMIT = 100
MAX_FILES_SCANNED = 500
MAX_FILE_BYTES = 1_000_000
MAX_LINE_LENGTH = 300


def _is_inside_root(root: Path, target: Path) -> bool:
    """判断解析后的目标是否位于工作区内。"""
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _is_allowed_file(root: Path, file_path: Path) -> bool:
    """只允许工作区内的普通、非敏感文本文件。"""
    try:
        resolved = file_path.resolve()

        if not _is_inside_root(root, resolved):
            return False

        if not resolved.is_file():
            return False

        parts = [part.casefold() for part in file_path.relative_to(root).parts]

        if any(part.startswith(".") for part in parts):
            return False

        if any(part.startswith("backups_") for part in parts):
            return False

        if any(part in BLOCKED_DIRS for part in parts[:-1]):
            return False

        if parts[-1] in BLOCKED_FILES:
            return False

        if parts[-1].startswith(".env"):
            return False

        if resolved.suffix.casefold() not in ALLOWED_EXTENSIONS:
            return False

        if resolved.stat().st_size > MAX_FILE_BYTES:
            return False

        return True

    except (OSError, ValueError):
        return False


def search_project(
    root: Path,
    query: str,
    max_results: int = 50,
    allowed_root: Path | None = None,
) -> str:
    """
    在工作区内进行大小写不敏感的普通文本搜索。

    返回匹配文件的相对路径、行号和匹配行。
    不执行代码，也不修改文件。
    """
    if not isinstance(query, str):
        return "搜索请求被拒绝：关键词必须是字符串。"

    query = query.strip()

    if not query:
        return "搜索请求被拒绝：关键词不能为空。"

    if len(query) > MAX_QUERY_LENGTH:
        return f"搜索请求被拒绝：关键词不能超过 {MAX_QUERY_LENGTH} 个字符。"

    if (
        not isinstance(max_results, int)
        or isinstance(max_results, bool)
        or not 1 <= max_results <= MAX_RESULTS_LIMIT
    ):
        return f"搜索请求被拒绝：max_results 必须是 1 到 {MAX_RESULTS_LIMIT} 之间的整数。"

    try:
        root = Path(root).resolve()

        if allowed_root is not None:
            allowed_root = Path(allowed_root).resolve()
            if not allowed_root.is_dir():
                return "搜索失败：授权工作区目录不存在。"

            if not _is_inside_root(allowed_root, root):
                return "搜索请求被拒绝：搜索目录超出授权工作区范围。"

    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return f"搜索失败：工作区路径无效（{type(exc).__name__}）。"

    if not root.is_dir():
        return "搜索失败：工作区目录不存在。"

    matches = []
    scanned_files = 0
    stopped_by_limit = False
    needle = query.casefold()

    for current_dir, dir_names, file_names in os.walk(
        root, topdown=True, followlinks=False
    ):
        current_path = Path(current_dir)

        # 不进入隐藏目录、备份目录、虚拟环境及缓存目录。
        safe_dirs = []
        for name in dir_names:
            lower_name = name.casefold()
            candidate = current_path / name

            if lower_name.startswith(".") or lower_name.startswith("backups_"):
                continue

            if lower_name in BLOCKED_DIRS or candidate.is_symlink():
                continue

            try:
                resolved_dir = candidate.resolve()
                if _is_inside_root(root, resolved_dir) and resolved_dir.is_dir():
                    safe_dirs.append(name)
            except (OSError, RuntimeError):
                continue

        dir_names[:] = safe_dirs

        for name in file_names:
            candidate = current_path / name

            if not _is_allowed_file(root, candidate):
                continue

            if scanned_files >= MAX_FILES_SCANNED:
                stopped_by_limit = True
                break

            scanned_files += 1

            try:
                with candidate.open("r", encoding="utf-8") as handle:
                    for line_number, line in enumerate(handle, start=1):
                        if needle not in line.casefold():
                            continue

                        relative_path = candidate.relative_to(root).as_posix()
                        preview = line.rstrip("\r\n")

                        if len(preview) > MAX_LINE_LENGTH:
                            preview = preview[:MAX_LINE_LENGTH] + "..."

                        matches.append(
                            f"{relative_path}:{line_number}: {preview}"
                        )

                        if len(matches) >= max_results:
                            break

            except (OSError, UnicodeError, ValueError):
                # 无法读取的文件直接跳过，不输出文件内容或系统路径。
                continue

            if len(matches) >= max_results:
                break

        if stopped_by_limit or len(matches) >= max_results:
            break

    if not matches:
        result = f"没有找到关键词：{query}"
    else:
        result = (
            f"搜索关键词：{query}\n"
            f"匹配条数：{len(matches)}\n"
            + "\n".join(matches)
        )

    if stopped_by_limit:
        result += f"\n提示：已达到最多扫描 {MAX_FILES_SCANNED} 个文件的限制。"
    elif len(matches) >= max_results:
        result += f"\n提示：已达到最多返回 {max_results} 条结果的限制。"

    return result
