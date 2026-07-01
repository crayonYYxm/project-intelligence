# Project Intelligence

Project Intelligence is a local Codex/Claude-compatible project plugin for generating and using repository-level specs, plans, standards, knowledge, graph context, systematic debugging, quality checks, lifecycle maintenance, and review guidance.

It intentionally does not integrate with cgraphx. GitNexus and Understand-Anything are treated as recommended graph sources when available.

## Install

### Claude Code

1. Add the marketplace first:
   ```bash
   /plugin marketplace add crayonYYxm/project-intelligence
   ```

2. Then install the plugin:
   ```bash
   /plugin add project-intelligence@project-intelligence
   ```

3. Start a new Claude Code session so the plugin skills are loaded.

### Codex CLI

```bash
git clone https://github.com/crayonYYxm/project-intelligence.git
cd project-intelligence
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
plugins/project-intelligence/scripts/project-intel --project /path/to/repo init --interactive
plugins/project-intelligence/scripts/project-intel --project /path/to/repo lifecycle --task "new requirement"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo debug --bug "error or unexpected behavior"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo spec --title "feature" --from "requirement"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo plan --title "feature" --from-spec .project-intel/specs/...
plugins/project-intelligence/scripts/project-intel --project /path/to/repo refresh
plugins/project-intelligence/scripts/project-intel --project /path/to/repo check
plugins/project-intelligence/scripts/project-intel --project /path/to/repo maintain --task "summary"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo install --hooks
plugins/project-intelligence/scripts/project-intel --project /path/to/repo query "table"
```

## Skills

- `project-task`: use project standards and knowledge before implementation.
- `project-brainstorm`: shape requirements and compare implementation approaches.
- `project-spec`: write requirement specs and impact notes from project facts.
- `project-plan`: turn specs into implementation plans.
- `project-debug`: investigate bugs with project context and root-cause discipline.
- `project-maintain`: refresh project knowledge after tasks or changes.
- `project-review`: review code with standards, graph context, quality checks, and reuse risks.
- `project-knowledge`: answer questions about components, APIs, modules, services, and standards.
- `project-refresh`: initialize or refresh `.project-intel`.
- `project-standards`: explain and manage rule levels.
- `project-quality`: run and interpret lint/type/style/format and redundancy checks.
