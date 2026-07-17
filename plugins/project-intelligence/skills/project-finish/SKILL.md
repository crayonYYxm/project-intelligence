---
name: project-finish
description: Use after implementation evidence and review when the user asks to finish, accept, or check release readiness. 收尾吧, 收口, 验收, 检查是否完成, 完成检查, 发布前检查, 交付前检查. Do not treat it as proof when test or review evidence is missing.
---

# Project Finish

Use this after implementation and review fixes, before project maintenance.

1. Inspect the diff and changed files.
2. Read `.project-intel/requirements/<id>/test-report.md` and `manifest.testEvidence`. Confirm the feature/bugfix claim with fresh, task-matching evidence from the current diff: targeted tests, affected regression tests, or an approved reproducible manual procedure.
3. Verify scope did not drift. If it did, update the spec/plan before claiming completion.
4. Check high-risk categories when relevant: interface compatibility, data migration, permissions, cache, transactions, remote calls, async jobs, release flags, rollback, monitoring, and user-visible edge states.
5. If evidence is missing, return to `project-test`. Do not use `project-intel check`, lint, type-check, build output, or an Agent summary as a substitute for changed-behavior proof.
6. Ask whether to generate, register, or defer the closure summary, then run finish only when the task is actually at the finish stage:

```bash
project-intel requirement generate --requirement-id "<id>" --type closure
project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>
```

Generation is create-only by default. If `closure-summary.md` already exists, complete or register the existing file; use `--replace` only after explicit user approval.

7. `project-intel finish` must return non-zero when changed source lacks current task/file-scoped passing evidence. For requirement-level tasks, manual evidence must already be registered through the approval-style `project-test` flow; do not bypass it with `finish --manual-evidence`.
8. Do not commit, push, deploy, publish, run migrations, or change production state unless the user explicitly authorizes that action.
9. After finish, run maintenance once:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

`project-finish` records release-readiness in `manifest.finishResult`. `project-maintain` refreshes project facts and records `manifest.maintenanceResult`; neither creates a shared report or per-source history file.

For a requirement-level task, ask how to handle the closure summary: `generate`, `register existing`, or `later`. Execute one of:

```bash
project-intel requirement generate --requirement-id "<id>" --type closure
project-intel requirement add --requirement-id "<id>" --type closure --path <repo-relative-file>
project-intel requirement defer --requirement-id "<id>" --type closure
```

Then run `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>`. Finish must verify documents, test policy, acceptance mapping, review, current diff hash, complete scope, and closure summary.

The four durable lifecycle documents are `requirement.md`, `design.md`, `test-report.md`, and `closure-summary.md` in the same requirement directory. `plan.md` is optional.
