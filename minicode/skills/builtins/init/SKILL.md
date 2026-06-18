---
name: init
description: 分析项目结构并生成 AGENTS.md
allowedTools:
  - Bash
  - ReadFile
  - Glob
  - Grep
  - WriteFile
  - EditFile
mode: fork
context: none
---

# 任务

你需要分析当前项目的代码库，然后生成一份高质量的 `AGENTS.md` 文件。

## 什么是 AGENTS.md

`AGENTS.md` 是一份给 AI 编程助手的项目指引文件。它帮助 AI 快速理解项目的结构、常用命令和核心架构。minicode 会自动加载项目根目录及 git root 到工作目录之间所有目录的 `AGENTS.md`，将其内容作为系统指令注入。

## 步骤

### 1. 项目类型识别
- 检查 `pyproject.toml` / `setup.py` → Python 项目
- 检查 `package.json` → Node.js 项目
- 检查 `go.mod` → Go 项目
- 检查 `Cargo.toml` → Rust 项目
- 检查 `Makefile` / `CMakeLists.txt` → C/C++ 项目

### 2. 文件结构分析
- 用 `Glob` 搜索关键模式：`**/*.py`、`**/__init__.py`、`**/main.*`、`**/app.*`
- 用 `Bash` 运行 `ls -la` 查看根目录
- 用 `Bash` 运行 `git log --oneline -20` 了解开发历史

### 3. 深度分析
- 阅读入口文件（如 `__main__.py`、`main.go`、`index.ts`、`App.tsx`）
- 阅读 `README.md`（如果存在）
- 阅读关键配置文件（`pyproject.toml`、`package.json` 等）
- 用 `Grep` 搜索关键模式识别核心组件和模块

### 4. 生成 AGENTS.md

以以下格式输出：

```markdown
# AGENTS.md

This file provides guidance to AI coding assistants when working with code in this repository.

## 项目概述

[项目名称] 是一个 [类型/用途]，使用 [主要技术栈]。

## 常用命令

```bash
# 安装依赖
[具体命令]

# 运行
[具体命令]

# 测试
[具体命令]

# 构建/其他
[具体命令]
```

## 核心架构

### 目录结构

```
项目/
├── src/
├── tests/
└── ...
```

### 关键模块

- `模块路径` — 功能说明
- `模块路径` — 功能说明

## 配置说明

[如果探测到配置文件或环境变量，在此说明]

## 开发约定

[从代码风格中推断的约定，如果有的话]
```

### 5. 写入文件

分析完成后，直接使用 `WriteFile` 将生成的 `AGENTS.md` 写入项目根目录，无需询问用户确认。

### 6. 注意事项

- 不要编造不存在的命令 —— 必须从实际配置文件中推断
- 如果项目已有 `AGENTS.md`，直接覆盖，无需询问
- 保持简洁：每个模块/目录说明不超过 2 行
- 如果项目很小，文档也应相应精简
- 不要写入任何机密信息（API Key、密码等）
- 用中文编写内容（项目概述、架构说明等），命令示例保持原样

$ARGUMENTS
