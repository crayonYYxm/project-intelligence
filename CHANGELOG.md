# Changelog

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
