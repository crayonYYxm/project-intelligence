// Adapter block content + target definitions (phase 3.C.2).
//
// The managed block written into AGENTS.md / CLAUDE.md / .claude/CLAUDE.md by
// `install` and `adapters apply`. Mirrors application.codex_adapter_rules /
// claude_adapter_rules / nested_claude_adapter_rules (a concise Project
// Intelligence directive block), with marker pairs per target.

import {
  PROJECT_INTEL_BLOCK_START,
  PROJECT_INTEL_BLOCK_END,
  AGENT_PROJECT_INTEL_BLOCK_START,
  AGENT_PROJECT_INTEL_BLOCK_END,
  type AdapterTarget,
} from "./adapter-blocks.js";
import { join } from "node:path";

/** The block written to AGENTS.md (codex target). */
export function codexAdapterRules(): string {
  return `## Project Intelligence

This repository uses \`.project-intel/\` for project facts, standards, requirement history, test evidence, review, finish, and maintenance.

Use the plugin skill namespace when available:

- Implementation or bug work: \`$project-intelligence:project-intake\` → \`$project-intelligence:project-spec\` → \`$project-intelligence:project-design\` → \`$project-intelligence:project-test\` → \`$project-intelligence:project-task\`.
- Debugging: \`$project-intelligence:project-debug\` before fixing.
- Review only: \`$project-intelligence:project-review\`; do not finish or maintain from review.
- Completion: \`$project-intelligence:project-finish\`; run \`$project-intelligence:project-maintain\` only after finish succeeds.
- Knowledge, standards, quality, refresh, and init use their matching \`$project-intelligence:*\` skills.

For requirement-level work, carry one requirement ID through every CLI call. Keep readable files under \`.project-intel/requirements/<id>/\`: \`requirement.md\`, \`design.md\`, optional \`plan.md\`, \`test-report.md\`, \`closure-summary.md\`, and \`manifest.json\`.

\`project-intel init\` and \`project-intel refresh\` are fact-only by default. Root adapters are changed only by explicit \`project-intel adapters apply\`, \`project-intel install\`, or \`project-intel refresh --adapters\`.`;
}

/** The block written to CLAUDE.md (claude target). */
export function claudeAdapterRules(): string {
  return `## Project Intelligence

This repository uses \`.project-intel/\` for project facts and requirement workflow evidence.

Use slash skills when available:

- Implementation or bug work: \`/project-intake\` → \`/project-spec\` → \`/project-design\` → \`/project-test\` → \`/project-task\`.
- Debugging: \`/project-debug\` before fixing.
- Review only: \`/project-review\`; do not finish or maintain from review.
- Completion: \`/project-finish\`; run \`/project-maintain\` only after finish succeeds.
- Knowledge, standards, quality, refresh, and init use their matching \`/project-*\` skills.

For requirement-level work, keep all readable artifacts in \`.project-intel/requirements/<id>/\`. \`init\` and \`refresh\` are fact-only by default; adapters change only when explicitly requested.`;
}

/** The block written to .claude/CLAUDE.md (claude-nested target). */
export function nestedClaudeAdapterRules(): string {
  return `# Project Intelligence

Use the root \`CLAUDE.md\` Project Intelligence block and the \`/project-*\` plugin skills. Do not keep a second full workflow copy in \`.claude/CLAUDE.md\`.`;
}

/** Build the list of adapter targets for a --target value (both/codex/claude). */
export function adapterTargets(root: string, target: string): AdapterTarget[] {
  const requested = target === "both" || target === "all" ? new Set(["codex", "claude"]) : new Set([target]);
  const targets: AdapterTarget[] = [];
  if (requested.has("codex")) {
    targets.push({
      name: "codex",
      path: join(root, "AGENTS.md"),
      block: codexAdapterRules(),
      start: AGENT_PROJECT_INTEL_BLOCK_START,
      end: AGENT_PROJECT_INTEL_BLOCK_END,
      prepend: true,
    });
  }
  if (requested.has("claude")) {
    targets.push({
      name: "claude",
      path: join(root, "CLAUDE.md"),
      block: claudeAdapterRules(),
      start: PROJECT_INTEL_BLOCK_START,
      end: PROJECT_INTEL_BLOCK_END,
      prepend: true,
    });
    targets.push({
      name: "claude-nested",
      path: join(root, ".claude", "CLAUDE.md"),
      block: nestedClaudeAdapterRules(),
      start: PROJECT_INTEL_BLOCK_START,
      end: PROJECT_INTEL_BLOCK_END,
      prepend: false,
    });
  }
  return targets;
}
