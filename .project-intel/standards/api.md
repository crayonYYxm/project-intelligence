# API 与请求规范

## 请求封装

| 封装/信号 | 出现次数 |
| --- | --- |
| request | 3 |
| fetch | 2 |
| axios | 1 |

## 服务前缀

_None detected._

## 接口路径热点

| 接口路径前缀 | 出现次数 |
| --- | --- |
| api/list | 1 |
| api/orders | 1 |

## API 模块清单

| 模块 | 请求封装 | 导出函数数 | 接口样例 |
| --- | --- | --- | --- |
| src/__tests__/frontend-files-quality.test.ts | request | 2 | /api/list; /api/orders |
| src/standards/docs.ts | axios, fetch, request | 1 |  |

## 约定

- 新增接口优先放在 `src/api/<domain>/index.ts` 或既有同域 API 模块中。
- 页面和组件不要直接调用 `uni.request`、`axios` 或裸 `fetch`；优先复用项目请求封装和已有 API 方法。
- 接口参数包装方式应跟随同域模块，例如是否使用数组包裹参数、是否传入 headerInfo、是否关闭缓存。
- 涉及登录态、错误上报、订阅消息、支付链路的接口变更，需要同步检查 `src/api/request.ts` 的拦截、错误处理和缓存逻辑。
