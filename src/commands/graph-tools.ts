// `graph-tools` command (phase 3.G.2). Reports the status of optional graph tools
// (GitNexus / Understand-Anything) and their available commands.

import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { detectGraphActions } from "../graph/actions.js";

export function runGraphTools(root: string, args: string[], global: GlobalOptions): CommandResult {
  const report = detectGraphActions(root);
  void args;
  void global;
  return ok(report);
}
