import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync, readlinkSync, realpathSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { RequirementError } from "../errors.js";

export interface ScopeEntry {
  status: string;
  path: string;
  oldPath?: string;
  sha256: string;
}

export interface ScopeSnapshot {
  capturedAt: string;
  gitAvailable: boolean;
  gitCommit: string;
  diffHash: string;
  files: string[];
  entries: ScopeEntry[];
  artifactFiles?: string[];
  evidenceFiles?: string[];
  evidenceEntries?: ScopeEntry[];
  evidenceDiffHash?: string;
  baselineFiles?: string[];
}

interface ScopeManifest {
  requirementId?: string;
  baselineCommit?: string | null;
  baselineScope?: { entries?: ScopeEntry[] } | null;
  artifacts?: Record<string, unknown>[];
  testEvidence?: Record<string, unknown>[];
}

function nowIso(): string {
  return new Date().toISOString();
}

function git(root: string, args: string[]): { code: number; stdout: Buffer } {
  const result = spawnSync("git", args, {
    cwd: root,
    encoding: null,
    timeout: 10_000,
    stdio: ["ignore", "pipe", "ignore"],
  });
  return {
    code: typeof result.status === "number" ? result.status : 127,
    stdout: Buffer.isBuffer(result.stdout) ? result.stdout : Buffer.alloc(0),
  };
}

