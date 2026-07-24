// Backend scanner (phase 3.A.1), ported from scanner/backend.py.
//
// Scans .java/.kt/.py/.go/.ts/.js + config files for APIs, services, dataTypes,
// repositories, configs, permissionChecks, transactions, remoteCalls,
// messagesJobs, errorCodes, utilities, candidateEntrypoints, testFixtures.
//
// Python files use a lightweight Node-native structural parser so the product
// runtime does not depend on Python while retaining framework-aware semantics.

import { simpleMatch } from "./files.js";

export const BACKEND_SUFFIXES = new Set([".java", ".kt", ".py", ".go", ".ts", ".js"]);
export const CONFIG_SUFFIXES = new Set([".yaml", ".yml", ".properties", ".xml"]);

export type BackendFactKey =
  | "apis"
  | "services"
  | "dataTypes"
  | "repositories"
  | "configs"
  | "permissionChecks"
  | "transactions"
  | "remoteCalls"
  | "messagesJobs"
  | "errorCodes"
  | "utilities"
  | "candidateEntrypoints"
  | "testFixtures";

export interface BackendFacts {
  apis: unknown[];
  services: unknown[];
  dataTypes: unknown[];
  repositories: unknown[];
  configs: unknown[];
  permissionChecks: unknown[];
  transactions: unknown[];
  remoteCalls: unknown[];
  messagesJobs: unknown[];
  errorCodes: unknown[];
  utilities: unknown[];
  candidateEntrypoints: unknown[];
  testFixtures: unknown[];
  scanMode?: string;
}

function uniqueLimited<T>(items: T[], limit = 40): T[] {
  const values: T[] = [];
  const seen = new Set<string>();
  for (const item of items) {
    const key =
      item && typeof item === "object" ? JSON.stringify(item) : String(item);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    values.push(item);
    if (values.length >= limit) break;
  }
  return values;
}

function flattenRegexHits(hits: RegExpMatchArray[]): string[] {
  const values: string[] = [];
  for (const hit of hits) {
    if (hit.length > 1) {
      for (let i = 1; i < hit.length; i++) {
        if (hit[i]) values.push(String(hit[i]));
      }
    } else if (hit[0]) {
      values.push(String(hit[0]));
    }
  }
  return uniqueLimited(values);
}

function allMatches(text: string, pattern: RegExp): RegExpExecArray[] {
  const out: RegExpExecArray[] = [];
  let m: RegExpExecArray | null;
  const re = new RegExp(pattern.source, pattern.flags.includes("g") ? pattern.flags : pattern.flags + "g");
  while ((m = re.exec(text)) !== null) {
    out.push(m);
    if (m.index === re.lastIndex) re.lastIndex++;
  }
  return out;
}

function annotationValues(text: string, names: string): string[] {
  const values: string[] = [];
  const re = new RegExp(`@(?:${names})\\s*(?:\\(([^)]*)\\))?`, "gs");
  for (const m of allMatches(text, re)) {
    const args = m[1];
    if (!args) {
      values.push("");
      continue;
    }
    for (const q of allMatches(args, /['"]([^'"]+)['"]/g)) values.push(q[1]!);
    for (const v of allMatches(args, /\bvalue\s*=\s*([^,\n)]+)/g)) values.push(v[1]!.trim());
  }
  return uniqueLimited(values.filter((v) => v !== undefined) as string[]);
}

function annotationValuesInCode(text: string, masked: string, names: string): string[] {
  const values: string[] = [];
  const re = new RegExp(`@(?:${names})\\s*(?:\\([^)]*\\))?`, "gs");
  for (const m of allMatches(masked, re)) {
    values.push(...annotationValues(text.slice(m.index!, m.index! + m[0].length), names));
  }
  return uniqueLimited(values);
}

