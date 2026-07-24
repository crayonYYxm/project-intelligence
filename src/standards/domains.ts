const GENERIC_SEGMENTS = new Set([
  "src", "app", "apps", "packages", "modules", "components", "pages", "services",
  "controllers", "api", "common", "shared", "utils", "lib", "main", "java", "resources",
]);

/** Derive recurring business-domain path segments from project and graph facts. */
export function projectDomainCandidates(
  frontend: object,
  backend: object,
  graph: Record<string, unknown>
): Record<string, unknown>[] {
  const frontendFacts = frontend as Record<string, unknown[] | undefined>;
  const backendFacts = backend as Record<string, unknown[] | undefined>;
  const counts = new Map<string, number>();
  const locations = new Map<string, string[]>();
  const paths: string[] = [];
  for (const key of ["components", "hooks", "routes", "apiModules", "stores"]) {
    for (const item of frontendFacts[key] ?? []) {
      if (item && typeof item === "object") paths.push(String((item as Record<string, unknown>).path ?? ""));
    }
  }
  for (const key of ["apis", "services", "dataTypes", "repositories"]) {
    for (const item of backendFacts[key] ?? []) {
      if (item && typeof item === "object") paths.push(String((item as Record<string, unknown>).path ?? ""));
    }
  }
  const record = (name: string, count: number, itemPaths: string[]) => {
    counts.set(name, (counts.get(name) ?? 0) + count);
    locations.set(name, [...(locations.get(name) ?? []), ...itemPaths]);
  };
  for (const path of paths) {
    const parts = path.split("/").slice(0, -1)
      .filter((part) => !GENERIC_SEGMENTS.has(part.toLowerCase()) && !part.startsWith("."));
    if (parts.length) record(parts.at(-1)!, 1, [path]);
  }
  const understandSummary = (graph.understandSummary as Record<string, unknown> | undefined) ?? {};
  for (const item of (understandSummary.domains as unknown[] | undefined) ?? []) {
    if (!item || typeof item !== "object") continue;
    const domain = item as Record<string, unknown>;
    if (!domain.name) continue;
    record(
      String(domain.name),
      Number(domain.count) || 0,
      Array.isArray(domain.paths) ? domain.paths.map(String) : []
    );
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 20)
    .filter(([, count]) => count >= 2)
    .map(([name, count]) => ({
      name,
      count,
      paths: [...new Set(locations.get(name) ?? [])].slice(0, 12),
      source: "project-derived",
    }));
}
