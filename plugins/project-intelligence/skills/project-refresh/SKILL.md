---
name: project-refresh
description: Use when initializing, refreshing, or updating project standards, knowledge, graph summaries, quality configuration, reports, or Claude adapters.
---

# Project Refresh

Use this skill when the user says to initialize or update project standards, knowledge, graph context, reports, or Claude adapters.

Commands:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py refresh
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py install
```

`refresh` scans current workspace contents relative to the last generated project facts. It includes code pulled from other authors because project intelligence is based on file facts, not author identity.

The CLI intentionally does not read `.cgraphx`.
