---
name: project-task
description: Use when preparing to implement or actually implementing, building, adding, modifying, fixing, refactoring, or completing a project feature/需求 and needing project standards, reuse, components, Hooks, APIs, services, graph context, or post-task maintenance. 需求开发, 功能开发, 实现需求, 开发任务, 做需求, 写功能.
---

# Project Task

Before implementing, read `.project-intel/manifest.json`. Then load only the relevant files under `.project-intel/standards`, `.project-intel/knowledge`, `.project-intel/graph`, and `.project-intel/reports`.

If a conversation begins as discussion, explanation, spec, or plan and then turns into code modification, pause before the first `Edit`/`Write` and switch into this task workflow. Basic tools such as Grep, Read, Edit, Bash, Glob, or Write do not replace this workflow.

Use this sequence:

1. Before the first code edit, run or mentally follow `project-intake` to classify the work as `quick`, `standard`, or `complex`, and confirm readiness:

```bash
project-intel intake --requirement-id "<id>" --requirement-name "<name>" --ticket-kind bug|requirement --external-api yes|no --track auto
```

2. Before the first code edit, confirm `project-design` has registered a validated design artifact and `project-spec` has written acceptance criteria to the manifest. Do not add AC headings to the design document.
3. Invoke `project-test` before production edits for features, fixes, refactors, and behavior changes. Name the target test file, command, expected RED failure, GREEN proof, regression scope, and any justified manual-evidence exception.
4. Identify related modules, components, Hooks, APIs, services, routes, and standards.
5. Prefer existing project abstractions before creating new ones.
6. Treat redundancy findings as `candidate` unless a rule has been promoted to `hard`.
7. Use GitNexus for symbol-level calls, impact, and change risk when available.
8. Use Understand-Anything for architecture, module, and domain-flow context when available.
9. Before the first code edit, run impact/reuse analysis with GitNexus impact/explore tools when available; otherwise use `.project-intel`, `project-intel query "<symbol-or-feature>"`, or `project-intel lifecycle --task "<requirement>"`. `lifecycle` prints by default and includes track/readiness; use `--write` only when the user explicitly wants a persistent task-impact report.
10. Decide execution mode:
   - small or tightly coupled change: implement inline in this session.
   - independent planned subtasks: switch to `project-orchestrate` for subagent handoffs, task review, and final review.
   - independent investigations or impact questions: use parallel read-only agents when the host supports them.
   - high-risk long-running work: use a worktree only when the user asks or the host workflow already uses one.
11. If implementation reveals a bug, error, test failure, or regression, switch to `project-debug` before proposing fixes.
12. Use `.project-intel`, GitNexus, Understand-Anything, and direct source reads as the task context sources.

If `.project-intel` is missing or stale, inspect it without mutating root adapters:

```bash
project-intel doctor
project-intel init --dry-run
```

Run `project-intel init` only after explicit user authorization. Do not silently modify `.gitignore`, `AGENTS.md`, or `CLAUDE.md`.

Before broad implementation, inspect task impact when useful. This does not create a report file by default:

```bash
project-intel lifecycle --task "<requirement>"
```

After implementation, run check and maintain. Pass the actual changed source files so each file keeps exactly one concise Chinese requirement markdown:

```bash
project-intel check
project-intel test --requirement-id "<id>" --test-kind unit --report-action generate \
  --phase verify --files <changed-source-and-test-files> --acceptance AC-01,AC-02
project-intel review --requirement-id "<id>" --result passed --summary "<review-summary>" --files <all-actual-changed-files>
project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

The requirement name must be Chinese when file-level maintenance history is written. `maintain` overwrites `.project-intel/maintenance/latest.md` by default and updates `.project-intel/requirements/files/<source-path>.md`; add `--archive` only when the user wants to keep a timestamped maintenance history.

Before finalizing:

1. Inspect the git diff.
2. Use GitNexus change/impact tools when available.
3. Run fresh verification that proves the actual claim: targeted tests, type checks, build, lint, or manual device/browser evidence as appropriate.
4. Ensure the proof is recorded by `project-test`; `project-intel finish` must reject changed source without fresh task-matching evidence.
5. Only claim complete, fixed, passing, or ready after reading that verification output.

`project-intel check` proves project-intelligence rules and known quality commands. It does not by itself prove the business requirement unless the check directly exercises the changed behavior.

For requirement-level implementation, require the ID/name created by `project-intake`, confirm `requirement status` is `ready`, and run this immediately before the first code edit:

```bash
project-intel requirement begin --requirement-id "<id>"
```

Pass the same ID to `project-test`, `project-review`, `project-finish`, `project-maintain`, and every orchestration handoff. The older `--task`-only commands are compatibility mode, not the preferred workflow.
