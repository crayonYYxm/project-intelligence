---
name: project-knowledge
description: Use when answering questions about project structure, components, Hooks, APIs, services, modules, standards, business flows, generated knowledge, or reusable patterns. 项目知识, 项目结构, 项目架构, 组件, 接口, 服务, 模块.
---

# Project Knowledge

Answer from `.project-intel` first:

- `.project-intel/manifest.json` for project overview and graph source status
- `.project-intel/standards/*.md` for rules and conventions
- `.project-intel/knowledge/*.json` for components, Hooks, APIs, services, files, and candidates
- `.project-intel/graph/project-graph.json` for graph summary
- `.project-intel/specs/*.md` and `.project-intel/plans/*.md` only when the user explicitly generated specs/plans
- `.project-intel/reports/*.md` for stable initialization, tooling, quality, and optional task/debug reports
- `.project-intel/maintenance/latest.md` for the latest post-task refresh; timestamped maintenance files exist only when `--archive` was requested
- `.project-intel/requirements/files/**/*.md` for one concise Chinese requirement history per affected source file

Use GitNexus for precise symbol-level questions. Use Understand-Anything for architecture/domain questions.

Search with:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py query "<question>"
```

Do not read or rely on `.cgraphx`.
