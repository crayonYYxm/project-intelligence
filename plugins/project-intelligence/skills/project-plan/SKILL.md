---
name: project-plan
description: Use when turning a project spec or approved requirement into an implementation plan, task checklist, execution plan, write plan, 技术方案, or development steps.
---

# Project Plan

Create plans that preserve project standards and are ready to execute.

1. Start from the spec or requirement plus `.project-intel` facts.
2. Include reuse checks before implementation steps.
3. Include tests, quality commands, review, and post-task maintenance.
4. Keep the implementation plan in context by default. Generate a plan file only when the user explicitly asks for a persistent plan and provides or requests a spec file:

```bash
project-intel plan --title "<title>" --from-spec <spec-path>
```

If there is no persistent spec file, plan directly from the approved requirement. Do not create spec or plan files merely because the skill triggered.
