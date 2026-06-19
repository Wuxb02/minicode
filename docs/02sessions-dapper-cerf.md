# 为 `/sessions` 命令增加交互式会话选择器

## Context

当前 `/session` 命令只能以纯文本方式列出历史会话，用户需要通过 `/session resume <id>` 或数字序号来恢复会话，操作不够直观。项目中已存在一个完整的 `InlineResumeWidget` 组件（`session_dialog.py`），提供可搜索、键盘导航的会话选择 UI，但尚未接入命令系统。

本次改动将 `/session`（及新别名 `/sessions`）命令与 `InlineResumeWidget` 连接起来，实现输入命令后在输入框上方弹出交互式选择框的体验。

## 修改文件

### 1. `minicode/commands/handlers/session.py` — 命令重命名与路由

- 将 `SESSION_COMMAND` 的 `name` 从 `"session"` 改为 `"sessions"`，usage 同步更新
- 修改 `handle_session`：当无参数、`list` 或 `resume` 不带 ID 时，调用新的 `show_session_selector` config 回调，传入会话列表，不再输出纯文本

### 2. `minicode/app.py` — 挂载与事件处理

- 新增 `_show_session_selector(metas: list[SessionMeta])` 方法：
  - 将 `InlineResumeWidget` 挂载到 `#chat-area` 底部
  - 禁用 `#chat-input`，滚动到底部
  - 与现有 `_show_plan_approval()` 模式一致
- 新增 `on_inline_resume_widget_selected()` 消息处理器：
  - 若 `session_id` 为 `None`（ESC 取消）：仅移除 widget、恢复输入
  - 若 `session_id` 有值：执行完整的会话恢复流程（调用 `SessionManager.resume`、关闭当前会话、创建新的 `ConversationManager`、渲染历史消息、重置 agent loop counter）
- 在 `_build_command_context` 的 `config` 字典中添加 `show_session_selector` 回调

### 3. `minicode/session_dialog.py` — 无需修改

现有的 `InlineResumeWidget` 已具备完整功能：键盘导航、实时搜索过滤、会话选择。代码可直接复用。

## 验证方式

1. 启动 `uv run minicode`
2. 输入 `/sessions` → 确认弹出会话选择器
3. 输入 `/sessions resume` → 同样弹出选择器（无 ID 时）
4. 使用 ↑↓ 键浏览会话、输入文字搜索过滤
5. 按 Enter 选择一个历史会话 → 确认会话被正确恢复，历史消息渲染到聊天区域
6. 按 ESC 取消 → 确认选择器消失，输入框恢复
7. 确认 `/sessions resume <id>`、`/sessions new`、`/sessions delete <id>` 仍正常工作
