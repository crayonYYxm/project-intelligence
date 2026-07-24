// `check` command (phase 3.B.3), ported from application.run_check.
//
// Evaluates hard rules against project facts, optionally runs detected quality
// commands, and writes project-status.md. With no hard rules configured (the
// default) and `--run-quality` absent, `check` succeeds.

import { join } from "node:path";
import { existsSync } from "node:fs";
import { collectProjectState } from "../app/project-state.js";
import { evaluateHardRules, DEFAULT_HARD_RULES, parseHardRulesFromConfig, type HardRuleContext } from "../rules/hard.js";
import { runShell } from "../process/exec-shell.js";
import { loadJson } from "../fs/atomic-write.js";
import { writeText } from "../fs/atomic-write.js";
import { projectIntelDir } from "./init.js";
import { RuntimeError, UsageError } from "../errors.js";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { doctorReport } from "./doctor.js";

interface CheckOptions {
  runQuality?: boolean;
  dryRun?: boolean;
}

function parseArgs(args: string[]): CheckOptions {
  return {
    runQuality: args.includes("--run-quality"),
    dryRun: args.includes("--dry-run"),
  };
}

export function runCheck(root: string, args: string[], global: GlobalOptions): CommandResult {
  const opts = parseArgs(args);
  const pdir = projectIntelDir(root);
  if (opts.dryRun) {
    return ok({ dryRun: true, check: doctorReport(root) });
  }
  if (!existsSync(join(pdir, "manifest.json"))) {
    throw new UsageError("未找到 .project-intel/manifest.json。请先运行 project-intel init。");
  }
  const config = loadJson<Record<string, unknown>>(join(pdir, "config.json"), { rules: { hard: [] } });
  // Parse JSON hard-rule entries from config into executable HardRule objects
  // (mirrors Python's run_hard_rule_checks which dispatches on check.type).
  const configHardRules = parseHardRulesFromConfig(config, root);
  const allRules = [...DEFAULT_HARD_RULES, ...configHardRules];

  const state = collectProjectState(root);
  const ctx: HardRuleContext = {
    manifest: state.manifest,
    config,
    frontend: state.frontend as unknown as Record<string, unknown>,
    backend: state.backend as unknown as Record<string, unknown>,
    root,
    files: state.files.map((f) => f.path),
  };
  const violations = evaluateHardRules(allRules, ctx);

  let qualityFailed = false;
  const qualityResults: Record<string, unknown>[] = [];
  if (opts.runQuality) {
    const commands = ((config.quality as Record<string, unknown>)?.commands ?? []) as Record<string, unknown>[];
    for (const cmd of commands) {
      const command = String(cmd.command ?? "");
      if (!command) continue;
      const result = runShell(command, root);
      qualityResults.push({ kind: cmd.kind, command, exitCode: result.code });
      if (result.code !== 0) qualityFailed = true;
    }
  }

  if (!opts.dryRun) {
    writeText(
      join(pdir, "project-status.md"),
      buildCheckStatus(state, violations, qualityResults)
    );
  }

  if (violations.length) {
    throw new RuntimeError(`硬规则违反：\n${violations.join("\n")}`);
  }
  if (qualityFailed) {
    return { exitCode: 1, result: { report: ".project-intel/project-status.md" } };
  }
  void global;
  return ok({ report: ".project-intel/project-status.md" });
}

function buildCheckStatus(
  state: ReturnType<typeof collectProjectState>,
  violations: string[],
  qualityResults: Record<string, unknown>[]
): string {
  return [
    "# 项目状态",
    "",
    `更新时间：\`${new Date().toISOString()}\``,
    "",
    "## 硬规则检查",
    "",
    violations.length ? violations.map((v) => `- ❌ ${v}`).join("\n") : "- ✅ 无硬规则违反",
    "",
    "## 质量检查",
    "",
    qualityResults.length
      ? qualityResults.map((r) => `- ${r.kind}: \`${r.command}\` → ${r.exitCode}`).join("\n")
      : "_未运行质量检查（使用 --run-quality 运行）。_",
    "",
  ].join("\n");
}
