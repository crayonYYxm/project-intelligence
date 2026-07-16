---
name: project-spec
description: Use when writing, updating, or explaining a project spec, design note, requirement document, acceptance criteria, task impact report, 需求文档, or 需求涉及关系和规范.
---

# Project Spec

Write specs from project facts, not guesses.

For requirement-level implementation, require a requirement/design artifact. It may be a combined document. Keep `.project-intel/specs/*.md` as a legacy compatibility output; use the requirement archive as the durable workflow source.

1. Read `.project-intel/manifest.json`, relevant standards, knowledge JSON, graph summary, and reports.
2. Run `project-intel intake --task "<requirement>"` or use the same track/readiness fields.
3. Capture the requirement, impacted modules, reusable capabilities, standards, quality gates, acceptance criteria, behavior contracts, and evidence mapping.
4. Keep unknowns explicit; do not invent hard rules from `candidate` findings.
5. Generate the spec only when the user explicitly asks for a persistent requirements/spec document:

```bash
project-intel spec --title "<title>" --from "<requirement>" --track auto
```

For impact-only requests, run:

```bash
project-intel lifecycle --task "<requirement>" --track auto
```

This prints impact by default. Add `--write` only when the user explicitly wants `.project-intel/reports/task-impact.md`.

Base the spec on `.project-intel`, GitNexus context when available, Understand-Anything context when available, and direct source reads.

Ask for one action and execute it:

- Generate: `project-intel requirement generate --requirement-id "<id>" --type requirement-design`.
- Register existing: `project-intel requirement add --requirement-id "<id>" --type requirement-design --path <repo-relative-file>`.
- Later: `project-intel requirement defer --requirement-id "<id>" --type requirement-design` and stop before readiness.

Require background, scope, non-goals, design, risks, and numbered acceptance criteria such as `AC-01`. After the document and implementation plan are approved, run `project-intel requirement ready --requirement-id "<id>" --resolution "<confirmation>"`.
