// Frontend scanner (phase 3.A.2), ported from scanner/frontend.py.
//
// Scans .vue/.tsx/.jsx/.ts/.js + style files for components, hooks, routes,
// apiModules, stores, styles, and redundancy candidates. Uses brace/quote-aware
// object argument parsing for defineProps/defineEmits (regex-fallback mode).

export const FRONTEND_SUFFIXES = new Set([".vue", ".tsx", ".jsx", ".ts", ".js"]);
export const STYLE_SUFFIXES = new Set([".scss", ".css", ".less", ".sass"]);

function allMatches(text: string, pattern: RegExp): RegExpExecArray[] {
  const out: RegExpExecArray[] = [];
  const re = new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : pattern.flags + "g");
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    out.push(m);
    if (m.index === re.lastIndex) re.lastIndex++;
  }
  return out;
}

/** Extract balanced { ... } argument blocks following `functionName(`. */
export function extractObjectArgumentBlocks(text: string, functionName: string): string[] {
  const blocks: string[] = [];
  const pattern = new RegExp(`\\b${escapeRegex(functionName)}\\s*\\(\\s*{`, "g");
  for (const match of allMatches(text, pattern)) {
    const start = match.index! + match[0].length - 1;
    let depth = 0;
    let quote = "";
    let escaped = false;
    for (let idx = start; idx < text.length; idx++) {
      const char = text[idx]!;
      if (quote) {
        if (escaped) escaped = false;
        else if (char === "\\") escaped = true;
        else if (char === quote) quote = "";
        continue;
      }
      if (char === "'" || char === '"' || char === "`") {
        quote = char;
      } else if (char === "{") {
        depth++;
      } else if (char === "}") {
        depth--;
        if (depth === 0) {
          blocks.push(text.slice(start + 1, idx));
          break;
        }
      }
    }
  }
  return blocks;
}

export function splitTopLevelItems(block: string): string[] {
  const items: string[] = [];
  let start = 0;
  let depth = 0;
  let quote = "";
  let escaped = false;
  for (let idx = 0; idx < block.length; idx++) {
    const char = block[idx]!;
    if (quote) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) quote = "";
      continue;
    }
    if (char === "'" || char === '"' || char === "`") {
      quote = char;
    } else if (char === "(" || char === "[" || char === "{") {
      depth++;
    } else if (char === ")" || char === "]" || char === "}") {
      depth = Math.max(0, depth - 1);
    } else if (char === "," && depth === 0) {
      const item = block.slice(start, idx).trim();
      if (item) items.push(item);
      start = idx + 1;
    }
  }
  const tail = block.slice(start).trim();
  if (tail) items.push(tail);
  return items;
}

export function topLevelObjectKeys(block: string): string[] {
  const names: string[] = [];
  for (const item of splitTopLevelItems(block)) {
    const m = /(?:['"]([^'"]+)['"]|([A-Za-z_$][\w$]*))\??\s*:/.exec(item);
    if (m) names.push(m[1] ?? m[2]!);
  }
  return names;
}

export function extractVueProps(text: string): string[] {
  const names = new Set<string>();
  for (const m of allMatches(text, /defineProps\s*<\s*{([^}]*)}/gs)) {
    for (const p of allMatches(m[1]!, /\b([A-Za-z_$][\w$]*)\??\s*:/g)) names.add(p[1]!);
  }
  for (const m of allMatches(text, /defineProps\s*<\s*([A-Za-z_$][\w$]*)\s*>/g)) {
    const type = m[1]!;
    const pat = new RegExp(`(?:interface\\s+${escapeRegex(type)}|type\\s+${escapeRegex(type)}\\s*=)\\s*{([^}]*)}`, "gs");
    for (const block of allMatches(text, pat)) {
      for (const p of allMatches(block[1]!, /\b([A-Za-z_$][\w$]*)\??\s*:/g)) names.add(p[1]!);
    }
  }
  for (const block of extractObjectArgumentBlocks(text, "defineProps")) {
    for (const key of topLevelObjectKeys(block)) names.add(key);
  }
  return [...names].sort();
}

