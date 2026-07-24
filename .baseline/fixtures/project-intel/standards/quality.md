# 质量检查

规则等级：

- `hard`：已确认的必守规则；带结构化 `check` 的规则自动验证，失败时 `project-intel check` 返回非零
- `preferred`：稳定的项目约定
- `inferred`：扫描器推断，需要人工审查
- `candidate`：非阻塞建议

纯文本 `hard` 规则会在质量报告中标记为 `manual-review`，由 Agent/评审人员核对，不会被 CLI 误判为自动通过或失败。

## 检测到的命令

| 类型 | 命令 | 来源 |
| --- | --- | --- |
| lint | npm run lint | package.json |
| test | npm run test | package.json |

## 策略

- 优先使用项目已有的 package scripts，而非推断的命令。
- 冗余发现默认为 `candidate`，直到人工升级规则。
- 审查时将项目质量检查与规范和图谱上下文结合使用。
