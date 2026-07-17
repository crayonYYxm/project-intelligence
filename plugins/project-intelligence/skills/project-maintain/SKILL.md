---
name: project-maintain
description: Use only after `project-finish` succeeds and the requirement state is `finished`, to refresh facts and close that requirement. 关闭需求, 提交后维护, 需求完成后维护, finished 需求关闭, project-finish 后维护. Use project-refresh after git pull/merge or for standalone knowledge refresh; do not close a requirement merely because the user says refresh.
---

# Project Maintain

Close project tasks by refreshing facts and recording what changed.

Run maintenance once after the task is implemented, reviewed when needed, freshly verified, accepted by `project-finish`, and currently in `finished`. Do not use maintenance as proof that the business behavior works.

Run with the requirement ID:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

`--files` should list the source files actually affected by the requirement. They are stored once in `manifest.changedFiles` and queried with `project-intel requirement query --file <path>`; no `.project-intel/requirements/files/` mirror is created.

Use `--run-quality` only when the user asks to run real lint/type/style/format commands:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files> --run-quality
```

Maintenance validates the affected files, refreshes `.project-intel` without installing or rerunning graph tools, runs `project-intel check`, records `maintenanceResult`, and closes the requirement. Redundancy findings stay at `candidate` unless a human promotes them.

For subagent workflows, keep per-subagent handoffs under ignored `.project-intel/tmp/execution/` when needed. Durable history stays in the requirement directory and manifest.

For requirement-level work, run maintenance only after `project-intel finish --requirement-id "<id>"` succeeds:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

Maintain rechecks the finish Git commit and diff hash before refreshing and again before closing. If code or the commit changed after finish, stop and return to project-test, project-review, and project-finish; never force the manifest to closed.

Maintenance must start from `finished`; a refresh/check failure keeps the requirement in `finished`, and only success changes it to `closed`. Default refresh is fact-only and must not modify root agent adapters. Use explicit `refresh --adapters` or `install` only when the user requests adapter maintenance.
