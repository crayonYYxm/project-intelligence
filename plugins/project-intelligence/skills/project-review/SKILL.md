---
name: project-review
description: Use when reviewing code changes, PRs, diffs, review fixes, implementation quality, reuse, standards, GitNexus impact, Understand-Anything context, redundancy, and test gaps. 代码审查, 代码评审, PR审查, 代码检查, 审查代码, review, review代码.
---

# Project Review

Review findings first, ordered by severity. Use `.project-intel` as the local project fact source.

Workflow:

1. Read `.project-intel/manifest.json`, relevant standards, knowledge JSON, graph summary, and reports.
2. Inspect the git diff and impacted files.
3. Use GitNexus for symbol impact/call chains when available.
4. Use Understand-Anything for architecture/domain context when available.
5. Run `project-intel check`; use `--run-quality` only when the user asks to run lint/type/style/format commands.
6. Flag hard-rule violations, behavioral risks, missing tests, repeated implementations, ignored reuse opportunities, and stale `.project-intel` facts.
7. If a finding is a bug or failed behavior, use `project-intel debug --bug "<finding>"` before recommending a fix. `debug` prints by default; use `--write` only when a persistent debug report is explicitly needed.
8. After fixes are completed, use `project-intel maintain --task "<summary>"` to refresh facts and update `.project-intel/maintenance/latest.md`. Use `--archive` only when the user wants a historical maintenance record.

Command:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py check
```

Do not use `.cgraphx`.
