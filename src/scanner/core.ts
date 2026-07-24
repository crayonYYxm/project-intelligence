// Scan caching primitives (phase 3.A), ported from core.py.
//
// file_signature: size+mtime hash for cheap cache keys.
// IncrementalScanCache: schemaVersion 1, per-(path,namespace) cache with
// signature invalidation and a `seen` set for retention on save.

import { createHash } from "node:crypto";
import { statSync, readFileSync } from "node:fs";

export const GENERATED_AGENT_FILES = new Set(["AGENTS.md", "CLAUDE.md"]);

/** Cheap signature for repository-local scan caching (size:mtime). */
export function fileSignature(path: string): string {
  try {
    const st = statSync(path, { bigint: true });
    return createHash("sha256").update(`${st.size}:${st.mtimeNs}`).digest("hex").slice(0, 20);
  } catch {
    return "missing";
  }
}

type CacheEntry = { signature?: string; [namespace: string]: unknown };

export class IncrementalScanCache {
  readonly entries: Record<string, CacheEntry> = {};
  readonly seen = new Set<string>();

  constructor(payload?: { entries?: Record<string, CacheEntry> }) {
    if (payload && typeof payload.entries === "object" && payload.entries) {
      Object.assign(this.entries, payload.entries);
    }
  }

  static load(path: string): IncrementalScanCache {
    try {
      const payload = JSON.parse(readFileSync(path, "utf8"));
      return new IncrementalScanCache(payload);
    } catch {
      return new IncrementalScanCache();
    }
  }

  get(relPath: string, namespace: string, signature: string): unknown | null {
    this.seen.add(relPath);
    const entry = this.entries[relPath];
    if (!entry || entry.signature !== signature) return null;
    return structuredCloneSafe(entry[namespace]);
  }

  put(relPath: string, namespace: string, signature: string, value: unknown): void {
    this.seen.add(relPath);
    let entry = this.entries[relPath];
    if (!entry) {
      entry = this.entries[relPath] = {};
    }
    if (entry.signature !== signature) {
      for (const k of Object.keys(entry)) delete entry[k];
      entry.signature = signature;
    }
    entry[namespace] = structuredCloneSafe(value);
  }

  payload(): { schemaVersion: 1; entries: Record<string, CacheEntry> } {
    const retained: Record<string, CacheEntry> = {};
    for (const path of [...this.seen].sort()) {
      if (this.entries[path]) retained[path] = this.entries[path]!;
    }
    return { schemaVersion: 1, entries: retained };
  }
}

function structuredCloneSafe<T>(value: T): T {
  return value === undefined ? (undefined as T) : (JSON.parse(JSON.stringify(value)) as T);
}

/**
 * Portable tooling sanitizer (core.sanitize_tooling). Returns the safe-to-commit
 * subset of a detected tooling report, dropping machine-specific paths.
 */
export function sanitizeTooling(tooling: Record<string, unknown> | null | undefined): Record<string, unknown> {
  const t = tooling ?? {};
  const optional = (t.optional as Record<string, unknown>) ?? {};
  return {
    schemaVersion: 1,
    required: pickList(t.required as Record<string, unknown>[] | undefined, ["name", "status"]),
    optional: {
      git: { status: (optional.git as Record<string, unknown>)?.status },
      node: { status: (optional.node as Record<string, unknown>)?.status },
      packageManagers: pickList(optional.packageManagers as Record<string, unknown>[] | undefined, [
        "name",
        "status",
        "selected",
      ]),
      gitnexus: {
        status: (optional.gitnexus as Record<string, unknown>)?.status,
        indexPath: (optional.gitnexus as Record<string, unknown>)?.indexPath,
        runnerPath: (optional.gitnexus as Record<string, unknown>)?.runnerPath,
      },
      understandAnything: {
        status: (optional.understandAnything as Record<string, unknown>)?.status,
        graphPath: (optional.understandAnything as Record<string, unknown>)?.graphPath,
      },
      qualityTools: pickList(optional.qualityTools as Record<string, unknown>[] | undefined, [
        "kind",
        "status",
        "command",
      ]),
    },
    recommendedActions: pickList(t.recommendedActions as Record<string, unknown>[] | undefined, [
      "tool",
      "reason",
      "command",
      "canRun",
    ]),
    followUpActions: pickList(t.followUpActions as Record<string, unknown>[] | undefined, [
      "tool",
      "command",
      "refreshCommand",
      "fallbackRefreshCommand",
      "canRun",
    ]),
  };
}

function pickList(items: Record<string, unknown>[] | undefined, keys: string[]): Record<string, unknown>[] {
  if (!Array.isArray(items)) return [];
  return items
    .filter((item) => item && typeof item === "object")
    .map((item) => {
      const out: Record<string, unknown> = {};
      for (const k of keys) out[k] = item[k];
      return out;
    });
}
