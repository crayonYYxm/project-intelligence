// Requirement layout + artifact helpers (phase 3.D.5), ported from
// requirements.requirement_dir / ARTIFACT_FILES / migrate_layout. The v2 layout
// stores new requirements under `.project-intel/requirements/<date>-<id>-<title>/`
// (no by-id/); id-only and legacy by-id archives remain readable.

import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { requirementDir, legacyManifestPath, manifestPath, activeManifestPath } from "./state-machine.js";
import { RequirementError } from "../errors.js";
export { ARTIFACT_FILES, artifactFilename } from "./artifacts.js";

/** Whether a requirement id has a registered archive (v2 or legacy). */
export function hasRequirement(root: string, requirementId: string): boolean {
  return existsSync(activeManifestPath(root, requirementId));
}

/** Migrate a legacy by-id archive to the v2 direct layout (mirrors migrate_layout). */
export function migrateLayout(root: string, requirementId: string, apply: boolean): { migrated: boolean; from?: string; to?: string } {
  const legacy = legacyManifestPath(root, requirementId);
  if (!existsSync(legacy)) return { migrated: false };
  if (existsSync(manifestPath(root, requirementId))) return { migrated: false }; // v2 already present
  const legacyManifest = JSON.parse(readFileSync(legacy, "utf8")) as {
    requirementName?: unknown;
    versionDate?: unknown;
  };
  const requirementName = String(legacyManifest.requirementName ?? "").trim() || "untitled";
  const versionDate = String(legacyManifest.versionDate ?? "").trim() || undefined;
  const fromDir = join(legacy, "..");
  const toDir = requirementDir(root, requirementId, requirementName, versionDate);
  const target = join(toDir, "manifest.json");
  if (existsSync(toDir)) {
    throw new RequirementError(`迁移目标目录已存在，拒绝覆盖：${toDir}`);
  }
  if (apply) {
    copyTree(fromDir, toDir);
    rewriteManifestPaths(target, requirementId, `${relative(root, toDir).replaceAll("\\", "/")}/`);
    return { migrated: true, from: fromDir, to: toDir };
  }
  return { migrated: true, from: fromDir, to: toDir };
}

function copyTree(src: string, dest: string): void {
  if (!existsSync(src) || !statSync(src).isDirectory()) {
    throw new RequirementError(`legacy requirement archive is not a directory: ${src}`);
  }
  mkdirSync(dest, { recursive: true });
  const entries = readdirSync(src);
  for (const name of entries) {
    const from = join(src, name);
    const to = join(dest, name);
    if (statSync(from).isDirectory()) {
      copyTree(from, to);
    } else {
      copyFileSync(from, to);
    }
  }
}

function rewriteManifestPaths(path: string, requirementId: string, directPrefix: string): void {
  const manifest = JSON.parse(readFileSync(path, "utf8")) as unknown;
  const legacyPrefix = `.project-intel/requirements/by-id/${requirementId}/`;
  const rewrite = (value: unknown): unknown => {
    if (typeof value === "string") return value.split(legacyPrefix).join(directPrefix);
    if (Array.isArray(value)) return value.map(rewrite);
    if (value && typeof value === "object") {
      return Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, rewrite(item)]));
    }
    return value;
  };
  writeFileSync(path, `${JSON.stringify(rewrite(manifest), null, 2)}\n`);
}
