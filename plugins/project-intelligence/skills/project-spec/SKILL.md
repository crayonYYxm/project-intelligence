---
name: project-spec
description: Use after project-intake and before project-debug/project-design to create or register the requirement document and persist matching numbered acceptance criteria. 写需求文档, 整理需求, 需求澄清, 补充验收标准, 生成 requirement.md, acceptance criteria. Do not use for source-backed technical design or execution-task planning.
---

# Project Spec

Write specs from project facts, not guesses.

For requirement-level implementation, create or register `.project-intel/requirements/<id>/requirement.md` and keep its numbered acceptance criteria identical to `manifest.acceptanceCriteria`. Do not create `.project-intel/specs/`.

1. Read `.project-intel/manifest.json`, `.project-intel/project-status.md`, relevant standards, knowledge JSON, and graph summary.
2. Use the identity, ticket kind, track, and readiness fields already established by `project-intake`. Run read-only `project-intel intake --task "<requirement>"` only for an impact-only request that is not inside a lifecycle.
3. Read `project-intel requirement status --requirement-id "<id>" --json` and use its identity, ticket kind, and `workflowSelections.requirement` action/path persisted during intake. Do not ask again or infer a different action.
4. Handle exactly one requirement-document action before continuing to debug/design:
   - `generate`: create the canonical scaffold only when it does not exist, complete it, persist matching AC, and register it.
   - `register existing`: read the supplied repository-relative file without rewriting it, confirm its AC with the user, persist the same AC in the manifest, then register it. Registration copies validated content to the canonical `requirement.md` when necessary.
   - `later`: persist the blocker and stop before `project-debug`, `project-design`, or readiness:

```bash
project-intel requirement defer --requirement-id "<id>" --type requirement
```

5. For `generate` or `register existing`, capture the requirement, impacted modules, reusable capabilities, standards, quality gates, acceptance criteria, behavior contracts, and evidence mapping in `requirement.md`.
6. Keep unknowns explicit; do not invent hard rules from `candidate` findings.
7. For `generate`, create the canonical requirement scaffold only when it does not exist, complete it, then register it:

```bash
project-intel requirement generate --requirement-id "<id>" --type requirement
```

If the canonical file already exists, edit and validate that file instead of regenerating it. Use `--replace` only after the user explicitly approves replacement; never overwrite a completed document as an incidental workflow step. For `register existing`, skip scaffold generation and pass the supplied repository-relative path to `requirement add` after persisting the matching AC.

```bash
project-intel requirement acceptance set --requirement-id "<id>" \
  --criterion "AC-01:<observable behavior>"
project-intel requirement add --requirement-id "<id>" --type requirement \
  --path <existing-repo-relative-requirement-document>
```

For impact-only requests, run:

```bash
project-intel lifecycle --task "<requirement>" --track auto
```

This prints impact only; do not persist a separate impact report.

Base the spec on `.project-intel`, GitNexus context when available, Understand-Anything context when available, and direct source reads.

Confirm numbered, testable acceptance criteria, write the same IDs into `requirement.md`, and persist them in the manifest before registering the completed document:

```bash
project-intel requirement acceptance set --requirement-id "<id>" \
  --criterion "AC-01:<observable behavior>" \
  --criterion "AC-02:<regression or compatibility result>"
project-intel requirement add --requirement-id "<id>" --type requirement \
  --path .project-intel/requirements/<id>/requirement.md
```

Do not add an acceptance-criteria heading to the Bug or CRM Requirement design. For a Bug, `project-debug` follows this step and supplies the diagnosis used by `project-design`; for a Requirement, `project-design` follows directly. Run `requirement ready` only after both `requirementValidation.ok` and `designValidation.ok` are true and any optional complex-task plan is complete.
