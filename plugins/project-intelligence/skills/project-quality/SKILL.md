---
name: project-quality
description: Use when running or interpreting frontend/backend quality checks, ESLint, Stylelint, Prettier check, tsc/vue-tsc, tooling reports, redundancy checks, standards checks, or quality gaps. 质量检查, 代码质量, 检查工具, lint检查, 质量报告.
---

# Project Quality

Read `.project-intel/config.json` for detected quality commands and `.project-intel/reports/frontend-quality.md` for the latest result.
Also read `.project-intel/reports/tooling-report.md` to see missing optional tools and setup suggestions.

Default command:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project_intel.py" check
```

Run real lint/type/style/format commands only when requested:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/project_intel.py" check --run-quality
```

Redundancy findings are `candidate` by default. They should inform refactoring and reuse discussions but should not block unless promoted by team policy.

When a quality command fails, treat it as a debugging task: read the full failure output, generate debug context with `project-intel debug --bug "<failure>"`, and identify root cause before suggesting fixes.

Do not use `.cgraphx`.
