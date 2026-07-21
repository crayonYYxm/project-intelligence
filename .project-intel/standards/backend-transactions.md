# 后端事务边界规范

## 事务信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py | @Transactional, TransactionTemplate, DataSourceTransactionManager, EntityManager, UnitOfWork | candidate |
| plugins/project-intelligence/tests/test_project_intel.py | @Transactional | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| @Transactional | 2 |
| TransactionTemplate | 1 |
| DataSourceTransactionManager | 1 |
| EntityManager | 1 |
| UnitOfWork | 1 |

## 约定

- 涉及订单、支付、库存、状态变更、多表写入时，先确认已有事务边界。
- 不要把一个原子业务流程拆成多个无保护写操作；异步流程需要说明补偿和幂等。
- 远程调用和事务混用时要特别审查超时、重复提交、回滚语义和最终一致性。
- 新增事务注解或事务模板时同步检查调用链是否经过代理，避免事务不生效。
