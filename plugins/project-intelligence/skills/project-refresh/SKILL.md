---
name: project-refresh
description: Use when initializing, refreshing, updating, installing, or setting up project standards, knowledge, graph summaries, quality configuration, tooling checks, reports, hooks, Claude adapters, or after Understand-Anything finishes generating a graph. 刷新, 更新, 刷新项目, 更新项目, 刷新知识库, 更新知识库, 图谱完成, understand完成.
---

# Project Refresh

Use this skill when the user says to initialize or update project standards, knowledge, graph context, reports, or Claude adapters.

Commands:

```bash
project-intel graph-tools --json
project-intel init
project-intel init --no-graph
project-intel init --interactive
project-intel init --setup-missing
project-intel refresh
project-intel refresh --with-graph
project-intel install
project-intel install --hooks
```

`refresh` scans current workspace contents relative to the last generated project facts. It includes code pulled from other authors because project intelligence is based on file facts, not author identity.

`init`, `refresh`, and `install` maintain local agent adapters and root-level agent entrypoints:

- `AGENTS.md` for Codex and other agents that read AGENTS conventions.
- `CLAUDE.md` for Claude Code.
- `.claude/CLAUDE.md` for the Claude adapter. Skills are loaded from the installed plugin and are not copied into the project.

Use managed Project Intelligence blocks in root entrypoint files so existing team instructions are preserved. These rules are required because skill triggering is not guaranteed; agents must still consult `.project-intel` even when no dedicated Project Intelligence skill fires.

Routine refresh/check commands should keep stable files rather than producing a new file for every conversation. `init`, `refresh`, tooling, and quality reports overwrite their fixed outputs. `project-intel lifecycle` and `project-intel debug` print by default and write fixed reports only with `--write`. `project-intel maintain` overwrites `.project-intel/maintenance/latest.md`; add `--archive` only when the user wants timestamped history. Requirement deposition is file-level: maintain one concise Chinese markdown per source file under `.project-intel/requirements/files/`, not one requirement document per conversation.

`init` and `refresh` already write the local Claude adapter. Do not ask the user to run `project-intel install` after initialization just to see Project Intelligence skills. Use `install` only to repair/regenerate adapter files or to generate/activate optional hooks.

The managed entrypoint rules must distinguish tools from skills: Grep/Read/Edit/Bash are execution tools only, while Project Intelligence skills define the workflow. Keep task-to-skill routing explicit so implementation work uses `project-task`, bug investigation uses `project-debug`, review uses `project-review`, and completed work uses `project-maintain` even when the agent ultimately edits files with basic tools.

The managed entrypoint rules must also handle conversation transitions: if a discussion/spec/plan turns into code changes, the agent must pause before the first `Edit`/`Write`, enter `project-task`, run impact/reuse analysis, and only then edit. After edits, it must inspect the diff, run project checks/maintenance, and use GitNexus change or impact tools when available.

When the user says `/understand . --language zh` completed, graph generation finished, or `.understand-anything/knowledge-graph.json` was updated, immediately run `project-intel refresh` without asking another confirmation. In Claude Code, prefer `/project-refresh` as the user-facing continuation; if the agent cannot issue slash commands programmatically, run the CLI refresh command directly.

`init` checks optional tools such as GitNexus, Understand-Anything, Node/package managers, and quality commands. By default it runs installed graph analysis commands and only reports missing tools. `init --interactive` asks in a TTY; `init --setup-missing` installs only after approval. Plain `refresh` never installs or runs graph tools; use `refresh --with-graph` to rerun already-installed analyzers. In noninteractive agent shells, run `graph-tools --json` first and ask the user in Chinese before calling `init --setup-missing`.

Understand-Anything behavior:

- If it is `installed`, `init` can run the configured analysis command.
- If it is `agent-installed`, ask the user to run `/reload-plugins` after a fresh Claude Code install/enable, then `/understand . --language zh` or trigger the installed Understand-Anything skill. After the graph finishes, immediately run `/project-refresh` or `project-intel refresh`.
- If it is `partially-installed`, keep the `/understand` follow-up and also offer installation/enabling for the missing platform.
- If it is `installable`, ask whether to install/enable/repair it for Codex, Claude Code, or both. Only install after approval.
- For Codex, use the Understand-Anything installer with the `codex` platform from `Egonex-AI/Understand-Anything`.
- For Claude Code CLI, use `claude plugin marketplace add Egonex-AI/Understand-Anything`, `claude plugin install understand-anything@understand-anything`, and `claude plugin enable understand-anything@understand-anything`; verify with `claude plugin list`. Do not fall back to the official Anthropic marketplace name.
- In Claude Code slash UI, `/plugin marketplace add Egonex-AI/Understand-Anything` followed by `/plugin install understand-anything` is equivalent after the marketplace is added.
- If Claude Code shows `understand-anything@local` with `failed to load` or `Marketplace local not found`, treat it as broken and run the marketplace repair flow instead of telling the user `/understand` is ready.

When presenting choices, always include an “全部” option when more than one graph action is available, and accept combination answers such as `1,2` or `GitNexus + Understand-Anything`. If the user asks for “1 和 2” or “都要”, execute the shell-runnable setup first. If the remaining step is a Claude Code slash command, explain that shell code cannot inject it into the active prompt; tell the user to run `/reload-plugins`, then `/understand . --language zh`. Once they report completion, immediately refresh project intelligence.

The CLI writes and refreshes `.project-intel` as the project fact layer.
