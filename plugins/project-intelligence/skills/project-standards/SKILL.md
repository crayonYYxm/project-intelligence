---
name: project-standards
description: Use when querying, explaining, confirming, promoting, demoting, or applying project standards and rule levels such as hard, preferred, inferred, or candidate. 项目规范, 规范, 代码规范, 标准, 规则.
---

# Project Standards

Read `.project-intel/standards/*.md` and `.project-intel/config.json` before answering standard-related questions.

Rule levels:

- `hard`: confirmed rule that can fail checks
- `preferred`: stable project convention
- `inferred`: scanner inference that needs review
- `candidate`: non-blocking suggestion

Do not upgrade `candidate` redundancy or entrypoint findings to `hard` without explicit human confirmation.

When a task reveals a stable reusable pattern, record it as `candidate` first and ask for confirmation before treating it as `preferred` or `hard`.

Use:

```bash
project-intel query "<standard or rule>"
```
