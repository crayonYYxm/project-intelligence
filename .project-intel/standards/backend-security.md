# 后端权限与认证规范

## 权限/认证信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| src/__tests__/backend.test.ts | @PreAuthorize(\"hasRole('ADMIN')\")\npublic void secure() | candidate |
| src/__tests__/json-envelope.test.ts | session, token | candidate |
| src/__tests__/review-finish-graph.test.ts | token | candidate |
| src/__tests__/test-evidence.test.ts | session, token | candidate |
| src/app/dispatcher.ts | token | candidate |
| src/cli/command-flags.ts | token | candidate |
| src/cli/json-envelope.ts | token | candidate |
| src/cli/parser.ts | token | candidate |
| src/requirements/scope.ts | token | candidate |
| src/scanner/backend.ts | jwt, token, session, principal, SecurityContext, AuthGuard, CanActivate | candidate |
| src/standards/docs.ts | token, session | candidate |
| src/testing/sanitize.ts | token | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| token | 11 |
| session | 4 |
| @PreAuthorize(\"hasRole('ADMIN')\")\npublic void secure() | 1 |
| jwt | 1 |
| principal | 1 |
| SecurityContext | 1 |
| AuthGuard | 1 |
| CanActivate | 1 |

## 约定

- 新增入口必须检查同模块已有认证、鉴权、token、session、角色和权限注解。
- 权限判断优先复用已有 guard/interceptor/filter/helper，不要在业务方法里复制判断。
- 修改鉴权逻辑时同步检查匿名访问、内部调用、批量接口、管理端和定时任务入口。
- 权限缺失默认是 review 阻断风险；扫描命中仍为 `candidate`，最终以源码和人工确认升级。
