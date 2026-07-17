---
name: project-test
description: Use after requirement ready to choose the test type and report action, and after requirement begin to execute or record RED/GREEN/regression/manual evidence. 测试, 单元测试, 服务测试, 接口测试, 回归测试, 测试报告, 真机验证, TDD, 验证证据.
---

# Project Test

Use this as the testing workflow inside `project-task` and `project-debug`. It is not a replacement for project context, review, or finish.

## Choose The Evidence Mode

1. Read `.project-intel/config.json` and the relevant source/test files.
2. Prefer the smallest command that proves the changed behavior.
3. Use automated tests for testable behavior. Use manual evidence only for visual, device, configuration, generated, or legacy behavior that cannot be automated reasonably.
4. Record the affected source and test files with every evidence entry. Empty `--files` is invalid; use explicit `--project-wide` only for genuine project-wide evidence.

## Automated Test Cycle

For a feature, bug fix, or behavior change:

1. Write one focused test or reproduction before production code.
2. Record RED and read the output. It must fail for the expected missing behavior, not because the command is invalid, times out, or has a syntax/setup error:

```bash
project-intel test --requirement-id "<id>" --test-kind unit --report-action generate --phase red \
  --command "<targeted-test-command>" --expect-failure "<expected-error-regex>" \
  --files <source-file> <test-file>
```

3. Implement the smallest change that satisfies the test.
4. Record GREEN and confirm the target test passes:

```bash
project-intel test --requirement-id "<id>" --test-kind unit --report-action generate --phase green \
  --command "<targeted-test-command>" --files <source-file> <test-file>
```

5. Refactor only while the target test stays green.
6. Run affected regression tests, then broader verification when risk justifies it:

```bash
project-intel test --requirement-id "<id>" --test-kind unit --report-action generate --phase regression \
  --command "<affected-test-command>" --files <changed-source-and-test-files>
project-intel test --requirement-id "<id>" --test-kind unit --report-action generate \
  --phase verify --files <changed-source-and-test-files> --acceptance AC-01,AC-02
```

When no `--command` is supplied outside RED, the CLI runs detected `test` and `verify` commands from `.project-intel/config.json`.

## Manual Evidence

If automated tests are not reasonable, record a reproducible procedure and observed result instead of silently skipping verification:

```bash
project-intel test --requirement-id "<id>" --test-kind manual --report-action generate --phase manual \
  --manual-approved --manual-category visual \
  --manual-reason "<why-automation-is-unreasonable>" --manual-steps "<steps>" \
  --manual-input "<input>" --manual-observation "<observation>" \
  --manual-evidence-path <repo-relative-screenshot-or-log> --files <changed-source-files> \
  --acceptance AC-01,AC-02
```

Manual evidence must describe what was exercised and what was observed. “已手动验证” is not sufficient.

## Existing Code And Exceptions

- Do not delete valid existing work merely because the test was added late. State that RED was not observed, add the strongest regression or characterization test available, and keep the limitation visible.
- For refactors that preserve behavior, a passing characterization baseline can be acceptable; record regression/verify evidence and explain why RED is not applicable.
- Avoid tests that only assert mocks, test-only production APIs, or implementation details unless isolation makes them unavoidable.
- A passing lint, type check, build, `project-intel check`, or Agent report does not by itself prove changed behavior.

## Completion Gate

`project-intel finish` requires task-matching, file-scoped, fresh passing evidence for changed source files. It accepts GREEN, regression, verify, or explicit manual evidence. RED is required by this workflow for new behavior and bug fixes, but the CLI keeps it visible rather than deleting existing code or guessing whether a legacy task is testable.

Always read the command output before claiming a test passed or a regression was fixed.

## Requirement-Level Report Gate

Before executing tests, ask both questions explicitly:

1. Test type: `unit`, `service`, `both`, or `manual`.
2. Test document action: `generate`, `register existing`, or `later`.

In a requirement lifecycle, these questions may be answered while the requirement is `ready`, but do not execute the CLI command, generate/register the report, or edit a test file until `project-task` has successfully run `requirement begin` and the state is `implementing`.

Pass the requirement ID and the selected action:

```bash
project-intel test --requirement-id "<id>" --test-kind unit \
  --report-action generate|register|later --report-path <existing-report-if-register> \
  --phase green --command "<command>" --files <source-and-test-files> \
  --acceptance AC-01,AC-02
```

For external API impact, require `service` or `both`. A generated `test-report.md` starts as a plan and becomes valid only after actual execution is appended. `later`, empty, RED-only, stale, or failed evidence never satisfies finish.

Use manual testing only for visual, device, hardware, or configuration behavior that cannot reasonably be automated. Obtain explicit approval and record reason, steps, input, observation, and an existing screenshot/log path using the `--manual-*` options. A one-line “verified manually” statement is invalid.
