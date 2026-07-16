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
6. Generate a fixed finish report only when the task is actually at the finish stage:

```bash
project-intel finish --task "<中文简短需求摘要>" --files <changed-source-files>
```

7. `project-intel finish` must return non-zero when changed source lacks current task/file-scoped passing evidence. Use `--manual-evidence "<可复现步骤与观察结果>"` only when automation is unreasonable.
8. Do not commit, push, deploy, publish, run migrations, or change production state unless the user explicitly authorizes that action.
9. After finish, run maintenance once:

```bash
project-intel maintain --task "<中文简短需求摘要>" --files <changed-source-files>
```

`project-finish` is evidence and release-readiness closure. `project-maintain` is knowledge refresh and file-level Chinese requirement history. Do not treat either as proof unless the actual behavior was freshly verified.
