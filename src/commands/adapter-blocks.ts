// Adapter managed-block management (phase 3.C.2), ported from application's
// adapter block functions. Upserts/removes/statuses a single managed block
// delimited by start/end markers in AGENTS.md / CLAUDE.md / .claude/CLAUDE.md.

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve } from "node:path";

export const PROJECT_INTEL_BLOCK_START = "<!-- project-intelligence:start -->";
export const PROJECT_INTEL_BLOCK_END = "<!-- project-intelligence:end -->";
export const AGENT_PROJECT_INTEL_BLOCK_START = "<!-- agent-project-intelligence:start -->";
export const AGENT_PROJECT_INTEL_BLOCK_END = "<!-- agent-project-intelligence:end -->";

const ADAPTER_FILE_CAP = 2 * 1024 * 1024; // 2 MiB

export interface AdapterTarget {
  name: string;
  path: string;
  block: string;
  start: string;
  end: string;
  prepend: boolean;
}

/** Resolve a single adapter-managed file (AGENTS.md / CLAUDE.md / .claude/CLAUDE.md). */
export function safeAdapterPath(root: string, rel: string): string {
  const candidate = resolve(root, rel);
  const relFromRoot = relative(root, candidate);
  if (relFromRoot.startsWith("..") || isAbsolute(relFromRoot)) {
    throw new Error(`适配器路径越界：${rel}`);
  }
  const allowed = new Set(
    ["AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md", ".claude"].map((p) => p.split("\\").join("/"))
  );
  if (!allowed.has(relFromRoot.split("\\").join("/"))) {
    throw new Error(`适配器只支持 AGENTS.md、CLAUDE.md、.claude/CLAUDE.md：${rel}`);
  }
  return candidate;
}

function readAdapter(root: string, rel: string): string {
  const path = safeAdapterPath(root, rel);
  if (!existsSync(path)) return "";
  const st = statSync(path);
  if (st.size > ADAPTER_FILE_CAP) throw new Error(`适配器文件过大（>2MiB）：${rel}`);
  return readFileSync(path, "utf8");
}

function writeAdapter(root: string, rel: string, text: string): void {
  const path = safeAdapterPath(root, rel);
  const dir = dirname(path);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(path, text.replace(/\s+$/, "") + "\n", "utf8");
}

function adapterRelative(root: string, path: string): string {
  return relative(root, path).split("\\").join("/");
}

/** Replace a single managed block delimited by start/end markers. */
export function replaceSingleManagedBlock(
  current: string,
  managed: string,
  start: string,
  end: string,
  prepend = false
): { text: string; action: string } {
  const startCount = (current.match(new RegExp(escapeRegex(start), "g")) || []).length;
  const endCount = (current.match(new RegExp(escapeRegex(end), "g")) || []).length;
  if (startCount !== endCount) throw new Error("适配器管理标记不完整，请人工处理后重试。");
  if (startCount > 1) throw new Error("适配器存在重复 Project Intelligence 管理块，请人工处理后重试。");
  const pattern = new RegExp(`${escapeRegex(start)}.*?${escapeRegex(end)}`, "gs");
  if (startCount === 1) {
    return { text: current.replace(pattern, managed).replace(/\s+$/, ""), action: "updated" };
  }
  if (current.trim() && prepend) return { text: managed + "\n\n" + current.replace(/\s+$/, ""), action: "created" };
  if (current.trim()) return { text: current.replace(/\s+$/, "") + "\n\n" + managed, action: "created" };
  return { text: managed, action: "created" };
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function upsertAdapterManagedBlock(
  root: string,
  rel: string,
  block: string,
  start: string,
  end: string,
  options: { prepend?: boolean; dryRun?: boolean } = {}
): Record<string, unknown> {
  const current = readAdapter(root, rel);
  const managed = `${start}\n${block.trim()}\n${end}`;
  const { text, action } = replaceSingleManagedBlock(current, managed, start, end, options.prepend);
  const changed = text.replace(/\s+$/, "") !== current.replace(/\s+$/, "");
  if (changed && !options.dryRun) writeAdapter(root, rel, text);
  return {
    path: rel,
    action: changed ? action : "unchanged",
    changed,
    sha256: createHash("sha256").update(managed, "utf8").digest("hex"),
  };
}

export function removeAdapterManagedBlock(
  root: string,
  rel: string,
  start: string,
  end: string,
  options: { dryRun?: boolean } = {}
): Record<string, unknown> {
  const current = readAdapter(root, rel);
  const startCount = (current.match(new RegExp(escapeRegex(start), "g")) || []).length;
  const endCount = (current.match(new RegExp(escapeRegex(end), "g")) || []).length;
  if (startCount !== endCount) throw new Error("适配器管理标记不完整，请人工处理后重试。");
  if (startCount > 1) throw new Error("适配器存在重复 Project Intelligence 管理块，请人工处理后重试。");
  if (startCount === 0) return { path: rel, action: "absent", changed: false };
  const pattern = new RegExp(`${escapeRegex(start)}.*?${escapeRegex(end)}\\n*`, "gs");
  const next = current.replace(pattern, "").trim();
  if (!options.dryRun) writeAdapter(root, rel, next);
  return { path: rel, action: "removed", changed: true };
}

/** Status of a single adapter (current/missing/drifted/malformed/duplicate). */
export function adapterStatus(root: string, target: AdapterTarget): Record<string, unknown> {
  const current = readAdapter(root, adapterRelative(root, target.path));
  const managed = `${target.start}\n${target.block.trim()}\n${target.end}`;
  let status: string;
  if (current.includes(managed)) status = "current";
  else if (!current.includes(target.start)) status = "missing";
  else status = "drifted";
  const startCount = (current.match(new RegExp(escapeRegex(target.start), "g")) || []).length;
  const endCount = (current.match(new RegExp(escapeRegex(target.end), "g")) || []).length;
  if (startCount !== endCount) status = "malformed";
  else if (startCount > 1) status = "duplicate";
  return {
    target: target.name,
    path: adapterRelative(root, target.path),
    status,
    managedSha256: createHash("sha256").update(managed, "utf8").digest("hex"),
  };
}

/** Upsert with a no-op remove of the legacy project-intel markers first (codex target). */
export function clearLegacyBlock(root: string, rel: string): string {
  const current = readAdapter(root, rel);
  const pattern = new RegExp(`${escapeRegex(PROJECT_INTEL_BLOCK_START)}.*?${escapeRegex(PROJECT_INTEL_BLOCK_END)}`, "gs");
  return current.replace(pattern, "").trim();
}
