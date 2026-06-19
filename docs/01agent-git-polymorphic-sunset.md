# 在 TUI 中以 Git Diff 形式展示代码修改

## Context

当前 WriteFile/EditFile 工具执行后，TUI 中仅显示纯文本成功消息（如 "Successfully wrote to /path/to/file"），用户展开工具结果时无法直观看到代码变更的差异。本方案实现类似 `git diff` 的彩色 unified diff 展示，提升代码修改的可视化体验。

核心约束：diff 内容仅用于 TUI 显示，不进入 LLM 对话上下文（不增加 token 消耗）。

## 修改文件清单

### 1. 新建 `minicode/tools/diff_gen.py` — 统一 diff 生成模块

- 使用 Python 标准库 `difflib.unified_diff` 生成 unified diff 格式
- `generate_diff(file_path, old_content, new_content) -> str | None` 函数
- 二进制文件检测（前 8KB 含 null 字节则跳过）
- 1MB 以上的旧文件跳过读取，避免性能问题
- **不做 diff 内容截断**，完整 diff 交由 TUI 层渲染（`VerticalScroll` 容器自然支持滚动）
- 确保尾行换行符语义与 git diff 一致

### 2. 修改 `minicode/tools/base.py`

- `ToolResult` dataclass 新增可选字段 `diff: str | None = None`

### 3. 修改 `minicode/tools/write_file.py`

- 在 `execute()` 中，写入前先读取旧文件内容（文件存在时）
- 写入后调用 `generate_diff` 生成 diff 字符串
- 返回 `ToolResult(output=..., diff=diff_str)`
- 错误路径返回 `diff=None`，保持现有行为

### 4. 修改 `minicode/tools/edit_file.py`

- 在 `execute()` 中，利用已有的 `content` 变量（旧内容，line 51）和 `new_content`（新内容，line 64）
- 写入后调用 `generate_diff` 生成 diff 字符串
- 返回 `ToolResult(output=..., diff=diff_str)`
- 错误路径返回 `diff=None`

### 5. 修改 `minicode/agent.py`

- `ToolResultEvent` dataclass 新增可选字段 `diff: str | None = None`
- 在 3 处 `yield ToolResultEvent(...)` 中提取 `result.diff` 透传：并行批量路径 (line 680)、顺序执行路径 (line 765)、hook 拒绝路径保持无 diff (line 719)
- **关键**：`ToolResultBlock.content` 仅使用 `result.output`，不包含 diff，LLM 上下文不受影响

### 6. 修改 `minicode/app.py`

#### 6a. `ToolCallBlock.set_result` 方法签名增加 `diff` 参数

```python
def set_result(self, output: str, is_error: bool, elapsed: float,
               diff: str | None = None) -> None:
```

存储 `self._diff_output = diff`

#### 6b. 调用处传递 diff

`_send_message()` 中 `block.set_result(event.output, event.is_error, event.elapsed, diff=event.diff)` (line 1362)

#### 6c. `_format_detail` 函数增加 `diff` 参数

对 `WriteFile`/`EditFile` 分支：当 `diff` 不为 None 时，调用 `_colorize_diff(diff)` 渲染彩色 diff（不限行数，完整展示）；否则回退现有纯文本渲染（保持 `MAX_TRUNCATED_LINES=20` 的截断行为）。

#### 6d. 新增 `_colorize_diff` 和 `_escape_rich` 函数

利用 Textual `Static` widget 原生支持的 Rich markup（`[...]` 标签）实现着色：

- `@@ ... @@` hunk 头部 → `[bold cyan]`
- `+` 新增行 → `[green]`
- `-` 删除行 → `[red]`
- 上下文行 → `[dim]`
- `_escape_rich` 转义代码内容中的 `[` `]` 防止误解析

**折叠策略**：不截断 diff 内容。完整的 colored diff 渲染在 `Static` widget 中，父级 `VerticalScroll` 容器提供自然滚动。`ToolCallBlock` 自带的点击折叠/展开作为第一层折叠：折叠时只显示 `"✓ WriteFile (1.2s)"` 摘要行，展开时才显示完整 diff。这种双层机制自然地处理了长 diff 的展示问题。

#### 6e. `_render_expanded` 方法

传递 `self._diff_output` 给 `_format_detail`

## 数据流

```
WriteFile/EditFile.execute()
  └→ ToolResult(output=<LLM文本>, diff=<unified diff|None>)
       ├→ [LLM路径] ToolResultBlock(content=output) → 对话上下文 (diff 不进入)
       └→ [TUI路径] ToolResultEvent(output, diff)
             └→ ToolCallBlock.set_result(output, diff)
                  └→ _format_detail + _colorize_diff → Static 渲染
```

## 边界情况处理

| 场景 | 处理 |
|---|---|
| 编辑/写入错误 (is_error=True) | diff 始终为 None，回退现有错误渲染 |
| 二进制文件 | WriteFile 跳过旧内容读取，diff=None |
| 大文件 (>1MB 旧内容) | 跳过读取，diff=None |
| diff 内容很多 | 不做截断。`ToolCallBlock` 点击折叠/展开控制显示；展开时 `VerticalScroll` 容器提供滚动 |
| 代码含 `[` `]` | `_escape_rich` 转义为 `\[` `\]` |
| 新旧内容一致 | `difflib.unified_diff` 返回空，`generate_diff` 返回 None |
| 其他工具 (Bash, ReadFile 等) | diff 始终为 None，不受影响 |

## 向后兼容性

- `ToolResult.diff` 默认 `None`，现有代码无需修改
- `ToolResultEvent.diff` 默认 `None`，现有代码无需修改
- `set_result` 的 `diff` 参数默认 `None`，现有测试无需修改
- `_format_detail` 的 `diff` 参数默认 `None`，未传则行为不变

## 验证方案

1. 启动 `uv run minicode`，发送 prompt 让 agent 修改一个文件
2. 展开 `ToolCallBlock`（点击 WriteFile/EditFile 结果行），确认显示彩色 unified diff
3. 确认新增行显示绿色 `+`、删除行显示红色 `-`、hunk 头部显示青色
4. 确认会话恢复后仍正常渲染
5. 确认其他工具 (Bash, ReadFile) 展示不受影响
6. 运行 `uv run pytest` 确认无回归
