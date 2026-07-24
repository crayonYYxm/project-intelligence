// Requirement layout + artifact helpers (phase 3.D.5), ported from
// requirements.requirement_dir / ARTIFACT_FILES / migrate_layout. The v2 layout
// stores requirements directly under `.project-intel/requirements/<id>/` (no
// by-id/); legacy by-id archives are read transparently for 0.6.1 compat (AC-04).

import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { requirementDir, legacyManifestPath, manifestPath, activeManifestPath } from "./state-machine.js";
import { RequirementError } from "../errors.js";

export const ARTIFACT_FILES: Record<string, string> = {
  requirement: "requirement.md",
  design: "design.md",
  "requirement-design": "design.md",
  plan: "plan.md",
  test: "test-report.md",
  "test-report": "test-report.md",
  "unit-test": "test-report.md",
  "service-test": "test-report.md",
  "manual-test": "test-report.md",
  closure: "closure-summary.md",
};

/** Resolve the canonical filename for an artifact type. */
export function artifactFilename(type: string): string {
  return ARTIFACT_FILES[type] ?? `${type}.md`;
}

/** Whether a requirement id has a registered archive (v2 or legacy). */
export function hasRequirement(root: string, requirementId: string): boolean {
  return existsSync(activeManifestPath(root, requirementId));
}

/** Migrate a legacy by-id archive to the v2 direct layout (mirrors migrate_layout). */
export function migrateLayout(root: string, requirementId: string, apply: boolean): { migrated: boolean; from?: string; to?: string } {
  const legacy = legacyManifestPath(root, requirementId);
  if (!existsSync(legacy)) return { migrated: false };
  const target = manifestPath(root, requirementId);
  if (existsSync(target)) return { migrated: false }; // v2 already present
  const fromDir = join(legacy, "..");
  const toDir = requirementDir(root, requirementId);
  if (apply) {
    copyTree(fromDir, toDir);
    rewriteManifestPaths(target, requirementId);
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

function rewriteManifestPaths(path: string, requirementId: string): void {
  const manifest = JSON.parse(readFileSync(path, "utf8")) as unknown;
  const legacyPrefix = `.project-intel/requirements/by-id/${requirementId}/`;
  const directPrefix = `.project-intel/requirements/${requirementId}/`;
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
