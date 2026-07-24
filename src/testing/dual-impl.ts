// Dual-implementation comparison harness.
//
// During the Python → Node.js/TypeScript migration (plan phase 3), each migrated
// module must produce output equivalent to the 0.6.1 Python baseline. This module
// provides:
//   - normalizeForCompare: scrubs non-deterministic fields (timestamps, absolute
//     paths, temp dirs, git hashes, OS path separators) so two outputs can be
//     compared deterministically.
//   - compareJsonOutputs: deep-equals two normalized JSON values and reports the
//     first differing path (for readable test failures).
//   - runDual: invokes the baseline (Python v0.6.1 worktree) CLI and the Node CLI
//     with the same args, returns both envelopes for a test to assert on.
//
// Used by the per-module equivalence tests in phase 3 (AC-06) and the CLI
// contract tests (AC-02).

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

// ISO-8601 timestamps (with optional timezone / fractional seconds).
const ISO_RE =
  /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})/g;
// 40-char lowercase hex git object ids.
const GIT_HASH_RE = /\b[0-9a-f]{40}\b/g;
// Epoch seconds / millis (>= 10 digits) embedded as JSON numbers or text.
const EPOCH_RE = /\b1[6-9]\d{8,}\b/g;

/**
 * Scrub non-deterministic content from a string or JSON value so two runs can be
 * compared. Rules:
 *   - timestamps (ISO-8601) → `<TIME>`
 *   - git object ids (40 hex) → `<GIT_HASH>`
 *   - epoch-second/milli integers → `<EPOCH>`
 *   - absolute paths (POSIX and Windows) → posixified, then the repo/sample
 *     roots are masked
 *   - backslashes normalized to forward slashes
 *
 * `roots` is a list of absolute path prefixes (e.g. the repo root, a sample
 * project dir) that should be masked to `<ROOT>` / `<SAMPLE_ROOT>`.
 */
