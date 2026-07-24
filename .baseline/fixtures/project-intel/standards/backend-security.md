# 后端权限与认证规范

## 权限/认证信号

_None detected._

## 信号热点

_None detected._

## 约定

- 新增入口必须检查同模块已有认证、鉴权、token、session、角色和权限注解。
- 权限判断优先复用已有 guard/interceptor/filter/helper，不要在业务方法里复制判断。
- 修改鉴权逻辑时同步检查匿名访问、内部调用、批量接口、管理端和定时任务入口。
- 权限缺失默认是 review 阻断风险；扫描命中仍为 `candidate`，最终以源码和人工确认升级。
