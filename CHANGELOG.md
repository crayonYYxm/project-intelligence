# Changelog

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
