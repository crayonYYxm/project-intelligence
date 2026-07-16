---
name: project-plan
description: Use when turning a project spec or approved requirement into an implementation plan, task checklist, execution plan, write plan, 技术方案, or development steps.
---

# Project Plan

Create plans that preserve project standards and are ready to execute.

1. Start from the spec or requirement plus `.project-intel` facts.
2. Include intake track/readiness and reuse checks before implementation steps.
3. Map exact files or modules to create/modify, with each file's responsibility.
4. Define interfaces between tasks: consumed APIs, produced functions/components/types, compatibility constraints, and no-touch files.
5. Add a readiness gate before code edits for complex work: missing info resolved, behavior/API/state/permission/exception boundaries confirmed, and verification evidence named.
6. Break work into independently verifiable tasks. Mark each task as `inline`, `sequential-subagent`, or `parallelizable-readonly`.
7. Include a `project-test` cycle for every code task: exact test file, targeted RED command and expected failure, GREEN command, affected regression scope, justified manual alternative when automation is unreasonable, review checkpoints, `project-finish`, and post-task maintenance.
8. Keep the implementation plan in context by default. Generate a plan file only when the user explicitly asks for a persistent plan and provides or requests a spec file:

```bash
project-intel plan --title "<title>" --from-spec <spec-path> --track auto
```

If there is no persistent spec file, plan directly from the approved requirement. Do not create spec or plan files merely because the skill triggered.

For a requirement-level task, carry the same requirement ID into every task and map every implementation/test task to one or more numbered acceptance criteria. Treat `requirement-design.md` as the source of truth. End the planning phase with the readiness gate:

```bash
project-intel requirement ready --requirement-id "<id>" --resolution "需求范围、验收标准、边界和验证方式已确认"
```

Do not start code edits when this command fails.

Plan quality rules:

- Do not use placeholders such as `TODO`, `TBD`, “适当处理”, or “后续补充”.
- Do not say “写测试” without naming the test file, RED/GREEN phase, command, expected evidence, and regression scope.
- Do not make a subagent plan unless tasks are independent enough to review separately.
- For large plans, include a `Global Constraints` section with exact hard rules, dependency limits, platform constraints, and user decisions.
- For code changes, each task should end with fresh verification evidence and a review decision before the next task starts.
