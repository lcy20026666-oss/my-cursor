from pathlib import Path


def _safe_path(root: Path, relative_path: str) -> Path:
    """确保目标路径位于工作区内。"""
    root = root.resolve()
    target = (root / relative_path).resolve()

    if target != root and root not in target.parents:
        raise ValueError("拒绝访问工作区之外的路径。")

    return target


def read_file(
    root: Path,
    relative_path: str,
    max_chars: int = 20000,
    start_line: int = 1,
    line_count: int | None = None,
) -> str:
    """
    读取工作区内的 UTF-8 文本文件。

    start_line：从第几行开始，行号从 1 开始。
    line_count：读取多少行；None 表示读取到文件末尾。
    max_chars：返回内容的最大字符数。
    """
    try:
        path = _safe_path(Path(root), relative_path)

        if not path.is_file():
            return f"失败：文件不存在：{relative_path}"

        if not isinstance(start_line, int) or isinstance(start_line, bool):
            return "失败：start_line 必须是整数。"

        if start_line < 1:
            return "失败：start_line 必须大于等于 1。"

        if line_count is not None:
            if (
                not isinstance(line_count, int)
                or isinstance(line_count, bool)
                or line_count < 1
            ):
                return "失败：line_count 必须是正整数，或 None。"

        if not isinstance(max_chars, int) or max_chars < 1:
            return "失败：max_chars 必须是正整数。"

        # 先按行读取，再截取需要的范围
        with path.open("r", encoding="utf-8") as file:
            selected_lines = []

            for line_number, line in enumerate(file, start=1):
                if line_number < start_line:
                    continue

                if line_count is not None:
                    if line_number >= start_line + line_count:
                        break

                selected_lines.append(line)

        if not selected_lines:
            return (
                f"读取成功：{relative_path}\n"
                f"请求起始行：{start_line}\n"
                "该位置没有可读取的内容。"
            )

        content = "".join(selected_lines)
        truncated = len(content) > max_chars

        if truncated:
            content = content[:max_chars] + "\n...[内容已截断]"

        end_line = start_line + len(selected_lines) - 1

        result = (
            f"读取成功：{relative_path}\n"
            f"读取行范围：{start_line}-{end_line}\n"
            f"---\n{content}"
        )

        if truncated:
            result += "\n提示：内容超过字符上限，已截断。"

        return result

    except UnicodeDecodeError:
        return f"读取失败：{relative_path} 不是有效的 UTF-8 文本文件。"
    except Exception as exc:
        return f"读取失败：{type(exc).__name__}: {exc}"
