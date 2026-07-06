---
name: project-maintain
description: Use when a task is finished, after implementation, after review fixes, after git pull/merge/commit, or when maintaining project standards, knowledge base, reports, hooks, or lifecycle artifacts. 维护, 项目维护, 更新知识库, 生命周期维护, 完成任务.
---

# Project Maintain

Close project tasks by refreshing facts and recording what changed.

Run. By default this overwrites `.project-intel/maintenance/latest.md` instead of creating a new history file. Use a Chinese task summary:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "<中文简短需求摘要>" --files <changed-source-files>
```

`--files` should list the source files actually affected by the requirement. Project Intelligence maintains one concise Chinese requirement markdown per source file at `.project-intel/requirements/files/<source-path>.md`; it should not create a new requirement file for every conversation.

Use `--archive` only when the user explicitly wants a timestamped maintenance record:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "<中文简短需求摘要>" --files <changed-source-files> --archive
```

Use `--run-quality` only when the user asks to run real lint/type/style/format commands:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "<中文简短需求摘要>" --files <changed-source-files> --run-quality
```

Maintenance refreshes `.project-intel`, writes the latest maintenance report, updates file-level requirement records, runs `project-intel check`, and keeps redundancy findings at `candidate` unless a human promotes them. Do not read or rely on `.cgraphx`.
