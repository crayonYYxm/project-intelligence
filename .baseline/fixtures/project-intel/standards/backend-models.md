# 后端 DTO/VO/Entity 规范

## 类型分布

_None detected._

## 数据类型清单

_None detected._

## 字段热点

_None detected._

## 注解热点

_None detected._

## 约定

- DTO/VO 用于接口入参和出参，Entity/Model 用于持久化或领域状态，不要混用职责。
- 新增字段时同步检查序列化名称、校验注解、默认值、兼容性和前后端字段映射。
- Entity 改动需要检查 Mapper/Repository SQL、数据库迁移、缓存键和历史数据兼容。
- 相同字段组合重复出现时，优先复用已有 DTO/VO 或抽取公共片段。
