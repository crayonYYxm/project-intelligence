// Hard rules engine (phase 3.B.3), ported from application.run_hard_rule_checks.
// Hard rules block a project (exit non-zero) when violated.
//
// The Python implementation evaluates JSON rule definitions from config.rules.hard.
// Each rule is either a plain string (manual-review) or an object with a `check`
// field containing `type` (forbid-regex/require-regex/require-file/forbid-path),
// `pattern` (for regex types), `path` (for file types), and optional
// `include`/`exclude` glob arrays. This module mirrors that evaluation.
//
// Key difference from the previous implementation: regex checks READ FILE CONTENTS
// (not just file paths), and file discovery uses the scanner's file list (not
// manifest.files which doesn't exist).

import { existsSync, readFileSync } from "node:fs";
import { join, resolve, relative } from "node:path";

export interface HardRule {
  id: string;
  description: string;
  /** Evaluate against project facts; return a violation message or null when OK. */
  evaluate(facts: HardRuleContext): string | null;
}

export interface HardRuleContext {
  manifest: Record<string, unknown>;
  config: Record<string, unknown>;
  frontend: Record<string, unknown>;
  backend: Record<string, unknown>;
  /** Project root path (for reading file contents during regex checks). */
  root: string;
  /** Discovered project files (relative paths from root). */
  files: string[];
}

/** Default shipped hard rules (empty set, matching Python baseline). */
export const DEFAULT_HARD_RULES: HardRule[] = [];

/**
 * A JSON hard-rule entry from config.rules.hard, as defined by the Python
 * validate_project_config schema.
 */
interface HardRuleEntry {
  id?: string;
  rule?: string;
  description?: string;
  check?: {
    type: "forbid-regex" | "require-regex" | "require-file" | "forbid-path";
    pattern?: string;
    path?: string;
    include?: string[];
    exclude?: string[];
  };
}

/** Read file contents (mirrors Python's read_text, capped at 500KB). */
function readText(path: string): string {
  try {
    return readFileSync(path, "utf8").slice(0, 500_000);
  } catch {
    return "";
  }
}

/**
 * Convert a JSON config rule entry into a HardRule with an executable evaluate
 * function. Mirrors run_hard_rule_checks' per-rule dispatch.
 */
function jsonRuleToHardRule(entry: HardRuleEntry | string, index: number): HardRule {
  if (typeof entry === "string") {
    return {
      id: `hard-${index + 1}`,
      description: entry,
      evaluate: () => null, // manual-review: never auto-fails
    };
  }

  const id = entry.id ?? `hard-${index + 1}`;
  const description = entry.rule ?? entry.description ?? "未命名 hard 规则";
  const check = entry.check;

  if (!check) {
    // No check configured → manual-review, never auto-fails.
    return { id, description, evaluate: () => null };
  }

  const { type } = check;
  const include = check.include ?? ["**/*"];
  const exclude = check.exclude ?? [];

  return {
    id,
    description,
    evaluate: (facts: HardRuleContext): string | null => {
      if (type === "forbid-regex" || type === "require-regex") {
        const pattern = check.pattern;
        if (!pattern) return `[${id}] 规则评估异常：缺少 pattern`;
        let regex: RegExp;
        try {
          regex = new RegExp(pattern);
        } catch {
          return `[${id}] 规则评估异常：无效正则 ${pattern}`;
        }
        // Select files matching include/exclude globs, then READ THEIR CONTENTS
        // and search for the regex in the file body (mirrors Python's
        // selected_hard_rule_files + read_text + regex.search).
        const matches: string[] = [];
        for (const relPath of facts.files) {
          if (!matchesGlobs(relPath, include) || matchesGlobs(relPath, exclude)) continue;
          const absPath = join(facts.root, relPath);
          if (!existsSync(absPath)) continue;
          const body = readText(absPath);
          const match = regex.exec(body);
          if (match) {
            // Compute line number (mirrors Python: body.count("\n", 0, match.index) + 1).
            const line = body.slice(0, match.index).split("\n").length;
            matches.push(`${relPath}:${line}`);
            if (matches.length >= 20) break;
          }
        }
        if (type === "forbid-regex") {
          return matches.length > 0 ? `禁止正则匹配：${matches.slice(0, 5).join(", ")}` : null;
        }
        // require-regex
        return matches.length === 0 ? `未找到必须的正则匹配：${pattern}` : null;
      }

      if (type === "require-file" || type === "forbid-path") {
        const globPath = check.path;
        if (!globPath) return `[${id}] 规则评估异常：缺少 path`;
        // Check if any discovered file matches the glob path.
        const matched = facts.files.filter((f) => simpleGlobMatch(globPath, f));
        if (type === "require-file") {
          return matched.length > 0 ? null : `未找到必须的文件：${globPath}`;
        }
        // forbid-path
        return matched.length > 0 ? `禁止路径存在：${matched.slice(0, 5).join(", ")}` : null;
      }

      return `[${id}] 规则评估异常：未知 check.type ${type}`;
    },
  };
}

/**
 * Parse JSON hard-rule entries from config and convert them to executable
 * HardRule objects. This is the bridge between the config schema and the
 * rule engine.
 */
export function parseHardRulesFromConfig(config: Record<string, unknown>, _root: string): HardRule[] {
  const rulesConfig = config.rules as Record<string, unknown> | undefined;
  const hardEntries = (rulesConfig?.hard ?? []) as (HardRuleEntry | string)[];
  return hardEntries.map((entry, i) => jsonRuleToHardRule(entry, i));
}

/**
 * Evaluate hard rules against project facts. Returns the list of violations
 * (empty when the project passes). Mirrors run_check's hard-rule phase.
 */
export function evaluateHardRules(rules: HardRule[], facts: HardRuleContext): string[] {
  const violations: string[] = [];
  for (const rule of rules) {
    try {
      const violation = rule.evaluate(facts);
      if (violation) violations.push(`[${rule.id}] ${violation}`);
    } catch {
      // A failing rule evaluator is treated as a violation rather than crashing.
      violations.push(`[${rule.id}] 规则评估异常`);
    }
  }
  return violations;
}

/** Simple glob matching: supports * and ** patterns. */
function simpleGlobMatch(pattern: string, path: string): boolean {
  // Convert glob to regex: ** → .*, * → [^/]*
  const regexStr = pattern
    .replace(/\*\*/g, "\0STARSTAR\0")
    .replace(/\*/g, "[^/]*")
    .replace(/\0STARSTAR\0/g, ".*")
    .replace(/\?/g, ".");
  return new RegExp(`^${regexStr}$`).test(path);
}

/** Check if a path matches any of the glob patterns. */
function matchesGlobs(path: string, patterns: string[]): boolean {
  return patterns.some((p) => simpleGlobMatch(p, path));
}
