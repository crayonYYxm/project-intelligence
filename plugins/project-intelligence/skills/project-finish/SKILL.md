---
name: project-finish
description: Use when finishing a task, checking acceptance evidence, release readiness, scope drift, completion safety, or before project-maintain after code changes. 收口, 完成检查, 验收证据, 交付前检查.
---

# Project Finish

Use this after implementation and review fixes, before project maintenance.

1. Inspect the diff and changed files.
2. Read `.project-intel/reports/test-evidence.json`. Confirm the feature/bugfix claim with fresh, task-matching evidence from the current turn: targeted tests, affected regression tests, or a reproducible manual procedure with screenshots, API calls, or logs.
3. Verify scope did not drift. If it did, update the spec/plan before claiming completion.
4. Check high-risk categories when relevant: interface compatibility, data migration, permissions, cache, transactions, remote calls, async jobs, release flags, rollback, monitoring, and user-visible edge states.
5. If evidence is missing, return to `project-test`. Do not use `project-intel check`, lint, type-check, build output, or an Agent summary as a substitute for changed-behavior proof.
6. Ask whether to generate, register, or defer the closure summary, then run finish only when the task is actually at the finish stage:

```bash
project-intel requirement generate --requirement-id "<id>" --type closure
project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>
```

7. `project-intel finish` must return non-zero when changed source lacks current task/file-scoped passing evidence. For requirement-level tasks, manual evidence must already be registered through the approval-style `project-test` flow; do not bypass it with `finish --manual-evidence`.
8. Do not commit, push, deploy, publish, run migrations, or change production state unless the user explicitly authorizes that action.
9. After finish, run maintenance once:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

`project-finish` is evidence and release-readiness closure. `project-maintain` is knowledge refresh and file-level Chinese requirement history. Do not treat either as proof unless the actual behavior was freshly verified.

For a requirement-level task, ask how to handle the closure summary: `generate`, `register existing`, or `later`. Execute one of:

```bash
project-intel requirement generate --requirement-id "<id>" --type closure
project-intel requirement add --requirement-id "<id>" --type closure --path <repo-relative-file>
project-intel requirement defer --requirement-id "<id>" --type closure
```

Then run `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>`. Finish must verify documents, test policy, acceptance mapping, review, current diff hash, complete scope, and closure summary.
