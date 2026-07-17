---
name: project-knowledge
description: Use when answering read-only questions about project structure, components, Hooks, APIs, services, modules, standards, business flows, generated knowledge, or reusable patterns. 项目知识查询, 项目结构说明, 项目架构说明, 查询组件, 查询接口, 查询服务, 模块说明. Do not use as the terminal route for requests that add or modify an API, service, module, or feature.
---

# Project Knowledge

Answer from `.project-intel` first:

- `.project-intel/manifest.json` for project overview and graph source status
- `.project-intel/standards/*.md` for rules and conventions
- `.project-intel/knowledge/*.json` for components, Hooks, APIs, services, files, and candidates
- `.project-intel/graph/project-graph.json` for graph summary
- `.project-intel/project-status.md` for the replaceable current scan, tooling, and quality summary
- `.project-intel/requirements/<id>/manifest.json` plus its four lifecycle documents for requirement history
- `.project-intel/requirements/<id>/plan.md` only when a complex task or explicit request created it

Use GitNexus for precise symbol-level questions. Use Understand-Anything for architecture/domain questions.

Search with:

```bash
project-intel query "<question>"
project-intel requirement query --file <repo-relative-source-path>
```

Prefer `.project-intel` facts, GitNexus context, Understand-Anything context, and direct source reads.

`project-knowledge` supplies context; it is not a terminal route for an implementation-intent request. If intake selected implementation work, return to the required same-turn handoff: invoke `project-test`, then `project-task`, even when the user asked to stop before edits.
