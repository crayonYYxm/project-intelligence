---
name: project-standards
description: Use when querying, explaining, confirming, promoting, demoting, or applying project standards and rule levels such as hard, preferred, inferred, or candidate.
---

# Project Standards

Read `.project-intel/standards/*.md` and `.project-intel/config.json` before answering standard-related questions.

Rule levels:

- `hard`: confirmed rule that can fail checks
- `preferred`: stable project convention
- `inferred`: scanner inference that needs review
- `candidate`: non-blocking suggestion

Do not upgrade `candidate` redundancy or entrypoint findings to `hard` without explicit human confirmation.

Use:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py query "<standard or rule>"
```
