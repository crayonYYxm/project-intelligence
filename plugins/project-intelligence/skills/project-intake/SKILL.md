---
name: project-intake
description: Use at the start of implementation intent to register and route a Bug or Requirement before any code or test execution. 我要做一个需求, 实现这个功能, 修复这个 Bug, 接入这个需求, 需求入口分析, 需求分流, readiness, quick/standard/complex. Do not use for read-only knowledge, standalone design-only, review-only, plugin installation, or project-fact refresh requests.
---

# Project Intake

Use this before code changes when a request may become implementation work.

1. Read `.project-intel/manifest.json` when it exists. If facts are missing, run read-only `project-intel doctor` or `project-intel init --dry-run`; run `init` only after the user explicitly authorizes initialization.
2. Run the intake analysis without writing a file by default:

```bash
project-intel intake --task "<requirement>"
```

3. Classify the track:
   - `quick`: small local behavior, copy, style, config, or low-risk fix.
   - `standard`: normal feature/change that needs lightweight spec and plan in context.
   - `complex`: cross-module, API/data/auth/payment/cache/async/release/compatibility/security/performance work.
4. If readiness is `needs-clarification`, resolve only the missing information that can change implementation or acceptance.
5. Do not create shared spec, plan, lifecycle, intake, or report files. Requirement-level durable files belong only in `.project-intel/requirements/<id>/`.
6. Route first to `project-spec` after collecting the requirement-document and design-document actions during intake. Persist both choices in `manifest.workflowSelections`; when `register` is chosen, persist the validated repository-relative source path too. Always execute the lifecycle in this order: `project-spec` first, then `project-debug` for a Bug, then `project-design`. `project-spec` must generate or register `requirement.md` and persist the same numbered acceptance criteria in the manifest. A `later` requirement document is a blocking choice.
7. After `project-spec`, handle the selected development-design action:
   - `generate`: invoke `project-design`; for a Bug, invoke `project-debug` first so the design contains an evidence-backed root cause.
   - `register existing`: for a Bug, ensure `project-debug` has persisted the current diagnosis first; then invoke `project-design` to validate and register the supplied repository-relative document.
   - `later`: defer the design artifact and stop before readiness.
8. After `requirement.md`, manifest AC, and `design.md` are current, invoke `project-test` for evidence-mode/report-action selection **before** `requirement ready`, then persist the testing contract. The Skill must run `project-intel requirement test-contract set --requirement-id "<id>" --kind unit|service|both|manual --report-action generate|register|later --acceptance <explicit-AC-ids>`; no default contract or automatic AC mapping is valid. Generate the optional `plan.md` only for complex work or when the user explicitly asks for a persistent plan. Then run `requirement ready`. Only after ready succeeds, route into `project-task` or `project-orchestrate`. `project-task` must run `requirement begin` before any test-file edit, report generation, or test command is executed.
9. The same-turn handoff is mandatory for implementation-intent requests. If the user says not to edit yet, complete the applicable pre-edit Skill handoff and stop before file changes; do not stop at intake or substitute `project-knowledge` for the test/task workflow.

Use GitNexus for precise impact when available and Understand-Anything for architecture/domain context when available.

For implementation intent, ask for the requirement ID and requirement name before routing. Generate `LOCAL-YYYYMMDD-HHMMSS` when no formal ID exists, explicitly ask whether external APIs are affected, then register the requirement:

```bash
project-intel intake --requirement-id "<id>" --requirement-name "<name>" \
  --ticket-kind bug|requirement --external-api yes|no --track auto \
  --requirement-action generate|register|later \
  --design-action generate|register|later
```

When either action is `register`, also pass its repository-relative file via `--requirement-path` or `--design-path`. Future sessions and subagents must reuse `requirement status --json` instead of asking again or guessing. Change an unfinished selection only with `requirement amend --reason ...`.

Infer Bug versus Requirement from the ticket and source, asking only when ambiguous. Pure numeric IDs are canonicalized to `bug<digits>` or `req<digits>` by intake; use the returned ID for every later command. Do not ask for requirement identity during knowledge-only explanation or read-only review.
