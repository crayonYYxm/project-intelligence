# 后端远程调用规范

## 远程调用信号

| 路径 | 信号样例 | 等级 |
| --- | --- | --- |
| src/__tests__/frontend-files-quality.test.ts | fetch | candidate |
| src/__tests__/project-facts.test.ts | RestTemplate | candidate |
| src/scanner/backend.ts | @FeignClient, RestTemplate, WebClient, Feign, HttpClient, OkHttpClient, ServiceMeshAdapter, grpc, axios, fetch | candidate |
| src/scanner/frontend.ts | fetch, axios | candidate |
| src/standards/docs.ts | axios, fetch, Feign | candidate |
| src/standards/infer.ts | axios, fetch | candidate |

## 信号热点

| 信号 | 出现次数 |
| --- | --- |
| fetch | 5 |
| axios | 4 |
| RestTemplate | 2 |
| Feign | 2 |
| @FeignClient | 1 |
| WebClient | 1 |
| HttpClient | 1 |
| OkHttpClient | 1 |
| ServiceMeshAdapter | 1 |
| grpc | 1 |

## 约定

- 远程调用优先复用已有 Feign/Dubbo/gRPC/HTTP 客户端或公司内部适配器。
- 新增调用必须检查超时、重试、熔断、错误码映射、日志追踪和调用方降级行为。
- 变更远程接口入参/出参时同步检查 DTO、调用链、Mock、契约测试和下游兼容。
- Review 时把远程调用视为影响面扩大点，优先结合 GitNexus 调用链或图谱上下文确认风险。
