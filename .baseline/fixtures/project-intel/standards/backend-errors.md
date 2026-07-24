# 后端错误码与异常规范

## 错误码/异常信号

_None detected._

## 信号热点

_None detected._

## 约定

- 新增业务异常前先搜索既有 ErrorCode/ResultCode/ResponseCode 和异常类型。
- 错误码语义需要让前端、调用方和日志排障都能识别，不要只抛通用异常。
- 改错误码或异常映射时同步检查接口响应、重试逻辑、告警、埋点和用户提示。
- 异常处理属于硬规范候选；团队确认后可升级为 `preferred` 或 `hard`。
