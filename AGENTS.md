<!-- agent-project-intelligence:start -->
## Project Intelligence First

Before any code change, debugging, review, requirement analysis, planning, spec work, or standards update, use the project-level intelligence workflow first.

Prefer available project skills such as:

- `project-brainstorm`
- `project-spec`
- `project-plan`
- `project-intake`
- `project-task`
- `project-debug`
- `project-review`
- `project-quality`
- `project-knowledge`
- `project-standards`
- `project-finish`
- `project-maintain`
- `project-orchestrate`
- `project-init`
- `project-refresh`

If skills are exposed through a plugin namespace, use the equivalent `project-intelligence:*` skill. If slash skills are unavailable, follow the same workflow manually with `.project-intel/` and the `project-intel` CLI. Do not rely only on basic file tools when project skills or project facts are available.
<!-- agent-project-intelligence:end -->

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **project-intelligence** (1502 symbols, 3574 relationships, 131 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/project-intelligence/context` | Codebase overview, check index freshness |
| `gitnexus://repo/project-intelligence/clusters` | All functional areas |
| `gitnexus://repo/project-intelligence/processes` | All execution flows |
| `gitnexus://repo/project-intelligence/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

<!-- project-intelligence:start -->
## Project Intelligence

This repository uses `.project-intel/` as the project-level fact source.

Project Intelligence is the workflow layer. Tools such as Grep, Read, Edit, Bash, Glob, or Write are only execution tools; using them does not replace the required Project Intelligence workflow.

If a conversation starts as explanation or discussion and later turns into code modification, pause before the first Edit/Write and enter the matching Project Intelligence workflow. Do not continue from discussion mode directly into code changes.

Before implementing, debugging, reviewing, planning, writing specs, answering component/API questions, or modifying behavior:

1. Classify the request and explicitly invoke the matching Project Intelligence skill when available:
   - Requirement intake, task routing, readiness, or scope classification: `project-intake` or `project-intelligence:project-intake`
   - Requirement shaping or brainstorming: `project-brainstorm` or `project-intelligence:project-brainstorm`
   - Requirement/spec/acceptance criteria/impact: `project-spec` or `project-intelligence:project-spec`
   - Implementation plan or checklist: `project-plan` or `project-intelligence:project-plan`
   - Implementation, modification, fix, refactor, or feature work: `project-task` or `project-intelligence:project-task`
   - Bug, error, regression, failed test, or unexpected behavior: `project-debug` or `project-intelligence:project-debug`
   - Code review, PR review, diff review, reuse/quality risk review: `project-review` or `project-intelligence:project-review`
   - Independent planned subtasks, subagent handoffs, task-level review, or parallel read-only investigations: `project-orchestrate` or `project-intelligence:project-orchestrate`
   - Quality, lint, type, format, style, redundancy checks: `project-quality` or `project-intelligence:project-quality`
   - Project knowledge, component/API/service usage, architecture questions: `project-knowledge` or `project-intelligence:project-knowledge`
   - Standards lookup, rule promotion/demotion, hard/preferred/inferred/candidate explanation: `project-standards` or `project-intelligence:project-standards`
   - Task finish, acceptance evidence, release readiness, or completion checks: `project-finish` or `project-intelligence:project-finish`
   - Post-task refresh and lifecycle maintenance: `project-maintain` or `project-intelligence:project-maintain`
   - Initialization of project facts and local adapters: `project-init` or `project-intelligence:project-init`
   - Refresh of project facts, tooling reports, and adapters: `project-refresh` or `project-intelligence:project-refresh`
2. If slash skills are not available or do not trigger automatically, follow the same workflow manually before using execution tools and state which Project Intelligence workflow is being followed.
3. Check `.project-intel/manifest.json` for project metadata and refresh status.
4. Read only the relevant files under `.project-intel/standards/`, `.project-intel/knowledge/`, `.project-intel/graph/`, and `.project-intel/reports/`.
5. Apply `hard` standards as requirements; treat `preferred` as default project style; treat `inferred` and `candidate` as suggestions that need confirmation before enforcement.
6. Prefer existing public components, Hooks, utilities, API wrappers, services, DTO/VO/entity patterns, permission checks, transaction boundaries, and error-code conventions before adding new ones.
7. For implementation work, before the first Edit/Write, run `project-intake` or `project-intel intake --task "<requirement>"` to classify `quick` / `standard` / `complex` and confirm readiness. Then run the `project-task` workflow: check reuse, affected modules, relevant standards, and impact. First produce or internally confirm a lightweight Chinese task spec: requirement summary, acceptance points, affected files/modules, reuse candidates, and assumptions/open questions. Do not create a spec file unless the user explicitly asks for one.
8. Use GitNexus impact/explore/detect_changes tools when available; otherwise use `.project-intel` plus `project-intel lifecycle --task "<requirement>"` or `project-intel query "<symbol-or-feature>"`. `lifecycle` prints by default and includes track/readiness; use `--write` only when a persistent task-impact report is explicitly needed.
9. Use `project-orchestrate` only when planned subtasks are independent enough to review separately. Implementation subagents should normally run sequentially; parallel agents are for read-only investigations or disjoint impact analysis.
10. After meaningful code changes, run change review, finish, and maintenance: inspect the diff, run `project-intel check`, run the concrete verification that proves the actual behavior claim, run `project-intel finish --task "<中文简短需求摘要>" --files <changed-source-files>`, and then run or recommend `project-intel maintain --task "<中文简短需求摘要>" --files <changed-source-files>`. The `--task` value used for finish/maintenance must be Chinese. `maintain` overwrites `.project-intel/maintenance/latest.md` by default and updates one short requirement markdown per affected source file under `.project-intel/requirements/files/`; use `--archive` only when the user wants a historical maintenance record.
11. Do not claim a change is complete, fixed, passing, or ready without fresh evidence from the current turn. `project-intel check` proves Project Intelligence rules; it does not prove business behavior unless the check directly exercises that behavior.
12. For bug investigation, first gather symptoms, reproduce or locate evidence, trace likely paths through project knowledge/graph context, then propose one testable hypothesis and avoid stacked guesses.
13. For review, inspect diff plus `.project-intel` standards/knowledge/graph context and report findings by severity before summaries. Verify review feedback against project reality before applying it.
14. Use `--run-quality` only when real lint/type/style/format checks should run.
15. If GitNexus or Understand-Anything graph context is available, use it for impact analysis and architecture/domain relationships.
Stable generated files are preferred for routine runs: refresh/tooling/quality reports are overwritten in place, `debug` and `lifecycle` only print unless `--write` is passed, `maintain` writes `maintenance/latest.md` unless `--archive` is passed, and file-level requirements are maintained as one concise Chinese markdown per source file.

Useful CLI fallbacks: `project-intel intake`, `project-intel lifecycle`, `project-intel query`, `project-intel refresh`, `project-intel check`, `project-intel spec`, `project-intel plan`, `project-intel debug`, `project-intel finish`, `project-intel requirements`, and `project-intel maintain`.
<!-- project-intelligence:end -->
