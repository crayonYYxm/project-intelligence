---
name: project-finish
description: Use when finishing a task, checking acceptance evidence, release readiness, scope drift, completion safety, or before project-maintain after code changes. 收口, 完成检查, 验收证据, 交付前检查.
---

# Project Finish

Use this after implementation and review fixes, before project maintenance.

1. Inspect the diff and changed files.
2. Confirm the feature/bugfix claim with fresh evidence from the current turn: targeted tests, type/lint/build, manual reproduction, screenshots, API calls, or logs.
3. Verify scope did not drift. If it did, update the spec/plan before claiming completion.
4. Check high-risk categories when relevant: interface compatibility, data migration, permissions, cache, transactions, remote calls, async jobs, release flags, rollback, monitoring, and user-visible edge states.
5. Generate a fixed finish report only when the task is actually at the finish stage:

```bash
project-intel finish --task "<中文简短需求摘要>" --files <changed-source-files>
```

6. Do not commit, push, deploy, publish, run migrations, or change production state unless the user explicitly authorizes that action.
7. After finish, run maintenance once:

```bash
project-intel maintain --task "<中文简短需求摘要>" --files <changed-source-files>
```

`project-finish` is evidence and release-readiness closure. `project-maintain` is knowledge refresh and file-level Chinese requirement history. Do not treat either as proof unless the actual behavior was freshly verified.