export function extractEmits(text: string): string[] {
  const names = new Set<string>();
  for (const m of allMatches(text, /defineEmits\s*\(\s*\[([^\]]*)\]/gs)) {
    for (const q of allMatches(m[1]!, /['"]([^'"]+)['"]/g)) names.add(q[1]!);
  }
  for (const m of allMatches(text, /defineEmits\s*\(\s*{([^}]*)}/gs)) {
    for (const q of allMatches(m[1]!, /(?:^|[,{\s])(?:['"]([^'"]+)['"]|([A-Za-z_$][\w$]*))\s*:/g)) {
      if (q[1]) names.add(q[1]);
      if (q[2]) names.add(q[2]);
    }
  }
  for (const m of allMatches(text, /defineEmits\s*<([^>]*)>/gs)) {
    for (const q of allMatches(m[1]!, /['"]([A-Za-z0-9:_-]+)['"]/g)) names.add(q[1]!);
  }
  return [...names].filter((n) => /^[A-Za-z][A-Za-z0-9:_-]*$/.test(n)).sort();
}

export function extractSlots(text: string): string[] {
  const expanded = new Set<string>();
  for (const m of allMatches(text, /<slot(?:\s+name=['"]([^'"]+)['"])?/g)) {
    expanded.add(m[1] || "default");
  }
  for (const m of allMatches(text, /defineSlots\s*<\s*{([^}]*)}/gs)) {
    for (const p of allMatches(m[1]!, /\b([A-Za-z_$][\w$]*)\??\s*[:(]/g)) expanded.add(p[1]!);
  }
  return [...expanded].sort();
}

export function extractExpose(text: string): string[] {
  const names = new Set<string>();
  for (const block of extractObjectArgumentBlocks(text, "defineExpose")) {
    for (const item of splitTopLevelItems(block)) {
      const m = /^([A-Za-z_$][\w$]*)/.exec(item);
      if (m) names.add(m[1]!);
    }
  }
  return [...names].sort();
}

export function extractDependencies(text: string): string[] {
  const values = (text.match(/(?:import\s+[^;]*?\s+from\s+|import\s*\(|require\s*\()\s*['"]([^'"]+)['"]/g) || []).map(
    (s) => s.match(/['"]([^'"]+)['"]/)![1]!
  );
  return [...new Set(values)].sort().slice(0, 50);
}

export function componentScope(path: string): string {
  if (path.startsWith("src/components/") || path.startsWith("components/")) return "public";
  if (path.includes("/components/")) return "page-local";
  if (path.startsWith("src/pages/") || path.startsWith("pages/") || path.startsWith("app/")) return "page";
  return "module";
}

export function extractServicePrefixes(text: string): { name: string; value: string }[] {
  const prefixes: { name: string; value: string }[] = [];
  for (const m of allMatches(text, /\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*['"]([^'"]*\/[^'"]*)['"]/g)) {
    const value = m[2]!;
    if (["service", "openapi", "api", "adapt"].some((tok) => value.includes(tok))) {
      prefixes.push({ name: m[1]!, value: value.replace(/\/$/, "") || value });
    }
  }
  return prefixes.slice(0, 20);
}

export function extractApiEndpoints(text: string): string[] {
  const endpoints: string[] = [];
  const pattern = /(?<![\w$])(?:\$post|\$get|\$put|\$delete|request|fetch|axios)\s*\(\s*(`([^`]+)`|['"]([^'"]+)['"])/g;
  for (const m of allMatches(text, pattern)) {
    const raw = m[2] ?? m[3] ?? "";
    if (raw) endpoints.push(raw);
  }
  for (const m of allMatches(text, /['"](\/[^'"]*(?:service|openapi|api|adapt)[^'"]*)['"]/g)) {
    endpoints.push(m[1]!);
  }
  return [...new Set(endpoints)].sort().slice(0, 40);
}

export function extractExportedFunctions(text: string): string[] {
  let names = (text.match(/\bexport\s+const\s+([A-Za-z_$][\w$]*)\s*=/g) || []).map((m) => m.match(/const\s+(\w+)/)![1]!);
  names = names.concat(
    (text.match(/\bexport\s+function\s+([A-Za-z_$][\w$]*)\s*\(/g) || []).map((m) => m.match(/function\s+(\w+)/)![1]!)
  );
  return [...new Set(names)].sort().slice(0, 80);
}

export function extractReactProps(text: string): string[] {
  const names = new Set<string>();
  for (const m of allMatches(text, /(?:interface|type)\s+\w*Props\w*\s*(?:=\s*)?{([^}]*)}/gs)) {
    for (const p of allMatches(m[1]!, /\b([A-Za-z_$][\w$]*)\??\s*:/g)) names.add(p[1]!);
  }
  let blocks = (text.match(/function\s+[A-Z][A-Za-z0-9_]*\s*\(\s*{([^}]*)}/gs) || []).map((m) => m);
  blocks = blocks.concat((text.match(/=\s*\(\s*{([^}]*)}\s*\)\s*=>/gs) || []).map((m) => m));
  for (const block of blocks) {
    const inner = block.match(/{([^}]*)}/)?.[1] ?? "";
    for (const name of inner.split(",")) {
      const trimmed = name.trim().split(":")[0]!.trim();
      if (trimmed && /^[A-Za-z_$][\w$]*$/.test(trimmed)) names.add(trimmed);
    }
  }
  return [...names].sort();
}

export function routeModuleInfo(text: string): Record<string, unknown> {
  const routes = [...new Set((text.match(/path\s*:\s*['"]([^'"]+)['"]/g) || []).map((s) => s.match(/['"]([^'"]+)['"]/)![1]!))].sort();
  return {
    baseUrls: [...new Set((text.match(/baseUrl\s*:\s*['"]([^'"]+)['"]/g) || []).map((s) => s.match(/['"]([^'"]+)['"]/)![1]!))].sort(),
    routes,
    routeCount: routes.length,
    customNavigationCount: (text.match(/navigationStyle\s*:\s*['"]custom['"]/g) || []).length,
    pluginProviders: [...new Set((text.match(/provider\s*:\s*['"]([^'"]+)['"]/g) || []).map((s) => s.match(/['"]([^'"]+)['"]/)![1]!))].sort(),
    titlesSample: (text.match(/navigationBarTitleText\s*:\s*['"]([^'"]+)['"]/g) || []).map((s) => s.match(/['"]([^'"]+)['"]/)![1]!).slice(0, 20),
  };
}

export const PATTERN_DEFS: Record<string, RegExp[]> = {
  table: [/<(el-table|ProTable)\b/, /\bcolumns\s*=/, /type:\s*['"]selection/],
  pagination: [/<(el-pagination|Pagination)\b/, /page(Size|Num|Index)/, /usePagination/],
  "dialog-drawer": [/<(el-dialog|el-drawer|Drawer|nut-popup|dx-dialog)\b/, /v-model:visible/, /defineEmits|showModal/],
  "search-form": [/<el-form\b/, /handle(Search|Reset)/, /search(Form|Params)/],
  permission: [/\b(permission|auth|v-permission|hasPermission)\b/],
  "export-download": [/\b(export|download|导出)\b/],
};

export interface FrontendFacts {
  components: unknown[];
  hooks: unknown[];
  routes: unknown[];
  apiModules: unknown[];
  stores: unknown[];
  styles: unknown[];
  patterns?: string[];
  scanMode?: string;
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function extname(path: string): string {
  const i = path.lastIndexOf(".");
  return i === -1 ? "" : path.slice(i);
}

function stem(path: string): string {
  const base = path.split("/").pop() ?? path;
  const i = base.lastIndexOf(".");
  return i === -1 ? base : base.slice(0, i);
}

/** Scan a single frontend file (mirrors scan_frontend_file). */
export function scanFrontendFile(relPath: string, text: string): FrontendFacts {
  const suffix = extname(relPath).toLowerCase();
  const lower = relPath.toLowerCase();
  const facts: FrontendFacts = { components: [], hooks: [], routes: [], apiModules: [], stores: [], styles: [] };
  if ((suffix === ".vue" || suffix === ".tsx" || suffix === ".jsx") && (lower.includes("/components/") || suffix === ".vue")) {
    const name = stem(relPath) !== "index" ? stem(relPath) : (relPath.split("/").slice(-2)[0] ?? stem(relPath));
    facts.components.push({
      name,
      path: relPath,
      kind: suffix === ".vue" ? "vue" : "react",
      scope: componentScope(relPath),
      props: suffix === ".vue" ? extractVueProps(text) : extractReactProps(text),
      emits: suffix === ".vue" ? extractEmits(text) : [],
      slots: suffix === ".vue" ? extractSlots(text) : [],
      expose: suffix === ".vue" ? extractExpose(text) : [],
      dependencies: extractDependencies(text),
      level: "candidate",
    });
  }
  if (/(^|\/)use[A-Z][A-Za-z0-9_]*\.(ts|tsx|js|jsx)$/.test(relPath)) {
    facts.hooks.push({
      name: stem(relPath),
      path: relPath,
      exports: extractExportedFunctions(text),
      dependencies: extractDependencies(text),
      level: "candidate",
    });
  }
  if (lower.includes("/router") || stem(relPath).toLowerCase().includes("route")) {
    const info = routeModuleInfo(text);
    if ((info.routes as string[]).length) facts.routes.push({ path: relPath, ...info });
  }
  if (lower.includes("/api/") || /\b(axios|fetch|request)\s*[.(]/.test(text)) {
    facts.apiModules.push({
      path: relPath,
      signals: [...new Set((text.match(/\b(axios|fetch|request)\b/g) || []) as string[])].sort(),
      wrappers: [...new Set((text.match(/(?<![\w$])(\$post|\$get|\$put|\$delete|axios|fetch|request)\s*\(/g) || []).map((s) => s.match(/(\$\w+|\w+)/)![1]!))].sort(),
      endpoints: extractApiEndpoints(text),
      servicePrefixes: extractServicePrefixes(text),
      exports: extractExportedFunctions(text),
    });
  }
  if (lower.includes("/stores/") && (suffix === ".ts" || suffix === ".js")) {
    facts.stores.push({
      path: relPath,
      definesStore: /\bdefineStore\s*\(/.test(text),
      exports: extractExportedFunctions(text),
    });
  }
  if (STYLE_SUFFIXES.has(suffix) || suffix === ".vue") {
    const hardcoded = text.match(/#[0-9a-fA-F]{3,8}|\b\d+px\b/g) || [];
    if (hardcoded.length) facts.styles.push({ path: relPath, hardcodedValuesSample: hardcoded.slice(0, 20), count: hardcoded.length });
  }
  facts.patterns = Object.entries(PATTERN_DEFS)
    .filter(([, regexes]) => regexes.filter((re) => re.test(text)).length >= 2)
    .map(([name]) => name);
  return facts;
}

export interface ScanFrontendResult extends Omit<FrontendFacts, "scanMode"> {
  redundancyCandidates: unknown[];
  scanMode: string;
}

/** Scan a list of frontend files, aggregating facts + redundancy candidates. */
export function scanFrontend(
  files: { path: string; text?: string; readText?: () => string; signature?: string }[],
  cache?: import("./core.js").IncrementalScanCache
): ScanFrontendResult {
  const groups: Record<string, unknown[]> = { components: [], hooks: [], routes: [], apiModules: [], stores: [], styles: [] };
  const patterns = new Map<string, number>();
  const locations = new Map<string, string[]>();
  for (const file of files) {
    const { path } = file;
    const suffix = extname(path).toLowerCase();
    if (!FRONTEND_SUFFIXES.has(suffix) && !STYLE_SUFFIXES.has(suffix)) continue;
    let facts = file.signature && cache
      ? cache.get(path, "frontend", file.signature) as FrontendFacts | null
      : null;
    if (!facts) {
      const text = file.text ?? file.readText?.() ?? "";
      facts = scanFrontendFile(path, text);
      if (file.signature && cache) cache.put(path, "frontend", file.signature, facts);
    }
    for (const key of ["components", "hooks", "routes", "apiModules", "stores", "styles"] as const) {
      (groups[key] as unknown[]).push(...(facts[key] as unknown[]));
    }
    for (const name of facts.patterns ?? []) {
      patterns.set(name, (patterns.get(name) ?? 0) + 1);
      const arr = locations.get(name) ?? [];
      arr.push(path);
      locations.set(name, arr);
    }
  }
  const redundancyCandidates = [...patterns.entries()]
    .filter(([, count]) => count >= 3)
    .map(([name, count]) => ({
      type: "frontend-pattern",
      name,
      count,
      locations: (locations.get(name) ?? []).slice(0, 20),
      level: "candidate",
      recommendation: "审查重复使用是否应复用或抽取为组件/Hook；默认不阻塞。",
    }));
  return { ...groups, redundancyCandidates, scanMode: "regex-fallback" } as ScanFrontendResult;
}
