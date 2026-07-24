// Top-level `install` command (phase 3.C.1), ported from application.install_claude.
//
// Per the migration requirement (P1.5): the top-level `install` is its own public
// command with ONLY --hooks / --activate-git-hooks / --allow-external-hooks. It
// is NOT a synonym for `adapters` or `agent install` (those are separate command
// families). `install` creates the Claude adapter dir, applies adapters to both
// targets, and optionally writes/activates git hooks.

import { mkdirSync } from "node:fs";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { safeAdapterPath } from "./adapter-blocks.js";
import { adaptersApply } from "./adapters.js";
import { writeHookTemplates, activateGitHooks } from "./hooks.js";

interface InstallOptions {
  hooks: boolean;
  activateHooks: boolean;
  allowExternalHooks: boolean;
}

function parseArgs(args: string[]): InstallOptions {
  return {
    hooks: args.includes("--hooks"),
    activateHooks: args.includes("--activate-git-hooks"),
    allowExternalHooks: args.includes("--allow-external-hooks"),
  };
}

/**
 * Run the top-level install. Mirrors install_claude: create .claude/, apply
 * adapters (both targets), optionally write + activate git hooks.
 */
export function runInstall(root: string, args: string[], global: GlobalOptions): CommandResult {
  const opts = parseArgs(args);
  const claudeDir = safeAdapterPath(root, ".claude");
  mkdirSync(claudeDir, { recursive: true });

  const adapterResult = adaptersApply(root, "both", false);
  const agentFiles = (adapterResult.entries as Record<string, unknown>[]).map((e) => String(e.path));

  let hookTemplates: string[] = [];
  let hookResults: Record<string, unknown>[] = [];
  if (opts.hooks || opts.activateHooks) {
    hookTemplates = writeHookTemplates(root);
  }
  if (opts.activateHooks) {
    hookResults = activateGitHooks(root, opts.allowExternalHooks);
  }

  void global;
  return ok({
    claude: claudeDir,
    agentFiles,
    adapters: adapterResult,
    hookTemplates,
    hookResults,
    legacyCleanup: [],
  });
}
