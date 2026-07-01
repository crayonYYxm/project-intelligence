# Project Intelligence

Project Intelligence is a local Codex/Claude-compatible project plugin for generating and using repository-level standards, knowledge, graph context, quality checks, and review guidance.

It intentionally does not integrate with cgraphx. GitNexus and Understand-Anything are treated as recommended graph sources when available.

## Install

Clone this repository:

```bash
git clone https://github.com/crayonYYxm/project-intelligence.git
cd project-intelligence
```

Add this repository as a Codex marketplace:

```bash
codex plugin marketplace add .
codex plugin add project-intelligence@project-intelligence
```

Start a new Codex thread after installation so the plugin skills are loaded.

## CLI

The plugin CLI lives at:

```bash
plugins/project-intelligence/scripts/project-intel
```

Typical usage:

```bash
plugins/project-intelligence/scripts/project-intel --project /path/to/repo init
plugins/project-intelligence/scripts/project-intel --project /path/to/repo refresh
plugins/project-intelligence/scripts/project-intel --project /path/to/repo check
plugins/project-intelligence/scripts/project-intel --project /path/to/repo install
plugins/project-intelligence/scripts/project-intel --project /path/to/repo query "table"
```

## Skills

- `project-task`: use project standards and knowledge before implementation.
- `project-review`: review code with standards, graph context, quality checks, and reuse risks.
- `project-knowledge`: answer questions about components, APIs, modules, services, and standards.
- `project-refresh`: initialize or refresh `.project-intel`.
- `project-standards`: explain and manage rule levels.
- `project-quality`: run and interpret lint/type/style/format and redundancy checks.
