// `finish` command (phase 3.F.2). Runs the finish gate via the state machine's
// finishRequirement (which enforces test evidence + approved review), then writes
// a closure-summary.md. Per AC-11, the gate rejects when test/review evidence is
// missing or failed.

import { existsSync } from "node:fs";
import { join } from "node:path";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import {
  finishRequirement,
  generateArtifact,
  requirementDir,
  validateFinishRequirement,
} from "../requirements/state-machine.js";
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

  const preflight = validateFinishRequirement(root, id, files, undefined, { requireClosure: false });
  if (dryRun) {
    void global;
    return ok({
      requirementId: id,
      dryRun: true,
      files: preflight.selectedFiles,
      diffHash: preflight.snapshot.diffHash,
      message: "finish --dry-run：测试、评审和范围门禁已检查；正式执行时将生成收口总结。",
    });
  }

  let closureReady = true;
  try {
    validateFinishRequirement(root, id, files, preflight.snapshot);
  } catch (error) {
    if (error instanceof Error && error.message.includes("缺少当前有效的复盘收口总结文件")) {
      closureReady = false;
    } else {
      throw error;
    }
  }
  if (!closureReady) {
    const closurePath = join(requirementDir(root, id), "closure-summary.md");
    if (existsSync(closurePath)) {
      throw new UsageError("closure-summary.md 已存在但未有效登记；请先使用 requirement add --type closure 登记。");
    }
    generateArtifact(root, id, "closure");
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
