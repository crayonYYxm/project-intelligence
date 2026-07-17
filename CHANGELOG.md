# Changelog

## 0.5.0 - 2026-07-17

- Add explicit `project-intel adapters status|preview|apply|remove` commands and make `install` / `refresh --adapters` use the same safe adapter writer.
- Replace large root adapter copies with short Codex and Claude entry blocks; keep `.claude/CLAUDE.md` as a pointer instead of a second full workflow copy.
- Harden adapter writes against symlink paths, malformed or duplicate managed markers, oversized files, and unmarked user-created same-name local skills.
- Add requirement `testContract` state and `requirement test-contract set` so test type, report action, and acceptance mapping are persisted before implementation.
- Tighten JSON error redaction and add read-only dry-run paths for check, review, finish, and maintain.

## 0.4.0 - 2026-07-17

- Consolidate each lifecycle under `.project-intel/requirements/<id>/` with mandatory `requirement.md`, `design.md`, `test-report.md`, and `closure-summary.md`, plus optional `plan.md`.
- Replace shared init, refresh, tooling, quality, finish, and maintenance reports with one replaceable `.project-intel/project-status.md` and requirement-manifest results.
- Add schema v2 `draft -> specified -> designed` document gates, canonical document registration, direct requirement directories, and v1/by-id read compatibility.
- Store changed-file history in requirement manifests and add `requirement query --file|--state` instead of creating ambiguous `requirements/files` mirrors.
- Add dry-run-first `requirement migrate` support and report legacy shared outputs that cannot be assigned safely to a requirement.
- Update Skills, generated Agent rules, CLI examples, and project documentation so new workflows do not create shared `reports`, `specs`, `plans`, or `maintenance` directories.
- Require a persisted source-backed Bug diagnosis before readiness, invalidate designs created before the confirmed root cause, and recheck all readiness inputs again at begin.
- Validate requirement, design, optional plan, test, and closure documents against the current manifest; retain readable per-requirement test history with test scope and immutable registered-report evidence.
- Make layout migration preflight-and-rollback safe, register delivery documents under one manifest lock, and reject test/review/finish evidence when the Git scope changes during registration.
- Harden persisted output redaction and Markdown rendering, including authorization schemes, URL credentials, customer identifiers, review text, manual evidence, and command output.
- Make Skill routing and live-eval evidence fail closed, remove hard-coded test choices from generated workflows, and add installed-tarball launcher smoke validation.
- Merge committed changes from the intake baseline with the live worktree when calculating requirement scope, so clean post-commit worktrees cannot hide delivered source changes.
- Evaluate the latest result independently for each test channel, verify every contributing report and hash again at finish/maintain, and serialize concurrent readable-report updates.
- Refresh the packaged introduction page around per-requirement files and expand natural-language routing coverage so every packaged Skill has a positive scenario.
- Persist intake requirement/design actions and registered source paths in `workflowSelections`, expose them through status, and require explicit amend instead of cross-session guessing.

## 0.3.1 - 2026-07-17

- Parse registered Markdown/TXT, JSON, and XML test reports and reject a declared `passed` result when the report records failure; revalidate current reports again at finish so older manifests cannot retain a false pass.
- Validate closure summaries for required result, scope, acceptance, test, review, manual-exception, remaining-issue, and retrospective sections; generated summaries now contain current Git scope and manifest evidence instead of generic placeholders.
- Separate validated delivery artifacts from business evidence scope so `docs/requirements/` designs remain in the delivery diff and review while source-focused tests can cover the actual behavior files.
- Restore `project-design` detection in live Claude/Codex Skill evals by discovering packaged Skill names dynamically, and extend workflow scenarios for design/spec routing plus init/refresh/maintain trigger boundaries.
- Align intake `requiredStages`, Skill instructions, generated Agent rules, and documentation around `intake → design → spec → ready → begin → test/task → review → finish → maintain`.
- Narrow first-time init, fact refresh, post-finish maintenance, and read-only knowledge triggers to reduce accidental cross-routing.

## 0.3.0 - 2026-07-16

- Add `project-design` as the single source-backed Bug/Requirement development-design Skill, usable standalone without `.project-intel` side effects or inside the requirement lifecycle.
- Add strict compact Bug and CRM Requirement templates plus one shared validator for structure, identity, repository paths, placeholders, and sensitive information.
- Separate numbered acceptance criteria from the design document with `requirement acceptance set`; readiness now requires both a validated current design artifact and manifest criteria.
- Add `ticketKind`, numeric `bug`/`req` ID canonicalization, scaffold-only requirement generation, design validation status, and stale-design invalidation after material amendments.
- Route intake, debugging, spec, plan, task, orchestration, generated Agent rules, documentation, and Skill behavior evals through the new design stage.

## 0.2.1 - 2026-07-16

