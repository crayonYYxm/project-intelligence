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
- `partially-installed`: current agent already has Understand-Anything, but another platform still has an install option. Offer both the `/understand` follow-up and the missing-platform install option.
- `installable`: Understand-Anything is not installed. Ask whether to install it. If approved, use `init --setup-missing` or run the selected install command before `init`.
- `missing`: no supported install path was detected. Print the setup suggestion and continue without graph enhancement.

In noninteractive agent shells such as Codex/Claude tool runs, do not rely on the CLI `input()` prompt to collect that choice. First run `graph-tools --json`, inspect `installOptions`, and ask the user in Chinese whether to run all graph setup, install GitNexus, install/enable Understand-Anything for Codex or Claude Code, run the `/understand` follow-up, or skip. Support combination answers such as `1,2`, `1+3`, `全部`, or `all`.

Use a concise Chinese choice prompt, for example:

```text
检测到可选图谱工具：
1. GitNexus：可下载并运行分析
2. Understand-Anything：已安装到 agent，当前 shell 不能直接分析
3. Understand-Anything：可安装或启用到 Claude Code

请选择：
1. 全部准备：GitNexus + Understand-Anything 安装/启用 + 后续分析提示
2. 准备 GitNexus 并分析
3. 安装/启用 Understand-Anything 到 Claude Code，并提示运行 /understand
4. GitNexus + Understand-Anything 后续分析
5. 跳过图谱增强并继续初始化

也可以输入组合：`2,3` 表示同时准备 GitNexus 和 Claude Code 的 Understand-Anything。
```

After the user answers:
- If they approved all supported installs, run `init --setup-missing`.
- If they approved only part of the list, install that subset first, run installed shell analyzers such as GitNexus, then run `init`.
- If they choose any Understand-Anything analysis option and only an agent skill is available, explain that the remaining action is to run `/understand . --language zh` in the current Codex/Claude Code session, then run `refresh`.
- If they chose to skip, run `init --no-graph` or plain `init` only after explicitly telling them graph tools will be skipped.
- Keep all user-facing narration in Chinese unless the user asked for another language.

Use `--setup-missing` only when the user has already approved automatic setup. For GitNexus this usually means downloading the CLI via `npx` and immediately running `analyze`, not a separate global install. For Understand-Anything, install according to the chosen target:

- Codex: `curl -fsSL https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/install.sh | bash -s codex`
- Claude Code: `claude plugin marketplace add Lum1104/Understand-Anything`, then `claude plugin install understand-anything@understand-anything`

Do not use the Codex installer as a substitute for Claude Code plugin installation, and do not claim Claude Code cannot install it just because it is absent from the official Anthropic marketplace. Use the Understand-Anything marketplace repo instead.

After initialization, use `/project-refresh` to update existing project facts.
