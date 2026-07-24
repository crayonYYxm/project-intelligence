import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

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

function extractPackFiles(result) {
  // npm pack --json returns either a list of pack results (older npm) or a dict
  // keyed by package name (newer npm with workspaces). Normalize to a file list.
  if (Array.isArray(result)) {
    return result[0]?.files?.map((item) => item.path) ?? [];
  }
  if (result && typeof result === "object") {
    const values = Object.values(result);
    const entry = values.find((v) => v && typeof v === "object" && Array.isArray(v.files));
    return entry?.files?.map((item) => item.path) ?? [];
  }
  return [];
}

// Build dist/ first (it's gitignored and not in the repo; prepack only fires on
// real npm pack, not --dry-run). This ensures a clean checkout can pass.
// Use npx for cross-platform tsc resolution (Windows needs .cmd suffix).
execFileSync(process.execPath, ["scripts/gen-version.mjs"], { cwd: ROOT, stdio: "ignore", env: npmEnvironment });
execFileSync("npx", ["tsc", "-p", "tsconfig.json"], { cwd: ROOT, stdio: "inherit", env: npmEnvironment, shell: process.platform === "win32" });

// Use --ignore-scripts to prevent prepack from running (we already built above;
// prepack's stdout would pollute the JSON output).
const packResult = JSON.parse(runNpm(
  ["pack", "--dry-run", "--json", "--ignore-scripts"],
  { encoding: "utf8", env: npmEnvironment },
));
const files = extractPackFiles(packResult);
const forbidden = files.filter((path) => path.includes("__pycache__") || path.endsWith(".pyc") || path.includes("/tests/"));
if (forbidden.length) {
  throw new Error(`npm tarball contains development artifacts: ${forbidden.join(", ")}`);
}
for (const required of [
  "bin/project-intel.mjs",
  "dist/cli.js",
  "dist/version.js",
  ".agents/plugins/marketplace.json",
  ".claude-plugin/marketplace.json",
  "plugins/project-intelligence/assets/plugin-intro.html",
  "plugins/project-intelligence/skills/project-test/SKILL.md",
  "plugins/project-intelligence/skills/project-design/SKILL.md",
  "plugins/project-intelligence/skills/project-design/references/bug-design-template.md",
  "plugins/project-intelligence/skills/project-design/references/requirement-design-template.md",
  "plugins/project-intelligence/skills/project-design/scripts/validate_design_doc.mjs",
  "docs/project-intelligence-guide.md",
]) {
  if (!files.includes(required)) {
    throw new Error(`npm tarball is missing ${required}`);
  }
}
// Reject any Python runtime sources in the shipped core (they are excluded from
// files; this is a defense-in-depth guard for AC-14).
const pythonSources = files.filter((path) => path.startsWith("plugins/project-intelligence/scripts/") && path.endsWith(".py"));
if (pythonSources.length) {
  throw new Error(`npm tarball must not ship Python runtime sources: ${pythonSources.join(", ")}`);
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
function firstEntry(obj) {
  if (Array.isArray(obj)) return obj[0];
  if (obj && typeof obj === "object") {
    const values = Object.values(obj);
    return values.find((v) => v && typeof v === "object" && typeof v.filename === "string");
  }
  return undefined;
}
try {
  const packed = JSON.parse(runNpm(
    ["pack", "--json", "--pack-destination", smokeRoot, "--ignore-scripts"],
    { encoding: "utf8", env: npmEnvironment },
  ));
  const packedEntry = firstEntry(packed);
  const tarball = resolve(smokeRoot, packedEntry?.filename ?? "");
  const version = packedEntry?.version ?? "";
  const installRoot = join(smokeRoot, "installed");
  mkdirSync(installRoot, { recursive: true });
  runNpm(
    ["install", "--ignore-scripts", "--no-audit", "--no-fund", "--prefix", installRoot, tarball],
    { stdio: "pipe", env: npmEnvironment },
  );
  const installedBin = join(installRoot, "node_modules", "project-intelligence", "bin", "project-intel.mjs");
  const versionOutput = execFileSync(process.execPath, [installedBin, "--version"], { encoding: "utf8" });
  if (version && !versionOutput.includes(version)) {
    throw new Error(`installed npm launcher returned an unexpected version: ${versionOutput.trim()}`);
  }
  execFileSync(process.execPath, [installedBin, "--help"], { stdio: "pipe" });
} finally {
  rmSync(smokeRoot, { recursive: true, force: true });
}

console.log(`npm package contents and installed launcher verified: ${files.length} files`);
