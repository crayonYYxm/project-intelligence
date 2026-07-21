# 后端消息与任务规范

## 消息/任务信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| plugins/project-intelligence/scripts/project_intel_lib/application.py | @MessageListener, @Scheduled | candidate |
| plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py | Queue, Topic, Consumer, Producer, BullMQ, agenda, cron, schedule | candidate |
| plugins/project-intelligence/tests/test_project_intel.py | @Scheduled(cron = \"0 * * * * ?\"), cron | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| cron | 2 |
| @MessageListener | 1 |
| @Scheduled | 1 |
| Queue | 1 |
| Topic | 1 |
| Consumer | 1 |
| Producer | 1 |
| BullMQ | 1 |
| agenda | 1 |
| schedule | 1 |
| @Scheduled(cron = \"0 * * * * ?\") | 1 |

## 约定

- 消息消费者、事件监听器和定时任务都是后端入口，需求影响分析不能只看 HTTP Controller。
- 修改异步入口需要检查幂等、重试、死信/补偿、并发控制、调度频率和监控告警。
- 新增任务配置时同步检查配置文件、部署环境、开关和测试数据隔离。
- 定时任务或消费者调用 Service 时，复用同一套事务、权限边界和错误处理策略。
