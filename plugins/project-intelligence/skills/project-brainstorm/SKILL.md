---
name: project-brainstorm
description: Use when shaping a project requirement, brainstorming approaches, clarifying scope, comparing implementation directions, writing 需求脑暴, or deciding what a feature should do before code changes.
---

# Project Brainstorm

Start with project facts, then turn the idea into a concrete direction.

1. Read `.project-intel/manifest.json` if it exists; if missing, run `project-intel init`.
2. Inspect relevant standards, knowledge JSON, graph summary, and recent reports.
3. Ask only questions that materially affect scope, success criteria, reuse, risk, or UX/API behavior.
4. Present 2-3 feasible approaches with tradeoffs and a recommendation.
5. When the direction is stable, keep a lightweight Chinese spec in context. Create a persistent spec file only when the user explicitly asks for one:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project_intel.py" spec --title "<title>" --from "<requirement>"
```

Prefer existing components, Hooks, services, APIs, domain flows, and standards. Use GitNexus for precise impact when available and Understand-Anything for architecture/domain context.
