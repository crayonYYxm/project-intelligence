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
5. Do not create shared spec, plan, lifecycle, intake, or report files. New requirement-level durable files belong only in `.project-intel/requirements/<YYYY-MM-DD>-<id>-<title>/`; legacy `<id>-<title>/` and `<id>/` archives remain readable.
6. The four durable lifecycle documents are mandatory: the titled requirement/Bug document, design document, test document, and closure document. They cannot be deferred. Do not ask the user to choose a document action: use `register` when a valid existing repository-relative file was supplied, otherwise use `generate`, and persist both choices in `manifest.workflowSelections`.
7. Route first to `project-spec`. Always execute the lifecycle in this order: `project-spec` first, then `project-debug` for a Bug, then `project-design`. `project-spec` must generate or register the titled requirement/Bug document and persist the same numbered acceptance criteria in the manifest.
   - If a standalone spec was supplied, register and validate it.
   - If no standalone spec exists but a design document was supplied, keep `requirement=generate` and `design=register`; `project-spec` must read the selected design source and derive the spec and AC before `project-design` validates and registers that design.
   - If neither document exists, generate the spec first and the design second.
8. After the titled requirement/Bug document, manifest AC, and titled design document are current, invoke `project-test` **before** `requirement ready`. Ask for the evidence kind, then use `report-action=register` only for a supplied valid structured report; otherwise use `report-action=generate`. The Skill must run `project-intel requirement test-contract set --requirement-id "<id>" --kind unit|service|both|manual --report-action generate|register --acceptance <explicit-AC-ids>`; no default test kind or automatic AC mapping is valid. Generate the optional titled implementation plan only for complex work or when the user explicitly asks for a persistent plan. Then run `requirement ready`. Only after ready succeeds, route into `project-task` or `project-orchestrate`. `project-task` must run `requirement begin` before any test-file edit, report generation, or test command is executed.
9. The same-turn handoff is mandatory for implementation-intent requests. If the user says not to edit yet, complete the applicable pre-edit Skill handoff and stop before file changes; do not stop at intake or substitute `project-knowledge` for the test/task workflow.

Use GitNexus for precise impact when available and Understand-Anything for architecture/domain context when available.

For implementation intent, ask for the requirement ID, requirement name, and user-supplied version date before routing. Generate `LOCAL-YYYYMMDD-HHMMSS` when no formal ID exists. Accept a full version date such as `2026-07-23` or a current-year shorthand such as `7.23版本` / `7月23日`; do not silently use today's date. If the user supplies a local requirement document plus its requirement ID and version, use those values for the same intake. Explicitly ask whether external APIs are affected, then register the requirement:

```bash
project-intel intake --requirement-id "<id>" --requirement-name "<name>" \
  --version-date "<YYYY-MM-DD or M.D版本>" \
  --ticket-kind bug|requirement --external-api yes|no --track auto \
  --requirement-action generate|register \
  --design-action generate|register
```

When either action is `register`, also pass its repository-relative file via `--requirement-path` or `--design-path`. When actions are omitted, the CLI defaults missing documents to `generate` and a supplied path to `register`. Future sessions and subagents must reuse `requirement status --json` instead of asking again or guessing.

Infer Bug versus Requirement from the ticket and source, asking only when ambiguous. Pure numeric IDs are canonicalized to `bug<digits>` or `req<digits>` by intake; use the returned ID for every later command. Do not ask for requirement identity during knowledge-only explanation or read-only review.
