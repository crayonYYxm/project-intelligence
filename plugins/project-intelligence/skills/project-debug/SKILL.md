---
name: project-debug
description: Use when investigating bugs, errors, test failures, regressions, unexpected behavior, 查询bug, 排查bug, 定位问题, root cause, or debugging with project standards, graph context, and systematic-debugging discipline.
---

# Project Debug

Use project facts and systematic debugging before proposing fixes.

1. Read `.project-intel/manifest.json`; if missing, run `project-intel doctor` or `project-intel init --dry-run`, and initialize only with explicit user authorization.
2. Generate debug context. This prints context by default and does not create a report file:

```bash
project-intel debug --bug "<bug or error>"
```

3. Read relevant standards, knowledge JSON, graph summary, tooling report, and the printed debug context. Use `--write` only when the user explicitly wants `.project-intel/reports/debug-context.md`.
4. Complete root-cause investigation before fixes: read the full error, reproduce, inspect recent changes, trace data/control flow, compare with working project examples, then state one testable hypothesis.
5. Use GitNexus for call chains, impact, changed-code risk, and “what calls this” questions when available. Use Understand-Anything for architecture/domain context.
6. Invoke `project-test`. Add a failing regression test or minimal reproduction before implementing the fix when the project supports tests, then record the expected RED output.
7. Test exactly one hypothesis at a time. If three fix attempts fail or the symptom moves without a clear explanation, stop changing code and re-check the architecture, assumptions, inputs, environment, and reproduction path.
8. After the fix, record GREEN/regression evidence with the same requirement ID, then run `project-intel check`, persist `project-intel review --requirement-id "<id>" ...`, and run `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>`. Only after finish succeeds, run `project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>`.

Do not guess fixes or stack multiple changes.

When the bug fix changes code, obtain the requirement ID/name through `project-intake` with `--ticket-kind bug`. Complete root-cause investigation, then invoke `project-design` to generate or validate the compact Bug design, invoke `project-spec` to persist acceptance criteria in the manifest, and pass the readiness gate. Run `project-intel requirement begin --requirement-id "<id>"` before editing and pass that ID through RED, GREEN, review, finish, and maintain.
