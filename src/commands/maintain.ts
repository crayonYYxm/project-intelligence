// `maintain` command (phase 3.F.3). Refreshes the project facts (re-runs the
// scan collection) and closes the requirement via the state machine's
// closeRequirement.

import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import { closeRequirement, loadRequirement, validateFinishedFreshness } from "../requirements/state-machine.js";
import { validateScopeSelection } from "../requirements/scope.js";
import { runInit } from "./init.js";
import { print } from "../io/output.js";
import { runCheck } from "./check.js";

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

export function runMaintain(root: string, args: string[], global: GlobalOptions): CommandResult {
  const id = flag(args, "--requirement-id");
  const dryRun = args.includes("--dry-run");
  const files = multiFiles(args);
  const checkArgs = args.includes("--run-quality") ? ["--run-quality"] : [];
  if (dryRun) checkArgs.push("--dry-run");
  const check = runCheck(root, checkArgs, global);
  if (check.exitCode !== 0) throw new UsageError("maintain 门禁：project-intel check 未通过。");

  if (dryRun) {
    let selectedFiles: string[] = [];
    let diffHash: string | null = null;
    if (id) {
      const snapshot = validateFinishedFreshness(root, id);
      selectedFiles = validateScopeSelection(root, files, snapshot);
      diffHash = snapshot.diffHash;
    }
    void global;
    return ok({
      requirementId: id ?? null,
      dryRun: true,
      files: selectedFiles,
      diffHash,
      message: "maintain --dry-run：完整门禁已检查，未关闭需求。",
    });
  }

  // Validate the requirement AND state BEFORE refreshing (so refresh doesn't
  // modify files when the requirement doesn't exist or is in the wrong state).
  if (id) {
    const manifest = loadRequirement(root, id); // throws if not found
    if (manifest.state !== "finished") {
      throw new UsageError(`maintain 需要 finished 状态，当前为 ${manifest.state}。`);
    }
    const snapshot = validateFinishedFreshness(root, id);
    validateScopeSelection(root, files, snapshot);
  }

  // Refresh project facts (no graph setup, no adapters).
  runInit(root, ["--no-graph"], global, true);
  let state = "(未指定需求)";
  if (id) {
    const manifest = closeRequirement(root, id, check.exitCode === 0);
    state = manifest.state;
    print(`maintain：已刷新 .project-intel 并关闭需求 ${id}（→ ${state}）`);
  } else {
    print("maintain：已刷新 .project-intel（未指定 --requirement-id，不关闭需求）。");
  }
  return ok({ refreshed: true, requirementId: id ?? null, state });
}

function multiFiles(args: string[]): string[] {
  const index = args.indexOf("--files");
  if (index < 0) return [];
  const values: string[] = [];
  for (let cursor = index + 1; cursor < args.length && !args[cursor]!.startsWith("--"); cursor++) {
    values.push(args[cursor]!);
  }
  return values;
}
