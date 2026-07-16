---
name: project-maintain
description: Use when a task is finished, after implementation, after review fixes, after git pull/merge/commit, or when maintaining project standards, knowledge base, reports, hooks, or lifecycle artifacts. 维护, 项目维护, 更新知识库, 生命周期维护, 完成任务.
---

# Project Maintain

Close project tasks by refreshing facts and recording what changed.

Run maintenance once after the task is implemented, reviewed when needed, freshly verified, and closed by `project-finish`. Do not use maintenance as proof that the business behavior works.

Run with the requirement ID. By default this overwrites `.project-intel/maintenance/latest.md` instead of creating a new history file:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

`--files` should list the source files actually affected by the requirement. Project Intelligence maintains one concise Chinese requirement markdown per source file at `.project-intel/requirements/files/<source-path>.md`; it should not create a new requirement file for every conversation.

Use `--archive` only when the user explicitly wants a timestamped maintenance record:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files> --archive
```

Use `--run-quality` only when the user asks to run real lint/type/style/format commands:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files> --run-quality
```

Maintenance validates the Chinese task summary and affected files, refreshes `.project-intel` without installing or rerunning graph tools, runs `project-intel check`, then updates file-level requirement records and the latest maintenance report. Redundancy findings stay at `candidate` unless a human promotes them.

For subagent workflows, keep per-subagent handoffs and reports under ignored `.project-intel/tmp/execution/` when needed. The durable committed output should stay compact: one latest maintenance summary plus one concise Chinese requirement history per affected source file.

For requirement-level work, run maintenance only after `project-intel finish --requirement-id "<id>"` succeeds:

```bash
project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>
```

Maintain rechecks the finish Git commit and diff hash before refreshing and again before closing. If code or the commit changed after finish, stop and return to project-test, project-review, and project-finish; never force the manifest to closed.

Maintenance must start from `finished`; a refresh/check failure keeps the requirement in `finished`, and only success changes it to `closed`. Default refresh is fact-only and must not modify root agent adapters. Use explicit `refresh --adapters` or `install` only when the user requests adapter maintenance.
