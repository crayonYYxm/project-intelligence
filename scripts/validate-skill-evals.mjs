import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildSkillNamePattern, evaluateSkillRoute, skillToolInvocations } from "./skill-eval-events.mjs";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const plugin = resolve(root, "plugins/project-intelligence");
const payload = JSON.parse(readFileSync(resolve(root, "evals/skill-behavior-scenarios.json"), "utf8"));
const available = new Set(
  readdirSync(resolve(plugin, "skills"), { withFileTypes: true })
    .filter((item) => item.isDirectory())
    .map((item) => item.name),
);
const skillText = (name) => readFileSync(resolve(plugin, "skills", name, "SKILL.md"), "utf8");

if (payload.schemaVersion !== 1 || !Array.isArray(payload.scenarios) || payload.scenarios.length < 5) {
  throw new Error("Skill behavior scenarios must use schemaVersion 1 and contain at least five scenarios");
}

const ids = new Set();
const routeClasses = new Set([
  "brainstorm",
  "bug-lifecycle",
  "bug-lifecycle-continuation",
  "delivery",
  "feature-lifecycle",
  "implementation",
  "initialization",
  "maintenance",
  "negative",
  "orchestration",
  "planning",
  "quality",
  "read-only",
  "refresh",
  "standalone-design",
  "standards",
  "testing",
]);
const requiredNaturalLanguageScenarios = new Set([
  "plain-write-plan",
  "plain-start-fixing",
  "closure-summary-required",
  "plain-continue-from-diagnosis",
  "standalone-development-design",
  "git-pull-refreshes-facts-not-lifecycle",
  "cloud-plugin-update-is-not-project-refresh",
  "new-page-is-not-project-intelligence-init",
  "first-time-project-intelligence-init",
  "stable-plan-orchestrates-subagents",
  "explain-project-standard-levels",
]);
for (const scenario of payload.scenarios) {
  if (!scenario.id || ids.has(scenario.id)) throw new Error(`Invalid or duplicate scenario id: ${scenario.id}`);
  ids.add(scenario.id);
  if (!scenario.prompt?.trim()) throw new Error(`Scenario prompt missing: ${scenario.id}`);
  const promptedSkill = [...available].find((skill) => scenario.prompt.includes(skill));
  if (promptedSkill) throw new Error(`Scenario ${scenario.id} names ${promptedSkill} instead of testing natural triggering`);
  if (!routeClasses.has(scenario.routeClass)) throw new Error(`Scenario routeClass invalid: ${scenario.id}`);
  if (!Array.isArray(scenario.expectedSkills)) {
    throw new Error(`Scenario expectedSkills missing: ${scenario.id}`);
  }
  if (scenario.allowedSkills !== undefined && !Array.isArray(scenario.allowedSkills)) {
    throw new Error(`Scenario allowedSkills must be an array: ${scenario.id}`);
  }
  if (!scenario.expectedSkills.length && !(scenario.forbiddenSkills ?? []).length) {
    throw new Error(`Scenario must require or forbid at least one skill: ${scenario.id}`);
  }
  for (const skill of [...scenario.expectedSkills, ...(scenario.allowedSkills ?? []), ...(scenario.expectedOrder ?? []), ...(scenario.forbiddenSkills ?? [])]) {
    if (!available.has(skill)) throw new Error(`Scenario ${scenario.id} references missing skill ${skill}`);
  }
  const allowedSet = new Set(scenario.allowedSkills ?? []);
  if (allowedSet.size !== (scenario.allowedSkills ?? []).length) {
    throw new Error(`Scenario ${scenario.id} repeats an allowed skill`);
  }
  const overlap = [...scenario.expectedSkills, ...(scenario.allowedSkills ?? [])]
    .filter((skill) => (scenario.forbiddenSkills ?? []).includes(skill));
  if (overlap.length) throw new Error(`Scenario ${scenario.id} both requires and forbids ${overlap.join(",")}`);
  for (const skill of scenario.expectedOrder ?? []) {
    if (!scenario.expectedSkills.includes(skill)) {
      throw new Error(`Scenario ${scenario.id} expectedOrder contains non-required skill ${skill}`);
    }
  }
  if (scenario.routeClass === "feature-lifecycle") {
    const prefix = ["project-intake", "project-spec", "project-design"];
    if (!prefix.every((skill, index) => scenario.expectedOrder?.[index] === skill)) {
      throw new Error(`Feature lifecycle ${scenario.id} must start intake -> spec -> design`);
    }
  }
  if (scenario.routeClass === "bug-lifecycle") {
    const prefix = ["project-intake", "project-spec", "project-debug", "project-design"];
    if (!prefix.every((skill, index) => scenario.expectedOrder?.[index] === skill)) {
      throw new Error(`Bug lifecycle ${scenario.id} must start intake -> spec -> debug -> design`);
    }
  }
  if (scenario.routeClass === "standalone-design") {
    if (scenario.expectedSkills.length !== 1 || scenario.expectedSkills[0] !== "project-design") {
      throw new Error(`Standalone design ${scenario.id} must require only project-design`);
    }
    for (const forbidden of ["project-intake", "project-spec", "project-task"]) {
      if (!(scenario.forbiddenSkills ?? []).includes(forbidden)) {
        throw new Error(`Standalone design ${scenario.id} must forbid ${forbidden}`);
      }
    }
  }
  if (scenario.routeClass === "negative" && scenario.expectedSkills.length) {
    throw new Error(`Negative scenario ${scenario.id} must not require a project skill`);
  }
}

