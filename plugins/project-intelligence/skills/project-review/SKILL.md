---
name: project-review
description: Use when reviewing code changes against project standards, reusable components, APIs, services, GitNexus impact, Understand-Anything context, quality checks, redundancy, and test gaps.
---

# Project Review

Review findings first, ordered by severity. Use `.project-intel` as the local project fact source.

Workflow:

1. Read `.project-intel/manifest.json`, relevant standards, knowledge JSON, graph summary, and reports.
2. Inspect the git diff and impacted files.
3. Use GitNexus for symbol impact/call chains when available.
4. Use Understand-Anything for architecture/domain context when available.
5. Run `project-intel check`; use `--run-quality` only when the user asks to run lint/type/style/format commands.
6. Flag hard-rule violations, behavioral risks, missing tests, repeated implementations, and ignored reuse opportunities.

Command:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py check
```

Do not use `.cgraphx`.
