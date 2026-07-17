---
name: project-debug
description: Use when investigating bugs, errors, test failures, regressions, or unexpected behavior and proving a root cause. 查询 Bug, 排查 Bug, 定位问题, 定位根因, 为什么会这样, root cause, regression. In a Bug lifecycle it runs after project-spec and before project-design.
---

# Project Debug

Use project facts and systematic debugging before proposing fixes.

1. Read `.project-intel/manifest.json`; if missing, run `project-intel doctor` or `project-intel init --dry-run`, and initialize only with explicit user authorization.
2. Generate debug context. This prints context by default and does not create a report file:

```bash
project-intel debug --bug "<bug or error>"
```

3. Read relevant standards, knowledge JSON, graph summary, `.project-intel/project-status.md`, and the printed debug context. Do not create a shared debug report.
4. Complete root-cause investigation before fixes: read the full error, reproduce, inspect recent changes, trace data/control flow, compare with working project examples, then state one testable hypothesis.
5. Use GitNexus for call chains, impact, changed-code risk, and “what calls this” questions when available. Use Understand-Anything for architecture/domain context.
6. During the pre-design diagnosis, gather a read-only reproduction and evidence-backed root cause without executing lifecycle test commands. Persist the diagnosis before `project-design`:

```bash
project-intel requirement diagnose --requirement-id "<id>" \
  --root-cause "<evidence-backed-root-cause>" \
  --evidence "<repo-relative-path#symbol>"
```

7. Each evidence path must resolve inside the repository and identify the file or `path#symbol` that supports the root-cause claim; repeat `--evidence` when more than one source location is necessary. A Bug cannot pass `requirement ready` without a current diagnosis. After `project-design`, optional planning, and ready are complete, invoke `project-test` to select the evidence mode and report action. After `project-task` runs `requirement begin`, add a failing regression test or minimal reproduction before implementing the fix, then record the expected RED output.
8. Test exactly one hypothesis at a time. If three fix attempts fail or the symptom moves without a clear explanation, stop changing code and re-check the architecture, assumptions, inputs, environment, and reproduction path.
9. After the fix, record GREEN/regression evidence with the same requirement ID, then run `project-intel check`, persist `project-intel review --requirement-id "<id>" ...`, and run `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>`. Only after finish succeeds, run `project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>`.

Do not guess fixes or stack multiple changes.

When the bug fix changes code, use exactly this pre-edit lifecycle: `project-intake --ticket-kind bug` → `project-spec` → `project-debug` → `project-design` → optional `project-plan` → `requirement ready`. Do not route back from design to spec unless source evidence exposes a real requirement contradiction that the user must resolve. Then select the test strategy, run `project-intel requirement begin --requirement-id "<id>"` before editing or executing tests, and pass that ID through RED, GREEN, review, finish, and maintain.
