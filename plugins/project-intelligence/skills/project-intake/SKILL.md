---
name: project-intake
description: Use when classifying a requirement, clarifying scope, deciding quick/standard/complex track, checking readiness, routing to spec/plan/task, or doing 需求入口分析 before implementation.
---

# Project Intake

Use this before code changes when a request may become implementation work.

1. Read `.project-intel/manifest.json` when it exists; if project facts are missing, ask for or run `project-intel init` only when initialization is part of the task.
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
   - quick: go to `project-task`.
   - standard: keep a Chinese lightweight spec and plan in context, then `project-task`.
   - complex: use `project-brainstorm`, `project-spec`, `project-plan`, and a readiness gate before `project-task` or `project-orchestrate`.

Use GitNexus for precise impact when available and Understand-Anything for architecture/domain context when available.