function quotedLiteralAt(text: string, quoteIndex: number): string {
  if (quoteIndex < 0 || quoteIndex >= text.length) return "";
  const quote = text[quoteIndex];
  if (quote !== "'" && quote !== '"') return "";
  const value: string[] = [];
  let i = quoteIndex + 1;
  while (i < text.length) {
    const c = text[i]!;
    if (c === "\\" && i + 1 < text.length) {
      value.push(text[i + 1]!);
      i += 2;
      continue;
    }
    if (c === quote) return value.join("");
    if (c === "\n" || c === "\r") return "";
    value.push(c);
    i++;
  }
  return "";
}

/** Mask comments and string contents (preserves positions), ported from backend.py. */
export function maskCommentsAndStrings(text: string): string {
  const chars = [...text];
  const masked = [...text];
  let i = 0;
  let state: "code" | "line-comment" | "block-comment" | "string" = "code";
  let quote = "";
  while (i < chars.length) {
    const cur = chars[i]!;
    const next = chars[i + 1] ?? "";
    if (state === "code") {
      if (cur === "/" && next === "/") {
        masked[i] = masked[i + 1] = " ";
        i += 2;
        state = "line-comment";
        continue;
      }
      if (cur === "/" && next === "*") {
        masked[i] = masked[i + 1] = " ";
        i += 2;
        state = "block-comment";
        continue;
      }
      if (cur === "'" || cur === '"' || cur === "`") {
        quote = cur;
        state = "string";
        i++;
        continue;
      }
      i++;
      continue;
    }
    if (state === "line-comment") {
      if (cur === "\n" || cur === "\r") state = "code";
      else masked[i] = " ";
      i++;
      continue;
    }
    if (state === "block-comment") {
      if (cur === "*" && next === "/") {
        masked[i] = masked[i + 1] = " ";
        i += 2;
        state = "code";
        continue;
      }
      if (cur !== "\n" && cur !== "\r") masked[i] = " ";
      i++;
      continue;
    }
    // string
    if (cur === "\\") {
      masked[i] = " ";
      if (chars[i + 1] !== "\n" && chars[i + 1] !== "\r") {
        masked[i + 1] = " ";
        i += 2;
      } else {
        i++;
      }
      continue;
    }
    if (cur === quote) {
      state = "code";
      quote = "";
      i++;
      continue;
    }
    if (cur !== "\n" && cur !== "\r") masked[i] = " ";
    i++;
  }
  return masked.join("");
}

