---
name: project-review
description: Use when reviewing code changes, PRs, diffs, review fixes, implementation quality, reuse, standards, GitNexus impact, Understand-Anything context, redundancy, and test gaps. 代码审查, 代码评审, PR审查, 代码检查, 审查代码, review, review代码.
---

# Project Review

Review findings first, ordered by severity. Use `.project-intel` as the local project fact source.

Workflow:

1. Read `.project-intel/manifest.json`, relevant standards, knowledge JSON, graph summary, and reports. If facts are missing, run read-only `project-intel doctor` or `project-intel init --dry-run`; initialize only after explicit user authorization.
2. Inspect the git diff and impacted files.
3. Use GitNexus for symbol impact/call chains when available.
4. Use Understand-Anything for architecture/domain context when available.
5. Run `project-intel check`; use `--run-quality` only when the user asks to run lint/type/style/format commands.
6. Flag hard-rule violations, behavioral risks, missing tests, repeated implementations, ignored reuse opportunities, and stale `.project-intel` facts. For changed behavior, inspect `.project-intel/reports/test-evidence.json` and verify that evidence matches the task, changed files, and current source state.
7. If a finding is a bug or failed behavior, use `project-intel debug --bug "<finding>"` before recommending a fix. `debug` prints by default; use `--write` only when a persistent debug report is explicitly needed.
8. For subagent or multi-task execution, review each task diff before moving to the next task, then perform one final whole-diff review.
9. When receiving review feedback, verify each item against the current codebase before editing. Clarify unclear feedback first, apply valid feedback one item at a time, and push back with technical evidence when feedback conflicts with project reality, YAGNI, compatibility, or prior user decisions.
10. After fixes are freshly recorded through `project-test`, persist a new review round with the same requirement ID. Then use `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>` before `project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>`.

Command:

```bash
project-intel check
```

Use `.project-intel`, GitNexus impact context when available, Understand-Anything architecture context when available, and direct source reads.

Do not claim a review finding is fixed until the relevant diff and verification output have been inspected in the current turn.

For requirement-level delivery, persist the review against the current Git diff hash:

```bash
project-intel review --requirement-id "<id>" --result passed|failed \
  --summary "<summary>" --finding important:<finding> --files <all-changed-files>
```

Do not report `passed` while critical or important findings remain unresolved. Any source change after review invalidates the review and requires a new round.

Resolve verified fixes by stable finding ID before recording the new review round:

```bash
project-intel requirement resolve-finding --requirement-id "<id>" \
  --finding-id "FINDING-01-01" --resolved-by "<reviewer>" --resolution "<verified-fix>"
```

Do not edit the manifest directly and do not let a clean later review silently erase earlier blocking findings.
