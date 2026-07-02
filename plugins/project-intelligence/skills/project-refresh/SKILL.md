---
name: project-refresh
description: Use when initializing, refreshing, updating, installing, or setting up project standards, knowledge, graph summaries, quality configuration, tooling checks, reports, hooks, or Claude adapters. 刷新, 更新, 刷新项目, 更新项目, 刷新知识库, 更新知识库.
---

# Project Refresh

Use this skill when the user says to initialize or update project standards, knowledge, graph context, reports, or Claude adapters.

Commands:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py graph-tools --json
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init --no-graph
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init --interactive
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init --setup-missing
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py refresh
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py install
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py install --hooks
```

`refresh` scans current workspace contents relative to the last generated project facts. It includes code pulled from other authors because project intelligence is based on file facts, not author identity.

`init` checks optional tools such as GitNexus, Understand-Anything, Node/package managers, and quality commands. By default it runs installed graph analysis commands automatically and asks before preparing missing graph tools. In noninteractive agent shells, run `graph-tools --json` first and ask the user in Chinese before calling `init --setup-missing`.

Understand-Anything behavior:

- If it is `installed`, `init` can run the configured analysis command.
- If it is `agent-installed`, ask the user to run `/understand . --language zh` or trigger the installed Understand-Anything skill, then run `refresh`.
- If it is `installable`, ask whether to install it for Codex, Claude Code, or both. Only install after approval.
- For Codex, use the Understand-Anything installer with the `codex` platform.
- For Claude Code, use `claude plugin marketplace add Lum1104/Understand-Anything` and `claude plugin install understand-anything@understand-anything`; do not fall back to the official Anthropic marketplace name.

The CLI intentionally does not read `.cgraphx`.
