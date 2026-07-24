#!/usr/bin/env node
// Phase 5.1: Smoke-test the npm pack artifact in a clean temp directory.
//
// Packs the project, installs it into a fresh temp dir, runs the core flow
// (--version / doctor / init --dry-run), and verifies no Python subprocess is
// spawned during execution by running with a PATH that excludes Python. AC-09.

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, mkdirSync, rmSync, readdirSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const tmp = mkdtempSync(join(tmpdir(), "pi-smoke-"));

function npm(args, opts = {}) {
  return execFileSync("npm", args, { encoding: "utf8", cwd: opts.cwd ?? ROOT, env: { ...process.env, ...opts.env }, stdio: opts.stdio ?? "pipe" });
}

try {
  // 1. Build + pack.
  execFileSync(process.execPath, ["scripts/gen-version.mjs"], { cwd: ROOT, encoding: "utf8", stdio: "inherit" });
  const packed = JSON.parse(npm(["pack", "--json", "--pack-destination", tmp, "--ignore-scripts"]));
  const entry = Array.isArray(packed) ? packed[0] : Object.values(packed)[0];
  const tarball = resolve(tmp, entry.filename);
  if (!existsSync(tarball)) throw new Error(`pack did not produce tarball: ${tarball}`);
  console.log(`✅ packed: ${entry.filename}`);

  // 2. Install into clean temp.
  const installDir = join(tmp, "installed");
  mkdirSync(installDir, { recursive: true });
  npm(["install", "--ignore-scripts", "--no-audit", "--no-fund", "--prefix", installDir, tarball], { cwd: installDir });
  console.log("✅ installed in clean temp dir");

  // 3. Core flow with Python-free PATH.
  // Build a PATH that contains ONLY the Node binary directory. This proves
  // the CLI runs without any Python runtime available (AC-01/AC-09).
  // We deliberately exclude /usr/bin and /bin to avoid python3 on macOS/Linux.
  const bin = join(installDir, "node_modules", "project-intelligence", "bin", "project-intel.mjs");
  const nodeBinDir = dirname(process.execPath);
  const cleanPath = nodeBinDir;

  for (const [label, args] of [["--version", ["--version"]], ["doctor", ["doctor"]], ["init --dry-run", ["init", "--dry-run", "--no-graph"]]]) {
    const r = spawnSync(process.execPath, [bin, ...args], {
      encoding: "utf8",
      cwd: installDir,
      timeout: 30_000,
      env: { ...process.env, PATH: cleanPath },
    });
    if ((r.status ?? -1) !== 0) {
      throw new Error(`core flow '${label}' failed (exit ${r.status}): ${r.stderr || r.stdout}`);
    }
    console.log(`✅ ${label} → exit 0 (Python-free PATH)`);
  }

  // 5. Static scan for Python runtime references in the INSTALLED package
  // (not the workspace source — the installed dist is what ships).
  const installedDist = join(installDir, "node_modules", "project-intelligence", "dist");
  const installedBin = join(installDir, "node_modules", "project-intelligence", "bin");
  const pyInDist = walkForPy(installedDist);
  const pyInBin = walkForPy(installedBin);
  const allPy = [...pyInDist, ...pyInBin];
  if (allPy.length > 0) {
    throw new Error(`installed package contains .py files: ${allPy.join(", ")}`);
  }
  console.log("✅ no .py files in installed package");

  console.log("\nSmoke test PASSED.");
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

function walkForPy(dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walkForPy(full, out);
    else if (name.endsWith(".py")) out.push(full);
  }
  return out;
}
