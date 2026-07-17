---
name: project-task
description: Use after lifecycle readiness when the user wants to begin or continue implementation, fixing, refactoring, or other business-code changes. 开始实现, 开始修复, 继续开发, 需求开发, 功能开发, 实现需求, 做需求, 写功能. Do not use for design-only, planning-only, review-only, or read-only questions.
---

# Project Task

Before implementing, read `.project-intel/manifest.json`, `.project-intel/project-status.md`, and the active `.project-intel/requirements/<id>/manifest.json`. Then load only relevant standards, knowledge, graph facts, `requirement.md`, `design.md`, and optional `plan.md`.

If a conversation begins as discussion, explanation, spec, or plan and then turns into code modification, pause before the first `Edit`/`Write` and switch into this task workflow. Basic tools such as Grep, Read, Edit, Bash, Glob, or Write do not replace this workflow.

Use this sequence:

1. Read the existing lifecycle status and require `state: ready` before the first code edit:

```bash
project-intel requirement status --requirement-id "<id>" --json
```

Do not run intake again for an existing lifecycle requirement: it may have an explicitly confirmed track or other intake values that must not be re-inferred. If no requirement ID or manifest exists, return to `project-intake` and complete spec/design/readiness before resuming this Skill.

2. Before the first code edit, confirm `project-spec` registered `requirement.md`, persisted matching acceptance criteria, and `project-design` registered `design.md`. Do not add AC headings to the design document.
3. Confirm `project-test` has selected the test type, report action, target test file, command, expected RED failure, GREEN proof, regression scope, and any justified manual-evidence exception. While the requirement is still `ready`, this is planning only. Then run `project-intel requirement begin --requirement-id "<id>"` and confirm `state: implementing` before generating the test report, editing the test file, or executing/recording RED.
4. Identify related modules, components, Hooks, APIs, services, routes, and standards.
5. Prefer existing project abstractions before creating new ones.
6. Treat redundancy findings as `candidate` unless a rule has been promoted to `hard`.
7. Use GitNexus for symbol-level calls, impact, and change risk when available.
8. Use Understand-Anything for architecture, module, and domain-flow context when available.
9. Before the first code edit, run impact/reuse analysis with GitNexus impact/explore tools when available; otherwise use `.project-intel`, `project-intel query "<symbol-or-feature>"`, or `project-intel lifecycle --task "<requirement>"`. `lifecycle` prints only; do not create a shared task-impact report.
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

After implementation, run check, record the selected verification evidence, review, finish, and maintain. Reuse the test type, report action, and AC IDs confirmed for this requirement; never replace them with a generic unit/generate/AC-01 example:

```bash
project-intel check
project-intel test --requirement-id "<id>" --test-kind "<selected-kind>" \
  --report-action "<selected-action>" --phase verify \
  --files <changed-source-and-test-files> --acceptance <confirmed-ac-ids> \
  [--command "<targeted-command>"] [--report-path <existing-report-for-register>]
project-intel review --requirement-id "<id>" --result passed --summary "<review-summary>" --files <all-actual-changed-files>
project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

`finish` and `maintain` record their results in the same requirement manifest. They must not create shared reports, maintenance histories, or per-source markdown files.

The bracketed options above are conditional documentation, not literal CLI text. `register` requires its existing report path; `generate` does not. External API impact requires `service` or `both`, and manual evidence uses the approval-style arguments defined by `project-test`.

Before finalizing:

1. Inspect the git diff.
2. Use GitNexus change/impact tools when available.
3. Run fresh verification that proves the actual claim: targeted tests, type checks, build, lint, or manual device/browser evidence as appropriate.
4. Ensure the proof is recorded by `project-test`; `project-intel finish` must reject changed source without fresh task-matching evidence.
5. Only claim complete, fixed, passing, or ready after reading that verification output.

`project-intel check` proves project-intelligence rules and known quality commands. It does not by itself prove the business requirement unless the check directly exercises the changed behavior.

For requirement-level implementation, require the ID/name created by `project-intake`, confirm `requirement status` is `ready`, and run this before the first test-report generation, test-file edit, production edit, or test execution:

```bash
project-intel requirement begin --requirement-id "<id>"
```

Pass the same ID to `project-test`, `project-review`, `project-finish`, `project-maintain`, and every orchestration handoff. The older `--task`-only commands are compatibility mode, not the preferred workflow.
