// `agent install` subcommand (phase 3.C.3), ported from application.agent_install_commands
// + install_agent_plugin. Per the migration requirement (P1.5): `agent install`
// accepts ONLY --target {codex,claude,all} (default all) and --dry-run. There is
// NO status/remove subcommand. Each install is classified present/ok/failed/missing.

import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import { run, commandExists } from "../process/spawn.js";

const VALID_TARGETS = new Set(["codex", "claude", "all"]);

interface AgentInstallOptions {
  target: string;
  dryRun: boolean;
}

function parseArgs(args: string[]): AgentInstallOptions {
  const idx = args.indexOf("--target");
  const target = idx >= 0 ? args[idx + 1] : "all";
  if (!target || !VALID_TARGETS.has(target)) {
    throw new UsageError(`--target 只支持 codex/claude/all：${target ?? "(空)"}`);
  }
  return { target, dryRun: args.includes("--dry-run") };
}

/** Build the codex/claude plugin install command lists (mirrors agent_install_commands). */
export function agentInstallCommands(target: string, source?: string): Record<string, string[][]> {
  const src = source ?? "crayonYYxm/project-intelligence";
  const commands: Record<string, string[][]> = {};
  if (target === "codex" || target === "all") {
    commands.codex = [
      ["codex", "plugin", "marketplace", "add", src],
      ["codex", "plugin", "add", "project-intelligence@project-intelligence", "--json"],
    ];
  }
  if (target === "claude" || target === "all") {
    commands.claude = [
      ["claude", "plugin", "marketplace", "add", src],
      ["claude", "plugin", "install", "project-intelligence@project-intelligence"],
    ];
  }
  return commands;
}

/** Run the agent install, classifying each command (present/ok/failed/missing). */
export function runAgentInstall(root: string, args: string[], global: GlobalOptions): CommandResult {
  const opts = parseArgs(args);
  const commands = agentInstallCommands(opts.target);
  const results: Record<string, unknown>[] = [];

  for (const [platform, cmds] of Object.entries(commands)) {
    const cli = cmds[0]?.[0];
    if (!cli || !commandExists(cli)) {
      results.push({ platform, status: "missing", detail: `未找到 ${cli} 命令` });
      continue;
    }
    if (opts.dryRun) {
      results.push({ platform, status: "present", commands: cmds.map((c) => c.join(" ")) });
      continue;
    }
    let okFlag = false;
    for (const cmd of cmds) {
      const r = run(cmd, root, 180);
      if (r.code === 0) okFlag = true;
      else {
        results.push({ platform, status: "failed", command: cmd.join(" "), exitCode: r.code, stderr: r.stderr });
        okFlag = false;
        break;
      }
    }
    if (okFlag) results.push({ platform, status: "ok" });
  }

  void global;
  return ok({ target: opts.target, dryRun: opts.dryRun, results, restartRequired: opts.target !== "all" });
}