function pythonFacts(text: string): {
  parser: string;
  methods: string[];
  classes: string[];
  routes: string[];
  frameworks: string[];
  apiClass: boolean;
} {
  // Keep the Python scanner contract without requiring Python at runtime:
  // resolve framework imports, constructor aliases, route owners and Django
  // class bases before accepting route-like syntax. This avoids treating
  // examples in strings or an unbound `@app.get` decorator as real APIs.
  if (!pythonSyntaxLooksValid(text)) {
    return {
      parser: "python-syntax-error",
      methods: [],
      classes: [],
      routes: [],
      frameworks: [],
      apiClass: false,
    };
  }
  const methods = (text.match(/\b(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(/g) || [])
    .map((m) => m.match(/def\s+(\w+)/)![1]!);
  const classes = (text.match(/\bclass\s+([A-Za-z_]\w*)\s*[(:]/g) || []).map((m) => m.match(/class\s+(\w+)/)![1]!);
  const routes: string[] = [];
  const frameworks: string[] = [];
  const importedNames = new Map<string, string>();
  const moduleAliases = new Map<string, string>();
  const routeObjects = new Map<string, string>();
  for (const match of allMatches(text, /^\s*import\s+([A-Za-z_][\w.]*)\s*(?:as\s+([A-Za-z_]\w*))?/gm)) {
    const moduleName = match[1]!;
    moduleAliases.set(match[2] ?? moduleName.split(".")[0]!, moduleName);
  }
  for (const match of allMatches(text, /^\s*from\s+([A-Za-z_][\w.]*)\s+import\s+([^\n#]+)/gm)) {
    for (const rawItem of match[2]!.split(",")) {
      const imported = /^\s*([A-Za-z_]\w*)\s*(?:as\s+([A-Za-z_]\w*))?\s*$/.exec(rawItem);
      if (imported) importedNames.set(imported[2] ?? imported[1]!, `${match[1]}.${imported[1]}`);
    }
  }
  const resolveName = (value: string): string => {
    const parts = value.split(".");
    const head = parts.shift()!;
    const resolved = importedNames.get(head) ?? moduleAliases.get(head) ?? head;
    return [resolved, ...parts].join(".");
  };
  for (const match of allMatches(text, /^\s*([A-Za-z_]\w*)\s*(?::[^=\n]+)?=\s*([A-Za-z_][\w.]*)\s*\(/gm)) {
    const constructor = resolveName(match[2]!);
    if (["fastapi.FastAPI", "fastapi.APIRouter", "flask.Flask", "flask.Blueprint"].includes(constructor)) {
      routeObjects.set(match[1]!, constructor);
    }
  }
  for (const m of allMatches(text, /^\s*@([A-Za-z_]\w*)\.(get|post|put|delete|patch|route)\s*\(\s*(['"])([^'"]+)\3/gm)) {
    if (!routeObjects.has(m[1]!)) continue;
    routes.push(m[4]!);
    frameworks.push("FastAPI/Flask");
  }
  for (const m of allMatches(text, /\b([A-Za-z_][\w.]*)\s*\(\s*['"]([^'"]+)['"]/g)) {
    const callable = resolveName(m[1]!);
    if (callable === "django.urls.path" || callable === "django.urls.re_path") {
      routes.push(m[2]!);
      frameworks.push("Django");
    }
  }
  let apiClass = false;
  for (const match of allMatches(text, /\bclass\s+[A-Za-z_]\w*\s*\(([^)]*)\)/g)) {
    const bases = match[1]!.split(",").map((base) => resolveName(base.trim()));
    if (bases.some((base) =>
      base.startsWith("rest_framework.") &&
      ["APIView", "ViewSet", "ModelViewSet", "GenericViewSet"].includes(base.split(".").at(-1) ?? "")
    )) {
      frameworks.push("Django");
      apiClass = true;
    }
  }
  return {
    parser: "python-ast",
    methods: uniqueLimited(methods),
    classes: uniqueLimited(classes),
    routes: uniqueLimited(routes),
    frameworks: uniqueLimited(frameworks),
    apiClass,
  };
}

function pythonSyntaxLooksValid(text: string): boolean {
  let quote = "";
  let triple = false;
  let escaped = false;
  const stack: string[] = [];
  const pairs: Record<string, string> = { ")": "(", "]": "[", "}": "{" };
  for (let index = 0; index < text.length; index++) {
    const char = text[index]!;
    if (quote) {
      if (triple && text.slice(index, index + 3) === quote.repeat(3)) {
        quote = "";
        triple = false;
        index += 2;
      } else if (!triple && escaped) {
        escaped = false;
      } else if (!triple && char === "\\") {
        escaped = true;
      } else if (!triple && char === quote) {
        quote = "";
      }
      continue;
    }
    if (char === "#") {
      while (index < text.length && text[index] !== "\n") index++;
      continue;
    }
    if (char === "'" || char === '"') {
      quote = char;
      triple = text.slice(index, index + 3) === char.repeat(3);
      if (triple) index += 2;
      continue;
    }
    if ("([{".includes(char)) stack.push(char);
    else if (char in pairs && stack.pop() !== pairs[char]) return false;
  }
  if (quote || stack.length) return false;
  return !/(?:^|\n)\s*(?:async\s+)?def\s+[A-Za-z_]\w*\s*\([^)]*$/.test(text);
}

function detectBackendFramework(path: string, code: string, astFacts: ReturnType<typeof pythonFacts> | null): string {
  const suffix = extname(path).toLowerCase();
  if (
    (suffix === ".java" || suffix === ".kt") &&
    /@(RestController|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|Service|Repository|Mapper|Transactional|Scheduled|MessageListener|KafkaListener|RabbitListener)\b/.test(
      code
    )
  )
    return "Spring";
  if (
    (suffix === ".ts" || suffix === ".js") &&
    /@(Controller|Get|Post|Put|Delete|Patch|Injectable|UseGuards|MessagePattern|Cron)\b/.test(code)
  )
    return "NestJS";
  if (
    (suffix === ".ts" || suffix === ".js") &&
    /\b(router|app|server)\.(get|post|put|delete|patch|use|route)\s*\(/.test(code)
  )
    return "Express/Koa/Fastify";
  if (suffix === ".py" && astFacts && astFacts.frameworks.length) return astFacts.frameworks[0]!;
  if (suffix === ".go" && /\b(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['"]/.test(code)) return "Go Gin";
  if (path.endsWith(".xml")) return "Mapper XML";
  return "Unknown";
}

function extractBackendEndpoints(
  text: string,
  suffix: string,
  astFacts: ReturnType<typeof pythonFacts> | null,
  masked?: string
): string[] {
  const endpoints: string[] = [...(astFacts?.routes ?? [])];
  const code = masked ?? text;
  if (suffix === ".java" || suffix === ".kt") {
    endpoints.push(...annotationValuesInCode(text, code, "RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping"));
  }
  if (suffix === ".ts" || suffix === ".js") {
    endpoints.push(...annotationValuesInCode(text, code, "Controller"));
    const routeRe = /\b(?:router|app|server)\.(?:get|post|put|delete|patch|use|route)\s*\(\s*(['"])/g;
    for (const m of allMatches(code, routeRe)) {
      endpoints.push(quotedLiteralAt(text, m.index! + m[0].length - 1));
    }
  }
  if (suffix === ".go") {
    endpoints.push(...(text.match(/\b(?:GET|POST|PUT|DELETE|PATCH)\s*\(\s*['"]([^'"]+)['"]/g) || []).map((s) => s.match(/['"]([^'"]+)['"]/)![1]!));
    endpoints.push(...(text.match(/\b(?:HandleFunc|Handle)\s*\(\s*['"]([^'"]+)['"]/g) || []).map((s) => s.match(/['"]([^'"]+)['"]/)![1]!));
  }
  return uniqueLimited(endpoints.map((s) => s.trim()).filter(Boolean));
}

function extractBackendMethods(text: string, suffix: string, astFacts: ReturnType<typeof pythonFacts> | null): string[] {
  if (suffix === ".py" && astFacts && astFacts.methods.length) return uniqueLimited(astFacts.methods);
  const names: string[] = [];
  if (suffix === ".java" || suffix === ".kt") {
    for (const m of allMatches(text, /\b(?:public|private|protected)\s+(?:static\s+)?(?:[\w<>\[\], ?]+\s+)+([A-Za-z_$][\w$]*)\s*\(/g)) {
      names.push(m[1]!);
    }
  }
  if (suffix === ".ts" || suffix === ".js") {
    for (const m of allMatches(text, /\b(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*[{:]?/g)) names.push(m[1]!);
  }
  if (suffix === ".py") {
    for (const m of allMatches(text, /\bdef\s+([A-Za-z_]\w*)\s*\(/g)) names.push(m[1]!);
  }
  if (suffix === ".go") {
    for (const m of allMatches(text, /\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(/g)) names.push(m[1]!);
  }
  return uniqueLimited(names.filter((n) => !["if", "for", "while", "switch", "catch"].includes(n)));
}

function extractBackendFields(text: string, suffix: string): string[] {
  const fields: string[] = [];
  if (suffix === ".java" || suffix === ".kt") {
    for (const m of allMatches(text, /\b(?:private|protected|public)\s+(?:final\s+)?[\w<>\[\], ?]+\s+([A-Za-z_$][\w$]*)\s*[;=]/g)) fields.push(m[1]!);
  }
  if (suffix === ".ts" || suffix === ".js") {
    for (const m of allMatches(text, /\b([A-Za-z_$][\w$]*)\??\s*:\s*(?:string|number|boolean|Date|Array|Record|[A-Z][\w<>]*)/g)) fields.push(m[1]!);
  }
  if (suffix === ".py") {
    for (const m of allMatches(text, /^\s*([A-Za-z_]\w*)\s*:\s*[\w\[\]."']+/gm)) fields.push(m[1]!);
  }
  if (suffix === ".go") {
    for (const m of allMatches(text, /^\s*([A-Z][A-Za-z0-9_]*)\s+[\w\[\]*.]+/gm)) fields.push(m[1]!);
  }
  return uniqueLimited(fields);
}

function extractRepositoryMethods(text: string, suffix: string, astFacts: ReturnType<typeof pythonFacts> | null): string[] {
  const names = extractBackendMethods(text, suffix, astFacts);
  if (suffix === ".xml") {
    for (const m of allMatches(text, /\b(?:select|insert|update|delete)\b[^>]*\bid\s*=\s*['"]([^'"]+)['"]/gi)) names.push(m[1]!);
  }
  for (const m of allMatches(text, /\b(?:find|query|get|select|insert|update|delete|save|remove)[A-Z][A-Za-z0-9_]*\b/g)) names.push(m[0]!);
  return uniqueLimited(names, 50);
}

function extractSqlOps(text: string): string[] {
  return uniqueLimited(
    (text.match(/\b(SELECT|INSERT|UPDATE|DELETE|MERGE)\b/gi) || []).map((s) => s.toUpperCase()),
    10
  );
}

function extractConfigKeys(text: string, suffix: string): string[] {
  const keys: string[] = [];
  if (suffix === ".properties") {
    for (const m of allMatches(text, /^\s*([A-Za-z0-9_.-]+)\s*=/gm)) keys.push(m[1]!);
  } else if (suffix === ".yaml" || suffix === ".yml") {
    for (const m of allMatches(text, /^\s*([A-Za-z0-9_.-]+)\s*:/gm)) keys.push(m[1]!);
  } else if (suffix === ".xml") {
    for (const m of allMatches(text, /\b(?:id|name|key)\s*=\s*['"]([^'"]+)['"]/g)) keys.push(m[1]!);
  }
  for (const m of allMatches(text, /@Value\s*\(\s*['"]\$\{([^}:]+)/g)) keys.push(m[1]!);
  for (const m of allMatches(text, /@ConfigurationProperties\s*\(\s*(?:prefix\s*=\s*)?['"]([^'"]+)['"]/g)) keys.push(m[1]!);
  for (const m of allMatches(text, /process\.env\.([A-Z0-9_]+)/g)) keys.push(m[1]!);
  return uniqueLimited(keys, 60);
}

function extractSignals(text: string, patterns: RegExp[], limit = 30): string[] {
  const values: string[] = [];
  for (const pattern of patterns) {
    for (const m of allMatches(text, pattern)) values.push(...flattenRegexHits([m]));
  }
  return uniqueLimited(values.filter(Boolean).map((v) => v.trim()), limit);
}

function extractPermissionSignals(text: string): string[] {
  return extractSignals(text, [
    /@(?:PreAuthorize|PostAuthorize|Secured|RolesAllowed|RequiresPermissions|SaCheckPermission|PermitAll|UseGuards)\b[^\n\r{;]*/g,
    /\b(?:hasPermission|checkPermission|checkAuth|authorize|isAuthorized)\s*\(/g,
    /\b(?:jwt|token|session|principal|SecurityContext|AuthGuard|CanActivate)\b/g,
  ]);
}

function extractTransactionSignals(text: string): string[] {
  return extractSignals(text, [
    /@Transactional\b(?:\([^)]*\))?/g,
    /\b(?:TransactionTemplate|DataSourceTransactionManager|EntityManager|UnitOfWork)\b/g,
    /\b(?:transaction|withTransaction|db\.transaction|sequelize\.transaction)\s*\(/g,
  ]);
}

function extractRemoteCallSignals(text: string): string[] {
  return extractSignals(text, [
    /@FeignClient\b(?:\([^)]*\))?/g,
    /@(?:DubboReference|Reference|GrpcClient)\b(?:\([^)]*\))?/g,
    /\b(?:RestTemplate|WebClient|Feign|HttpClient|OkHttpClient|ServiceMeshAdapter|grpc|requests\.|axios|fetch)\b/g,
    /\b(?:call|invoke|proxy|exchange|getForObject|postForObject)\s*\(/g,
  ]);
}

function extractMessageJobSignals(text: string): string[] {
  return extractSignals(text, [
    /@(?:Scheduled|KafkaListener|RabbitListener|JmsListener|MessageListener|SqsListener|EventListener|Cron|MessagePattern)\b(?:\([^)]*\))?/g,
    /\b(?:Queue|Topic|Consumer|Producer|BullMQ|agenda|cron|schedule)\b/g,
  ]);
}

function extractErrorCodeSignals(text: string): string[] {
  const values: string[] = [];
  for (const m of allMatches(text, /\b(?:ErrorCode|ErrCode|ResultCode|ResponseCode)\.([A-Z0-9_]+)/g)) values.push(m[1]!);
  for (const m of allMatches(text, /\b([A-Z][A-Z0-9_]*(?:_ERROR|_FAILED|_FAIL|_INVALID|_NOT_FOUND|_DENIED))\b/g)) values.push(m[1]!);
  for (const m of allMatches(text, /['"]([A-Z]\d{3,}|[BE]\d{3,}|ERR[_-][A-Z0-9_-]+)['"]/g)) values.push(m[1]!);
  for (const m of allMatches(text, /\bthrow\s+new\s+([A-Za-z_$][\w$]*(?:Exception|Error))\b/g)) values.push(m[1]!);
  for (const m of allMatches(text, /@ResponseStatus\s*\(([^)]*)\)/g)) values.push(m[1]!);
  return uniqueLimited(values.filter(Boolean).map((v) => v.trim()), 40);
}

function extractExportedFunctions(text: string): string[] {
  const names = (text.match(/\bexport\s+const\s+([A-Za-z_$][\w$]*)\s*=/g) || []).map((m) => m.match(/const\s+(\w+)/)![1]!);
  names.push(...(text.match(/\bexport\s+function\s+([A-Za-z_$][\w$]*)\s*\(/g) || []).map((m) => m.match(/function\s+(\w+)/)![1]!));
  return uniqueLimited(names, 80);
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

/** Scan a single backend file, returning categorized facts. Mirrors scan_backend_file. */
export function scanBackendFile(relPath: string, text: string, configuredEntrypoints: string[] = []): BackendFacts {
  const suffix = extname(relPath).toLowerCase();
  const lower = relPath.toLowerCase();
  const facts: BackendFacts = {
    apis: [],
    services: [],
    dataTypes: [],
    repositories: [],
    configs: [],
    permissionChecks: [],
    transactions: [],
    remoteCalls: [],
    messagesJobs: [],
    errorCodes: [],
    utilities: [],
    candidateEntrypoints: [],
    testFixtures: [],
  };
  const astFacts = suffix === ".py" ? pythonFacts(text) : null;
  const codeText =
    suffix === ".java" || suffix === ".kt" || suffix === ".ts" || suffix === ".js"
      ? maskCommentsAndStrings(text)
      : text;
  const mapperXml = suffix === ".xml" && (text.toLowerCase().includes("<mapper") || lower.includes("/mapper"));
  const javaRoutePattern = /@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|MessageListener|Scheduled)/;
  const jsRoutePattern = /\b(router|app|server)\.(get|post|put|delete|patch|use|route)\s*\(|@(Controller|Get|Post|Put|Delete|Patch|MessagePattern|Cron)\b/;
  const routeSignals =
    suffix === ".java" || suffix === ".kt"
      ? flattenRegexHits(allMatches(codeText, javaRoutePattern))
      : suffix === ".ts" || suffix === ".js"
        ? flattenRegexHits(allMatches(codeText, jsRoutePattern))
        : [];
  const framework = detectBackendFramework(relPath, codeText, astFacts);
  if (routeSignals.length || configuredEntrypoints.length || (astFacts?.routes.length ?? 0) || astFacts?.apiClass) {
    facts.apis.push({
      path: relPath,
      framework,
      parser: astFacts?.parser ?? "regex-fallback",
      signals: [...new Set([...routeSignals, ...configuredEntrypoints])].sort().slice(0, 20),
      endpoints: extractBackendEndpoints(text, suffix, astFacts, codeText),
      methods: extractBackendMethods(text, suffix, astFacts).slice(0, 20),
    });
  }
  const serviceName = /(?:Service|Manager|UseCase|Facade)\.(?:java|kt|ts|js|py)$|(?:^|\/)[^/]+[._-](?:service|manager|usecase|facade)\.(?:ts|js|py)$/i.test(relPath);
  const serviceAnnotation =
    (suffix === ".java" || suffix === ".kt") && codeText.includes("@Service") ||
    (suffix === ".ts" || suffix === ".js") && codeText.includes("@Injectable");
  if (serviceName || serviceAnnotation) {
    facts.services.push({
      name: stem(relPath),
      path: relPath,
      framework,
      parser: astFacts?.parser ?? "regex-fallback",
      methods: extractBackendMethods(text, suffix, astFacts).slice(0, 30),
      transactions: extractTransactionSignals(text),
      remoteCalls: extractRemoteCallSignals(text),
      permissionSignals: extractPermissionSignals(text),
    });
  }
  if (/(?:DTO|Dto|VO|Entity|Model|Schema)\.(?:java|kt|ts|js|py)$/.test(relPath) || /@(Entity|Table|Column)\b/.test(text)) {
    facts.dataTypes.push({
      name: stem(relPath),
      path: relPath,
      kind: /@(Entity|Table)\b/.test(text) || stem(relPath).endsWith("Entity") ? "Entity" : "DTO/VO/Model",
      fields: extractBackendFields(text, suffix).slice(0, 40),
      annotations: [...new Set((text.match(/@(Entity|Table|Column|NotNull|NotBlank|Size|Schema|JsonProperty)\b/g) || []).map((s) => s))].slice(0, 20),
    });
  }
  if (/(?:Repository|Mapper|Dao|DAO)\.(?:java|kt|ts|js|py)$/.test(relPath) || /@(Repository|Mapper)\b/.test(text) || mapperXml) {
    facts.repositories.push({
      name: stem(relPath),
      path: relPath,
      kind: /Mapper\.(?:java|kt|ts|js|py|xml)$/.test(relPath) || text.includes("@Mapper") || mapperXml ? "Mapper" : "Repository/DAO",
      methods: extractRepositoryMethods(text, suffix, astFacts).slice(0, 50),
      sqlOps: extractSqlOps(text),
    });
  }
  if (suffix === ".yaml" || suffix === ".yml" || suffix === ".properties" || (suffix === ".xml" && !mapperXml) || lower.includes("/config")) {
    facts.configs.push({ path: relPath, keys: extractConfigKeys(text, suffix), kind: suffix.slice(1) || "config" });
  }
  const signals: Record<string, string[]> = {
    permissionChecks: extractPermissionSignals(text),
    transactions: extractTransactionSignals(text),
    remoteCalls: extractRemoteCallSignals(text),
    messagesJobs: extractMessageJobSignals(text),
    errorCodes: extractErrorCodeSignals(text),
  };
  for (const [key, values] of Object.entries(signals)) {
    if (values.length) {
      (facts[key as BackendFactKey] as unknown[]).push({ path: relPath, signals: values, level: "candidate" });
    }
  }
  if (/(^|\/)(utils?|common|helpers?|support)\//.test(lower) && BACKEND_SUFFIXES.has(suffix)) {
    facts.utilities.push({
      name: stem(relPath),
      path: relPath,
      exports: extractExportedFunctions(text) || extractBackendMethods(text, suffix, astFacts).slice(0, 30),
    });
  }
  if (!routeSignals.length && !configuredEntrypoints.length && !(astFacts?.routes.length) && !astFacts?.apiClass && /(?:handler|endpoint|facade|adapter|action)/.test(lower)) {
    facts.candidateEntrypoints.push({ path: relPath, reason: "路径/名称暗示非标准入口点", level: "candidate" });
  }
  if (facts.apis.length && /(^|\/)(?:tests?|__tests__|fixtures?)(\/|$)/.test(lower)) {
    facts.testFixtures = facts.apis.map((item) => ({ ...(item as object), classification: "test-fixture" }));
    facts.apis = [];
  }
  facts.scanMode = astFacts?.parser ?? "regex-fallback";
  return facts;
}

export interface ScanBackendResult extends Omit<BackendFacts, "scanMode"> {
  scanModes: string[];
}

/** Scan a list of backend files, aggregating facts (mirrors scan_backend). */
export function scanBackend(
  files: { path: string; text?: string; readText?: () => string; signature?: string }[],
  config?: Record<string, unknown>,
  cache?: import("./core.js").IncrementalScanCache
): ScanBackendResult {
  const groups: Record<string, unknown[]> = {
    apis: [],
    services: [],
    dataTypes: [],
    repositories: [],
    configs: [],
    permissionChecks: [],
    transactions: [],
    remoteCalls: [],
    messagesJobs: [],
    errorCodes: [],
    utilities: [],
    candidateEntrypoints: [],
    testFixtures: [],
  };
  const parserModes = new Set<string>();
  const backendConfig = (config?.backend as Record<string, unknown> | undefined) ?? {};
  const entrypointRules = Array.isArray(backendConfig.entrypointRules)
    ? backendConfig.entrypointRules as Record<string, unknown>[]
    : [];
  for (const file of files) {
    const { path } = file;
    const suffix = extname(path).toLowerCase();
    if (!BACKEND_SUFFIXES.has(suffix) && !CONFIG_SUFFIXES.has(suffix)) continue;
    let facts = file.signature && cache
      ? cache.get(path, "backend", file.signature) as BackendFacts | null
      : null;
    if (facts) {
      for (const key of Object.keys(groups) as (keyof typeof groups)[]) {
        (groups[key] as unknown[]).push(...((facts[key as BackendFactKey] as unknown[]) ?? []));
      }
      parserModes.add(facts.scanMode ?? "regex-fallback");
      continue;
    }
    const text = file.text ?? file.readText?.() ?? "";
    const configuredEntrypoints: string[] = [];
    for (let index = 0; index < entrypointRules.length; index++) {
      const rule = entrypointRules[index]!;
      const type = String(rule.type ?? "");
      const pattern = String(rule.pattern ?? "");
      let matched = false;
      if (type === "path") {
        matched = simpleMatch(pattern, path);
      } else if (pattern) {
        try {
          matched = new RegExp(pattern).test(text);
        } catch {
          matched = false;
        }
      }
      if (matched) configuredEntrypoints.push(`config:${type}:${index + 1}`);
    }
    facts = scanBackendFile(path, text, configuredEntrypoints);
    if (file.signature && cache) cache.put(path, "backend", file.signature, facts);
    for (const key of Object.keys(groups) as (keyof typeof groups)[]) {
      (groups[key] as unknown[]).push(...((facts[key as BackendFactKey] as unknown[]) ?? []));
    }
    parserModes.add(facts.scanMode ?? "regex-fallback");
  }
  return { ...groups, scanModes: [...parserModes].sort() } as ScanBackendResult;
}
