// File discovery for scanning (phase 3.A.3), ported from application.py's file
// walk + the .understandignore / EXCLUDED_DIRS logic. The IncrementalScanCache
// lives in core.ts; this module provides the directory walk and category tagging.

import { readdirSync, statSync, type Stats } from "node:fs";
import { join, relative, extname } from "node:path";

export const EXCLUDED_DIRS = new Set([
  ".git",
  ".idea",
  ".vscode",
  ".claude",
  ".project-intel",
  ".project-intel/cache",
  ".project-intel/local",
  ".project-intel/tmp",
  "node_modules",
  "dist",
  "build",
  "coverage",
  "target",
  ".next",
  ".nuxt",
  ".turbo",
  ".cache",
]);

export const CODE_SUFFIXES = new Set([
  ".java", ".kt", ".py", ".go", ".ts", ".tsx", ".js", ".jsx", ".vue", ".rb", ".cs", ".php", ".rs", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp", ".m", ".mm",
]);
export const CONFIG_SUFFIXES = new Set([".yaml", ".yml", ".json", ".properties", ".xml", ".toml", ".conf", ".env"]);
export const DOCS_SUFFIXES = new Set([".md", ".rst", ".txt"]);
export const STYLE_SUFFIXES = new Set([".css", ".scss", ".sass", ".less"]);
export const MARKUP_SUFFIXES = new Set([".html", ".htm"]);
export const INFRA_SUFFIXES = new Set([".yml", ".yaml"]); // github workflows etc.

export type FileCategory = "code" | "config" | "docs" | "infra" | "data" | "script" | "markup" | "style";

export interface DiscoveredFile {
  path: string; // repo-relative, posix
  absolute: string;
  size: number;
  mtimeMs: number;
  suffix: string;
  language: string;
  fileCategory: FileCategory;
}

const SUFFIX_LANGUAGE: Record<string, string> = {
  ".java": "java", ".kt": "kotlin", ".py": "python", ".go": "go", ".ts": "typescript", ".tsx": "tsx",
  ".js": "javascript", ".jsx": "jsx", ".vue": "vue", ".rb": "ruby", ".cs": "csharp", ".php": "php",
  ".rs": "rust", ".swift": "swift", ".c": "c", ".cc": "cpp", ".cpp": "cpp", ".h": "c", ".hpp": "cpp",
  ".m": "objc", ".mm": "objcpp", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".xml": "xml",
  ".properties": "properties", ".toml": "toml", ".conf": "conf", ".env": "env", ".md": "markdown",
  ".rst": "rst", ".txt": "txt", ".css": "css", ".scss": "scss", ".sass": "sass", ".less": "less",
  ".html": "html", ".htm": "html", ".sql": "sql",
};

/** Categorize a file by suffix. Mirrors the scanner's fileCategory assignment. */
export function categorize(suffix: string, relPath: string): FileCategory {
  const lower = suffix.toLowerCase();
  if (CODE_SUFFIXES.has(lower) || lower === ".sql") return "code";
  if (STYLE_SUFFIXES.has(lower)) return "style";
  if (MARKUP_SUFFIXES.has(lower)) return "markup";
  if (INFRA_SUFFIXES.has(lower) && relPath.includes(".github/workflows")) return "infra";
  if (DOCS_SUFFIXES.has(lower)) return "docs";
  if (CONFIG_SUFFIXES.has(lower)) return "config";
  if (lower === ".sh" || lower === ".bash" || relPath.endsWith("Dockerfile") || relPath.endsWith(".dockerfile")) return "infra";
  return "data";
}

/** Minimal glob matcher: supports `*`, `**`, prefix `!`. */
export function simpleMatch(pattern: string, path: string): boolean {
  const neg = pattern.startsWith("!");
  const pat = neg ? pattern.slice(1) : pattern;
  // Convert glob to regex:
  // - ** matches any number of path segments (including zero)
  // - * matches any characters except /
  // - ? matches a single character except /
  // Special case: **/* and **/** should match root-level files too.
  let regexStr = pat
    .split("/")
    .map((seg) => {
      if (seg === "**") return "\0DOUBLESTAR\0";
      return seg.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, "[^/]*").replace(/\?/g, "[^/]");
    })
    .join("/")
    // **/ means "any directory prefix" — make the leading dir + / optional
    .replace(/\0DOUBLESTAR\0\//g, "(?:.*/)?")
    // standalone ** means "match anything"
    .replace(/\0DOUBLESTAR\0/g, ".*");
  const re = new RegExp("^" + regexStr + "$");
  const matched = re.test(path);
  // Directory matching: a bare directory name (no /) should exclude files
  // anywhere under that directory, including nested paths like src/vendor/a.ts.
  // This mirrors .gitignore directory matching.
  let dirMatched = false;
  if (!matched && !pat.includes("/") && !pat.includes("*")) {
    const segments = path.split("/");
    dirMatched = segments.includes(pat);
  }
  const result = neg ? !(matched || dirMatched) : (matched || dirMatched);
  return result;
}

/**
 * Walk a directory tree, returning discovered files (repo-relative posix paths).
 * Skips EXCLUDED_DIRS and respects a simple include/exclude glob set.
 */
export function discoverFiles(root: string, options: { exclude?: readonly string[]; excludeHidden?: boolean; include?: readonly string[] } = {}): DiscoveredFile[] {
  const excludePatterns = options.exclude ?? [];
  const includePatterns = options.include ?? [];
  const excludeHidden = options.excludeHidden ?? true;
  const out: DiscoveredFile[] = [];
  const walk = (dir: string) => {
    let entries: import("node:fs").Dirent[];
    try {
      entries = readdirSync(dir, { withFileTypes: true, encoding: "utf8" });
    } catch {
      return;
    }
    for (const entry of entries) {
      const name = entry.name;
      if (EXCLUDED_DIRS.has(name)) continue;
      // When excludeHidden is true, skip all dotfiles/dotdirs (except .github).
      if (excludeHidden && name.startsWith(".") && name !== ".github") continue;
      if (name.startsWith(".") && [".git", ".DS_Store"].includes(name)) continue;
      const full = join(dir, name);
      let st: Stats;
      try {
        st = statSync(full);
      } catch {
        continue;
      }
      if (st.isDirectory()) {
        walk(full);
      } else if (st.isFile()) {
        const rel = relative(root, full).split("\\").join("/");
        // If include patterns are specified, file must match at least one.
        if (includePatterns.length > 0 && !includePatterns.some((p) => simpleMatch(p, rel))) continue;
        if (excludePatterns.some((p) => simpleMatch(p, rel))) continue;
        const suffix = extname(name).toLowerCase();
        out.push({
          path: rel,
          absolute: full,
          size: st.size,
          mtimeMs: st.mtimeMs,
          suffix,
          language: SUFFIX_LANGUAGE[suffix] ?? "unknown",
          fileCategory: categorize(suffix, rel),
        });
      }
    }
  };
  walk(root);
  // Python's sorted(Path(...)) compares Unicode code points. localeCompare()
  // can place lowercase names before uppercase names on macOS, which changes
  // the stable fact order and therefore the generated compatibility snapshot.
  return out.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
}
