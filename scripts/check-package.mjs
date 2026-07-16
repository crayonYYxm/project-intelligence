import { execFileSync } from "node:child_process";

const result = JSON.parse(execFileSync("npm", ["pack", "--dry-run", "--json"], { encoding: "utf8" }));
const files = result[0]?.files?.map((item) => item.path) ?? [];
const forbidden = files.filter((path) => path.includes("__pycache__") || path.endsWith(".pyc") || path.includes("/tests/"));
if (forbidden.length) {
  throw new Error(`npm tarball contains development artifacts: ${forbidden.join(", ")}`);
}
for (const required of [
  "bin/project-intel.mjs",
  ".agents/plugins/marketplace.json",
  ".claude-plugin/marketplace.json",
  "plugins/project-intelligence/scripts/project_intel.py",
  "plugins/project-intelligence/scripts/project_intel_lib/application.py",
  "plugins/project-intelligence/scripts/project_intel_lib/requirements.py",
  "plugins/project-intelligence/scripts/project_intel_lib/testing.py",
  "plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py",
  "plugins/project-intelligence/skills/project-test/SKILL.md",
  "docs/project-intelligence-guide.md",
]) {
  if (!files.includes(required)) {
    throw new Error(`npm tarball is missing ${required}`);
  }
}
console.log(`npm package contents verified: ${files.length} files`);
