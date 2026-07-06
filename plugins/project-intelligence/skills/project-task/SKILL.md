---
name: project-task
description: Use when implementing, building, adding, modifying, fixing, refactoring, or completing a project feature/需求 and needing project standards, reuse, components, Hooks, APIs, services, graph context, or post-task maintenance. 需求开发, 功能开发, 实现需求, 开发任务, 做需求, 写功能.
---

# Project Task

Before implementing, read `.project-intel/manifest.json`. Then load only the relevant files under `.project-intel/standards`, `.project-intel/knowledge`, `.project-intel/graph`, and `.project-intel/reports`.

If a conversation begins as discussion, explanation, spec, or plan and then turns into code modification, pause before the first `Edit`/`Write` and switch into this task workflow. Basic tools such as Grep, Read, Edit, Bash, Glob, or Write do not replace this workflow.

Use this sequence:

1. Identify related modules, components, Hooks, APIs, services, routes, and standards.
2. Prefer existing project abstractions before creating new ones.
3. Treat redundancy findings as `candidate` unless a rule has been promoted to `hard`.
4. Use GitNexus for symbol-level calls, impact, and change risk when available.
5. Use Understand-Anything for architecture, module, and domain-flow context when available.
6. Before the first code edit, run impact/reuse analysis with GitNexus impact/explore tools when available; otherwise use `.project-intel`, `project-intel query "<symbol-or-feature>"`, or `project-intel lifecycle --task "<requirement>"`. `lifecycle` prints by default; use `--write` only when the user explicitly wants a persistent task-impact report.
7. If implementation reveals a bug, error, test failure, or regression, switch to `project-debug` before proposing fixes.
8. Do not read or rely on `.cgraphx`; do not use `cgraphx explore` as a fallback for this plugin.

If `.project-intel` is missing or stale, run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init
```

Before broad implementation, inspect task impact when useful. This does not create a report file by default:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py lifecycle --task "<requirement>"
```

After implementation, run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py check
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "<summary>"
```

`maintain` overwrites `.project-intel/maintenance/latest.md` by default. Add `--archive` only when the user wants to keep a timestamped maintenance history.

Also inspect the git diff after edits and use GitNexus change/impact tools when available before finalizing.
