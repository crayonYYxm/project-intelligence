---
name: project-maintain
description: Use when a task is finished, after implementation, after review fixes, after git pull/merge/commit, or when maintaining project standards, knowledge base, reports, hooks, or lifecycle artifacts.
---

# Project Maintain

Close project tasks by refreshing facts and recording what changed.

Run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "<summary>"
```

Use `--run-quality` only when the user asks to run real lint/type/style/format commands:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "<summary>" --run-quality
```

Maintenance refreshes `.project-intel`, writes a maintenance report, runs `project-intel check`, and keeps redundancy findings at `candidate` unless a human promotes them. Do not read or rely on `.cgraphx`.
