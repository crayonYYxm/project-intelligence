// Standards inference (phase 3.B.4), ported from application.infer_standards.
//
// Derives `inferred`-level rules from scan facts. All rules carry level
// "inferred" and require human confirmation before promotion to hard/preferred.

/** Structural subset of scan results used by the inference rules. */
export interface ScanFactsSubset {
  components?: unknown[];
  hooks?: unknown[];
  routes?: unknown[];
  apiModules?: unknown[];
  stores?: unknown[];
  styles?: unknown[];
  redundancyCandidates?: unknown[];
  apis?: unknown[];
  services?: unknown[];
  dataTypes?: unknown[];
  repositories?: unknown[];
  configs?: unknown[];
  permissionChecks?: unknown[];
  transactions?: unknown[];
  remoteCalls?: unknown[];
  messagesJobs?: unknown[];
  errorCodes?: unknown[];
  utilities?: unknown[];
}

export interface InferredRule {
  scope: string;
  category: string;
  rule: string;
  evidence: string;
  level: "inferred";
}

function dominantParent(paths: string[]): [string, number, number] | null {
  const counts = new Map<string, number>();
  for (const path of paths) {
    const parts = path.split("/");
    parts.pop();
    const dir = parts.join("/");
    if (dir) counts.set(dir, (counts.get(dir) ?? 0) + 1);
  }
  let top = "";
  let topHits = 0;
  for (const [dir, hits] of counts) {
    if (hits > topHits) {
      top = dir;
      topHits = hits;
    }
  }
  return top ? [top, topHits, paths.length] : null;
}

function counterTop<T>(items: Iterable<T>): [T, number] | null {
  const counts = new Map<T, number>();
  for (const item of items) counts.set(item, (counts.get(item) ?? 0) + 1);
  let top: T | null = null;
  let topHits = 0;
  for (const [item, hits] of counts) {
    if (hits > topHits) {
      top = item;
      topHits = hits;
    }
  }
  return top !== null ? [top, topHits] : null;
}

function componentScope(path: string): string {
  if (path.startsWith("src/components/") || path.startsWith("components/")) return "public";
  if (path.includes("/components/")) return "page-local";
  if (path.startsWith("src/pages/") || path.startsWith("pages/") || path.startsWith("app/")) return "page";
  return "module";
}

/**
 * Infer `inferred`-level standards from frontend + backend scan facts.
 * Mirrors application.infer_standards.
 */
