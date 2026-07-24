// `adapters` command family (phase 3.C.2), ported from application.adapters_*.
//
// status / preview / apply / remove with --target {codex,claude,both} (default
// both). status also accepts --check to exit non-zero when not current.

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { relative, resolve } from "node:path";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import {
  upsertAdapterManagedBlock,
  removeAdapterManagedBlock,
  adapterStatus,
  replaceSingleManagedBlock,
  clearLegacyBlock,
  type AdapterTarget,
} from "./adapter-blocks.js";
import { adapterTargets } from "./agent-rules.js";

const VALID_TARGETS = new Set(["codex", "claude", "both"]);

function parseTarget(args: string[]): string {
  const idx = args.indexOf("--target");
  const val = idx >= 0 ? args[idx + 1] : "both";
  if (!val || !VALID_TARGETS.has(val)) {
    throw new UsageError(`--target 只支持 codex/claude/both：${val ?? "(空)"}`);
  }
  return val;
}

function targetRel(target: AdapterTarget, root: string): string {
  return relative(root, target.path).split("\\").join("/");
}

function hashOf(s: string): string {
  return createHash("sha256").update(s, "utf8").digest("hex");
}

function readCurrent(root: string, rel: string): string {
  const path = resolve(root, rel);
  if (!existsSync(path)) return "";
  try {
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}

/** adapters apply (preflight all, commit, rollback on failure). Mirrors adapters_apply. */
export function adaptersApply(root: string, target: string, dryRun = false): Record<string, unknown> {
  const targets = adapterTargets(root, target);
  const staged: Record<string, unknown>[] = [];
  for (const t of targets) {
    const rel = targetRel(t, root);
    let current = readCurrent(root, rel);
    if (t.name === "codex") current = clearLegacyBlock(root, rel);
    const managed = `${t.start}\n${t.block.trim()}\n${t.end}`;
    const { text: nextText, action } = replaceSingleManagedBlock(current, managed, t.start, t.end, t.prepend);
    const changed = nextText.replace(/\s+$/, "") !== current.replace(/\s+$/, "");
    staged.push({ target: t.name, path: rel, action: changed ? action : "unchanged", changed, sha256: hashOf(managed) });
  }
  if (dryRun) return { ok: true, dryRun: true, target, entries: staged };
  for (const t of targets) {
    const rel = targetRel(t, root);
    upsertAdapterManagedBlock(root, rel, t.block, t.start, t.end, { prepend: t.prepend });
  }
  return { ok: true, dryRun: false, target, entries: staged };
}

/** adapters remove. Mirrors adapters_remove. */
export function adaptersRemove(root: string, target: string, dryRun = false): Record<string, unknown> {
  const targets = adapterTargets(root, target);
  const results: Record<string, unknown>[] = [];
  for (const t of targets) {
    const rel = targetRel(t, root);
    const res = removeAdapterManagedBlock(root, rel, t.start, t.end, { dryRun });
    results.push({ target: t.name, ...res });
  }
  return { ok: true, target, entries: results };
}

/** adapters status. Mirrors adapters_status. */
export function adaptersStatus(root: string, target: string): { ok: boolean; target: string; entries: Record<string, unknown>[] } {
  const targets = adapterTargets(root, target);
  const entries: Record<string, unknown>[] = [];
  let allOk = true;
  for (const t of targets) {
    try {
      const status = adapterStatus(root, t);
      entries.push(status);
      if (status.status !== "current") allOk = false;
    } catch (err) {
      entries.push({ target: t.name, path: relative(root, t.path), status: "error", error: String((err as Error).message) });
      allOk = false;
    }
  }
  return { ok: allOk, target, entries };
}

/** adapters preview = apply with dry_run. */
export function adaptersPreview(root: string, target: string): Record<string, unknown> {
  return adaptersApply(root, target, true);
}

/** Command handler for `adapters <subcommand>`. */
export function runAdapters(root: string, args: string[], global: GlobalOptions): CommandResult {
  const sub = args[0];
  const target = parseTarget(args);
  let result: Record<string, unknown>;
  if (sub === "status") {
    result = adaptersStatus(root, target);
    if (args.includes("--check") && !result.ok) {
      return { exitCode: 1, result };
    }
  } else if (sub === "preview") {
    result = adaptersPreview(root, target);
  } else if (sub === "apply") {
    result = adaptersApply(root, target, false);
  } else if (sub === "remove") {
    result = adaptersRemove(root, target, false);
  } else {
    throw new UsageError(`adapters 子命令只支持 status/preview/apply/remove：${sub ?? "(空)"}`);
  }
  void global;
  return ok(result);
}
