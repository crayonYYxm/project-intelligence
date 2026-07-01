---
name: project-quality
description: Use when running or interpreting frontend/backend quality checks, ESLint, Stylelint, Prettier check, tsc/vue-tsc, redundancy checks, or standards checks.
---

# Project Quality

Read `.project-intel/config.json` for detected quality commands and `.project-intel/reports/frontend-quality.md` for the latest result.

Default command:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py check
```

Run real lint/type/style/format commands only when requested:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py check --run-quality
```

Redundancy findings are `candidate` by default. They should inform refactoring and reuse discussions but should not block unless promoted by team policy.

Do not use `.cgraphx`.
