import type { ProjectState } from "../app/project-state.js";
import { sanitizeText } from "../testing/sanitize.js";
import { projectDomainCandidates } from "./domains.js";

type Fact = Record<string, unknown>;

function facts(value: unknown): Fact[] {
  return Array.isArray(value)
    ? value.filter((item): item is Fact => Boolean(item) && typeof item === "object" && !Array.isArray(item))
    : [];
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function pathPrefix(path: unknown, depth = 4): string {
  const parts = String(path ?? "").split("/");
  return parts.length > depth ? parts.slice(0, depth).join("/") : parts.join("/");
}

function componentScope(path: string): string {
  if (path.startsWith("src/components/") || path.startsWith("components/")) return "public";
  if (path.includes("/components/")) return "page-local";
  if (path.startsWith("src/pages/") || path.startsWith("pages/") || path.startsWith("app/")) return "page";
  return "module";
}

function countRows(values: Iterable<unknown>, limit?: number): unknown[][] {
  const counts = new Map<string, number>();
  for (const value of values) {
    const name = String(value ?? "");
    if (!name) continue;
    counts.set(name, (counts.get(name) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, count]) => [name, count]);
}

function cell(value: unknown): string {
  const raw = Array.isArray(value) ? value.map(String).join(", ") : String(value || "");
  return sanitizeText(raw).replace(/\r?\n/g, " ").replace(/\|/g, "\\|");
}

function table(headers: string[], rows: unknown[][]): string {
  if (!rows.length) return "_None detected._";
  return [
    `| ${headers.join(" | ")} |`,
    `| ${headers.map(() => "---").join(" | ")} |`,
    ...rows.map((row) => `| ${row.map(cell).join(" | ")} |`),
  ].join("\n");
}

function inferredRules(rules: Fact[], scope: string): string {
  const selected = rules.filter((rule) => rule.scope === scope);
  return selected.length
    ? selected.map((rule) => `- ${rule.rule}（证据：${rule.evidence}）`).join("\n")
    : "_本次扫描未推断出规范：样本不足或缺少该类信号。_";
}

function componentsDoc(frontend: Fact): string {
  const components = facts(frontend.components);
  const scopeOf = (item: Fact) => String(item.scope ?? componentScope(String(item.path ?? "")));
  const publicComponents = components.filter((item) => scopeOf(item) === "public");
  const pageLocal = components.filter((item) => scopeOf(item) === "page-local");
  const repeated = countRows(components.map((item) => item.name), 20).filter((row) => Number(row[1]) > 1);
  const props = countRows(components.flatMap((item) => strings(item.props)), 30);
  const emits = countRows(components.flatMap((item) => strings(item.emits)), 30);
  return `# 组件与复用规范

## 组件分布

${table(["范围", "数量"], countRows(components.map(scopeOf)))}

## 公共组件清单

以下组件位于公共组件目录，新增页面能力前优先检索和复用：

${table(["组件", "路径", "Props", "Emits"], publicComponents.slice(0, 40).map((item) => [
    item.name, item.path, strings(item.props).slice(0, 8).join(", "), strings(item.emits).slice(0, 8).join(", "),
  ]))}

## 页面局部组件热点

${table(["目录", "组件数"], countRows(pageLocal.map((item) => pathPrefix(item.path)), 20))}

## 重名/相似组件候选

重名组件通常意味着跨业务线复制或同类能力未沉淀，默认作为 \`candidate\` 检查：

${table(["组件名", "出现次数"], repeated)}

## 常见 Props / Emits

${table(["Prop", "出现次数"], props)}

${table(["Emit", "出现次数"], emits)}

## 约定

- \`src/components/**\` 下组件视为公共能力，新增前必须先检索是否已有同类组件。
- \`src/pages/**/components/**\` 下组件视为页面局部能力；跨两个以上业务域重复时应评估沉淀为公共组件。
- 修改公共组件时需要检查 Props、Emits 和所有引用页面，避免破坏订单、政企、信息填写、认证等页面。
- 重名组件和相同页面模式默认是 \`candidate\`，人工确认后再升级为 \`preferred\` 或 \`hard\`。
`;
}

function apiDoc(frontend: Fact): string {
  const modules = facts(frontend.apiModules);
  const prefixes = modules.flatMap((module) =>
    facts(module.servicePrefixes).map((item) => [item.name, item.value, module.path])
  );
  const endpointPrefixes = modules.flatMap((module) =>
    strings(module.endpoints).map((endpoint) => pathPrefix(endpoint.replace(/^\/+/, ""), 2))
  );
  return `# API 与请求规范

## 请求封装

${table(["封装/信号", "出现次数"], countRows(modules.flatMap((item) => [
    ...strings(item.wrappers), ...strings(item.signals),
  ]), 20))}

## 服务前缀

${table(["常量", "服务前缀", "来源"], prefixes.slice(0, 30))}

## 接口路径热点

${table(["接口路径前缀", "出现次数"], countRows(endpointPrefixes, 30))}

## API 模块清单

${table(["模块", "请求封装", "导出函数数", "接口样例"], modules.slice(0, 40).map((item) => [
    item.path,
    (strings(item.wrappers).length ? strings(item.wrappers) : strings(item.signals)).join(", "),
    strings(item.exports).length,
    strings(item.endpoints).slice(0, 4).join("; "),
  ]))}

## 约定

- 新增接口优先放在 \`src/api/<domain>/index.ts\` 或既有同域 API 模块中。
- 页面和组件不要直接调用 \`uni.request\`、\`axios\` 或裸 \`fetch\`；优先复用项目请求封装和已有 API 方法。
- 接口参数包装方式应跟随同域模块，例如是否使用数组包裹参数、是否传入 headerInfo、是否关闭缓存。
- 涉及登录态、错误上报、订阅消息、支付链路的接口变更，需要同步检查 \`src/api/request.ts\` 的拦截、错误处理和缓存逻辑。
`;
}

function routerDoc(frontend: Fact): string {
  const routes = facts(frontend.routes);
  return `# 路由与分包规范

## 路由模块

${table(["配置文件", "baseUrl", "页面数", "custom 导航数", "插件 provider"], routes.map((route) => [
    route.path,
    strings(route.baseUrls).join(", "),
    Number(route.routeCount ?? strings(route.routes).length),
    Number(route.customNavigationCount ?? 0),
    strings(route.pluginProviders).join(", "),
  ]))}

## 页面标题热点

${table(["标题", "出现次数"], countRows(routes.flatMap((route) => strings(route.titlesSample)), 30))}

## 约定

- 新增页面优先放入对应 \`src/router/modules/subpackages/*\` 分包配置，保持 \`baseUrl\` 与实际页面目录一致。
- 已使用 \`navigationStyle: 'custom'\` 的业务线新增页面应保持导航风格一致，并复用现有导航组件。
- 使用小程序插件的页面需要在路由配置里保留 provider/version 信息，避免只改页面文件漏改路由配置。
- 页面路径、标题和分包归属是需求影响分析的一部分；改页面入口时需要同步检查跳转 URL 和 \`uni.navigateTo/redirectTo\` 调用。
`;
}

function domainDoc(frontend: Fact, graph: Fact): string {
  const understand = (graph.understandSummary as Fact | undefined) ?? {};
  let domainRows = facts(understand.domains).map((item) => [
    item.name, item.count, strings(item.paths).slice(0, 8).join(", "), strings(item.summaries).slice(0, 2).join("；"),
  ]);
  if (!domainRows.length) {
    domainRows = projectDomainCandidates(frontend, {}, {}).map((item) => [
      item.name, item.count, strings(item.paths).slice(0, 8).join(", "), "",
    ]);
  }
  return `# 业务流与图谱规范

## 业务域候选

以下内容来自 Understand-Anything 图谱摘要和项目轻量扫描，默认是 \`inferred/candidate\`，用于需求前影响分析：

${table(["业务域", "节点/文件数", "关键路径", "图谱摘要"], domainRows)}

## 关键模块摘要

${table(["路径", "名称", "摘要", "标签"], facts(understand.keyModules).slice(0, 30).map((item) => [
    item.path, item.name, item.summary, strings(item.tags).join(", "),
  ]))}

## 图谱路径热点

${table(["路径前缀", "节点数"], (Array.isArray(understand.topPathPrefixes) ? understand.topPathPrefixes : []) as unknown[][])}

## 约定

- 需求涉及任一业务域时，先按项目实际目录、模块和图谱标签定位对应业务域，再查 GitNexus/Understand-Anything 影响面。
- 修改业务流入口时需要同时检查页面、路由、API 模块、store、公共组件和错误处理链路。
- 图谱摘要只作为项目理解和影响分析输入，不替代源码确认；最终实现仍以源码和 \`.project-intel/knowledge\` 为准。
`;
}

function backendApiDoc(backend: Fact): string {
  const apis = facts(backend.apis);
  const candidates = facts(backend.candidateEntrypoints);
  return `# 后端 API 与入口规范

## 框架入口分布

${table(["框架/入口风格", "文件数"], countRows(apis.map((item) => item.framework)))}

## API/入口清单

${table(["路径", "框架", "入口信号", "路径样例", "方法样例"], apis.slice(0, 60).map((item) => [
    item.path, item.framework, strings(item.signals).slice(0, 6).join(", "),
    strings(item.endpoints).slice(0, 6).join("; "), strings(item.methods).slice(0, 8).join(", "),
  ]))}

## 路径热点

${table(["路径前缀", "出现次数"], countRows(apis.flatMap((item) =>
    strings(item.endpoints).map((endpoint) => pathPrefix(endpoint.replace(/^\/+/, ""), 2))
  ), 30))}

## 非标准入口候选

${table(["路径", "原因", "等级"], candidates.slice(0, 40).map((item) => [item.path, item.reason, item.level]))}

## 约定

- 新增 API 入口应跟随同模块已有框架风格，例如 Spring 注解、Nest 装饰器或 router 注册。
- 不要只靠文件名判断入口；handler、facade、adapter、action 等候选入口需要在初始化后人工确认。
- 入口层只做参数接收、权限/校验编排和响应转换，业务编排应下沉到 Service/UseCase。
- 改入口路径时同步检查调用方、路由/网关配置、鉴权配置、测试和接口文档。
`;
}

function servicesDoc(backend: Fact): string {
  const services = facts(backend.services);
  const prefixes = services.flatMap((service) => strings(service.methods).map((method) => /^[a-z]+/.exec(method)?.[0] ?? ""));
  return `# 后端 Service 与业务编排规范

## Service 清单

${table(["名称", "路径", "方法样例", "事务信号", "远程调用", "权限信号"], services.slice(0, 60).map((item) => [
    item.name, item.path, strings(item.methods).slice(0, 10).join(", "), strings(item.transactions).length,
    strings(item.remoteCalls).length, strings(item.permissionSignals).length,
  ]))}

## 方法命名前缀热点

${table(["前缀", "出现次数"], countRows(prefixes, 30))}

## 约定

- Controller/API 层不要绕过 Service 直接访问 Repository/Mapper。
- 新增业务流程优先找同域 Service、Manager、UseCase、Facade，复用已有编排方式。
- 涉及写操作、支付、订单、库存、状态机等流程时，先确认事务边界和幂等策略。
- Service 内远程调用要复用已有客户端/适配器，并保留错误映射、超时、重试和日志链路。
`;
}

function modelsDoc(backend: Fact): string {
  const items = facts(backend.dataTypes);
  return `# 后端 DTO/VO/Entity 规范

## 类型分布

${table(["类型", "数量"], countRows(items.map((item) => item.kind)))}

## 数据类型清单

${table(["名称", "类型", "路径", "字段样例", "注解样例"], items.slice(0, 60).map((item) => [
    item.name, item.kind, item.path, strings(item.fields).slice(0, 12).join(", "), strings(item.annotations).slice(0, 8).join(", "),
  ]))}

## 字段热点

${table(["字段", "出现次数"], countRows(items.flatMap((item) => strings(item.fields)), 40))}

## 注解热点

${table(["注解", "出现次数"], countRows(items.flatMap((item) => strings(item.annotations)), 30))}

## 约定

- DTO/VO 用于接口入参和出参，Entity/Model 用于持久化或领域状态，不要混用职责。
- 新增字段时同步检查序列化名称、校验注解、默认值、兼容性和前后端字段映射。
- Entity 改动需要检查 Mapper/Repository SQL、数据库迁移、缓存键和历史数据兼容。
- 相同字段组合重复出现时，优先复用已有 DTO/VO 或抽取公共片段。
`;
}

function repositoryDoc(backend: Fact): string {
  const items = facts(backend.repositories);
  return `# 后端 Repository/Mapper 规范

## 仓库层分布

${table(["类型", "数量"], countRows(items.map((item) => item.kind)))}

## Repository/Mapper 清单

${table(["名称", "类型", "路径", "方法/SQL id 样例", "SQL 操作"], items.slice(0, 60).map((item) => [
    item.name, item.kind, item.path, strings(item.methods).slice(0, 12).join(", "), strings(item.sqlOps).slice(0, 8).join(", "),
  ]))}

## SQL 操作热点

${table(["操作", "出现次数"], countRows(items.flatMap((item) => strings(item.sqlOps))))}

## 约定

- Repository/Mapper 只负责数据访问，不承载业务流程、权限判断或跨服务编排。
- 新增查询优先复用已有方法；确需新增时保持同域命名、参数对象和分页约定。
- 修改 SQL 或 Mapper XML 时检查关联 DTO/Entity 字段、索引、排序、分页和空值行为。
- 写操作必须回看 Service 层事务边界，避免 Repository 内隐式提交破坏业务一致性。
`;
}

function configDoc(backend: Fact): string {
  const items = facts(backend.configs);
  return `# 后端配置规范

## 配置文件/配置类

${table(["路径", "类型", "配置键样例"], items.slice(0, 80).map((item) => [
    item.path, item.kind, strings(item.keys).slice(0, 15).join(", "),
  ]))}

## 配置前缀热点

${table(["前缀", "出现次数"], countRows(items.flatMap((item) => strings(item.keys).map((key) => key.split(".")[0])), 40))}

## 约定

- 新增配置项优先放到同域已有配置文件或配置类，并保持前缀命名一致。
- 配置变更需要同步默认值、环境变量、测试环境配置、部署文档和回滚策略。
- 涉及开关、限流、超时、重试、灰度的配置，需要在 review 中说明默认行为。
- 不要把密钥、token、密码或私有地址沉淀到项目规范；这里只保留配置键和路径。
`;
}

function signalDoc(
  title: string,
  items: Fact[],
  firstHeading: string,
  conventions: string[],
  signalLimit = 40
): string {
  return `# ${title}

## ${firstHeading}

${table(["路径", "信号样例", "等级"], items.slice(0, 80).map((item) => [
    item.path, strings(item.signals).slice(0, firstHeading.includes("错误") ? 15 : 12).join(", "), item.level,
  ]))}

## 信号热点

${table(["信号", "出现次数"], countRows(items.flatMap((item) => strings(item.signals)), signalLimit))}

## 约定

${conventions.map((item) => `- ${item}`).join("\n")}
`;
}

function utilitiesDoc(backend: Fact): string {
  const items = facts(backend.utilities);
  return `# 后端公共工具规范

## 工具类/公共函数

${table(["名称", "路径", "导出/方法样例"], items.slice(0, 80).map((item) => [
    item.name, item.path, strings(item.exports).slice(0, 12).join(", "),
  ]))}

## 工具目录热点

${table(["目录", "数量"], countRows(items.map((item) => pathPrefix(item.path)), 30))}

## 约定

- 新增转换、校验、签名、时间、序列化、缓存 key 等逻辑前先检索已有工具。
- 工具函数应保持无业务副作用；需要访问数据库、远程服务或上下文时应放回 Service/Adapter。
- 多处复制的工具逻辑默认作为 \`candidate\` 沉淀建议，人工确认后再升级规则等级。
- 修改公共工具需要检查调用面和单元测试，因为它通常跨模块复用。
`;
}

export function standardsDocs(state: ProjectState): Record<string, string> {
  const frontend = state.frontend as unknown as Fact;
  const backend = state.backend as unknown as Fact;
  const graph = state.graph as Fact;
  const config = state.config as Fact;
  const quality = facts((config.quality as Fact | undefined)?.commands);
  const inferred = facts((config.rules as Fact | undefined)?.inferred);
  return {
    "quality.md": `# 质量检查

规则等级：

- \`hard\`：已确认的必守规则；带结构化 \`check\` 的规则自动验证，失败时 \`project-intel check\` 返回非零
- \`preferred\`：稳定的项目约定
- \`inferred\`：扫描器推断，需要人工审查
- \`candidate\`：非阻塞建议

纯文本 \`hard\` 规则会在质量报告中标记为 \`manual-review\`，由 Agent/评审人员核对，不会被 CLI 误判为自动通过或失败。

## 检测到的命令

${table(["类型", "命令", "来源"], quality.map((item) => [item.kind, item.command, item.source]))}

## 策略

- 优先使用项目已有的 package scripts，而非推断的命令。
- 冗余发现默认为 \`candidate\`，直到人工升级规则。
- 审查时将项目质量检查与规范和图谱上下文结合使用。
`,
    "frontend.md": `# 前端规范

## 已提取的事实

- 发现的组件数：${facts(frontend.components).length}
- 发现的 Hooks 数：${facts(frontend.hooks).length}
- 发现的路由文件数：${facts(frontend.routes).length}
- 发现的 API 相关模块数：${facts(frontend.apiModules).length}
- 发现的状态管理文件数：${facts(frontend.stores).length}
- 冗余候选数：${facts(frontend.redundancyCandidates).length}

## 细分规范

- 公共组件与页面局部组件：\`components.md\`
- API 请求封装与服务前缀：\`api.md\`
- 路由、分包和页面入口：\`router.md\`
- 业务流与图谱摘要：\`domain-flows.md\`

## 推断规范

以下规范由扫描器从项目实际代码推断（\`inferred\` 等级），默认作为项目约定遵循；经人工确认后可升级为 \`preferred\` 或 \`hard\`：

${inferredRules(inferred, "frontend")}

## 默认规则

- 添加新组件或 Hook 前，优先复用已有的组件和 Hook。
- 使用项目已有的请求/状态/样式抽象（如果存在）。
- 最终审查前运行检测到的 lint/type/style/format 检查。
- 重复的表格/搜索/对话框/导出/权限模式视为组件或 Hook 抽取的候选。
`,
    "backend.md": `# 后端规范

## 已提取的事实

- 发现的 API/入口模块数：${facts(backend.apis).length}
- 发现的服务数：${facts(backend.services).length}
- 发现的 DTO/VO/Entity/模型文件数：${facts(backend.dataTypes).length}
- 发现的 Repository/Mapper 文件数：${facts(backend.repositories).length}
- 发现的配置文件/配置类数：${facts(backend.configs).length}
- 发现的权限/认证信号文件数：${facts(backend.permissionChecks).length}
- 发现的事务信号文件数：${facts(backend.transactions).length}
- 发现的远程调用信号文件数：${facts(backend.remoteCalls).length}
- 发现的消息/任务信号文件数：${facts(backend.messagesJobs).length}
- 发现的错误码/异常信号文件数：${facts(backend.errorCodes).length}
- 发现的公共工具候选数：${facts(backend.utilities).length}
- 候选非标准入口点数：${facts(backend.candidateEntrypoints).length}

## 细分规范

- API 与入口：\`backend-api.md\`
- Service 与业务编排：\`backend-services.md\`
- DTO/VO/Entity：\`backend-models.md\`
- Repository/Mapper：\`backend-repository.md\`
- 配置项：\`backend-config.md\`
- 权限与认证：\`backend-security.md\`
- 事务边界：\`backend-transactions.md\`
- 远程调用：\`backend-remote-calls.md\`
- 消息与任务：\`backend-async.md\`
- 错误码与异常：\`backend-errors.md\`
- 公共工具：\`backend-utilities.md\`

## 推断规范

以下规范由扫描器从项目实际代码推断（\`inferred\` 等级），默认作为项目约定遵循；经人工确认后可升级为 \`preferred\` 或 \`hard\`：

${inferredRules(inferred, "backend")}

## 默认规则

- 通过框架适配器、AST/调用模式和项目特定规则识别入口点。
- 不要仅依赖 \`Controller\` 命名。
- 保持服务、数据、仓库、权限、事务和配置的边界。
- 升级候选入口点为 hard 标准前需人工确认。
`,
    "reuse.md": `# 复用与冗余

## 策略

- 实现组件、Hook、API 客户端、服务或工具函数前，先搜索 \`.project-intel/knowledge\`。
- 重复的 UI、数据转换、校验、请求构建和样式块默认视为 \`candidate\` 发现。
- 候选升级为 \`preferred\` 或 \`hard\` 需人工确认。
`,
    "components.md": componentsDoc(frontend),
    "api.md": apiDoc(frontend),
    "router.md": routerDoc(frontend),
    "domain-flows.md": domainDoc(frontend, graph),
    "backend-api.md": backendApiDoc(backend),
    "backend-services.md": servicesDoc(backend),
    "backend-models.md": modelsDoc(backend),
    "backend-repository.md": repositoryDoc(backend),
    "backend-config.md": configDoc(backend),
    "backend-security.md": signalDoc("后端权限与认证规范", facts(backend.permissionChecks), "权限/认证信号", [
      "新增入口必须检查同模块已有认证、鉴权、token、session、角色和权限注解。",
      "权限判断优先复用已有 guard/interceptor/filter/helper，不要在业务方法里复制判断。",
      "修改鉴权逻辑时同步检查匿名访问、内部调用、批量接口、管理端和定时任务入口。",
      "权限缺失默认是 review 阻断风险；扫描命中仍为 `candidate`，最终以源码和人工确认升级。",
    ]),
    "backend-transactions.md": signalDoc("后端事务边界规范", facts(backend.transactions), "事务信号", [
      "涉及订单、支付、库存、状态变更、多表写入时，先确认已有事务边界。",
      "不要把一个原子业务流程拆成多个无保护写操作；异步流程需要说明补偿和幂等。",
      "远程调用和事务混用时要特别审查超时、重复提交、回滚语义和最终一致性。",
      "新增事务注解或事务模板时同步检查调用链是否经过代理，避免事务不生效。",
    ]),
    "backend-remote-calls.md": signalDoc("后端远程调用规范", facts(backend.remoteCalls), "远程调用信号", [
      "远程调用优先复用已有 Feign/Dubbo/gRPC/HTTP 客户端或公司内部适配器。",
      "新增调用必须检查超时、重试、熔断、错误码映射、日志追踪和调用方降级行为。",
      "变更远程接口入参/出参时同步检查 DTO、调用链、Mock、契约测试和下游兼容。",
      "Review 时把远程调用视为影响面扩大点，优先结合 GitNexus 调用链或图谱上下文确认风险。",
    ]),
    "backend-async.md": signalDoc("后端消息与任务规范", facts(backend.messagesJobs), "消息/任务信号", [
      "消息消费者、事件监听器和定时任务都是后端入口，需求影响分析不能只看 HTTP Controller。",
      "修改异步入口需要检查幂等、重试、死信/补偿、并发控制、调度频率和监控告警。",
      "新增任务配置时同步检查配置文件、部署环境、开关和测试数据隔离。",
      "定时任务或消费者调用 Service 时，复用同一套事务、权限边界和错误处理策略。",
    ]),
    "backend-errors.md": signalDoc("后端错误码与异常规范", facts(backend.errorCodes), "错误码/异常信号", [
      "新增业务异常前先搜索既有 ErrorCode/ResultCode/ResponseCode 和异常类型。",
      "错误码语义需要让前端、调用方和日志排障都能识别，不要只抛通用异常。",
      "改错误码或异常映射时同步检查接口响应、重试逻辑、告警、埋点和用户提示。",
      "异常处理属于硬规范候选；团队确认后可升级为 `preferred` 或 `hard`。",
    ], 60),
    "backend-utilities.md": utilitiesDoc(backend),
  };
}
