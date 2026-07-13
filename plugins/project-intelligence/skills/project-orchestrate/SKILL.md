---
name: project-orchestrate
description: Use when a project task has an implementation plan with independent subtasks and would benefit from subagents, task handoffs, task-level review, final review, or execution coordination. 子代理开发, 多任务编排, agent执行计划, 并行分析, 分任务实现.
---

# Project Orchestrate

Use this only for planned work with separable subtasks. Keep `project-task` as the default for small or tightly coupled changes.

## When To Use

Use this workflow when all are true:

1. There is a stable requirement or implementation plan.
2. The plan has independent tasks with clear file ownership or clear interfaces.
3. Each task can be verified and reviewed on its own.

Do not use subagents just because a task is important. Use inline execution for small changes, tightly coupled edits, or changes where the same files must be modified repeatedly.

## Execution Modes

- `inline`: default for small changes and tightly coupled work.
- `sequential-subagents`: fresh implementer per independent plan task, followed by task review.
- `parallel-investigation`: multiple read-only agents for independent investigations, failures, or impact questions.
- `worktree`: optional for high-risk or long-running work; do not create or switch worktrees unless the user asks or the host workflow already uses one.

Implementation subagents should usually run sequentially, because parallel implementation against the same working tree can conflict. Parallel agents are better for read-only analysis and disjoint investigations.

## Required Handoff

For every subagent task, provide a compact handoff instead of the full conversation:

1. Chinese task summary and acceptance criteria.
2. Exact files or modules allowed to change.
3. Files, APIs, components, hooks, services, or graph facts that must be reused.
4. Relevant `hard` and `preferred` standards.
5. No-touch files or compatibility constraints.
6. Required verification command or manual verification evidence.
7. Report contract: changed files, test evidence, concerns, and remaining risk.

If a handoff file is needed, place it under ignored `.project-intel/tmp/execution/`. Do not create permanent per-subagent requirement, report, or maintenance files unless the user explicitly asks.

## Review Loop

After each implementation task:

1. Inspect the diff for that task.
2. Review spec compliance, hard-rule compliance, reuse, redundancy, and test coverage.
3. Fix `critical` and `important` findings before moving to the next implementation task.
4. Keep `minor` findings visible for the final review.

After all tasks:

1. Run a final whole-diff review.
2. Run `project-intel check`.
3. Run the concrete project verification commands needed to prove the task, such as unit tests, type checks, builds, or manual device checks.
4. Only after fresh evidence, run `project-intel finish --task "<中文简短需求摘要>" --files <changed-source-files>`.
5. Then run `project-intel maintain --task "<中文简短需求摘要>" --files <changed-source-files>`.

## Review Feedback Discipline

When receiving review feedback, verify it against the current codebase before applying it.

- Clarify unclear feedback before editing.
- Push back with code or test evidence when a suggestion conflicts with project reality, YAGNI, compatibility, or user decisions.
- Apply valid feedback one item at a time and verify each meaningful fix.

## Completion Gate

Do not claim a task is complete, fixed, passing, or ready without fresh evidence from this turn.

For each completion claim, identify the proof, run or inspect the proof, read the result, then report the actual status. `project-intel check` proves project-intelligence rules only; it does not prove business behavior unless the rule directly covers that behavior.
