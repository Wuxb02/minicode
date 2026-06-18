# minicode

> 终端 AI 编程助手 — 基于 Python Textual 框架构建的 TUI 应用，支持 Anthropic 与 OpenAI 双协议。

[![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**minicode** 是一个运行在终端内的 AI 编程助手，提供丰富的 TUI 交互界面。它能够理解你的代码库、执行工具调用、管理多 agent 协作，并通过灵活的权限系统确保操作安全。

---

## 功能特性

- **双协议支持** — 同时兼容 Anthropic API 和 OpenAI Chat Completions API
- **丰富工具集** — 内置文件读写/编辑、Bash 执行、Glob/Grep 搜索等工具
- **多 Agent 协作** — 支持 Fork 子 Agent、后台任务、Team 团队协调（lead + specialist 模式）
- **MCP 集成** — 支持 stdio / HTTP 两种传输的 MCP 客户端，按需发现工具
- **Skills 系统** — 可扩展的 YAML 定义 Skill，从项目级和用户级加载
- **权限控制** — 四层权限模式（`default` / `accept-edits` / `plan` / `bypass`），危险命令检测 + 路径沙箱
- **Worktree 隔离** — 基于 Git Worktree 的操作隔离，符号链接复用依赖目录
- **上下文压缩** — 接近 Context Window 时自动压缩历史摘要，避免丢失关键上下文
- **Session 持久化** — JSONL 格式存储会话历史，支持恢复与回放
- **远程 WebSocket** — 可通过浏览器访问 `localhost:18888` 进行远程操作
- **Hooks 系统** — Shell 命令挂钩在事件生命周期（`turn_start` / `pre_tool_use` / `post_tool_use` 等）执行
- **记忆系统** — 自动提取并持久化关键信息，跨会话复用

---

## 安装

### 环境要求

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv)（推荐包管理器）

### 从源码安装

```bash
git clone <repo-url> minicode
cd minicode

# 安装依赖
uv sync
```

### 配置 API Key

在项目根目录创建 `.minicode/config.yaml`（已加入 `.gitignore`）：

```yaml
providers:
  - name: claude
    protocol: anthropic
    base_url: https://api.anthropic.com
    model: claude-sonnet-4-6-20250514
    api_key: ${ANTHROPIC_API_KEY}
```

或使用环境变量直接运行：

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run minicode
```

---

## 快速开始

```bash
# 交互模式（TUI）
uv run minicode

# 非交互模式 —— 传 prompt，流式 JSON 输出
uv run minicode -p "帮我重构这个函数" --output-format stream-json

# 远程 WebSocket 模式（浏览器访问 http://localhost:18888）
uv run minicode --remote

# 指定权限模式
uv run minicode --mode bypass
```

---

## 架构概览

```
minicode/
├── __main__.py        # CLI 入口，参数解析，配置加载
├── app.py             # Textual App（TUI 核心），初始化所有子系统
├── agent.py           # Agent 主循环：system prompt → compact → LLM → tool → loop
├── client.py          # LLM 客户端抽象层（Anthropic / OpenAI）
├── config.py          # 三层配置合并
├── conversation.py    # 对话历史管理，token 估算
├── tools/             # 工具系统：基类、注册表、内置工具
├── permissions/       # 权限检查：危险命令检测、路径沙箱、规则引擎
├── agents/            # 子 Agent 加载器 & 后台任务管理
├── teams/             # 多 Agent 团队协作
├── mcp/               # MCP 客户端管理（stdio + HTTP）
├── skills/            # Skills 加载与执行
├── hooks/             # Shell Hook 生命周期管理
├── context/           # 自动压缩 & tool result 截断
├── worktree/          # Git Worktree 隔离
├── memory/            # 自动记忆提取与持久化
├── filehistory/       # 文件修改版本快照
└── commands/          # 自定义命令
```

**Agent 主循环流程：**

```
构建 System Prompt → 自动压缩 → LLM 流式调用 → Tool 调用/执行 → 循环
                                                      ↓
                                              权限确认（TUI 弹窗）
```

---

## 配置参考

```yaml
# 多 Provider 支持
providers:
  - name: claude
    protocol: anthropic
    base_url: https://api.anthropic.com
    model: claude-sonnet-4-6-20250514
    api_key: ${ANTHROPIC_API_KEY}

# 权限模式
permission_mode: default       # default | accept-edits | plan | bypass

# 高级功能开关
enable_fork: false             # 启用 Fork 子 Agent
enable_verification_agent: false
enable_coordinator_mode: false
teammate_mode: "in-process"    # in-process | tmux | iterm2

# MCP 服务
mcp_servers: []
  # - name: filesystem
  #   command: npx
  #   args: [-y, @anthropic/mcp-server-filesystem, /path/to/dir]
  #   transport: stdio

# Hooks 定义
hooks: []

# Worktree 配置
worktree:
  symlink_directories: [node_modules, .venv, vendor]
  stale_cleanup_interval: 3600
  stale_cutoff_hours: 24
```

---

## 开发

```bash
# 安装开发依赖
uv sync --group dev

# 运行全部测试
uv run pytest

# 运行单个测试
uv run pytest tests/test_agent.py -k "test_run" -v

# 查看代码覆盖率
uv run pytest --cov=minicode
```

---

## 许可证

MIT License
