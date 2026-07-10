import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const readJson = (path) => JSON.parse(readFileSync(resolve(root, path), "utf8"));
const packageJson = readJson("package.json");
const claude = readJson("plugins/project-intelligence/.claude-plugin/plugin.json");
const codex = readJson("plugins/project-intelligence/.codex-plugin/plugin.json");
const python = readFileSync(resolve(root, "plugins/project-intelligence/scripts/project_intel.py"), "utf8");
const match = python.match(/^VERSION\s*=\s*"([^"]+)"/m);

if (!match) throw new Error("Unable to find Python CLI VERSION");
const version = match[1];
const values = [packageJson.version, claude.version, codex.version.split("+")[0], version];
if (new Set(values).size !== 1) {
  throw new Error(`Release versions differ: ${values.join(", ")}`);
}
console.log(`Release metadata is consistent: ${version}`);
