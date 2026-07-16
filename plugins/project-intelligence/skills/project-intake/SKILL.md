---
name: project-intake
description: Use when classifying a requirement, clarifying scope, deciding quick/standard/complex track, checking readiness, routing to spec/plan/task, or doing 需求入口分析 before implementation.
---

# Project Intake

Use this before code changes when a request may become implementation work.

1. Read `.project-intel/manifest.json` when it exists. If facts are missing, run read-only `project-intel doctor` or `project-intel init --dry-run`; run `init` only after the user explicitly authorizes initialization.
2. Run the intake analysis without writing a file by default:

```bash
project-intel intake --task "<requirement>"
```

3. Classify the track:
   - `quick`: small local behavior, copy, style, config, or low-risk fix.
   - `standard`: normal feature/change that needs lightweight spec and plan in context.
   - `complex`: cross-module, API/data/auth/payment/cache/async/release/compatibility/security/performance work.
4. If readiness is `needs-clarification`, resolve only the missing information that can change implementation or acceptance.
5. Do not create spec, plan, lifecycle, or intake files unless the user explicitly asks. Use `--write` only for a persistent intake report.
6. Route next:
   - quick: explicitly invoke `project-test`, then `project-task`.
   - standard: keep a Chinese lightweight spec and plan in context, then explicitly invoke `project-test` and `project-task`.
   - complex: use `project-brainstorm`, `project-spec`, `project-plan`, and a readiness gate; then explicitly invoke `project-test` before `project-task` or `project-orchestrate`.
7. The same-turn handoff is mandatory for implementation-intent requests. If the user says not to edit yet, complete the applicable pre-edit Skill handoff and stop before file changes; do not stop at intake or substitute `project-knowledge` for the test/task workflow.

Use GitNexus for precise impact when available and Understand-Anything for architecture/domain context when available.

For implementation intent, ask for the requirement ID and requirement name before routing. Generate `LOCAL-YYYYMMDD-HHMMSS` when no formal ID exists, explicitly ask whether external APIs are affected, then register the requirement:

```bash
project-intel intake --requirement-id "<id>" --requirement-name "<name>" --external-api yes|no --track auto
```

Ask how to handle the combined requirement/design document: `generate`, `register existing`, or `later`. Route to `project-spec`; choosing later must run `project-intel requirement defer --requirement-id "<id>" --type requirement-design` and remain blocked. Do not ask for requirement identity during knowledge-only explanation or read-only review.
