// `review` command (phase 3.F.1). Records a requirement-level code review result
// against the state machine's recordReview. Uses --result passed|failed (NOT
// --outcome) to match the Python CLI contract. --result failed keeps the
// requirement at verified (does NOT advance to reviewed). AC-11 / P0 fix.

import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import { recordReview, validateReviewRequirement } from "../requirements/state-machine.js";

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

function files(args: string[]): string[] {
  const index = args.indexOf("--files");
  if (index < 0) return [];
  const values: string[] = [];
  for (let cursor = index + 1; cursor < args.length && !args[cursor]!.startsWith("--"); cursor++) {
    values.push(args[cursor]!);
  }
  return values;
}

export function runReview(root: string, args: string[], global: GlobalOptions): CommandResult {
  const id = flag(args, "--requirement-id");
  if (!id) throw new UsageError("review 需要 --requirement-id。");
  const result = flag(args, "--result");
  if (!result || (result !== "passed" && result !== "failed")) {
    throw new UsageError("--result 只支持 passed 或 failed。");
  }
  const summary = flag(args, "--summary") ?? "";
  if (!summary.trim()) throw new UsageError("review 需要 --summary。");
  const findings = parseFindings(args);
  const selectedFiles = files(args);
  const dryRun = args.includes("--dry-run");

  if (dryRun) {
    const validated = validateReviewRequirement(root, id, result, selectedFiles);
    void global;
    return ok({
      requirementId: id,
      result,
      dryRun: true,
      state: validated.manifest.state,
      files: validated.selectedFiles,
      diffHash: validated.snapshot.diffHash,
      message: "review --dry-run：完整门禁已验证，未写入 manifest。",
    });
  }

  const manifest = recordReview(root, id, { result, summary, findings, files: selectedFiles });
  void global;
  // Output the EFFECTIVE result (which may differ from the user-requested result
  // when unresolved blocking findings force it to "failed"), not the requested one.
  const rounds = manifest.reviewRounds ?? [];
  const effectiveResult = rounds.length > 0 ? rounds[rounds.length - 1]!.result : result;
  return ok({ requirementId: id, result: effectiveResult, state: manifest.state });
}

function parseFindings(args: string[]): { severity: string; text: string }[] {
  const out: { severity: string; text: string }[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--finding" && args[i + 1]) {
      const raw = args[i + 1]!;
      const colon = raw.indexOf(":");
      if (colon < 0) continue;
      const severity = raw.slice(0, colon).trim().toLowerCase();
      const text = raw.slice(colon + 1).trim();
      if (["critical", "important", "minor"].includes(severity) && text) {
        out.push({ severity, text });
      }
    }
  }
  return out;
}
