import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { tmpdir } from "node:os";

const cacheDir = join(tmpdir(), "project-intelligence-npm-cache");
const result = spawnSync("npm", ["pack", "--dry-run", "--cache", cacheDir], {
  stdio: "inherit",
  shell: process.platform === "win32",
});

process.exit(result.status ?? 1);
