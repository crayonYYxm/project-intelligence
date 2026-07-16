import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const plugin = resolve(root, "plugins/project-intelligence");
const payload = JSON.parse(readFileSync(resolve(root, "evals/skill-behavior-scenarios.json"), "utf8"));
const available = new Set(
  readdirSync(resolve(plugin, "skills"), { withFileTypes: true })
    .filter((item) => item.isDirectory())
    .map((item) => item.name),
);

if (payload.schemaVersion !== 1 || !Array.isArray(payload.scenarios) || payload.scenarios.length < 5) {
  throw new Error("Skill behavior scenarios must use schemaVersion 1 and contain at least five scenarios");
}

const ids = new Set();
for (const scenario of payload.scenarios) {
  if (!scenario.id || ids.has(scenario.id)) throw new Error(`Invalid or duplicate scenario id: ${scenario.id}`);
  ids.add(scenario.id);
  if (!scenario.prompt?.trim()) throw new Error(`Scenario prompt missing: ${scenario.id}`);
  if (!Array.isArray(scenario.expectedSkills) || !scenario.expectedSkills.length) {
    throw new Error(`Scenario expectedSkills missing: ${scenario.id}`);
  }
  for (const skill of [...scenario.expectedSkills, ...(scenario.expectedOrder ?? []), ...(scenario.forbiddenSkills ?? [])]) {
    if (!available.has(skill)) throw new Error(`Scenario ${scenario.id} references missing skill ${skill}`);
  }
  for (const skill of scenario.expectedOrder ?? []) {
    if (!scenario.expectedSkills.includes(skill)) {
      throw new Error(`Scenario ${scenario.id} expectedOrder contains non-required skill ${skill}`);
    }
  }
}

console.log(`Skill behavior scenario contracts verified: ${payload.scenarios.length} scenarios, ${available.size} skills`);
