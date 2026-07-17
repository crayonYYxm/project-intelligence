import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { buildSkillNamePattern, evaluateSkillRoute, skillToolInvocations } from "./skill-eval-events.mjs";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const plugin = resolve(root, "plugins/project-intelligence");
const payload = JSON.parse(readFileSync(resolve(root, "evals/skill-behavior-scenarios.json"), "utf8"));
const skillNames = readdirSync(resolve(plugin, "skills"), { withFileTypes: true })
  .filter((item) => item.isDirectory())
  .map((item) => item.name);
const skillNamePattern = buildSkillNamePattern(skillNames);
const args = process.argv.slice(2);
const option = (name, fallback = "") => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : fallback;
};
const agent = option("--agent", "claude");
const only = option("--scenario");
const maxBudgetUsd = option("--max-budget-usd", process.env.PROJECT_INTEL_EVAL_MAX_BUDGET_USD || "1.00");
const dryRun = args.includes("--dry-run");
const scenarios = only ? payload.scenarios.filter((item) => item.id === only) : payload.scenarios;

if (!new Set(["claude", "codex"]).has(agent)) throw new Error(`Unsupported agent: ${agent}`);
if (!scenarios.length) throw new Error(`No matching scenarios: ${only}`);
if (!/^\d+(?:\.\d{1,2})?$/.test(maxBudgetUsd) || Number(maxBudgetUsd) <= 0 || Number(maxBudgetUsd) > 5) {
  throw new Error(`Invalid --max-budget-usd: ${maxBudgetUsd}; expected a value above 0 and at most 5.`);
}
let codexHome = "";
const prepareCodexProfile = () => {
  if (dryRun || agent !== "codex") return;
  if (!process.env.OPENAI_API_KEY) throw new Error("Codex live eval requires OPENAI_API_KEY for the isolated profile.");
  codexHome = mkdtempSync(join(tmpdir(), "project-intelligence-codex-eval-"));
  const env = { ...process.env, CODEX_HOME: codexHome };
  const marketplace = spawnSync("codex", ["plugin", "marketplace", "add", root, "--json"], { cwd: root, encoding: "utf8", env });
  if (marketplace.status !== 0) throw new Error(`Unable to register isolated Codex marketplace: ${marketplace.stderr || marketplace.stdout}`);
  const install = spawnSync("codex", ["plugin", "add", "project-intelligence@project-intelligence", "--json"], { cwd: root, encoding: "utf8", env });
  if (install.status !== 0) throw new Error(`Unable to install current working tree in isolated Codex profile: ${install.stderr || install.stdout}`);
};

process.on("exit", () => {
  if (codexHome) rmSync(codexHome, { recursive: true, force: true });
});
prepareCodexProfile();

const evalPrompt = (scenario) => `${scenario.prompt}\n\n这是只读路由评测。不要编辑文件、执行项目命令、初始化仓库或请求额外授权；请像正常对话一样处理请求。`;

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
        "--max-budget-usd", maxBudgetUsd,
        prompt,
      ],
      env: process.env,
    };
  }
  return {
    command: "codex",
    args: ["exec", "--ephemeral", "--sandbox", "read-only", "--json", "-C", root, prompt],
    env: { ...process.env, CODEX_HOME: codexHome },
  };
};

const failureDetail = (result) => {
  const invocations = skillToolInvocations(result.stdout ?? "", skillNamePattern);
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
  const result = spawnSync(call.command, call.args, { cwd: root, encoding: "utf8", timeout: 180_000, env: call.env });
  const actual = skillToolInvocations(result.stdout ?? "", skillNamePattern);
  const { missing, forbidden, unexpected, ordered } = evaluateSkillRoute(scenario, actual);
  const processFailed = Boolean(result.error) || result.status !== 0;
  if (missing.length || forbidden.length || unexpected.length || !ordered || processFailed) {
    failures += 1;
    const execution = processFailed ? `; process=${failureDetail(result)}` : "";
    console.error(`[failed] ${scenario.id}: actual=${actual.join(" -> ") || "none"}; missing=${missing.join(",") || "none"}; forbidden=${forbidden.join(",") || "none"}; unexpected=${unexpected.join(",") || "none"}; ordered=${ordered}${execution}`);
  } else {
    console.log(`[passed] ${scenario.id}: ${actual.join(" -> ") || "none"}`);
  }
}

if (codexHome) rmSync(codexHome, { recursive: true, force: true });
if (failures) process.exit(1);
console.log(dryRun ? `Skill eval dry-run verified: ${scenarios.length} scenarios` : `Skill behavior evals passed: ${scenarios.length}`);
