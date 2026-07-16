import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const plugin = resolve(root, "plugins/project-intelligence");
const payload = JSON.parse(readFileSync(resolve(root, "evals/skill-behavior-scenarios.json"), "utf8"));
const args = process.argv.slice(2);
const option = (name, fallback = "") => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : fallback;
};
const agent = option("--agent", "claude");
const only = option("--scenario");
const dryRun = args.includes("--dry-run");
const scenarios = only ? payload.scenarios.filter((item) => item.id === only) : payload.scenarios;

if (!new Set(["claude", "codex"]).has(agent)) throw new Error(`Unsupported agent: ${agent}`);
if (!scenarios.length) throw new Error(`No matching scenarios: ${only}`);
if (agent === "codex" && !dryRun && process.env.PROJECT_INTEL_CODEX_EVAL_READY !== "1") {
  throw new Error("Codex live eval uses the currently configured plugin. Set PROJECT_INTEL_CODEX_EVAL_READY=1 only after installing this working tree into an isolated Codex profile.");
}

const evalPrompt = (scenario) => `${scenario.prompt}\n\nDo not edit files or execute project commands. Invoke every applicable project-intelligence skill before answering. End with one line in the form WORKFLOW: skill-a -> skill-b.`;

const invocation = (scenario) => {
  const prompt = evalPrompt(scenario);
  if (agent === "claude") {
    const isolationArgs = process.env.ANTHROPIC_API_KEY
      ? ["--bare"]
      : [];
    return {
      command: "claude",
      args: [
        "-p",
        ...isolationArgs,
        "--plugin-dir", plugin,
        "--settings", '{"disableAllHooks":true}',
        "--strict-mcp-config",
        "--mcp-config", '{"mcpServers":{}}',
        "--tools", "Skill,Read,Glob,Grep",
        "--permission-mode", "dontAsk",
        "--output-format", "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--max-budget-usd", "0.30",
        prompt,
      ],
    };
  }
  return {
    command: "codex",
    args: ["exec", "--ephemeral", "--sandbox", "read-only", "--json", "-C", root, prompt],
  };
};

const skillToolInvocations = (stdout) => {
  const found = [];
  for (const line of stdout.split(/\r?\n/)) {
    if (!line.trim().startsWith("{")) continue;
    let value;
    try {
      value = JSON.parse(line);
    } catch {
      continue;
    }
    const visit = (item) => {
      if (!item || typeof item !== "object") return;
      if (item.type === "tool_use" && /skill/i.test(String(item.name ?? ""))) {
        const body = JSON.stringify(item.input ?? {});
        for (const match of body.matchAll(/project-(?:brainstorm|debug|finish|init|intake|knowledge|maintain|orchestrate|plan|quality|refresh|review|spec|standards|task|test)/g)) {
          found.push(match[0]);
        }
      }
      for (const child of Array.isArray(item) ? item : Object.values(item)) visit(child);
    };
    visit(value);
  }
  return found;
};

const failureDetail = (result) => {
  const invocations = skillToolInvocations(result.stdout ?? "");
  let terminal = "";
  for (const line of (result.stdout ?? "").split(/\r?\n/)) {
    if (!line.trim().startsWith("{")) continue;
    try {
      const value = JSON.parse(line);
      if (value.type === "result") {
        terminal = JSON.stringify({ subtype: value.subtype, result: value.result, terminal_reason: value.terminal_reason });
      }
    } catch {
      // Ignore partial stream lines and keep the latest valid terminal event.
    }
  }
  return [
    result.error?.message,
    result.stderr?.trim(),
    terminal,
    invocations.length ? `skills=${invocations.join(" -> ")}` : "skills=none",
    `exit=${result.status}${result.signal ? ` signal=${result.signal}` : ""}`,
  ].filter(Boolean).join("; ");
};

let failures = 0;
for (const scenario of scenarios) {
  const call = invocation(scenario);
  if (dryRun) {
    console.log(`[dry-run] ${scenario.id}: ${call.command} ${call.args.slice(0, -1).join(" ")} <prompt>`);
    continue;
  }
  const result = spawnSync(call.command, call.args, { cwd: root, encoding: "utf8", timeout: 180_000 });
  const actual = agent === "claude"
    ? skillToolInvocations(result.stdout ?? "")
    : [...(result.stdout ?? "").matchAll(/project-(?:brainstorm|debug|finish|init|intake|knowledge|maintain|orchestrate|plan|quality|refresh|review|spec|standards|task|test)/g)].map((item) => item[0]);
  const missing = scenario.expectedSkills.filter((skill) => !actual.includes(skill));
  const forbidden = (scenario.forbiddenSkills ?? []).filter((skill) => actual.includes(skill));
  const positions = (scenario.expectedOrder ?? []).map((skill) => actual.indexOf(skill));
  const ordered = positions.every((value, index) => value >= 0 && (index === 0 || value > positions[index - 1]));
  if (missing.length || forbidden.length || !ordered) {
    failures += 1;
    const execution = result.error || result.status !== 0 ? `; process=${failureDetail(result)}` : "";
    console.error(`[failed] ${scenario.id}: actual=${actual.join(" -> ") || "none"}; missing=${missing.join(",") || "none"}; forbidden=${forbidden.join(",") || "none"}; ordered=${ordered}${execution}`);
  } else {
    const terminal = result.error || result.status !== 0 ? `; process=${failureDetail(result)}` : "";
    console.log(`[passed] ${scenario.id}: ${actual.join(" -> ")}${terminal}`);
  }
}

if (failures) process.exit(1);
console.log(dryRun ? `Skill eval dry-run verified: ${scenarios.length} scenarios` : `Skill behavior evals passed: ${scenarios.length}`);
