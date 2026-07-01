---
name: project-knowledge
description: Use when answering questions about project structure, components, Hooks, APIs, services, modules, standards, business flows, generated knowledge, or reusable patterns.
---

# Project Knowledge

Answer from `.project-intel` first:

- `.project-intel/manifest.json` for project overview and graph source status
- `.project-intel/standards/*.md` for rules and conventions
- `.project-intel/knowledge/*.json` for components, Hooks, APIs, services, files, and candidates
- `.project-intel/graph/project-graph.json` for graph summary
- `.project-intel/specs/*.md` and `.project-intel/plans/*.md` for task lifecycle docs
- `.project-intel/reports/*.md` for initialization, tooling, quality, task impact, and redundancy reports

Use GitNexus for precise symbol-level questions. Use Understand-Anything for architecture/domain questions.

Search with:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py query "<question>"
```

Do not read or rely on `.cgraphx`.