for (const id of requiredNaturalLanguageScenarios) {
  if (!ids.has(id)) throw new Error(`Required natural-language routing scenario missing: ${id}`);
}

const positivelyCoveredSkills = new Set(payload.scenarios.flatMap((scenario) => scenario.expectedSkills));
const uncoveredSkills = [...available].filter((skill) => !positivelyCoveredSkills.has(skill));
if (uncoveredSkills.length) {
  throw new Error(`Every packaged Skill needs a positive natural-language route scenario; missing: ${uncoveredSkills.join(", ")}`);
}

const eventPattern = buildSkillNamePattern(available);
const claudeToolEvent = JSON.stringify({
  type: "assistant",
  message: { content: [{ type: "tool_use", name: "Skill", input: { skill: "project-intelligence:project-intake" } }] },
});
const codexSkillEvent = JSON.stringify({
  type: "item.completed",
  item: { type: "skill_call", arguments: { name: "project-design" } },
});
const finalMessageOnly = JSON.stringify({
  type: "item.completed",
  item: { type: "agent_message", text: "WORKFLOW: project-intake -> project-spec -> project-design" },
});
if (skillToolInvocations(claudeToolEvent, eventPattern).join(",") !== "project-intake") {
  throw new Error("Claude Skill tool invocation parsing contract failed");
}
if (skillToolInvocations(codexSkillEvent, eventPattern).join(",") !== "project-design") {
  throw new Error("Codex observable skill event parsing contract failed");
}
if (skillToolInvocations(finalMessageOnly, eventPattern).length) {
  throw new Error("Final answer text must not count as a Skill invocation");
}
const exactRoute = { expectedSkills: ["project-design"], forbiddenSkills: ["project-task"] };
const exactResult = evaluateSkillRoute(exactRoute, ["project-design"]);
if (exactResult.missing.length || exactResult.forbidden.length || exactResult.unexpected.length || !exactResult.ordered) {
  throw new Error("Exact Skill route evaluation contract failed");
}
const extraResult = evaluateSkillRoute(exactRoute, ["project-design", "project-debug"]);
if (extraResult.unexpected.join(",") !== "project-debug") {
  throw new Error("Unexpected Skill invocation must fail closed");
}
const allowedResult = evaluateSkillRoute(
  { expectedSkills: ["project-design"], allowedSkills: ["project-knowledge"] },
  ["project-knowledge", "project-design"],
);
if (allowedResult.unexpected.length || allowedResult.missing.length) {
  throw new Error("Explicitly allowed optional Skill contract failed");
}

const requiredSkillText = [
  ["project-intake", "Route first to `project-spec`"],
  ["project-intake", "`project-debug` for a Bug, then `project-design`"],
  ["project-debug", "project-intel requirement diagnose"],
  ["project-design", "**Standalone**"],
  ["project-design", "**Lifecycle**"],
  ["project-spec", "before project-debug/project-design"],
  ["project-spec", "requirement defer --requirement-id"],
  ["project-spec", "register existing"],
  ["project-task", "<selected-kind>"],
  ["project-task", "<selected-action>"],
  ["project-refresh", "cloud plugin"],
];
for (const [skill, fragment] of requiredSkillText) {
  if (!skillText(skill).includes(fragment)) {
    throw new Error(`Skill routing contract missing from ${skill}: ${fragment}`);
  }
}

const forbiddenSkillText = [
  ["project-spec", "Use after project-design"],
  ["project-brainstorm", "project-intel spec --title"],
  ["project-quality", "project-intel test --command"],
  ["project-task", "--test-kind unit --report-action generate"],
  ["project-task", "project-intel intake --requirement-id"],
];
for (const [skill, fragment] of forbiddenSkillText) {
  if (skillText(skill).includes(fragment)) {
    throw new Error(`Obsolete or hard-coded routing remains in ${skill}: ${fragment}`);
  }
}

console.log(`Skill behavior scenario contracts verified: ${payload.scenarios.length} scenarios, ${available.size} skills`);
