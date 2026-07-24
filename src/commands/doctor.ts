// `doctor` command (phase 3.B.2), ported from application.doctor_report.
//
// Reports runtime + project + tooling + graph-source state. In a Node-only
// environment it reports the Node runtime (not Python), satisfying AC-01.

import { existsSync } from "node:fs";
import { join } from "node:path";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { detectPackage } from "../scanner/quality.js";
import { detectTooling } from "../app/project-state.js";
import { sanitizeTooling } from "../scanner/core.js";
import { detectGraphSources } from "../graph/sources.js";
import { projectIntelDir } from "./init.js";
import { loadJson } from "../fs/atomic-write.js";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { VERSION } from "../version.js";

/** Build the doctor report (mirrors doctor_report). */
export function doctorReport(root: string): Record<string, unknown> {
  const pkg = detectPackage(root);
  const tooling = detectTooling(root, pkg);
  const configPath = join(projectIntelDir(root), "config.json");
  const config = existsSync(configPath) ? loadJson<Record<string, unknown>>(configPath, {}) : {};
  return {
    version: VERSION,
    runtime: { name: "node", version: process.version, executable: process.execPath },
    project: {
      path: ".",
      initialized: existsSync(join(projectIntelDir(root), "manifest.json")),
      configSchemaVersion: config.schemaVersion ?? null,
      frameworks: pkg.frameworks,
      packages: pkg.packages,
    },
    pluginBundle: { available: marketplaceBundleAvailable() },
    tooling: sanitizeTooling(tooling),
    graphSources: detectGraphSources(root),
  };
}

function marketplaceBundleAvailable(): boolean {
  const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
  return existsSync(join(packageRoot, ".agents", "plugins", "marketplace.json"))
    && existsSync(join(packageRoot, ".claude-plugin", "marketplace.json"));
}

export function runDoctor(root: string, args: string[], global: GlobalOptions): CommandResult {
  const report = doctorReport(root);
  if (global.jsonMode) {
    return ok(report);
  }
  // Text mode: print a human-readable summary.
  console.log(`Project Intelligence runtime: node ${process.version}`);
  console.log(`project initialized: ${String((report.project as Record<string, unknown>)?.initialized)}`);
  console.log(`frameworks: ${(pkgFrameworks(report) as string[]).join(", ") || "未识别"}`);
  void args;
  return ok(report);
}

function pkgFrameworks(report: Record<string, unknown>): unknown {
  return (report.project as Record<string, unknown>)?.frameworks ?? [];
}
