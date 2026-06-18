"""为 WriteFile/EditFile 工具生成 unified-diff 格式的变更展示。

仅供 TUI 层使用，不进入 LLM 对话上下文。
"""

from __future__ import annotations

import difflib

# 超过此大小的旧文件跳过读取，避免性能问题
MAX_OLD_CONTENT_BYTES = 1024 * 1024  # 1 MB


def _is_likely_binary(data: bytes) -> bool:
    """启发式检测：前 8KB 含 null 字节则认为是二进制文件。"""
    chunk = data[:8192]
    return b"\x00" in chunk


def _ensure_ending_newline(lines: list[str]) -> None:
    """确保最后一行以换行符结尾，让 difflib 行为与 git diff 一致。"""
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"


def generate_diff(
    file_path: str,
    old_content: str | None,
    new_content: str,
) -> str | None:
    """生成 unified diff 字符串。

    Args:
        file_path: 文件路径（用于 diff 头部的 a/ b/ 前缀）
        old_content: 修改前文件内容，None 表示新建文件
        new_content: 修改后文件内容

    Returns:
        unified diff 字符串，无变更时返回 None
    """
    if old_content is None:
        if not new_content:
            return None  # 空的新文件，无 diff
        old_lines: list[str] = []
    else:
        old_lines = old_content.splitlines(keepends=True)

    new_lines = new_content.splitlines(keepends=True)

    _ensure_ending_newline(old_lines)
    _ensure_ending_newline(new_lines)

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
    )

    if not diff:
        return None

    # difflib 输出混合了自带 \n 的行（来自 keepends 输入）和头部行（不带 \n），
    # 统一去除尾随 \n 后重新拼接
    diff = [line.rstrip("\n") for line in diff]
    return "\n".join(diff)
