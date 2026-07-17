---
name: project-design
description: Use when converting local Markdown/TXT Bug or requirement tickets into a source-backed technical development design, validating an existing design, or handling the lifecycle design action after project-spec and, for Bugs, project-debug. 根据 Bug 单写开发设计文档, 把需求单转成技术设计, 生成本地需求开发设计文档, 分析代码后补充设计文档, 写 Bug 修复设计说明. Standalone design-only requests use only this Skill; do not use it for brainstorming, task checklists, direct code changes, or prose polishing without source analysis.
---

# Project Design

Generate or validate a development design from ticket facts and repository evidence. Never edit business source code as part of this Skill.

## Choose the mode

- **Standalone**: When the user asks only for a design document, generate and validate a kind-specific file under `docs/requirements/`: Bugs use `<bug-id>-<name>-设计文档.md`; Requirements use `<requirement-id>_<name>_设计文档.md`. Do not run intake, initialize `.project-intel`, or register lifecycle artifacts.
- **Lifecycle**: When `project-intake` routes an implementation task here, use the existing requirement ID, name, ticket kind, repository, and selected action. Write the durable design as `.project-intel/requirements/<id>/design.md`; do not create a second manifest or a second lifecycle design file.

For lifecycle mode, read `project-intel requirement status --requirement-id <id> --json` first. Handle the persisted `workflowSelections.design` action/path; do not ask again or silently choose a different action:

- `generate`: analyze the ticket and source, write the document, validate it, then register it.
- `register existing`: validate the supplied repository-relative document and register it without rewriting unless the user requested changes.
- `later`: run `project-intel requirement defer --requirement-id <id> --type design` and stop before readiness.

For a lifecycle Bug, `project-debug` must have persisted a current `requirement diagnose` result before this Skill generates the document, so the root cause is evidence-backed and machine-gated. `project-spec` must already have produced the current `requirement.md` and manifest AC. Acceptance criteria do not belong in the design document.

## Establish inputs

1. In standalone mode, require one or more local `.md` or `.txt` tickets. In lifecycle mode, prefer supplied ticket files, but when none exists use the confirmed intake narrative and requirement manifest as the source ticket; ask only when those facts are insufficient to produce an evidence-backed design. Read explicitly supplied files outside the repository without copying them into the repository.
2. Use the current Git repository when available; otherwise ask for the target repository before producing a complete design.
3. Preserve formal ticket identifiers. Prefix a purely numeric Bug with `bug` and a purely numeric Requirement with `req`.
4. Identify one primary output repository when several repositories are involved. Treat unavailable repositories and services as external evidence gaps.
5. In standalone mode, write Bugs as `<bug-id>-<name>-设计文档.md` and Requirements as `<requirement-id>_<name>_设计文档.md`. In lifecycle mode always use `.project-intel/requirements/<id>/design.md`. Reject path separators, control characters, and output outside the primary repository.

## Analyze evidence

1. Read applicable repository instructions, manifests, build files, relevant source, tests, and useful Git history.
2. Search exact business terms, API names, field names, identifiers, errors, and symbols from the ticket.
3. Trace the real UI/API/service/data/external path as applicable. Do not invent unavailable implementations.
4. Use repository-relative paths and symbols for implementation claims.
5. Disclose ticket/source mismatches in the existing Bug or Requirement sections instead of adding a new heading.
6. Mask credentials, cookies, tokens, passwords, secrets, API keys, personal identifiers, phone numbers, and customer data.

## Write and validate

Read only the matching template completely:

- Bug: [references/bug-design-template.md](references/bug-design-template.md)
- Requirement: [references/requirement-design-template.md](references/requirement-design-template.md)

Keep Bugs in the compact five-part structure. Reproduce the CRM Requirement structure and order exactly. Do not add acceptance criteria, test matrices, source-evidence tables, or pending-item sections.

Resolve the validator from this Skill directory, not from the target repository. Run the bundled validator by absolute path and fix all exit-code `1` findings:

```bash
python3 <project-design-skill-dir>/scripts/validate_design_doc.py \
  --file <design.md> \
  --repo <primary-repository> \
  --kind auto \
  --json
```

In lifecycle mode, register the validated document:

```bash
project-intel requirement add \
  --requirement-id "<id>" \
  --type design \
  --path <repo-relative-design-path>
```

Do not call `requirement ready` inside this Skill. In lifecycle mode, return to the orchestrating flow after registration; it may generate the optional complex-task plan and then call ready. Do not loop back to `project-spec` unless source evidence exposes a real contradiction. If an existing output would be replaced rather than meaningfully updated, ask before overwriting it.

Report the output path, ticket type, implementation status, repositories inspected, validation result, lifecycle registration result when applicable, and unresolved external evidence gaps.
