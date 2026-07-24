# 后端 API 与入口规范

## 框架入口分布

| 框架/入口风格 | 文件数 |
| --- | --- |
| FastAPI/Flask | 1 |

## API/入口清单

| 路径 | 框架 | 入口信号 | 路径样例 | 方法样例 |
| --- | --- | --- | --- | --- |
| backend/api.py | FastAPI/Flask |  | /orders | create_order |

## 路径热点

| 路径前缀 | 出现次数 |
| --- | --- |
| orders | 1 |

## 非标准入口候选

_None detected._

## 约定

- 新增 API 入口应跟随同模块已有框架风格，例如 Spring 注解、Nest 装饰器或 router 注册。
- 不要只靠文件名判断入口；handler、facade、adapter、action 等候选入口需要在初始化后人工确认。
- 入口层只做参数接收、权限/校验编排和响应转换，业务编排应下沉到 Service/UseCase。
- 改入口路径时同步检查调用方、路由/网关配置、鉴权配置、测试和接口文档。
