---
name: project-init
description: Use when the user wants to initialize, set up, or bootstrap project intelligence for the first time. 初始化项目, 项目初始化, 搭建项目, 创建项目, 项目搭建, 初始化.
---

# Project Init

Use this skill when the user says to initialize, set up, or bootstrap project intelligence for a repository.

Commands:

```bash
python3 plugins/project-intelligence/scripts/project_intel.py init
python3 plugins/project-intelligence/scripts/project_intel.py init --no-graph
python3 plugins/project-intelligence/scripts/project_intel.py init --interactive
python3 plugins/project-intelligence/scripts/project_intel.py init --strict
```

`init` generates `.project-intel/` with standards, knowledge, graph summaries, quality configuration, tooling checks, and reports. It checks optional tools such as GitNexus, Understand-Anything, Node/package managers, and quality commands. Missing optional tools do not block initialization unless strict graph setup is requested.

By default, `init` attempts to generate graph sources (GitNexus). Use `--no-graph` to skip graph generation.

After initialization, use `/project-refresh` to update existing project facts.
