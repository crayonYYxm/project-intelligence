# 后端规范

## 已提取的事实

- 发现的 API/入口模块数：1
- 发现的服务数：1
- 发现的 DTO/VO/Entity/模型文件数：0
- 发现的 Repository/Mapper 文件数：0
- 发现的配置文件/配置类数：0
- 发现的权限/认证信号文件数：0
- 发现的事务信号文件数：0
- 发现的远程调用信号文件数：0
- 发现的消息/任务信号文件数：0
- 发现的错误码/异常信号文件数：0
- 发现的公共工具候选数：0
- 候选非标准入口点数：0

## 细分规范

- API 与入口：`backend-api.md`
- Service 与业务编排：`backend-services.md`
- DTO/VO/Entity：`backend-models.md`
- Repository/Mapper：`backend-repository.md`
- 配置项：`backend-config.md`
- 权限与认证：`backend-security.md`
- 事务边界：`backend-transactions.md`
- 远程调用：`backend-remote-calls.md`
- 消息与任务：`backend-async.md`
- 错误码与异常：`backend-errors.md`
- 公共工具：`backend-utilities.md`

## 推断规范

以下规范由扫描器从项目实际代码推断（`inferred` 等级），默认作为项目约定遵循；经人工确认后可升级为 `preferred` 或 `hard`：

- 后端入口主要使用 FastAPI/Flask 风格，新增 API 应跟随同框架入口声明方式（证据：1/1 个入口匹配）

## 默认规则

- 通过框架适配器、AST/调用模式和项目特定规则识别入口点。
- 不要仅依赖 `Controller` 命名。
- 保持服务、数据、仓库、权限、事务和配置的边界。
- 升级候选入口点为 hard 标准前需人工确认。
