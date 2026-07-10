#!/usr/bin/env node

import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cli = resolve(packageRoot, "plugins/project-intelligence/scripts/project_intel.py");

if (!existsSync(cli)) {
  console.error(`Project Intelligence CLI is missing: ${cli}`);
  process.exit(1);
}

const candidates = process.platform === "win32"
  ? [["py", ["-3"]], ["python3", []], ["python", []]]
  : [["python3", []], ["python", []]];

for (const [command, prefix] of candidates) {
  const result = spawnSync(command, [...prefix, cli, ...process.argv.slice(2)], { stdio: "inherit" });
  if (result.error?.code === "ENOENT") {
    continue;
  }
  if (result.error) {
    console.error(`Unable to start ${command}: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

console.error("Project Intelligence requires Python 3.9 or newer. Install python3 and run the command again.");
process.exit(1);
