#!/usr/bin/env node
// Phase 5.4: Rollback-read verification.
//
// Writes a `.project-intel` via the Node core, then reads it back with the v0.6.1
// baseline CLI (from the immutable worktree). Verifies 0.6.1 can read Node-written
// schema data without corruption (AC-13). Exits non-zero on failure.
//
// Usage: node scripts/rollback-read.mjs

import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const NODE_BIN = join(ROOT, "bin", "project-intel.mjs");
const BASELINE_BIN = join(ROOT, ".baseline", "worktree", "bin", "project-intel.mjs");

function main() {
  if (!existsSync(BASELINE_BIN)) {
    console.error("Baseline v0.6.1 worktree missing. Run plan 0.2 first.");
    process.exit(1);
  }
  const tmp = mkdtempSync(join(tmpdir(), "pi-rollback-"));
  mkdirSync(join(tmp, "backend"), { recursive: true });
  writeFileSync(join(tmp, "backend/Svc.py"), "class Svc: pass\n");
  writeFileSync(join(tmp, "package.json"), '{"name":"rollback"}');

  try {
    // 1. Node core writes .project-intel.
    const write = spawnSync(process.execPath, [NODE_BIN, "init", "--no-graph"], { encoding: "utf8", cwd: tmp, timeout: 30_000 });
    if ((write.status ?? -1) !== 0) throw new Error(`Node init failed: ${write.stderr}`);
    const nodeManifest = join(tmp, ".project-intel", "manifest.json");
    if (!existsSync(nodeManifest)) throw new Error("Node init produced no manifest.json");
    const schemaVersion = JSON.parse(readFileSync(nodeManifest, "utf8")).schemaVersion;
    if (schemaVersion !== 2) throw new Error(`Node wrote schemaVersion ${schemaVersion}, expected 2`);
    console.log(`✅ Node core wrote .project-intel (schemaVersion ${schemaVersion})`);

    // 2. v0.6.1 baseline reads it back (it also needs Python, which is fine — this
    //    verifies the *data* compatibility, not the product's runtime dep).
    const read = spawnSync(process.execPath, [BASELINE_BIN, "doctor", "--json"], { encoding: "utf8", cwd: tmp, timeout: 30_000 });
    if ((read.status ?? -1) !== 0) throw new Error(`0.6.1 doctor failed on Node-written data: ${read.stderr}`);
    const envelope = JSON.parse(read.stdout);
    if (envelope.ok !== true) throw new Error(`0.6.1 could not read Node-written data: ${envelope.error}`);
    const initialized = envelope.result?.project?.initialized;
    if (initialized !== true) throw new Error(`0.6.1 reports project not initialized on Node-written data`);
    console.log("✅ v0.6.1 baseline successfully read Node-written .project-intel (no corruption)");

    // 3. Verify no corrupt files (JSON parses cleanly).
    for (const f of ["manifest.json", "config.json", "knowledge/frontend.json", "knowledge/backend.json"]) {
      JSON.parse(readFileSync(join(tmp, ".project-intel", f), "utf8"));
    }
    console.log("✅ All .project-intel JSON files parse cleanly");

    console.log("\nRollback-read verification PASSED.");
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

main();
