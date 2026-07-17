---
name: project-quality
description: Use when running or interpreting frontend/backend quality checks, ESLint, Stylelint, Prettier check, tsc/vue-tsc, tooling reports, redundancy checks, standards checks, or quality gaps. 质量检查, 代码质量, 检查工具, lint检查, 质量报告.
---

# Project Quality

Read `.project-intel/config.json` for detected quality commands and `.project-intel/project-status.md` for the latest scan, tooling, and quality result.

Default command:

```bash
project-intel check
```

Run configured lint/type/style/format/test/verify commands only when requested. For task completion, prefer `project-test` so test results become task-scoped finish evidence:

```bash
project-intel check --run-quality
```

Redundancy findings are `candidate` by default. They should inform refactoring and reuse discussions but should not block unless promoted by team policy.

Structured `hard` checks can fail the command. Natural-language hard rules without a machine check appear as `manual-review`; review them explicitly without treating them as an automatic pass or failure.

When a quality command fails, treat it as a debugging task: read the full failure output, generate debug context with `project-intel debug --bug "<failure>"`, and identify root cause before suggesting fixes.

`project-intel check --run-quality` executes every configured command. For a large or noisy repository, run the targeted project command directly for diagnosis. If the result must become requirement evidence, route through `project-test` and pass the active requirement ID, selected test kind/report action, phase, changed files, confirmed AC IDs, and command. A test command without lifecycle identity and evidence scope is invalid.

Use `.project-intel` quality facts and the project's own configured quality commands.
