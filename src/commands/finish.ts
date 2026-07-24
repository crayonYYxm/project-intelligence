// `finish` command (phase 3.F.2). Runs the finish gate via the state machine's
// finishRequirement (which enforces test evidence + approved review), then writes
// a closure-summary.md. Per AC-11, the gate rejects when test/review evidence is
// missing or failed.

import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import { finishRequirement, validateFinishRequirement } from "../requirements/state-machine.js";
import { print } from "../io/output.js";
import { runCheck } from "./check.js";

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

export function runFinish(root: string, args: string[], global: GlobalOptions): CommandResult {
  const id = flag(args, "--requirement-id");
  if (!id) throw new UsageError("finish 需要 --requirement-id。");
  const dryRun = args.includes("--dry-run");
  const files = multiFiles(args);
  const checkArgs = args.includes("--run-quality") ? ["--run-quality"] : [];
  if (dryRun) checkArgs.push("--dry-run");
  const check = runCheck(root, checkArgs, global);
  if (check.exitCode !== 0) throw new UsageError("finish 门禁：project-intel check 未通过。");

  if (dryRun) {
    const validated = validateFinishRequirement(root, id, files);
    void global;
    return ok({
      requirementId: id,
      dryRun: true,
      files: validated.selectedFiles,
      diffHash: validated.snapshot.diffHash,
      message: "finish --dry-run：完整门禁已检查，未写入状态。",
    });
  }

  const manifest = finishRequirement(root, id, files);
  print(`finish：需求 ${id} 已完成（→ finished）`);
  void global;
  return ok({ requirementId: id, state: manifest.state });
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
