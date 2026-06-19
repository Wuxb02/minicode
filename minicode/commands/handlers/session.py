from __future__ import annotations

from minicode.commands.registry import Command, CommandContext, CommandType
from minicode.conversation import ConversationManager


async def handle_session(ctx: CommandContext) -> None:
    sm = ctx.session_manager
    if sm is None:
        ctx.ui.add_system_message("会话管理器未初始化")
        return

    parts = ctx.args.split(None, 1)
    sub = parts[0] if parts else ""

    if sub == "":
        # 无参数：显示交互式会话选择器
        await _show_selector(ctx)
        return

    if sub == "list":
        await _show_selector(ctx)
        return

    if sub == "resume":
        session_id = parts[1].strip() if len(parts) > 1 else ""
        if not session_id:
            await _show_selector(ctx)
            return
        candidates = ctx.config.get("_resume_candidates", [])
        if session_id.isdigit() and candidates:
            idx = int(session_id) - 1
            if 0 <= idx < len(candidates):
                session_id = candidates[idx]
        result = sm.resume(session_id)
        if result is None:
            ctx.ui.add_system_message(f"会话未找到: {session_id}")
            return
        if ctx.session:
            ctx.session.close()
        ctx.config["set_session"](result.session)
        conv = ConversationManager()
        for msg in result.messages:
            conv.history.append(msg)
        ctx.config["set_conversation"](conv)
        if ctx.agent:
            ctx.agent._loop_count = 0
        await ctx.config["render_restored"](result.messages)
        ctx.ui.add_system_message(
            f"会话已恢复: {session_id} ({result.session.meta.message_count} msgs)"
        )

    elif sub == "new":
        if ctx.session:
            ctx.session.close()
        new_session = sm.create()
        ctx.config["set_session"](new_session)
        ctx.config["set_conversation"](ConversationManager())
        if ctx.agent:
            ctx.agent._loop_count = 0
        ctx.config["clear_chat"]()
        ctx.ui.add_system_message(f"新会话已创建: {new_session.session_id}")

    elif sub == "delete":
        session_id = parts[1].strip() if len(parts) > 1 else ""
        if not session_id:
            ctx.ui.add_system_message("用法: /sessions delete <id>")
            return
        if ctx.session and ctx.session.session_id == session_id:
            ctx.ui.add_system_message("不能删除当前活跃的会话。")
            return
        if sm.delete(session_id):
            ctx.ui.add_system_message(f"会话已删除: {session_id}")
        else:
            ctx.ui.add_system_message(f"会话未找到: {session_id}")

    else:
        ctx.ui.add_system_message(
            "用法: /sessions [list | resume <id> | new | delete <id>]"
        )


async def _show_selector(ctx: CommandContext) -> None:
    """显示交互式会话选择器，由选择事件驱动后续恢复流程。"""
    sm = ctx.session_manager
    metas = sm.list()
    if not metas:
        ctx.ui.add_system_message("没有已保存的会话。")
        return
    show_selector = ctx.config.get("show_session_selector")
    if show_selector:
        await show_selector(metas)


SESSION_COMMAND = Command(
    name="sessions",
    description="会话管理",
    usage="/sessions [list | resume <id> | new | delete <id>]",
    type=CommandType.LOCAL,
    handler=handle_session,
)
