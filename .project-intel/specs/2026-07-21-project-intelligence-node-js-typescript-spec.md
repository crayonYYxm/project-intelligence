# Project Intelligence Node.js/TypeScript 运行时迁移 需求文档

生成时间：`2026-07-21T11:01:38.265261+00:00`

Track：`complex`
Readiness：`needs-clarification`

## 需求

docs/node-typescript-migration-requirement.md

## 需求入口与范围

- 影响区域：backend
- 必经阶段：intake, brainstorm, spec, plan, readiness-gate, task-or-orchestrate, review, finish, maintain

### 已知风险

_无_

### 待澄清信息

- 复杂需求需要补充验收、边界、兼容或回滚信息。

## 项目上下文

- 项目根目录：`.`
- 框架：未知
- 组件数：0
- Hooks 数：0
- API 模块数：0
- 后端 API 数：3
- 服务数：2

## 图谱来源

| 来源 | 状态 | 用途 |
| --- | --- | --- |
| GitNexus | present | 符号调用、影响、变更风险 |
| Understand-Anything | present | 架构、模块、领域流、入职 |

## 复用候选

| 类型 | 名称 | 路径 |
| --- | --- | --- |
| service | backend | plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py |
| service | test_project_intel | plugins/project-intelligence/tests/test_project_intel.py |

## 相关规范

- 添加新抽象前，复用已有的组件、Hook、请求工具、服务和领域模式。
- 冗余发现默认为 `candidate`，除非升级为 `hard`。
- 涉及接口、状态、权限、异常、兼容、缓存或异步行为时，必须在实现前锁定契约。

## 行为契约

- 当前行为：实施前从源码、图谱或现有页面/API 中确认。
- 目标行为：以本需求描述和后续澄清为准。
- 不做事项：没有被明确纳入的重构、视觉改版、接口迁移、强制 hook 拦截和发布动作不在本 spec 默认范围内。
- 输入/输出：涉及 API、组件 Props/Events、DTO/VO 或配置项时，需要列出字段、默认值、错误行为和兼容要求。
- 状态/权限/异常：涉及状态流转、权限校验、支付/订阅/事务/远程调用时，需要补充失败、取消、重试、超时和幂等策略。
- UI 验收：涉及页面时，需要覆盖加载、空态、错误态、禁用态、移动端/桌面端和可访问性可见行为。
- 发布与回滚：涉及数据、权限、远程调用、缓存或开关时，需要说明灰度、回滚和观测方式。

## 质量门禁

| 类型 | 命令 | 来源 |
| --- | --- | --- |
| test | npm run test | package.json |

## 验收到证据映射

- 功能行为：用对应页面操作、接口调用、单测或集成测试证明。
- 规范复用：说明复用的组件、Hook、服务、API 封装或模式；没有复用时说明原因。
- 质量检查：运行 `project-intel check`，必要时运行 lint/type/test/build。
- 维护闭环：完成后运行 `project-intel finish` 做收口检查，再运行 `project-intel maintain --task "<中文简短需求摘要>" --files <changed-source-files>`。
