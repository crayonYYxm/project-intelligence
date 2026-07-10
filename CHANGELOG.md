# Changelog

## 0.1.13 - 2026-07-11

- Split reusable scanner, graph, quality, lifecycle, standards, core, and CLI helpers from the main CLI facade.
- Keep committed project facts portable and move local tooling and scan cache data to `.project-intel/local/`.
- Validate graph sources before accepting strict initialization, support untracked-file requirement history, and improve knowledge query context.
- Add workspace and Java/Python/Go/Rust quality command discovery.
- Publish a Node-based npm launcher for the Python CLI, plus explicit Claude/Codex plugin installation and runtime diagnostics.
