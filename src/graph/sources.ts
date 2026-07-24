// Graph source readers (phase 3.G.1), ported from graph.py.
//
// Summarizes GitNexus (.gitnexus/meta.json) and Understand-Anything
// (.understand-anything/knowledge-graph.json) presence + stats, plus an
// architecture/domain aggregation of the UA graph. Used by init/doctor/graph-tools.

import { existsSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

const GENERIC_PATH_PARTS = new Set([
  "src", "app", "apps", "lib", "libs", "packages", "modules", "module", "main",
  "java", "kotlin", "python", "javascript", "typescript", "resources", "components",
  "pages", "services", "controllers", "api", "routes", "router", "common", "shared",
]);
const MODULE_MARKERS = new Set(["api", "components", "pages", "routes", "router", "services", "domain", "modules", "features"]);

function loadJsonChecked(path: string): [Record<string, unknown> | null, string | null] {
  try {
    const payload = JSON.parse(readFileSync(path, "utf8"));
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return [null, "根节点不是 JSON 对象"];
    }
    return [payload as Record<string, unknown>, null];
  } catch (err) {
    return [null, String((err as Error).message)];
  }
}

function posixRel(root: string, path: string): string {
  return relative(root, path).split("\\").join("/");
}

/** GitNexus summary (mirrors gitnexus_summary). */
export function gitnexusSummary(root: string): Record<string, unknown> {
  const dir = join(root, ".gitnexus");
  if (!existsSync(dir)) return { status: "missing", path: ".gitnexus", reason: "未找到索引目录" };
  let metaPath: string | null = null;
  for (const candidate of ["meta.json", "gitnexus.json"]) {
    const p = join(dir, candidate);
    if (existsSync(p)) {
      metaPath = p;
      break;
    }
  }
  if (!metaPath) return { status: "invalid", path: ".gitnexus", reason: "缺少 meta.json/gitnexus.json" };
  const [meta, error] = loadJsonChecked(metaPath);
  if (error) return { status: "invalid", path: posixRel(root, metaPath), reason: error };
  const stats = (meta?.stats as Record<string, unknown>) ?? {};
  const caps = (meta?.capabilities as Record<string, unknown>) ?? {};
  const graphCap = (caps.graph as Record<string, unknown>) ?? {};
  const counts: Record<string, number> = {};
  for (const name of ["files", "nodes", "edges", "communities", "processes"]) {
    counts[name] = parseInt(String(stats[name] ?? 0), 10) || 0;
  }
  const graphReady = graphCap.status === "available" || ((counts.nodes ?? 0) > 0 && (counts.edges ?? 0) > 0);
  if (!graphReady) {
    return { status: "invalid", path: posixRel(root, metaPath), reason: "索引元数据存在，但没有可用图关系", stats: counts };
  }
  return {
    status: "present",
    path: posixRel(root, metaPath),
    schemaVersion: meta?.schemaVersion,
    indexedCommit: meta?.lastCommit,
    stats: counts,
    capabilities: {
      graph: graphCap.status ?? "available",
      fts: (caps.fts as Record<string, unknown>)?.status ?? null,
      vectorSearch: (caps.vectorSearch as Record<string, unknown>)?.status ?? null,
    },
  };
}

/** Understand-Anything summary (mirrors understand_summary). */
export function understandSummary(root: string): Record<string, unknown> {
  const path = join(root, ".understand-anything", "knowledge-graph.json");
  if (!existsSync(path)) return { status: "missing", path: ".understand-anything/knowledge-graph.json", reason: "未找到知识图谱" };
  const [graph, error] = loadJsonChecked(path);
  if (error) return { status: "invalid", path: posixRel(root, path), reason: error };
  const nodes = (graph?.nodes as unknown[]) ?? [];
  const edges = (graph?.edges as unknown[]) ?? [];
  if (!Array.isArray(nodes) || !Array.isArray(edges) || !nodes.length) {
    return { status: "invalid", path: posixRel(root, path), reason: "图谱必须包含非空 nodes 数组和 edges 数组" };
  }
  return { status: "present", path: posixRel(root, path), nodes: nodes.length, edges: edges.length };
}

/** Detect both graph sources (mirrors detect_graph_sources). */
export function detectGraphSources(root: string): Record<string, unknown>[] {
  const gitnexus = gitnexusSummary(root);
  const understand = understandSummary(root);
  const stripPath = (obj: Record<string, unknown>): Record<string, unknown> => {
    const { path: _path, ...rest } = obj;
    void _path;
    return rest;
  };
  return [
    { name: "GitNexus", path: gitnexus.path ?? ".gitnexus", role: "符号调用、影响、变更风险", ...stripPath(gitnexus) },
    { name: "Understand-Anything", path: understand.path ?? ".understand-anything/knowledge-graph.json", role: "架构、模块、领域流、入职", ...stripPath(understand) },
  ];
}

function meaningfulDomain(path: string, tags: string[] = []): string | null {
  const parts = path.split("/").slice(0, -1);
  const candidates = parts.filter((p) => !GENERIC_PATH_PARTS.has(p.toLowerCase()) && !p.startsWith("."));
  if (candidates.length) return candidates[candidates.length - 1]!;
  const cleanTags = tags.map((t) => t.trim()).filter((t) => t && !GENERIC_PATH_PARTS.has(t.toLowerCase()));
  return cleanTags[0] ?? null;
}

/** UA architecture/domain aggregation (mirrors understand_graph_summary). */
export function understandGraphSummary(root: string): Record<string, unknown> {
  const inspected = understandSummary(root);
  if (inspected.status !== "present") {
    return { status: inspected.status, reason: inspected.reason, nodes: 0, edges: 0, domains: [], keyModules: [], topPathPrefixes: [] };
  }
  const path = join(root, ".understand-anything", "knowledge-graph.json");
  const [graph] = loadJsonChecked(path);
  const nodes = (graph?.nodes as Record<string, unknown>[]) ?? [];
  const edges = (graph?.edges as unknown[]) ?? [];
  const domainBuckets = new Map<string, Record<string, unknown>[]>();
  const keyModules: Record<string, unknown>[] = [];
  for (const node of nodes) {
    const filePath = String(node.filePath ?? node.id ?? "");
    if (!filePath) continue;
    const summary = String(node.summary ?? "");
    const tags = Array.isArray(node.tags) ? (node.tags as string[]) : [];
    const domain = meaningfulDomain(filePath, tags);
    if (domain) {
      const arr = domainBuckets.get(domain) ?? [];
      arr.push({ path: filePath, summary, tags: tags.slice(0, 8) });
      domainBuckets.set(domain, arr);
    }
    if (filePath.split("/").some((part) => MODULE_MARKERS.has(part.toLowerCase()))) {
      keyModules.push({ path: filePath, name: node.name ?? filePath.split("/").pop(), summary, tags: tags.slice(0, 8) });
    }
  }
  const domains = [...domainBuckets.entries()]
    .sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]))
    .slice(0, 20)
    .map(([name, items]) => ({
      name,
      count: items.length,
      paths: items.slice(0, 12).map((i) => i.path),
      summaries: items.map((i) => i.summary).filter(Boolean).slice(0, 5),
    }));
  return {
    status: "present",
    nodes: nodes.length,
    edges: edges.length,
    domains,
    keyModules: keyModules.slice(0, 50),
    topPathPrefixes: [],
  };
}
