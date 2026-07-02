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

By default, `init` checks graph tools before writing project facts. If GitNexus has an executable analysis command, `init` can run analysis automatically. Understand-Anything is optional but supported on both Codex and Claude Code:

- `installed`: a real `understand` CLI or `PROJECT_INTEL_UNDERSTAND_COMMAND` is available, so `init` can run analysis directly.
- `agent-installed`: Codex/Claude Code plugin files are installed, but the shell cannot run analysis. Ask the user to run `/understand . --language zh` or trigger the Understand-Anything skill, then run `refresh`.
- `installable`: Understand-Anything is not installed. Ask whether to install it. If approved, use `init --setup-missing` or run the selected install command before `init`.
- `missing`: no supported install path was detected. Print the setup suggestion and continue without graph enhancement.

In noninteractive agent shells such as Codex/Claude tool runs, do not rely on the CLI `input()` prompt to collect that choice. First run `graph-tools --json`, inspect `installOptions`, and ask the user in Chinese whether to install GitNexus, Understand-Anything for Codex, Understand-Anything for Claude Code, or skip.

Use a concise Chinese choice prompt, for example:

```text
检测到可选图谱工具：
1. GitNexus：可下载并运行分析
2. Understand-Anything：未安装，可安装到 Codex 或 Claude Code

请选择：
1. 准备 GitNexus 并分析
2. 安装 Understand-Anything 到 Codex
3. 安装 Understand-Anything 到 Claude Code
4. 跳过图谱增强并继续初始化
```

After the user answers:
- If they approved all supported installs, run `init --setup-missing`.
- If they approved only part of the list, install that subset first, then run `init`.
- If they chose to skip, run `init --no-graph` or plain `init` only after explicitly telling them graph tools will be skipped.
- Keep all user-facing narration in Chinese unless the user asked for another language.

Use `--setup-missing` only when the user has already approved automatic setup. For GitNexus this usually means downloading the CLI via `npx` and immediately running `analyze`, not a separate global install. For Understand-Anything, install according to the chosen target:

- Codex: `curl -fsSL https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/install.sh | bash -s codex`
- Claude Code: `claude plugin marketplace add Lum1104/Understand-Anything`, then `claude plugin install understand-anything@understand-anything`

Do not use the Codex installer as a substitute for Claude Code plugin installation, and do not claim Claude Code cannot install it just because it is absent from the official Anthropic marketplace. Use the Understand-Anything marketplace repo instead.

After initialization, use `/project-refresh` to update existing project facts.
