---
name: project-task
description: Use when implementing, building, adding, modifying, fixing, refactoring, or completing a project feature/需求 and needing project standards, reuse, components, Hooks, APIs, services, graph context, or post-task maintenance. 需求开发, 功能开发, 实现需求, 开发任务, 做需求, 写功能.
---

# Project Task

Before implementing, read `.project-intel/manifest.json`. Then load only the relevant files under `.project-intel/standards`, `.project-intel/knowledge`, `.project-intel/graph`, and `.project-intel/reports`.

If a conversation begins as discussion, explanation, spec, or plan and then turns into code modification, pause before the first `Edit`/`Write` and switch into this task workflow. Basic tools such as Grep, Read, Edit, Bash, Glob, or Write do not replace this workflow.

Use this sequence:

1. Before the first code edit,整理轻量中文 spec：需求摘要、验收点、影响范围、复用候选、假设/疑问。This is required for task work, but do not create a spec file unless the user explicitly asks.
2. Identify related modules, components, Hooks, APIs, services, routes, and standards.
3. Prefer existing project abstractions before creating new ones.
4. Treat redundancy findings as `candidate` unless a rule has been promoted to `hard`.
5. Use GitNexus for symbol-level calls, impact, and change risk when available.
6. Use Understand-Anything for architecture, module, and domain-flow context when available.
7. Before the first code edit, run impact/reuse analysis with GitNexus impact/explore tools when available; otherwise use `.project-intel`, `project-intel query "<symbol-or-feature>"`, or `project-intel lifecycle --task "<requirement>"`. `lifecycle` prints by default; use `--write` only when the user explicitly wants a persistent task-impact report.
8. Decide execution mode:
   - small or tightly coupled change: implement inline in this session.
   - independent planned subtasks: switch to `project-orchestrate` for subagent handoffs, task review, and final review.
   - independent investigations or impact questions: use parallel read-only agents when the host supports them.
   - high-risk long-running work: use a worktree only when the user asks or the host workflow already uses one.
9. If implementation reveals a bug, error, test failure, or regression, switch to `project-debug` before proposing fixes.
10. Use `.project-intel`, GitNexus, Understand-Anything, and direct source reads as the task context sources.

If `.project-intel` is missing or stale, run:

```bash
project-intel init
```

Before broad implementation, inspect task impact when useful. This does not create a report file by default:

```bash
project-intel lifecycle --task "<requirement>"
```

After implementation, run check and maintain. Pass the actual changed source files so each file keeps exactly one concise Chinese requirement markdown:

```bash
project-intel check
project-intel maintain --task "<中文简短需求摘要>" --files <changed-source-files>
```

The `--task` value used for maintenance must be Chinese. `maintain` overwrites `.project-intel/maintenance/latest.md` by default and updates `.project-intel/requirements/files/<source-path>.md`; add `--archive` only when the user wants to keep a timestamped maintenance history.

Before finalizing:

1. Inspect the git diff.
2. Use GitNexus change/impact tools when available.
3. Run fresh verification that proves the actual claim: targeted tests, type checks, build, lint, or manual device/browser evidence as appropriate.
4. Only claim complete, fixed, passing, or ready after reading that verification output.

`project-intel check` proves project-intelligence rules and known quality commands. It does not by itself prove the business requirement unless the check directly exercises the changed behavior.
