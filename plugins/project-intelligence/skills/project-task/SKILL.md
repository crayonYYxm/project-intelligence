---
name: project-task
description: Use when implementing a project request that should reuse existing project standards, components, Hooks, APIs, services, graph context, or knowledge before changing code.
---

# Project Task

Before implementing, read `.project-intel/manifest.json`. Then load only the relevant files under `.project-intel/standards`, `.project-intel/knowledge`, `.project-intel/graph`, and `.project-intel/reports`.

Use this sequence:

1. Identify related modules, components, Hooks, APIs, services, routes, and standards.
2. Prefer existing project abstractions before creating new ones.
3. Treat redundancy findings as `candidate` unless a rule has been promoted to `hard`.
4. Use GitNexus for symbol-level calls, impact, and change risk when available.
5. Use Understand-Anything for architecture, module, and domain-flow context when available.
6. Do not read or rely on `.cgraphx`.

If `.project-intel` is missing or stale, run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py init
```

After implementation, run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py check
```
