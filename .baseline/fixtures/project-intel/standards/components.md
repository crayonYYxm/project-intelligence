# 组件与复用规范

## 组件分布

| 范围 | 数量 |
| --- | --- |
| page-local | 1 |

## 公共组件清单

以下组件位于公共组件目录，新增页面能力前优先检索和复用：

_None detected._

## 页面局部组件热点

| 目录 | 组件数 |
| --- | --- |
| frontend/components/SearchForm.tsx | 1 |

## 重名/相似组件候选

重名组件通常意味着跨业务线复制或同类能力未沉淀，默认作为 `candidate` 检查：

_None detected._

## 常见 Props / Emits

_None detected._

_None detected._

## 约定

- `src/components/**` 下组件视为公共能力，新增前必须先检索是否已有同类组件。
- `src/pages/**/components/**` 下组件视为页面局部能力；跨两个以上业务域重复时应评估沉淀为公共组件。
- 修改公共组件时需要检查 Props、Emits 和所有引用页面，避免破坏订单、政企、信息填写、认证等页面。
- 重名组件和相同页面模式默认是 `candidate`，人工确认后再升级为 `preferred` 或 `hard`。
