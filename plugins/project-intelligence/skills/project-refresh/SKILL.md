---
name: project-refresh
description: Use when refreshing an existing `.project-intel` fact layer after workspace changes, git pull/merge, completed graph analysis, or an explicit adapter refresh request. 刷新项目智能, 刷新项目事实, 更新项目知识库, git pull 后刷新, understand 完成后刷新. Use project-init for first-time initialization and project-maintain only after a finished requirement. Do not use for npm/marketplace/cloud plugin install, upgrade, publish, or local plugin update requests.
---

# Project Refresh

Use this skill to refresh existing project standards, knowledge, graph context, the single `project-status.md`, or explicitly requested adapters. Use `project-init` when `.project-intel` does not exist.

Commands:

```bash
project-intel graph-tools --json
project-intel refresh
project-intel refresh --with-graph
project-intel refresh --with-graph --allow-repo-runner
project-intel refresh --with-graph --allow-env-command
project-intel refresh --with-graph --allow-external-path
project-intel refresh --adapters
project-intel install
project-intel install --hooks
```

`refresh` scans current workspace contents relative to the last generated project facts. It includes code pulled from other authors because project intelligence is based on file facts, not author identity.

Ordinary `refresh` is fact-only. Only explicit `refresh --adapters` or `install` maintains local agent adapters and root-level agent entrypoints:

- `AGENTS.md` for Codex and other agents that read AGENTS conventions.
- `CLAUDE.md` for Claude Code.
- `.claude/CLAUDE.md` for the Claude adapter. Skills are loaded from the installed plugin and are not copied into the project.

Use managed Project Intelligence blocks in root entrypoint files so existing team instructions are preserved. These rules are required because skill triggering is not guaranteed; agents must still consult `.project-intel` even when no dedicated Project Intelligence skill fires.

Routine refresh/check commands overwrite `.project-intel/project-status.md`. Intake, lifecycle, and debug print context only. Requirement finish and maintenance update the active requirement manifest. New-flow commands do not create shared `reports`, `specs`, `plans`, `maintenance`, `requirements/by-id`, or `requirements/files` directories.

Ordinary `refresh` does not write the local Claude adapter. Do not ask the user to run `project-intel install` just to see Project Intelligence skills. Use `refresh --adapters` or `install` only after the user explicitly requests adapter maintenance; use `install` for optional hooks.

The managed entrypoint rules must distinguish tools from skills: Grep/Read/Edit/Bash are execution tools only, while Project Intelligence skills define the workflow. Keep task-to-skill routing explicit so implementation work uses `project-task`, bug investigation uses `project-debug`, review uses `project-review`, and completed work uses `project-maintain` even when the agent ultimately edits files with basic tools.

The managed entrypoint rules must also handle conversation transitions: if a discussion/spec/plan turns into code changes, the agent must pause before the first `Edit`/`Write`, enter `project-intake` and `project-task`, run impact/reuse analysis, and only then edit. After edits, it must inspect the diff, run project checks, finish, maintenance, and use GitNexus change or impact tools when available.

When the user says `/understand . --language zh` completed, graph generation finished, or `.understand-anything/knowledge-graph.json` was updated, immediately run `project-intel refresh` without asking another confirmation. In Claude Code, prefer `/project-refresh` as the user-facing continuation; if the agent cannot issue slash commands programmatically, run the CLI refresh command directly.

Graph execution is off by default. `refresh --with-graph` runs authorized installed analyzers. A repository runner, environment-provided command, or project-external absolute path additionally requires `--allow-repo-runner`, `--allow-env-command`, or `--allow-external-path`. In noninteractive agent shells, run `graph-tools --json` first and ask the user in Chinese before calling any setup or authorization flag. First-time tool setup belongs to `project-init`.

Understand-Anything behavior:

- If it is `installed`, `refresh --with-graph` can run the configured analysis command.
- If it is `agent-installed`, ask the user to run `/reload-plugins` after a fresh Claude Code install/enable, then `/understand . --language zh` or trigger the installed Understand-Anything skill. After the graph finishes, immediately run `/project-refresh` or `project-intel refresh`.
- If it is `partially-installed`, keep the `/understand` follow-up and also offer installation/enabling for the missing platform.
- If it is `installable`, ask whether to install/enable/repair it for Codex, Claude Code, or both. Only install after approval.
- For Codex, use the Understand-Anything installer with the `codex` platform from `Egonex-AI/Understand-Anything`.
- For Claude Code CLI, use `claude plugin marketplace add Egonex-AI/Understand-Anything`, `claude plugin install understand-anything@understand-anything`, and `claude plugin enable understand-anything@understand-anything`; verify with `claude plugin list`. Do not fall back to the official Anthropic marketplace name.
- In Claude Code slash UI, `/plugin marketplace add Egonex-AI/Understand-Anything` followed by `/plugin install understand-anything` is equivalent after the marketplace is added.
- If Claude Code shows `understand-anything@local` with `failed to load` or `Marketplace local not found`, treat it as broken and run the marketplace repair flow instead of telling the user `/understand` is ready.

When presenting choices, always include an “全部” option when more than one graph action is available, and accept combination answers such as `1,2` or `GitNexus + Understand-Anything`. If the user asks for “1 和 2” or “都要”, execute the shell-runnable setup first. If the remaining step is a Claude Code slash command, explain that shell code cannot inject it into the active prompt; tell the user to run `/reload-plugins`, then `/understand . --language zh`. Once they report completion, immediately refresh project intelligence.

The CLI writes and refreshes `.project-intel` as the project fact layer. `cache/`, `local/`, `tmp/`, lock files, and atomic temporary files are ignored through `.project-intel/.gitignore`.