- Prevent registered reports from hiding business changes, revalidate the finish snapshot before close, and add stable finding resolution with `resolvedBy` history.
- Require explicit authorization for repository graph runners, environment-provided commands, and project-external command paths; redact review and quality-report content before persistence.
- Ignore Java/Kotlin and JavaScript/TypeScript route-like text inside comments and string literals while preserving real route extraction.
- Make backend API scanning language-aware: Python routes use AST facts, route-like strings no longer produce Spring APIs, and test fixtures are separated from production API counts.
- Add macOS and Windows CLI smoke jobs plus scheduled/manual isolated Claude and Codex live Skill evaluations with ten behavior scenarios.
- Make the live-eval per-scenario budget configurable and raise the default ceiling to avoid terminating after the intake Skill alone.
- Move requirement lifecycle, atomic manifest persistence, scope hashing, and artifact handling into `project_intel_lib/requirements.py`, keeping the main CLI as a compatibility facade for the new subsystem.
- Reduce `project_intel.py` to a thin backwards-compatible loader and move application services/command dispatch into `project_intel_lib/application.py`.

## 0.2.0 - 2026-07-16

- Add revisioned requirement archives under `.project-intel/requirements/by-id/<id>/` with requirement/design, living test report, closure summary, numbered acceptance criteria, and a `draft → documented → ready → implementing → verified → reviewed → finished → closed` state machine.
- Add `requirement`, requirement-aware `intake/test/finish/maintain`, and persistent `review` CLI commands with JSON-compatible results, explicit external-API confirmation, document actions, manual-test approval, and legacy warnings.
- Enforce explicit test scope, expected RED failure matching, pytest infrastructure error rejection, secret redaction, content/diff hashes, actual Git scope coverage, service-test policy for external APIs, stale evidence invalidation, and finish-before-maintain.
- Make init and routine refresh fact-only; root `.gitignore`, `AGENTS.md`, and `CLAUDE.md` change only through explicit `install` or `refresh --adapters`.
- Update lifecycle Skills to ask for requirement ID/name, document actions, test type/report action, review evidence, and closure-summary handling without adding external workflow dependencies.

## 0.1.17 - 2026-07-16

- Add `project-test` and `project-intel test` for targeted RED, GREEN, regression, verification, and reproducible manual evidence stored in stable task-scoped reports.
- Make `project-intel finish` reject changed source without fresh evidence matching the current task, file scope, and source timestamps; `--run-quality` can contribute detected test/verify results and `--manual-evidence` is an explicit fallback.
- Route feature, bug, plan, review, orchestration, and finish workflows through the test-evidence cycle without adopting automatic worktrees, commits, or destructive TDD rules.
- Make implementation-intent intake hand off to `project-test` and `project-task` in the same turn, including read-only pre-edit requests, so project knowledge cannot silently replace the implementation workflow.
- Add deterministic Skill scenario contracts plus an opt-in headless Claude behavior-eval runner, and split new test-evidence coverage into a dedicated test module.

## 0.1.16 - 2026-07-13

- Add `project-intake` for quick/standard/complex task routing, readiness checks, risk flags, missing information, affected areas, standards, and reuse candidates.
- Add `project-finish` and `project-intel finish` for completion evidence, scope drift, git diff, quality status, and release-safety closure before maintenance.
- Enrich `lifecycle`, `spec`, and `plan` with track-aware output, behavior contracts, readiness gates, and acceptance-to-evidence mapping while keeping default runs non-persistent.
- Update generated Agent entrypoint rules and existing skills to route through intake, finish, and then maintenance.

## 0.1.15 - 2026-07-13

- Add `project-orchestrate` for planned subagent execution, task handoffs, task-level review, final review, and verification gates.
- Strengthen `project-task`, `project-plan`, `project-review`, `project-debug`, and `project-maintain` with execution-mode selection, review feedback discipline, no stacked debug guesses, and evidence-before-completion rules.
- Update generated `AGENTS.md` / `CLAUDE.md` Project Intelligence blocks so initialized projects know when to use orchestration and fresh verification evidence.

## 0.1.14 - 2026-07-13

- Preserve existing `.gitignore` content when appending Project Intelligence local artifact rules.
- Avoid duplicate `.project-intel/*` ignore entries when a parent `.project-intel/` rule already covers them.

## 0.1.13 - 2026-07-11

- Split reusable scanner, graph, quality, lifecycle, standards, core, and CLI helpers from the main CLI facade.
- Keep committed project facts portable and move local tooling and scan cache data to `.project-intel/local/`.
- Validate graph sources before accepting strict initialization, support untracked-file requirement history, and improve knowledge query context.
- Add workspace and Java/Python/Go/Rust quality command discovery.
- Publish a Node-based npm launcher for the Python CLI, plus explicit Claude/Codex plugin installation and runtime diagnostics.
