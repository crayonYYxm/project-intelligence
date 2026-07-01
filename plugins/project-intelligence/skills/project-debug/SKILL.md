---
name: project-debug
description: Use when investigating bugs, errors, test failures, regressions, unexpected behavior, 查询bug, 排查bug, 定位问题, root cause, or debugging with project standards, graph context, and systematic-debugging discipline.
---

# Project Debug

Use project facts and systematic debugging before proposing fixes.

1. Read `.project-intel/manifest.json`; if missing, run `project-intel init`.
2. Generate debug context:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py debug --bug "<bug or error>"
```

3. Read `.project-intel/reports/debug-context.md`, relevant standards, knowledge JSON, graph summary, and tooling report.
4. Complete root-cause investigation before fixes: read the full error, reproduce, inspect recent changes, trace data/control flow, compare with working project examples, then state one testable hypothesis.
5. Use GitNexus for call chains, impact, changed-code risk, and “what calls this” questions when available. Use Understand-Anything for architecture/domain context.
6. Add a failing regression test or minimal reproduction before implementing the fix when the project supports tests.
7. After the fix, run `project-intel check`; then run `project-intel maintain --task "<bug summary>"`.

Do not guess fixes, stack multiple changes, or read/rely on `.cgraphx`.
