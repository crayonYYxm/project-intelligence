#!/usr/bin/env node
// Run the TypeScript unit test suite under node:test with the tsx loader.
//
// Portable across Node 18.11+ and 20+: globs `src/**/*.test.ts`, then invokes
// `node --import tsx --test <files>` so there is no separate test runner or
// config. Used by `npm run test:unit`; aggregated into `npm test` (run-tests.mjs).

import { spawnSync } from "node:child_process";
import { readdirSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function walk(dir, out = []) {
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return out;
  }
  for (const name of entries) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walk(full, out);
    else if (name.endsWith(".test.ts")) out.push(full);
  }
  return out;
}

function main() {
  const files = walk(join(ROOT, "src"));
  if (files.length === 0) {
    console.log("No unit tests found under src/ (expected during early migration).");
    return;
  }
  // node --import tsx --test <files...>
  const result = spawnSync(process.execPath, ["--import", "tsx", "--test", ...files], {
    cwd: ROOT,
    stdio: "inherit",
  });
  if (result.error) {
    console.error(`Unable to start node:test: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

main();
