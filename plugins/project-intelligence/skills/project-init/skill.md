---
name: project-init
description: Use when the user wants to initialize, set up, or bootstrap project intelligence for the first time.
---

# Project Init

Use this skill when the user says to initialize, set up, or bootstrap project intelligence for a repository.

Commands:

```bash
python3 plugins/project-intelligence/scripts/project_intel.py init
python3 plugins/project-intelligence/scripts/project_intel.py init --interactive
python3 plugins/project-intelligence/scripts/project_intel.py init --with-graph
```

`init` generates `.project-intel/` with standards, knowledge, graph summaries, quality configuration, tooling checks, and reports. It checks optional tools such as GitNexus, Understand-Anything, Node/package managers, and quality commands. Missing optional tools do not block initialization unless strict graph setup is requested.

After initialization, use `/project-refresh` to update existing project facts.