export function normalizeForCompare(
  value: unknown,
  roots: readonly string[] = []
): unknown {
  const maskRoots = [...roots]
    .filter(Boolean)
    .sort((a, b) => b.length - a.length); // longest first so nested roots win

  const scrubString = (s: string): string => {
    let out = s.replace(/\\/g, "/"); // normalize path separators
    for (let i = 0; i < maskRoots.length; i++) {
      const root = maskRoots[i];
      if (root === undefined) continue;
      const rootNorm = root.replace(/\\/g, "/");
      const label = i === 0 ? "<ROOT>" : `<ROOT${i}>`;
      out = out.split(rootNorm).join(label);
    }
    out = out
      .replace(ISO_RE, "<TIME>")
      .replace(GIT_HASH_RE, "<GIT_HASH>")
      .replace(EPOCH_RE, "<EPOCH>");
    return out;
  };

  if (typeof value === "string") return scrubString(value);
  if (typeof value === "number") {
    // Mask epoch-second/millisecond integers (>= year 2020) that drift per run.
    return Number.isInteger(value) && value >= 1577836800 ? "<EPOCH>" : value;
  }
  if (value === null || typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map((v) => normalizeForCompare(v, roots));
  const out: Record<string, unknown> = {};
  for (const key of Object.keys(value as Record<string, unknown>)) {
    // mtime is a per-file epoch drift; collapse regardless of scrub above.
    const k = key === "mtime" ? "mtime" : key;
    const v = (value as Record<string, unknown>)[key];
    if (k === "mtime" && typeof v === "number") out[k] = "<MTIME>";
    else out[k] = normalizeForCompare(v, roots);
  }
  return out;
}

/**
 * Deep-compare two normalized values. Returns null when equal, otherwise a
 * short path string describing the first divergence (for assertion messages).
 */
export function compareJsonOutputs(
  baseline: unknown,
  candidate: unknown,
  pathPrefix = ""
): string | null {
  if (typeof baseline !== typeof candidate) {
    return `${pathPrefix || "<root>"}: type ${typeof baseline} vs ${typeof candidate}`;
  }
  if (typeof baseline !== "object" || baseline === null) {
    return baseline === candidate
      ? null
      : `${pathPrefix || "<root>"}: ${JSON.stringify(baseline)} vs ${JSON.stringify(candidate)}`;
  }
  if (Array.isArray(baseline)) {
    if (!Array.isArray(candidate)) return `${pathPrefix || "<root>"}: array vs non-array`;
    const n = Math.max(baseline.length, candidate.length);
    for (let i = 0; i < n; i++) {
      const p = `${pathPrefix}[${i}]`;
      if (i >= baseline.length) return `${p}: missing in baseline`;
      if (i >= candidate.length) return `${p}: missing in candidate`;
      const diff = compareJsonOutputs(baseline[i], candidate[i], p);
      if (diff) return diff;
    }
    return null;
  }
  const bk = Object.keys(baseline as Record<string, unknown>);
  const ck = Object.keys(candidate as Record<string, unknown>);
  const keys = new Set([...bk, ...ck]);
  for (const key of keys) {
    const p = pathPrefix ? `${pathPrefix}.${key}` : key;
    const bv = (baseline as Record<string, unknown>)[key];
    const cv = (candidate as Record<string, unknown>)[key];
    if (bv === undefined) return `${p}: missing in baseline`;
    if (cv === undefined) return `${p}: missing in candidate`;
    const diff = compareJsonOutputs(bv, cv, p);
    if (diff) return diff;
  }
  return null;
}

export interface DualRunResult {
  baseline: { exitCode: number; envelope: unknown; stdout: string } | null;
  candidate: { exitCode: number; envelope: unknown; stdout: string } | null;
}

/**
 * Resolve the baseline (v0.6.1 worktree) CLI path. Returns null when the
 * worktree has not been set up (plan 0.2 not run), letting callers skip dual
 * comparison gracefully.
 */
export function baselineCliPath(): string | null {
  const p = resolve(PROJECT_ROOT, ".baseline/worktree/bin/project-intel.mjs");
  return existsSync(p) ? p : null;
}

/**
 * Resolve the Node CLI used during migration (the compiled dist entry, falling
 * back to the dev tsx entry). Returns null when neither is available yet.
 */
export function nodeCliPath(): string | null {
  const dist = resolve(PROJECT_ROOT, "dist/cli.js");
  if (existsSync(dist)) return dist;
  const src = resolve(PROJECT_ROOT, "src/cli.ts");
  return existsSync(src) ? src : null;
}

/**
 * Run a command with `--json` against both implementations and return parsed
 * envelopes. Used by equivalence tests once the Node CLI dispatches commands.
 */
export function runDual(
  args: readonly string[],
  cwd: string,
  options: { nodeExec?: string } = {}
): DualRunResult {
  const result: DualRunResult = { baseline: null, candidate: null };
  const baseCli = baselineCliPath();
  const nodeCli = nodeCliPath();

  const run = (cli: string | null, exec: string): DualRunResult["baseline"] => {
    if (!cli) return null;
    const r = spawnSync(exec, [cli, "--json", ...args], {
      cwd,
      encoding: "utf8",
      timeout: 60_000,
    });
    let envelope: unknown = null;
    try {
      envelope = r.stdout ? JSON.parse(r.stdout) : null;
    } catch {
      envelope = null;
    }
    return { exitCode: r.status ?? -1, envelope, stdout: r.stdout ?? "" };
  };

  if (baseCli) result.baseline = run(baseCli, process.execPath);
  // Candidate Node CLI runs through tsx when it is the .ts dev entry.
  const nodeExec =
    options.nodeExec ?? (nodeCli && nodeCli.endsWith(".ts") ? "tsx" : process.execPath);
  result.candidate = run(nodeCli, nodeExec);
  return result;
}
