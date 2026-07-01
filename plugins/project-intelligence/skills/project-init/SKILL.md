---
name: project-init
description: Use when the user wants to initialize, set up, or bootstrap project intelligence for the first time. 初始化项目, 项目初始化, 搭建项目, 创建项目, 项目搭建, 初始化.
---

# Project Init

Use this skill when the user says to initialize, set up, or bootstrap project intelligence for a repository.

Commands:

```bash
python3 plugins/project-intelligence/scripts/project_intel.py graph-tools --json
python3 plugins/project-intelligence/scripts/project_intel.py init
python3 plugins/project-intelligence/scripts/project_intel.py init --no-graph
python3 plugins/project-intelligence/scripts/project_intel.py init --interactive
python3 plugins/project-intelligence/scripts/project_intel.py init --setup-missing
python3 plugins/project-intelligence/scripts/project_intel.py init --strict
```

`init` generates `.project-intel/` with standards, knowledge, graph summaries, quality configuration, tooling checks, and reports. It checks optional tools such as GitNexus, Understand-Anything, Node/package managers, and quality commands. Missing optional tools do not block initialization unless strict graph setup is requested.

By default, `init` checks graph tools before writing project facts. If GitNexus or Understand-Anything has an executable analysis command, `init` runs analysis automatically. If a graph tool is missing but has a supported install command, `init` asks whether to install/initialize it; answering no continues initialization.

In noninteractive agent shells such as Codex/Claude tool runs, do not rely on the CLI `input()` prompt to collect that choice. First run `graph-tools --json`, inspect the returned graph actions, and if any optional graph tool is `installable` or `missing`, ask the user in Chinese before calling `init`.

Use a concise Chinese choice prompt, for example:

```text
检测到可选图谱工具：
1. GitNexus：可安装并运行分析
2. Understand-Anything：可安装并运行分析

请选择：
1. 全部安装并分析
2. 仅安装 GitNexus
3. 仅安装 Understand-Anything
4. 跳过并继续初始化
```

After the user answers:
- If they approved all supported installs, run `init --setup-missing`.
- If they approved only part of the list, install that subset first, then run `init`.
- If they chose to skip, run `init --no-graph` or plain `init` only after explicitly telling them graph tools will be skipped.
- Keep all user-facing narration in Chinese unless the user asked for another language.

Use `--setup-missing` only when the user has already approved automatic installation. Understand-Anything can be run automatically from the CLI when `PROJECT_INTEL_UNDERSTAND_COMMAND` or an `understand` shell command is available; otherwise the CLI can install the agent plugin and will tell the user to restart the agent and run `/understand .`.

After initialization, use `/project-refresh` to update existing project facts.
