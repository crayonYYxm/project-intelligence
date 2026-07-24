import { existsSync, readFileSync, realpathSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { isAbsolute, relative, resolve } from "node:path";
import { RequirementError } from "../errors.js";

export interface DocumentManifest {
  requirementId: string;
  requirementName: string;
  ticketKind: string;
  externalApiImpact: { confirmed: boolean; value: boolean };
  acceptanceCriteria: { id: string; description: string; status?: string }[];
}

export interface DocumentValidation {
  ok: true;
  kind: string;
  schema: string;
  errors: [];
  warnings: string[];
  acceptanceIds?: string[];
  acceptanceCriteria?: { id: string; description: string }[];
  documentIdentity?: Record<string, unknown>;
  blockingIssues?: string[];
  sourceEvidence?: { path: string; symbols: string[] }[];
  validatedAt: string;
}

interface Heading {
  level: number;
  name: string;
  normalized: string;
  start: number;
  end: number;
}

const PLACEHOLDER_RE = /\b(?:TODO|TBD|FIXME)\b|※[^※\n]+※|待填写|待补充|请填写|在此填写/i;
const HEADING_RE = /^\s*(#{1,6})\s+(?:(?:\d+(?:\\?\.\d+)*)\\?[.、]?\s+)?(.+?)\s*$/;
const AC_RE = /^\s*[-*]\s*(AC-\d{2,})\s*[:：]\s*(.*?)\s*$/i;

const REQUIREMENT_SECTIONS = [
  "文档信息",
  "背景与现状",
  "目标",
  "业务场景",
  "范围",
  "非目标",
  "业务规则与异常边界",
  "验收标准",
  "外部接口影响",
  "待确认事项",
];

const BUG_SECTIONS = ["复现条件", "当前行为", "预期行为"];
const DESIGN_REQUIREMENT_SECTIONS = [
  "需求问题概述",
  "需求描述",
  "需求提出部门及联系人",
  "电信需求负责人",
  "需求适用范围",
  "需求期望完成时间",
  "设计相关选项",
  "场景分析",
  "风险考虑",
  "实现方案",
  "数据模型",
  "表结构设计",
  "新增模型汇总",
  "表结构描述",
  "建表语句",
  "表数据转储策略",
  "界面设计",
];
const DESIGN_BUG_SECTIONS = [
  "bug现象",
  "原因分析",
  "修复方案",
  "改造思路",
  "新旧代码对照",
  "逻辑变更说明",
  "影响范围",
  "风险评估",
];

const SOURCE_SUFFIXES = new Set([
  ".c", ".cc", ".conf", ".cpp", ".cs", ".css", ".go", ".gradle", ".h", ".hpp", ".html",
  ".java", ".js", ".json", ".jsx", ".kt", ".kts", ".less", ".m", ".mm", ".php", ".properties",
  ".py", ".rb", ".rs", ".scss", ".sql", ".swift", ".ts", ".tsx", ".vue", ".wxml", ".wxss",
  ".xml", ".yaml", ".yml",
]);
const SOURCE_LINK_RE = /(?:中的?|内的?|定义的?|函数|方法|类|组件|符号|接口|调用)/;

export function resolveRepositoryFile(root: string, value: string): { path: string; relativePath: string } {
  const raw = String(value ?? "").trim();
  if (!raw || raw.includes("\0")) throw new RequirementError("产物路径不能为空。");
  const rootReal = realpathSync(root);
  const candidate = isAbsolute(raw) ? resolve(raw) : resolve(root, raw);
  if (!existsSync(candidate)) throw new RequirementError(`产物文件不存在：${value}`);
  const fileReal = realpathSync(candidate);
  const relativePath = relative(rootReal, fileReal).replaceAll("\\", "/");
  if (relativePath === ".." || relativePath.startsWith("../") || isAbsolute(relativePath)) {
    throw new RequirementError(`产物文件必须位于项目目录内：${value}`);
  }
  const stat = statSync(fileReal);
  if (!stat.isFile() || stat.size <= 0 || !fileReal.toLowerCase().endsWith(".md")) {
    throw new RequirementError(`交付文档必须是仓库内非空 Markdown 文件：${value}`);
  }
  return { path: fileReal, relativePath };
}

export function validateDeliveryDocument(
  manifest: DocumentManifest,
  type: string,
  content: string
): DocumentValidation {
  if (type === "requirement") return validateRequirement(manifest, content);
  if (type === "design") return validateDesign(manifest, content);
  if (type === "plan") return validatePlan(manifest, content);
  if (type === "closure") return validateClosure(manifest, content);
  throw new RequirementError(`不支持的交付文档类型：${type}`);
}

/**
 * Validate a delivery document with repository context. Design documents use
 * this stronger entry point so source claims cannot be satisfied by prose,
 * comments, strings, missing files, or symbols outside the repository.
 */
export function validateDeliveryDocumentInRepository(
  root: string,
  manifest: DocumentManifest,
  type: string,
  content: string
): DocumentValidation {
  const validation = validateDeliveryDocument(manifest, type, content);
  if (type === "design") validation.sourceEvidence = validateSourceEvidence(root, content);
  return validation;
}

function normalizeHeading(value: string): string {
  return value
    .replace(/[*_~]/g, "")
    .replace(/^\d+(?:\\?\.\d+)*\\?[.、]?\s*/, "")
    .replace(/[\s，,、/／:：\-—_]+/g, "")
    .toLowerCase();
}

function parseHeadings(lines: string[]): Heading[] {
  const headings: Heading[] = [];
  for (let index = 0; index < lines.length; index++) {
    const match = HEADING_RE.exec(lines[index] ?? "");
    if (!match) continue;
    headings.push({
      level: match[1]!.length,
      name: match[2]!.trim(),
      normalized: normalizeHeading(match[2]!),
      start: index,
      end: lines.length,
    });
  }
  for (let index = 0; index < headings.length; index++) {
    for (const next of headings.slice(index + 1)) {
      if (next.level <= headings[index]!.level) {
        headings[index]!.end = next.start;
        break;
      }
    }
  }
  return headings;
}

function section(lines: string[], headings: Heading[], name: string): string {
  const target = headings.find((heading) => heading.normalized === normalizeHeading(name));
  if (!target) return "";
  return lines.slice(target.start + 1, target.end).join("\n").trim();
}

function meaningful(value: string): boolean {
  return value.split(/\r?\n/).some((line) => /[A-Za-z0-9\u4e00-\u9fff]/.test(line.trim()));
}

function requireSections(lines: string[], headings: Heading[], names: string[], errors: string[]): void {
  for (const name of names) {
    const body = section(lines, headings, name);
    if (!body) errors.push(`缺少必要章节：${name}。`);
    else if (!meaningful(body)) errors.push(`章节缺少有效内容：${name}。`);
  }
}

function plain(value: string): string {
  return value.replace(/[*_~`]/g, "").replace(/\s+/g, " ").trim();
}

function splitSourceReference(value: string): { path: string; symbol?: string } | null {
  let clean = value.trim().replace(/^[<[\]({}'"]+|[>\])}'}"]+$/g, "");
  if (!clean || clean.includes("\n") || clean.includes("\0")) return null;
  clean = clean.replace(/#L\d+(?:-L\d+)?$/i, "").replace(/:\d+(?::\d+)?$/, "");
  let pathValue = clean;
  let symbol: string | undefined;
  for (const separator of ["::", "#"]) {
    const index = clean.indexOf(separator);
    if (index < 0) continue;
    const candidate = clean.slice(0, index);
    if (SOURCE_SUFFIXES.has(ext(candidate))) {
      pathValue = candidate;
      symbol = clean.slice(index + separator.length).trim() || undefined;
      break;
    }
  }
  if (!symbol && clean.includes(":") && !/^[A-Za-z]:[\\/]/.test(clean)) {
    const index = clean.lastIndexOf(":");
    const candidate = clean.slice(0, index);
    const attached = clean.slice(index + 1);
    if (SOURCE_SUFFIXES.has(ext(candidate)) && !/^\d+$/.test(attached)) {
      pathValue = candidate;
      symbol = attached.trim() || undefined;
    }
  }
  if (!SOURCE_SUFFIXES.has(ext(pathValue)) || /\s/.test(pathValue)) return null;
  return symbol ? { path: pathValue, symbol } : { path: pathValue };
}

function ext(value: string): string {
  const match = value.toLowerCase().match(/(\.[a-z0-9]+)$/);
  return match?.[1] ?? "";
}

function symbolName(value: string): string {
  return value.trim().replace(/\(\)$/, "").split("(", 1)[0]!.trim().split(/\.|::/).at(-1) ?? "";
}

function maskCommentsAndStrings(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, " ")
    .replace(/\/\/[^\n]*|#[^\n]*/g, " ")
    .replace(/(['"`])(?:\\.|(?!\1)[\s\S])*?\1/g, " ");
}

function sourceContainsSymbol(source: string, symbol: string): boolean {
  const name = symbolName(symbol);
  if (!/^[A-Za-z_$][\w$-]*$/.test(name)) return false;
  return new RegExp(`(?<![\\w$])${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?![\\w$])`).test(
    maskCommentsAndStrings(source)
  );
}

export function validateSourceEvidence(root: string, content: string): { path: string; symbols: string[] }[] {
  const rootReal = realpathSync(root);
  const matches = [...content.matchAll(/`([^`\n]+)`/g)];
  const evidence = new Map<string, Set<string>>();
  const errors: string[] = [];
  for (let index = 0; index < matches.length; index++) {
    const match = matches[index]!;
    const parsed = splitSourceReference(match[1]!);
    if (!parsed) continue;
    const symbols = new Set<string>();
    if (parsed.symbol) symbols.add(parsed.symbol);
    const following = matches[index + 1];
    if (following) {
      const between = content.slice((match.index ?? 0) + match[0].length, following.index ?? 0);
      const next = splitSourceReference(following[1]!);
      const candidate = following[1]!.trim();
      if (
        !between.includes("\n")
        && between.length <= 80
        && !next
        && SOURCE_LINK_RE.test(between)
        && /^[A-Za-z_$][\w$.:()<>-]*$/.test(candidate)
      ) {
        symbols.add(candidate);
      }
    }
    if (isAbsolute(parsed.path) || parsed.path.replaceAll("\\", "/").split("/").includes("..")) {
      errors.push(`源码证据必须是仓库内相对路径：${parsed.path}。`);
      continue;
    }
    const candidate = resolve(rootReal, parsed.path);
    if (!existsSync(candidate)) {
      errors.push(`源码证据路径不存在：${parsed.path}。`);
      continue;
    }
    let path: string;
    try {
      path = realpathSync(candidate);
    } catch {
      errors.push(`源码证据路径无法读取：${parsed.path}。`);
      continue;
    }
    const relativePath = relative(rootReal, path).replaceAll("\\", "/");
    if (relativePath === ".." || relativePath.startsWith("../") || isAbsolute(relativePath)) {
      errors.push(`源码证据路径越出项目目录：${parsed.path}。`);
      continue;
    }
    if (!statSync(path).isFile()) {
      errors.push(`源码证据必须指向真实文件：${parsed.path}。`);
      continue;
    }
    const source = readFileSync(path, "utf8");
    const accumulated = evidence.get(relativePath) ?? new Set<string>();
    for (const symbol of symbols) {
      if (!sourceContainsSymbol(source, symbol)) {
        errors.push(`源码证据符号不存在：${relativePath} 中未找到 ${symbol}。`);
      } else {
        accumulated.add(symbol);
      }
    }
    evidence.set(relativePath, accumulated);
  }
  if (evidence.size === 0) errors.push("设计文档至少需要一个存在的仓库相对源码路径作为实现依据。");
  if (errors.length > 0) throw new RequirementError(`设计文档验证失败：${[...new Set(errors)].join("；")}`);
  return [...evidence].map(([path, symbols]) => ({ path, symbols: [...symbols] }));
}

export function validateSourceEvidenceEntries(
  root: string,
  entries: { path: string; symbol?: string }[],
  context = "源码证据"
): { path: string; symbol?: string; sha256: string }[] {
  const rootReal = realpathSync(root);
  const normalized: { path: string; symbol?: string; sha256: string }[] = [];
  const errors: string[] = [];
  for (const entry of entries) {
    const rawPath = String(entry.path ?? "").trim();
    if (!rawPath) continue;
    if (rawPath.includes("\0") || isAbsolute(rawPath) || rawPath.replaceAll("\\", "/").split("/").includes("..")) {
      errors.push(`${context}必须是仓库内相对路径：${rawPath}。`);
      continue;
    }
    const candidate = resolve(rootReal, rawPath);
    if (!existsSync(candidate)) {
      errors.push(`${context}路径不存在：${rawPath}。`);
      continue;
    }
    let path: string;
    try {
      path = realpathSync(candidate);
    } catch {
      errors.push(`${context}路径无法读取：${rawPath}。`);
      continue;
    }
    const relativePath = relative(rootReal, path).replaceAll("\\", "/");
    if (relativePath === ".." || relativePath.startsWith("../") || isAbsolute(relativePath)) {
      errors.push(`${context}路径越出项目目录：${rawPath}。`);
      continue;
    }
    if (!statSync(path).isFile()) {
      errors.push(`${context}必须指向真实文件：${rawPath}。`);
      continue;
    }
    const source = readFileSync(path, "utf8");
    const symbol = String(entry.symbol ?? "").trim();
    if (symbol && !sourceContainsSymbol(source, symbol)) {
      errors.push(`${context}符号不存在：${relativePath} 中未找到 ${symbol}。`);
      continue;
    }
    normalized.push({
      path: relativePath,
      ...(symbol ? { symbol } : {}),
      sha256: createHash("sha256").update(source).digest("hex"),
    });
  }
  if (normalized.length === 0) errors.push(`${context}至少需要一个存在的仓库相对源码路径。`);
  if (errors.length > 0) throw new RequirementError(`${context}验证失败：${[...new Set(errors)].join("；")}`);
  return normalized;
}

function validateRequirement(manifest: DocumentManifest, content: string): DocumentValidation {
  const lines = content.split(/\r?\n/);
  const headings = parseHeadings(lines);
  const errors: string[] = [];
  const required = manifest.ticketKind === "bug"
    ? [...REQUIREMENT_SECTIONS, ...BUG_SECTIONS]
    : REQUIREMENT_SECTIONS;
  requireSections(lines, headings, required, errors);

  const expectedTitle = `# ${manifest.requirementId} ${manifest.requirementName} 需求文档`;
  const title = lines.find((line) => line.trim().startsWith("# "))?.trim() ?? "";
  if (title !== expectedTitle) errors.push(`需求文档标题与 manifest 不一致；应为“${expectedTitle}”。`);

  const info = section(lines, headings, "文档信息");
  const fields = new Map<string, string>();
  for (const line of info.split(/\r?\n/)) {
    const match = /^\s*[-*]\s*(需求号|需求名称|单据类型)\s*[:：]\s*(.*?)\s*$/.exec(line);
    if (match) fields.set(match[1]!, plain(match[2]!));
  }
  if (fields.get("需求号") !== manifest.requirementId) errors.push("文档信息中的需求号与 manifest 不一致。");
  if (fields.get("需求名称") !== manifest.requirementName) errors.push("文档信息中的需求名称与 manifest 不一致。");
  const expectedKind = manifest.ticketKind === "bug" ? "bug" : "requirement";
  const actualKind = (fields.get("单据类型") ?? "").toLowerCase();
  if (!actualKind.includes(expectedKind)) errors.push("文档信息中的单据类型与 manifest 不一致。");

  const criteria = new Map<string, string>();
  for (const line of section(lines, headings, "验收标准").split(/\r?\n/)) {
    const match = AC_RE.exec(line);
    if (!match) continue;
    const id = match[1]!.toUpperCase();
    const description = plain(match[2]!);
    if (criteria.has(id)) errors.push(`验收标准编号重复：${id}。`);
    else if (!description) errors.push(`验收标准描述不能为空：${id}。`);
    else criteria.set(id, description);
  }
  const expectedCriteria = new Map(
    manifest.acceptanceCriteria.map((criterion) => [criterion.id.toUpperCase(), plain(criterion.description)])
  );
  for (const [id, description] of expectedCriteria) {
    if (!criteria.has(id)) errors.push(`需求文档缺少验收标准：${id}。`);
    else if (criteria.get(id) !== description) errors.push(`验收标准 ${id} 的描述与 manifest 不一致。`);
  }
  for (const id of criteria.keys()) {
    if (!expectedCriteria.has(id)) errors.push(`需求文档包含 manifest 未登记的验收标准：${id}。`);
  }

  const external = section(lines, headings, "外部接口影响").replace(/\s+/g, "");
  const saysNo = /不影响(?:对外|外部)接口|(?:对外|外部)接口无影响|不涉及(?:对外|外部)接口|仅调整内部|确认为否/.test(external);
  const saysYes = /(?<!不)(?:影响|涉及)(?:对外|外部)接口|新增(?:对外|外部)接口|修改(?:对外|外部)接口|确认为是/.test(external);
  if (saysNo === saysYes) errors.push("外部接口影响必须明确且无矛盾地写明“影响”或“不影响”。");
  else if (manifest.externalApiImpact.confirmed && saysYes !== manifest.externalApiImpact.value) {
    errors.push("需求文档的外部接口影响与 manifest 不一致。");
  }

  const pending = section(lines, headings, "待确认事项").trim();
  if (!/^(无|没有|不涉及|无待确认事项)(?:[\s，,。；;:：]|$)/.test(pending)) {
    errors.push("待确认事项仍未解决。");
  }
  if (PLACEHOLDER_RE.test(content)) errors.push("文档存在未完成占位内容。");
  if (errors.length > 0) throw new RequirementError(`需求文档验证失败：${[...new Set(errors)].join("；")}`);
  return {
    ok: true,
    kind: manifest.ticketKind,
    schema: "requirement-v2",
    errors: [],
    warnings: [],
    acceptanceIds: [...criteria.keys()].sort(),
    acceptanceCriteria: [...criteria].sort().map(([id, description]) => ({ id, description })),
    documentIdentity: {
      requirementId: manifest.requirementId,
      requirementName: manifest.requirementName,
      ticketKind: manifest.ticketKind,
      externalApiImpact: manifest.externalApiImpact.value,
    },
    blockingIssues: [],
    validatedAt: new Date().toISOString(),
  };
}

function validateDesign(manifest: DocumentManifest, content: string): DocumentValidation {
  const lines = content.split(/\r?\n/);
  const headings = parseHeadings(lines);
  const errors: string[] = [];
  requireSections(
    lines,
    headings,
    manifest.ticketKind === "bug" ? DESIGN_BUG_SECTIONS : DESIGN_REQUIREMENT_SECTIONS,
    errors
  );
  if (!content.includes(manifest.requirementId) || !content.includes(manifest.requirementName)) {
    errors.push("设计文档标题或正文与需求身份不一致。");
  }
  if (content.trim().length < 200) errors.push("设计文档内容过短。");
  if (PLACEHOLDER_RE.test(content)) errors.push("设计文档存在未完成占位内容。");
  if (errors.length > 0) throw new RequirementError(`设计文档验证失败：${[...new Set(errors)].join("；")}`);
  return {
    ok: true,
    kind: manifest.ticketKind,
    schema: manifest.ticketKind === "bug" ? "bug-v1" : "requirement-crm-v2",
    errors: [],
    warnings: [],
    validatedAt: new Date().toISOString(),
  };
}

function validatePlan(manifest: DocumentManifest, content: string): DocumentValidation {
  const errors: string[] = [];
  for (const heading of ["实施范围", "输入基线", "文件级变更", "实施步骤", "测试与验收映射", "风险与回滚"]) {
    if (!content.includes(`## ${heading}`)) errors.push(`缺少必要章节：${heading}。`);
  }
  if (!content.includes(manifest.requirementId)) errors.push("实施计划与需求号不一致。");
  if (PLACEHOLDER_RE.test(content)) errors.push("实施计划仍包含占位内容。");
  for (const criterion of manifest.acceptanceCriteria) {
    if (!content.includes(criterion.id)) errors.push(`实施计划缺少验收标准映射：${criterion.id}。`);
  }
  if (errors.length > 0) throw new RequirementError(`实施计划验证失败：${[...new Set(errors)].join("；")}`);
  return {
    ok: true,
    kind: "plan",
    schema: "plan-v1",
    errors: [],
    warnings: [],
    validatedAt: new Date().toISOString(),
  };
}

function validateClosure(manifest: DocumentManifest, content: string): DocumentValidation {
  const errors: string[] = [];
  for (const heading of ["验收标准", "收口说明"]) {
    if (!content.includes(`## ${heading}`)) errors.push(`缺少必要章节：${heading}。`);
  }
  if (!content.includes(manifest.requirementId)) errors.push("收口总结与需求号不一致。");
  for (const criterion of manifest.acceptanceCriteria) {
    if (!content.includes(criterion.id)) errors.push(`收口总结缺少验收标准：${criterion.id}。`);
  }
  if (PLACEHOLDER_RE.test(content)) errors.push("收口总结仍包含占位内容。");
  if (errors.length > 0) throw new RequirementError(`收口总结验证失败：${[...new Set(errors)].join("；")}`);
  return {
    ok: true,
    kind: "closure",
    schema: "closure-v1",
    errors: [],
    warnings: [],
    validatedAt: new Date().toISOString(),
  };
}

export function readValidatedDocument(
  root: string,
  manifest: DocumentManifest,
  type: string,
  pathValue: string
): { sourcePath: string; relativePath: string; content: string; validation: DocumentValidation } {
  const resolved = resolveRepositoryFile(root, pathValue);
  const content = readFileSync(resolved.path, "utf8");
  const validation = validateDeliveryDocumentInRepository(root, manifest, type, content);
  return { sourcePath: resolved.path, relativePath: resolved.relativePath, content, validation };
}
