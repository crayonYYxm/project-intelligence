import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const packageCheckRoot = mkdtempSync(join(tmpdir(), "project-intelligence-package-"));
const npmEnvironment = {
  ...process.env,
  npm_config_cache: join(packageCheckRoot, "npm-cache"),
};
const quoteCmdArgument = (value) => {
  const text = String(value);
  if (/["\r\n]/.test(text)) {
    throw new Error(`Unsupported character in npm argument: ${text}`);
  }
  return /[\s&|<>^()]/.test(text) ? `"${text}"` : text;
};
const runNpm = (args, options = {}) => {
  if (process.platform !== "win32") {
    return execFileSync("npm", args, options);
  }
  const command = ["npm", ...args.map(quoteCmdArgument)].join(" ");
  return execFileSync(process.env.ComSpec || "cmd.exe", ["/d", "/s", "/c", command], options);
};
process.once("exit", () => rmSync(packageCheckRoot, { recursive: true, force: true }));

const result = JSON.parse(runNpm(
  ["pack", "--dry-run", "--json"],
  { encoding: "utf8", env: npmEnvironment },
));
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
  "plugins/project-intelligence/scripts/project_intel_lib/design_documents.py",
  "plugins/project-intelligence/scripts/project_intel_lib/requirements.py",
  "plugins/project-intelligence/scripts/project_intel_lib/requirement_documents.py",
  "plugins/project-intelligence/scripts/project_intel_lib/testing.py",
  "plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py",
  "plugins/project-intelligence/assets/plugin-intro.html",
  "plugins/project-intelligence/skills/project-test/SKILL.md",
  "plugins/project-intelligence/skills/project-design/SKILL.md",
  "plugins/project-intelligence/skills/project-design/references/bug-design-template.md",
  "plugins/project-intelligence/skills/project-design/references/requirement-design-template.md",
  "plugins/project-intelligence/skills/project-design/scripts/validate_design_doc.py",
  "docs/project-intelligence-guide.md",
]) {
  if (!files.includes(required)) {
    throw new Error(`npm tarball is missing ${required}`);
  }
}

const skillRoot = resolve("plugins/project-intelligence/skills");
const routingSkillFiles = readdirSync(skillRoot, { withFileTypes: true })
  .filter((item) => item.isDirectory())
  .map((item) => `plugins/project-intelligence/skills/${item.name}/SKILL.md`);
for (const required of routingSkillFiles) {
  if (!files.includes(required)) {
    throw new Error(`npm tarball is missing routing Skill ${required}`);
  }
}

const smokeRoot = packageCheckRoot;
try {
  const packed = JSON.parse(runNpm(
    ["pack", "--json", "--pack-destination", smokeRoot],
    { encoding: "utf8", env: npmEnvironment },
  ));
  const tarball = resolve(smokeRoot, packed[0]?.filename ?? "");
  const installRoot = join(smokeRoot, "installed");
  mkdirSync(installRoot, { recursive: true });
  runNpm(
    ["install", "--ignore-scripts", "--no-audit", "--no-fund", "--prefix", installRoot, tarball],
    { stdio: "pipe", env: npmEnvironment },
  );
  const installedBin = join(installRoot, "node_modules", "project-intelligence", "bin", "project-intel.mjs");
  const versionOutput = execFileSync(process.execPath, [installedBin, "--version"], { encoding: "utf8" });
  if (!versionOutput.includes(result[0]?.version ?? "")) {
    throw new Error(`installed npm launcher returned an unexpected version: ${versionOutput.trim()}`);
  }
  execFileSync(process.execPath, [installedBin, "--help"], { stdio: "pipe" });
} finally {
  rmSync(smokeRoot, { recursive: true, force: true });
}

console.log(`npm package contents and installed launcher verified: ${files.length} files`);
