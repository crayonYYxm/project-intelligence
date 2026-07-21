# 路由与分包规范

## 路由模块

_None detected._

## 页面标题热点

_None detected._

## 约定

- 新增页面优先放入对应 `src/router/modules/subpackages/*` 分包配置，保持 `baseUrl` 与实际页面目录一致。
- 已使用 `navigationStyle: 'custom'` 的业务线新增页面应保持导航风格一致，并复用现有导航组件。
- 使用小程序插件的页面需要在路由配置里保留 provider/version 信息，避免只改页面文件漏改路由配置。
- 页面路径、标题和分包归属是需求影响分析的一部分；改页面入口时需要同步检查跳转 URL 和 `uni.navigateTo/redirectTo` 调用。
