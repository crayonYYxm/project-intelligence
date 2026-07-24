# 后端 Service 与业务编排规范

## Service 清单

_None detected._

## 方法命名前缀热点

_None detected._

## 约定

- Controller/API 层不要绕过 Service 直接访问 Repository/Mapper。
- 新增业务流程优先找同域 Service、Manager、UseCase、Facade，复用已有编排方式。
- 涉及写操作、支付、订单、库存、状态机等流程时，先确认事务边界和幂等策略。
- Service 内远程调用要复用已有客户端/适配器，并保留错误映射、超时、重试和日志链路。