function normalizePath(value: string): string {
  return value.replaceAll("\\", "/").replace(/^\.\//, "");
}

export function isBusinessPath(value: string): boolean {
  const clean = normalizePath(value.trim());
  return Boolean(clean)
    && clean !== ".project-intel"
    && clean !== ".git"
    && !clean.startsWith(".project-intel/")
    && !clean.startsWith(".git/");
}

function fileDigest(root: string, pathValue: string): string {
  const absolute = resolve(root, pathValue);
  if (!existsSync(absolute)) return "<deleted>";
  const stat = lstatSync(absolute);
  if (stat.isSymbolicLink()) {
    return createHash("sha256").update(`symlink\0${readlinkSync(absolute)}`).digest("hex");
  }
  if (!stat.isFile()) return `<${stat.isDirectory() ? "directory" : "special"}>`;
  return createHash("sha256").update(readFileSync(absolute)).digest("hex");
}

function parsePorcelain(root: string, raw: Buffer, excluded: Set<string>): ScopeEntry[] {
  const tokens = raw.toString("utf8").split("\0");
  const entries: ScopeEntry[] = [];
  for (let index = 0; index < tokens.length;) {
    const token = tokens[index++] ?? "";
    if (!token) continue;
    const status = token.slice(0, 2);
    const pathValue = normalizePath(token.slice(3));
    let oldPath: string | undefined;
    if ((status.includes("R") || status.includes("C")) && index < tokens.length) {
      oldPath = normalizePath(tokens[index++] ?? "");
    }
    if (!isBusinessPath(pathValue) || excluded.has(pathValue)) continue;
    const entry: ScopeEntry = {
      status,
      path: pathValue,
      sha256: fileDigest(root, pathValue),
    };
    if (oldPath) entry.oldPath = oldPath;
    entries.push(entry);
  }
  return entries;
}

function committedEntries(
  root: string,
  baselineCommit: string | null | undefined,
  currentCommit: string,
  excluded: Set<string>
): { ok: boolean; entries: ScopeEntry[] } {
  const baseline = String(baselineCommit ?? "").trim();
  if (!baseline || baseline === currentCommit) return { ok: true, entries: [] };
  if (!/^[0-9a-f]{7,64}$/i.test(baseline) || !/^[0-9a-f]{7,64}$/i.test(currentCommit)) {
    return { ok: false, entries: [] };
  }
  const result = git(root, ["diff", "--name-status", "-z", "--find-renames", baseline, currentCommit, "--"]);
  if (result.code !== 0) return { ok: false, entries: [] };
  const tokens = result.stdout.toString("utf8").split("\0");
  const entries: ScopeEntry[] = [];
  for (let index = 0; index < tokens.length;) {
    const status = tokens[index++] ?? "";
    if (!status) continue;
    const kind = status[0] ?? "";
    if (kind === "R" || kind === "C") {
      const oldPath = normalizePath(tokens[index++] ?? "");
      const pathValue = normalizePath(tokens[index++] ?? "");
      if (isBusinessPath(pathValue) && !excluded.has(pathValue)) {
        entries.push({ status, path: pathValue, oldPath, sha256: fileDigest(root, pathValue) });
      }
      if (kind === "R" && isBusinessPath(oldPath) && !excluded.has(oldPath)) {
        entries.push({ status: "D", path: oldPath, sha256: "<deleted>" });
      }
      continue;
    }
    const pathValue = normalizePath(tokens[index++] ?? "");
    if (!isBusinessPath(pathValue) || excluded.has(pathValue)) continue;
    entries.push({ status, path: pathValue, sha256: fileDigest(root, pathValue) });
  }
  return { ok: true, entries };
}

function snapshotHash(commit: string, entries: ScopeEntry[]): string {
  const encoded = JSON.stringify({ commit, entries });
  return createHash("sha256").update(encoded).digest("hex");
}

export function captureScopeSnapshot(
  root: string,
  options: { excludePaths?: string[]; baselineCommit?: string | null } = {}
): ScopeSnapshot {
  const excluded = new Set((options.excludePaths ?? []).map(normalizePath));
  const status = git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"]);
  const commitResult = git(root, ["rev-parse", "HEAD"]);
  const commit = commitResult.stdout.toString("utf8").trim();
  if (status.code !== 0 || commitResult.code !== 0 || !commit) {
    return {
      capturedAt: nowIso(),
      gitAvailable: false,
      gitCommit: "",
      diffHash: "",
      files: [],
      entries: [],
    };
  }

  const committed = committedEntries(root, options.baselineCommit, commit, excluded);
  if (!committed.ok) {
    return {
      capturedAt: nowIso(),
      gitAvailable: false,
      gitCommit: "",
      diffHash: "",
      files: [],
      entries: [],
    };
  }

  const byPath = new Map<string, ScopeEntry>();
  for (const entry of committed.entries) byPath.set(entry.path, entry);
  for (const entry of parsePorcelain(root, status.stdout, excluded)) byPath.set(entry.path, entry);
  const entries = [...byPath.values()].sort((a, b) =>
    a.path.localeCompare(b.path, "en") || a.status.localeCompare(b.status, "en")
  );
  return {
    capturedAt: nowIso(),
    gitAvailable: true,
    gitCommit: commit,
    diffHash: snapshotHash(commit, entries),
    files: entries.map((entry) => entry.path),
    entries,
  };
}

function artifactPaths(manifest: ScopeManifest): Set<string> {
  const paths = new Set<string>();
  for (const artifact of manifest.artifacts ?? []) {
    for (const key of ["path", "sourcePath", "evidencePath"]) {
      const value = normalizePath(String(artifact[key] ?? "").trim());
      if (value) paths.add(value);
    }
  }
  for (const evidence of manifest.testEvidence ?? []) {
    for (const key of ["reportPath", "reportSourcePath", "reportOriginalPath"]) {
      const value = normalizePath(String(evidence[key] ?? "").trim());
      if (value) paths.add(value);
    }
  }
  return paths;
}

export function captureRequirementScope(root: string, manifest: ScopeManifest): ScopeSnapshot {
  const snapshot = captureScopeSnapshot(root, { baselineCommit: manifest.baselineCommit ?? null });
  if (!snapshot.gitAvailable) return snapshot;

  const baselineSignatures = new Set(
    (manifest.baselineScope?.entries ?? []).map((entry) => `${normalizePath(entry.path)}\0${entry.sha256}`)
  );
  const deltaEntries = snapshot.entries.filter(
    (entry) => !baselineSignatures.has(`${normalizePath(entry.path)}\0${entry.sha256}`)
  );
  const artifacts = artifactPaths(manifest);
  const evidenceEntries = deltaEntries.filter(
    (entry) => !artifacts.has(normalizePath(entry.path)) && !isUnderRequirementDir(entry.path, manifest.requirementId)
  );
  const artifactFiles = deltaEntries
    .filter((entry) => !evidenceEntries.includes(entry))
    .map((entry) => entry.path)
    .sort();
  const evidenceFiles = evidenceEntries.map((entry) => entry.path).sort();
  return {
    ...snapshot,
    entries: deltaEntries,
    files: deltaEntries.map((entry) => entry.path).sort(),
    baselineFiles: [...new Set((manifest.baselineScope?.entries ?? []).map((entry) => entry.path))].sort(),
    artifactFiles,
    evidenceFiles,
    evidenceEntries,
    evidenceDiffHash: snapshotHash(snapshot.gitCommit, evidenceEntries),
  };
}

function isUnderRequirementDir(pathValue: string, requirementId: string | undefined): boolean {
  if (!requirementId) return false;
  return normalizePath(pathValue).startsWith(`.project-intel/requirements/${requirementId}/`);
}

export function normalizeScopeFiles(root: string, files: string[]): string[] {
  const rootReal = realpathSync(root);
  const normalized = new Set<string>();
  for (const rawValue of files) {
    const raw = String(rawValue ?? "").trim();
    if (!raw) continue;
    const unresolved = isAbsolute(raw) ? resolve(raw) : resolve(rootReal, raw);
    const absolute = existsSync(unresolved) ? realpathSync(unresolved) : unresolved;
    const relativePath = normalizePath(relative(rootReal, absolute));
    if (relativePath === ".." || relativePath.startsWith("../") || isAbsolute(relativePath)) {
      throw new RequirementError(`文件范围越出项目目录：${raw}`);
    }
    if (isBusinessPath(relativePath)) normalized.add(relativePath);
  }
  return [...normalized].sort();
}

export function validateScopeSelection(root: string, files: string[], snapshot: ScopeSnapshot): string[] {
  if (!snapshot.gitAvailable || !snapshot.diffHash) {
    throw new RequirementError("无法读取 Git 状态，不能生成可追踪的需求证据。");
  }
  const selected = normalizeScopeFiles(root, files);
  const actual = new Set(snapshot.evidenceFiles ?? snapshot.files);
  const missing = [...actual].filter((pathValue) => !selected.includes(pathValue)).sort();
  if (missing.length > 0) {
    throw new RequirementError(`提交的文件范围遗漏实际 Git 变更：${missing.join(", ")}`);
  }
  return selected.length > 0 ? selected : [...actual].sort();
}

export function sameScope(
  expected: Pick<ScopeSnapshot, "gitCommit" | "diffHash" | "evidenceDiffHash">,
  actual: Pick<ScopeSnapshot, "gitCommit" | "diffHash" | "evidenceDiffHash">
): boolean {
  return expected.gitCommit === actual.gitCommit
    && (expected.evidenceDiffHash || expected.diffHash) === (actual.evidenceDiffHash || actual.diffHash);
}
