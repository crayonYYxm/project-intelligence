# 后端错误码与异常规范

## 错误码/异常信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| src/__tests__/backend.test.ts | ERR_001, BusinessException | candidate |
| src/__tests__/dispatcher.test.ts | UsageError, RuntimeError | candidate |
| src/__tests__/json-envelope.test.ts | USAGE_ERROR, COMMAND_FAILED | candidate |
| src/__tests__/project-facts.test.ts | ORDER_FAILED | candidate |
| src/app/dispatcher.ts | USAGE_ERROR, COMMAND_FAILED, RuntimeError | candidate |
| src/cli.ts | UsageError | candidate |
| src/cli/json-envelope.ts | USAGE_ERROR, COMMAND_FAILED | candidate |
| src/cli/parser.ts | UsageError | candidate |
| src/commands/adapters.ts | UsageError | candidate |
| src/commands/agent-install.ts | UsageError | candidate |
| src/commands/check.ts | UsageError, RuntimeError | candidate |
| src/commands/finish.ts | UsageError | candidate |
| src/commands/init.ts | UsageError | candidate |
| src/commands/maintain.ts | UsageError | candidate |
| src/commands/orchestration.ts | UsageError | candidate |
| src/commands/query.ts | UsageError | candidate |
| src/commands/requirement.ts | UsageError | candidate |
| src/commands/review.ts | UsageError | candidate |
| src/commands/test.ts | UsageError | candidate |
| src/errors.ts | EXIT_NOT_FOUND | candidate |
| src/fs/atomic-write.ts | StrictReadError | candidate |
| src/fs/lock.ts | RequirementError | candidate |
| src/fs/paths.ts | UsageError | candidate |
| src/process/spawn.ts | EXIT_NOT_FOUND | candidate |
| src/requirements/documents.ts | RequirementError | candidate |
| src/requirements/layout.ts | RequirementError | candidate |
| src/requirements/scope.ts | RequirementError | candidate |
| src/requirements/state-machine.ts | RequirementError | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| UsageError | 15 |
| RequirementError | 5 |
| RuntimeError | 3 |
| USAGE_ERROR | 3 |
| COMMAND_FAILED | 3 |
| EXIT_NOT_FOUND | 2 |
| ERR_001 | 1 |
| BusinessException | 1 |
| ORDER_FAILED | 1 |
| StrictReadError | 1 |

## 约定

- 新增业务异常前先搜索既有 ErrorCode/ResultCode/ResponseCode 和异常类型。
- 错误码语义需要让前端、调用方和日志排障都能识别，不要只抛通用异常。
- 改错误码或异常映射时同步检查接口响应、重试逻辑、告警、埋点和用户提示。
- 异常处理属于硬规范候选；团队确认后可升级为 `preferred` 或 `hard`。
