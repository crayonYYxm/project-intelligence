# 后端消息与任务规范

## 消息/任务信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| .github/workflows/live-skill-evals.yml | schedule, cron | candidate |
| src/app/project-state.ts | @MessageListener, @Scheduled | candidate |
| src/scanner/backend.ts | Queue, Topic, Consumer, Producer, BullMQ, agenda, cron, schedule | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| schedule | 2 |
| cron | 2 |
| @MessageListener | 1 |
| @Scheduled | 1 |
| Queue | 1 |
| Topic | 1 |
| Consumer | 1 |
| Producer | 1 |
| BullMQ | 1 |
| agenda | 1 |

## 约定

- 消息消费者、事件监听器和定时任务都是后端入口，需求影响分析不能只看 HTTP Controller。
- 修改异步入口需要检查幂等、重试、死信/补偿、并发控制、调度频率和监控告警。
- 新增任务配置时同步检查配置文件、部署环境、开关和测试数据隔离。
- 定时任务或消费者调用 Service 时，复用同一套事务、权限边界和错误处理策略。
