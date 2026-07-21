# 后端权限与认证规范

## 权限/认证信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| plugins/project-intelligence/scripts/project_intel_lib/application.py | token, session | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/cli.py | token | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/design_documents.py | token | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/requirements.py | token | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py | jwt, token, session, principal, SecurityContext, AuthGuard, CanActivate | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py | token | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/testing.py | token | candidate |
| plugins/project-intelligence/tests/test_project_intel.py | @PreAuthorize(\"hasRole('ORDER')\")"], "level": "candidate"}, @PreAuthorize("hasRole('ORDER')"), token, session | candidate |
| plugins/project-intelligence/tests/test_project_test.py | token, session | candidate |
| plugins/project-intelligence/tests/test_requirement_workflow.py | token | candidate |
| plugins/project-intelligence/tests/test_testing_security.py | token | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| token | 11 |
| session | 4 |
| jwt | 1 |
| principal | 1 |
| SecurityContext | 1 |
| AuthGuard | 1 |
| CanActivate | 1 |
| @PreAuthorize(\"hasRole('ORDER')\")"], "level": "candidate"} | 1 |
| @PreAuthorize("hasRole('ORDER')") | 1 |

## 约定

- 新增入口必须检查同模块已有认证、鉴权、token、session、角色和权限注解。
- 权限判断优先复用已有 guard/interceptor/filter/helper，不要在业务方法里复制判断。
- 修改鉴权逻辑时同步检查匿名访问、内部调用、批量接口、管理端和定时任务入口。
- 权限缺失默认是 review 阻断风险；扫描命中仍为 `candidate`，最终以源码和人工确认升级。
