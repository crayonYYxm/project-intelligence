---
name: project-plan
description: Use when turning a project spec or approved requirement into an implementation plan, task checklist, execution plan, write plan, 技术方案, or development steps.
---

# Project Plan

Create plans that preserve project standards and are ready to execute.

1. Start from the spec or requirement plus `.project-intel` facts.
2. Include reuse checks before implementation steps.
3. Include tests, quality commands, review, and post-task maintenance.
4. Generate a plan file when a spec exists:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project_intel.py" plan --title "<title>" --from-spec <spec-path>
```

If there is no spec yet, create one first with `project-intel spec`. Do not read or rely on `.cgraphx`.
