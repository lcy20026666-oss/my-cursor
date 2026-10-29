from pathlib import Path
import difflib


_SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.test",
    ".env.production",
    ".env.staging",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
}


def _is_sensitive_file(path: Path) -> bool:
    """判断目标文件是否为敏感配置文件或密钥文件。"""
    name = path.name.lower()

    if name in _SENSITIVE_NAMES:
        return True

    if name.startswith(".env."):
        return True

    if name.endswith((".pem", ".key")):
        return True

    return False


def _safe_path(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    target = (root / relative_path).resolve()

    if target != root and root not in target.parents:
        raise ValueError("拒绝修改工作区之外的路径。")

    if _is_sensitive_file(target):
        raise ValueError("拒绝修改敏感配置文件或密钥文件。")

    return target


def edit_file(root: Path, relative_path: str, new_content: str) -> str:
    """用新内容替换工作区内文本文件，并返回 unified diff。"""
    try:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("文件路径不能为空。")

        if not isinstance(new_content, str):
            raise TypeError("新文件内容必须是字符串。")

        path = _safe_path(Path(root), relative_path)

        if path.exists() and not path.is_file():
            raise ValueError("目标路径不是普通文件。")

        old_content = (
            path.read_text(encoding="utf-8")
            if path.exists()
            else ""
        )

        diff = "".join(difflib.unified_diff(
            old_content.splitlines(True),
            new_content.splitlines(True),
            fromfile=f"{relative_path} (旧)",
            tofile=f"{relative_path} (新)"
        ))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")

        return (
            f"修改成功：{relative_path}\n"
            f"差异预览：\n{diff or '（内容没有变化）'}"
        )

    except Exception as exc:
        return f"修改失败：{type(exc).__name__}: {exc}"
