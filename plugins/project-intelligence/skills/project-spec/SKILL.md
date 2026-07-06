---
name: project-spec
description: Use when writing, updating, or explaining a project spec, design note, requirement document, acceptance criteria, task impact report, 需求文档, or 需求涉及关系和规范.
---

# Project Spec

Write specs from project facts, not guesses.

For implementation requests handled by `project-task`, do not force creation of a spec file. The task workflow should first整理轻量中文 spec in context: requirement summary, acceptance points, impact scope, reuse candidates, and assumptions/open questions. Create `.project-intel/specs/*.md` only when the user explicitly asks for a requirements/spec document.

1. Read `.project-intel/manifest.json`, relevant standards, knowledge JSON, graph summary, and reports.
2. Capture the requirement, impacted modules, reusable capabilities, standards, quality gates, and acceptance criteria.
3. Keep unknowns explicit; do not invent hard rules from `candidate` findings.
4. Generate the spec when useful:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py spec --title "<title>" --from "<requirement>"
```

For impact-only requests, run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py lifecycle --task "<requirement>"
```

This prints impact by default. Add `--write` only when the user explicitly wants `.project-intel/reports/task-impact.md`.

Do not read or rely on `.cgraphx`.
