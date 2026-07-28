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

For requirement-level work, carry one requirement ID through every CLI call. Ask the user for a version date and pass it to intake with \`--version-date\`; do not silently use today's date. New archives keep readable files under \`.project-intel/requirements/<YYYY-MM-DD>-<id>-<title>/\`; legacy \`<id>-<title>/\` and \`<id>/\` archives remain readable.

四类必选文档是标题化的需求/Bug 文档、设计文档、测试文档和收口文档，不可延期；实施计划仍为可选。有现成文档时登记到规范目录，缺失时生成。仅提供设计文档但没有独立 spec 时，\`project-spec\` 必须先根据设计内容生成并登记需求/Bug 文档和一致的验收标准，再继续设计校验。需求级测试必须维护测试文档，\`finish\` 必须自动生成收口文档。Legacy short names remain readable.

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

For requirement-level work, ask the user for a version date, pass it to intake with \`--version-date\`, and keep all readable artifacts in \`.project-intel/requirements/<YYYY-MM-DD>-<id>-<title>/\`; legacy \`<id>-<title>/\` and \`<id>/\` archives remain readable.

四类必选文档是标题化的需求/Bug 文档、设计文档、测试文档和收口文档，不可延期；实施计划仍为可选。有现成文档时登记，缺失时生成。仅提供设计文档但没有独立 spec 时，\`project-spec\` 必须先根据设计内容生成需求/Bug 文档和一致的验收标准。需求级测试维护测试文档，\`finish\` 自动生成收口文档。\`init\` and \`refresh\` are fact-only by default; adapters change only when explicitly requested.`;
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
