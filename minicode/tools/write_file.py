from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from minicode.tools.base import Tool, ToolResult
from minicode.tools.diff_gen import MAX_OLD_CONTENT_BYTES, _is_likely_binary, generate_diff

if TYPE_CHECKING:
    from minicode.cache import FileCache
    from minicode.tools.file_state_cache import FileStateCache


class Params(BaseModel):
    file_path: str = Field(description="Path to the file to write")
    content: str = Field(description="Content to write to the file")


class WriteFile(Tool):
    name = "WriteFile"
    description = (
        "Write content to a file, creating parent directories if needed. Overwrites existing files.\n"
        "You MUST read existing files with ReadFile before overwriting them. This tool will fail otherwise."
    )
    params_model = Params
    category = "write"

    def __init__(self, file_cache: FileCache | None = None, file_history: Any = None, file_state_cache: FileStateCache | None = None) -> None:
        self._cache = file_cache
        self.file_history = file_history
        self._state_cache = file_state_cache

    async def execute(self, params: Params) -> ToolResult:
        if self.file_history is not None:
            self.file_history.track_edit(params.file_path)

        path = Path(params.file_path)

        # 读取旧内容用于 diff 生成（仅在文件存在且为文本时）
        old_content: str | None = None
        if path.exists():
            try:
                old_bytes = path.read_bytes()
                if len(old_bytes) <= MAX_OLD_CONTENT_BYTES and not _is_likely_binary(old_bytes):
                    old_content = old_bytes.decode("utf-8", errors="replace")
            except Exception:
                pass

        if self._state_cache and path.exists():
            resolved = str(path.resolve())
            ok, err_msg = self._state_cache.check(resolved)
            if not ok:
                return ToolResult(output=err_msg, is_error=True)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params.content, encoding="utf-8")
            if self._cache:
                self._cache.invalidate(str(path.resolve()))
            if self._state_cache:
                self._state_cache.update(str(path.resolve()))
        except Exception as e:
            return ToolResult(output=f"Error writing file: {e}", is_error=True)

        diff_str = None
        try:
            diff_str = generate_diff(str(path), old_content, params.content)
        except Exception:
            pass

        return ToolResult(
            output=f"Successfully wrote to {params.file_path}",
            diff=diff_str,
        )
