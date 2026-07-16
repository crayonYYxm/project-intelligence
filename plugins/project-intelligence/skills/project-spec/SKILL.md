---
name: project-spec
description: Use after project-design when clarifying requirement behavior, boundaries, acceptance criteria, or task impact and persisting numbered acceptance criteria to the requirement manifest. 需求澄清, 验收标准, acceptance criteria, 需求涉及关系和规范. Do not use to convert a local Bug/requirement ticket into a development design document; use project-design for that.
---

# Project Spec

Write specs from project facts, not guesses.

For requirement-level implementation, require a validated development-design artifact from `project-design`. Keep `.project-intel/specs/*.md` as a legacy compatibility output; use the requirement manifest plus its registered design artifact as the durable workflow source.

1. Read `.project-intel/manifest.json`, relevant standards, knowledge JSON, graph summary, and reports.
2. Run `project-intel intake --task "<requirement>"` or use the same track/readiness fields.
3. Read `project-intel requirement status --requirement-id "<id>" --json` and stop if `designValidation.ok` is false.
4. Capture the requirement, impacted modules, reusable capabilities, standards, quality gates, acceptance criteria, behavior contracts, and evidence mapping.
5. Keep unknowns explicit; do not invent hard rules from `candidate` findings.
6. Generate the legacy spec only when the user explicitly asks for a separate persistent requirements/spec document:

```bash
project-intel spec --title "<title>" --from "<requirement>" --track auto
```

For impact-only requests, run:

```bash
project-intel lifecycle --task "<requirement>" --track auto
```

This prints impact by default. Add `--write` only when the user explicitly wants `.project-intel/reports/task-impact.md`.

Base the spec on `.project-intel`, GitNexus context when available, Understand-Anything context when available, and direct source reads.

Confirm numbered, testable acceptance criteria and persist them separately from the design document:

```bash
project-intel requirement acceptance set --requirement-id "<id>" \
  --criterion "AC-01:<observable behavior>" \
  --criterion "AC-02:<regression or compatibility result>"
```

Do not add an acceptance-criteria heading to the Bug or CRM Requirement design. After the criteria and implementation plan are approved, run `project-intel requirement ready --requirement-id "<id>" --resolution "<confirmation>"`.
