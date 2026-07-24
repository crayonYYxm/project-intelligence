# 后端 Repository/Mapper 规范

## 仓库层分布

| 类型 | 数量 |
| --- | --- |
| Mapper | 1 |

## Repository/Mapper 清单

| 名称 | 类型 | 路径 | 方法/SQL id 样例 | SQL 操作 |
| --- | --- | --- | --- | --- |
| backend | Mapper | src/scanner/backend.ts | scanner, Set, stringify, String, add, push, flattenRegexHits, uniqueLimited, allMatches, RegExp, annotationValues, annotationValuesInCode | DELETE, SELECT, INSERT, UPDATE, MERGE |

## SQL 操作热点

| 操作 | 出现次数 |
| --- | --- |
| DELETE | 1 |
| SELECT | 1 |
| INSERT | 1 |
| UPDATE | 1 |
| MERGE | 1 |

## 约定

- Repository/Mapper 只负责数据访问，不承载业务流程、权限判断或跨服务编排。
- 新增查询优先复用已有方法；确需新增时保持同域命名、参数对象和分页约定。
- 修改 SQL 或 Mapper XML 时检查关联 DTO/Entity 字段、索引、排序、分页和空值行为。
- 写操作必须回看 Service 层事务边界，避免 Repository 内隐式提交破坏业务一致性。