export function inferStandards(frontend: ScanFactsSubset, backend: ScanFactsSubset): InferredRule[] {
  const rules: InferredRule[] = [];
  const add = (scope: string, category: string, rule: string, evidence: string) => {
    rules.push({ scope, category, rule, evidence, level: "inferred" });
  };

  const components = (frontend.components ?? []) as Record<string, unknown>[];
  const hooks = (frontend.hooks ?? []) as Record<string, unknown>[];
  const routes = (frontend.routes ?? []) as Record<string, unknown>[];
  const apiModules = (frontend.apiModules ?? []) as Record<string, unknown>[];
  const stores = (frontend.stores ?? []) as Record<string, unknown>[];
  const styles = (frontend.styles ?? []) as Record<string, unknown>[];
  const redundancy = (frontend.redundancyCandidates ?? []) as Record<string, unknown>[];

  // Naming: component file naming style
  const compNames = components.map((c) => String(c.name ?? "")).filter(Boolean);
  if (compNames.length >= 3) {
    const pascal = compNames.filter((n) => /^[A-Z][A-Za-z0-9]+$/.test(n));
    const kebab = compNames.filter((n) => /^[a-z][a-z0-9]*(-[a-z0-9]+)+$/.test(n));
    for (const [styleName, matched] of [["PascalCase", pascal], ["kebab-case", kebab]] as const) {
      if (matched.length / compNames.length >= 0.8) {
        add("frontend", "naming", `组件文件使用 ${styleName} 命名`, `${matched.length}/${compNames.length} 个组件符合`);
        break;
      }
    }
  }

  // Naming: custom hooks useXxx
  if (hooks.length >= 2) {
    add("frontend", "naming", "自定义 Hook 统一使用 useXxx 命名，一个文件一个 Hook", `${hooks.length} 个 Hook 均符合`);
  }

  // Directory structure: components / hooks / api modules centralized
  for (const [label, items] of [["公共组件", components], ["自定义 Hook 文件", hooks], ["API 请求模块", apiModules]] as const) {
    if (items.length >= 3) {
      const dom = dominantParent(items.map((i) => String(i.path ?? "")));
      if (dom) add("frontend", "structure", `${label}统一放在 \`${dom[0]}/\` 目录`, `${dom[1]}/${dom[2]} 个文件位于该目录`);
    }
  }
  const publicCount = components.filter((item) =>
    String(item.scope ?? componentScope(String(item.path ?? ""))) === "public"
  ).length;
  const pageLocalCount = components.filter((item) =>
    String(item.scope ?? componentScope(String(item.path ?? ""))) === "page-local"
  ).length;
  if (publicCount >= 3 && pageLocalCount >= 3) {
    add(
      "frontend",
      "component-reuse",
      "跨业务复用能力优先沉淀到公共组件目录，页面私有组件仅服务当前业务域",
      `公共组件 ${publicCount} 个，页面局部组件 ${pageLocalCount} 个`
    );
  }

  // Request wrapping: API modules unified
  if (apiModules.length >= 3) {
    const signals = apiModules.flatMap((m) => ((m.wrappers as string[]) ?? (m.signals as string[]) ?? []));
    const top = counterTop(signals);
    if (top && top[1] / apiModules.length >= 0.5) {
      add("frontend", "request", `API 请求统一通过 \`${top[0]}\` 封装发起；组件内不要直接调用 axios/fetch`, `${top[1]}/${apiModules.length} 个 API 模块使用 ${top[0]}`);
    }
    const prefixCounts = new Map<string, number>();
    for (const m of apiModules) {
      for (const p of (m.servicePrefixes as { value?: string }[]) ?? []) {
        if (p.value) prefixCounts.set(p.value, (prefixCounts.get(p.value) ?? 0) + 1);
      }
    }
    const sorted = [...prefixCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
    for (const [prefix, hits] of sorted) {
      if (hits >= 1) add("frontend", "api-prefix", `接口服务前缀 \`${prefix}\` 已在 API 模块中声明，新增接口应复用同域前缀常量`, `${hits} 处声明服务前缀`);
    }
  }

  // Router
  if (routes.length >= 2) {
    const routeCount = routes.reduce((sum, r) => sum + (Number(r.routeCount) || (r.routes as string[] | undefined)?.length || 0), 0);
    const customCount = routes.reduce((sum, r) => sum + (Number(r.customNavigationCount) || 0), 0);
    add("frontend", "router", "小程序页面入口通过路由/分包配置维护，新增页面需同步路由配置和页面跳转路径", `${routes.length} 个路由配置文件，${routeCount} 个页面路径`);
    if (customCount >= Math.max(3, Math.floor(routeCount / 2))) {
      add("frontend", "router", "业务页面普遍使用自定义导航，新增页面应保持导航风格一致", `${customCount}/${routeCount} 个页面配置 custom navigation`);
    }
  }

  // State (Pinia)
  if (stores.length) {
    const piniaCount = stores.filter((s) => s.definesStore).length;
    if (piniaCount) add("frontend", "state", "状态管理集中在 stores 目录，新增跨页面状态优先使用既有 Pinia store", `${piniaCount}/${stores.length} 个 store 文件使用 defineStore`);
  }

  // Style: hardcoded values
  const hardcodedTotal = styles.reduce((sum, s) => sum + (Number(s.count) || 0), 0);
  if (styles.length >= 2 && hardcodedTotal >= 20) {
    add("frontend", "style", "新增样式应使用主题变量/设计令牌，避免继续新增硬编码颜色和像素值", `检测到 ${hardcodedTotal} 处硬编码值，分布于 ${styles.length} 个文件`);
  }

  // High-frequency UI patterns
  for (const candidate of redundancy) {
    const count = Number(candidate.count) || 0;
    const name = String(candidate.name ?? "");
    if (count >= 3 && name) {
      const locations = ((candidate.locations as string[]) ?? []).slice(0, 3).join("、");
      add("frontend", "ui-pattern", `「${name}」模式在项目中重复出现，新页面应复用已有实现或抽取公共组件/Hook`, `${count} 处出现，如 ${locations}`);
    }
  }

  const apis = (backend.apis ?? []) as Record<string, unknown>[];
  const services = (backend.services ?? []) as Record<string, unknown>[];
  const dataTypes = (backend.dataTypes ?? []) as Record<string, unknown>[];
  const repositories = (backend.repositories ?? []) as Record<string, unknown>[];
  const configs = (backend.configs ?? []) as Record<string, unknown>[];
  const permissionChecks = (backend.permissionChecks ?? []) as Record<string, unknown>[];
  const transactions = (backend.transactions ?? []) as Record<string, unknown>[];
  const remoteCalls = (backend.remoteCalls ?? []) as Record<string, unknown>[];
  const messagesJobs = (backend.messagesJobs ?? []) as Record<string, unknown>[];
  const errorCodes = (backend.errorCodes ?? []) as Record<string, unknown>[];
  const utilities = (backend.utilities ?? []) as Record<string, unknown>[];

  // Backend naming: Service / DTO suffix
  const serviceNames = services.map((s) => String(s.name ?? "")).filter(Boolean);
  if (serviceNames.length >= 2) {
    const suffixMatched = serviceNames.filter((n) => /(?:Service|Manager|UseCase)$/.test(n));
    if (suffixMatched.length / serviceNames.length >= 0.8) {
      add("backend", "naming", "服务类使用 Service 等后缀命名", `${suffixMatched.length}/${serviceNames.length} 个服务符合`);
    }
  }
  const dtoNames = dataTypes.map((d) => String(d.name ?? "")).filter(Boolean);
  if (dtoNames.length >= 2) {
    for (const suffix of ["DTO", "Dto", "VO", "Entity", "Model"]) {
      const suffixMatched = dtoNames.filter((n) => n.endsWith(suffix));
      if (suffixMatched.length / dtoNames.length >= 0.8) {
        add("backend", "naming", `数据类型使用 ${suffix} 后缀命名`, `${suffixMatched.length}/${dtoNames.length} 个数据类型符合`);
        break;
      }
    }
  }

  if (apis.length >= 2 && services.length >= 2 && repositories.length >= 1) {
    add(
      "backend",
      "backend-layering",
      "后端遵循 Controller→Service→Repository 分层，新接口按此分层组织，不要跨层直接访问数据",
      `${apis.length} 个入口、${services.length} 个服务、${repositories.length} 个仓库层文件`
    );
    const annotationHits = apis.filter((api) =>
      ((api.signals as string[] | undefined) ?? []).includes("RestController")
    ).length;
    if (annotationHits / apis.length >= 0.8) {
      add("backend", "backend-layering", "HTTP 入口统一使用 @RestController 注解风格", `${annotationHits}/${apis.length} 个入口符合`);
    }
  }

  if (apis.length >= 1) {
    const top = counterTop(apis.map((api) => String(api.framework ?? "")).filter(Boolean));
    if (top) {
      add("backend", "backend-api", `后端入口主要使用 ${top[0]} 风格，新增 API 应跟随同框架入口声明方式`, `${top[1]}/${apis.length} 个入口匹配`);
    }
  }
  if (configs.length) {
    const keyCount = configs.reduce((sum, item) => sum + (((item.keys as unknown[]) ?? []).length), 0);
    add("backend", "config", "配置项应集中在已有配置文件或配置类中维护，新增配置需同步默认值和环境差异", `${configs.length} 个配置文件/类，${keyCount} 个配置键候选`);
  }
  if (permissionChecks.length) {
    add("backend", "permission", "已有权限/认证信号需要作为接口改动前置检查，新增入口不能绕过认证边界", `${permissionChecks.length} 个文件包含权限或认证信号`);
  }
  if (transactions.length) {
    add("backend", "transaction", "涉及写操作、订单、支付或跨表修改时复用已有事务边界，避免把事务拆散到调用方", `${transactions.length} 个文件包含事务信号`);
  }
  if (remoteCalls.length) {
    add("backend", "remote-call", "远程调用应复用已有客户端/适配器，变更前需要检查超时、重试、错误映射和调用链影响", `${remoteCalls.length} 个文件包含远程调用信号`);
  }
  if (messagesJobs.length) {
    add("backend", "message-job", "消息消费者和定时任务属于异步入口，修改时需要检查幂等、重试和调度配置", `${messagesJobs.length} 个文件包含消息或任务信号`);
  }
  if (errorCodes.length) {
    add("backend", "error-code", "业务异常和错误码应复用既有错误码体系，新增错误需同步前端/调用方可识别的语义", `${errorCodes.length} 个文件包含错误码或异常信号`);
  }
  if (utilities.length) {
    add("backend", "utility", "公共工具方法优先放在已有 util/common/helper 目录，业务代码不要复制相同转换、校验或封装逻辑", `${utilities.length} 个公共工具候选文件`);
  }

  return rules;
}
