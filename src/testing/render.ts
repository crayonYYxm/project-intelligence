// Test-evidence rendering + evaluation (phase 3.E.3), ported from testing.py.
//
// executedTestCount: extract a real test count from framework output (so a bare
// exit-0 from a formatter/empty selection never counts as passing evidence).
// renderTestEvidence: render the evidence payload to a Markdown table + recent
// output. phasePassed: evaluate whether a phase's results constitute a pass.

import { createHash } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { sanitizeText, COMMAND_ERROR_CODES, PASSING_PHASES, manualEvidenceValid } from "./sanitize.js";

export interface TestResult {
  command?: string;
  stdout?: string;
  stderr?: string;
  exitCode?: number;
  executedCount?: number;
}

/** Extract a real test count from recognized framework output. Mirrors executed_test_count. */
export function executedTestCount(result: TestResult): number {
  const text = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
  const patterns = [
    /^\s*Ran\s+(\d+)\s+tests?\b/im,
    /\b(\d+)\s+passed\b/im,
    /\bTests?\s+run:\s*(\d+)\b/im,
    /\b(\d+)\s+tests?\s+(?:completed|passed)\b/im,
    /\b(?:tests?|test cases?)\s*[:=]\s*(\d+)\b/im,
    /^[^\S\r\n]*(?:ℹ\s*)?tests\s+(\d+)\s*$/im,
    /"(?:tests|testCount|numTotalTests)"\s*:\s*(\d+)/,
  ];
  const counts: number[] = [];
  for (const p of patterns) {
    const m = text.match(p);
    if (m && m[1]) counts.push(parseInt(m[1], 10));
  }
  return counts.length ? Math.max(...counts) : 0;
}

export interface InspectedTestReport {
  format: "json" | "junit" | "tap" | "unittest";
  executedCount: number;
  failedCount: number;
  passed: boolean;
}

/**
 * Parse a registered test report. Free-form text such as "1 passed" is
 * deliberately rejected: report-action=register accepts only structured or
 * framework-identifiable reports.
 */
export function inspectTestReport(text: string): InspectedTestReport | null {
  const trimmed = text.trim();
  if (!trimmed) return null;

  try {
    const parsed = JSON.parse(trimmed) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      const record = parsed as Record<string, unknown>;
      const executed = firstFiniteNumber(record, ["numTotalTests", "testCount", "tests", "total"]);
      const failed = firstFiniteNumber(record, ["numFailedTests", "failed", "failures", "errors"]) ?? 0;
      if (executed !== null && executed > 0 && failed >= 0 && failed <= executed) {
        return {
          format: "json",
          executedCount: executed,
          failedCount: failed,
          passed: failed === 0 &&
            !["failed", "failure", "error"].includes(String(record.status ?? record.result ?? "").toLowerCase()),
        };
      }
    }
  } catch {
    // Continue with XML/framework text formats.
  }

  if (/<testsuites?\b/i.test(trimmed)) {
    const suites = [...trimmed.matchAll(/<testsuite\b([^>]*)>/gi)];
    if (suites.length > 0) {
      let executed = 0;
      let failed = 0;
      for (const suite of suites) {
        const attrs = suite[1] ?? "";
        executed += xmlNumber(attrs, "tests");
        failed += xmlNumber(attrs, "failures") + xmlNumber(attrs, "errors");
      }
      if (executed > 0 && failed <= executed) {
        return { format: "junit", executedCount: executed, failedCount: failed, passed: failed === 0 };
      }
    }
  }

  if (/^TAP version \d+/im.test(trimmed)) {
    const plan = [...trimmed.matchAll(/^\s*1\.\.(\d+)\s*$/gm)].at(-1);
    const executed = plan?.[1] ? Number(plan[1]) : executedTestCount({ stdout: trimmed });
    const failedMatch = trimmed.match(/^[^\S\r\n]*#\s*fail\s+(\d+)\s*$/im);
    const failed = failedMatch?.[1]
      ? Number(failedMatch[1])
      : (/(?:^|\n)\s*not ok\b/i.test(trimmed) ? 1 : 0);
    if (executed > 0 && failed <= executed) {
      return { format: "tap", executedCount: executed, failedCount: failed, passed: failed === 0 };
    }
  }

  const unittestCount = trimmed.match(/^\s*Ran\s+(\d+)\s+tests?\b/im);
  if (unittestCount?.[1]) {
    const executed = Number(unittestCount[1]);
    const failureSummary = trimmed.match(/FAILED\s*\(([^)]*)\)/i)?.[1] ?? "";
    const failed = [...failureSummary.matchAll(/(?:failures|errors)=(\d+)/gi)]
      .reduce((sum, match) => sum + Number(match[1] ?? 0), 0);
    if (executed > 0) {
      return {
        format: "unittest",
        executedCount: executed,
        failedCount: failed,
        passed: failed === 0 && /^\s*OK(?:\s|$)/im.test(trimmed),
      };
    }
  }

  return null;
}

function firstFiniteNumber(record: Record<string, unknown>, keys: string[]): number | null {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "number" && Number.isFinite(value) && Number.isInteger(value)) return value;
  }
  return null;
}

function xmlNumber(attrs: string, name: string): number {
  const match = attrs.match(new RegExp(`\\b${name}=["'](\\d+)["']`, "i"));
  return match?.[1] ? Number(match[1]) : 0;
}

/** Evaluate whether a phase passed. Mirrors phase_passed. */
export function phasePassed(
  phase: string,
  results: TestResult[],
  manualEvidence = "",
  expectedFailure = ""
): boolean {
  if (phase === "manual") return manualEvidenceValid(manualEvidence);
  if (!results.length) return false;
  const codes = results.map((r) => Number(r.exitCode ?? 1));
  if (phase === "red") {
    if (!expectedFailure.trim() || !codes.every((c) => c !== 0 && !COMMAND_ERROR_CODES.has(c))) return false;
    let re: RegExp;
    try {
      re = new RegExp(expectedFailure, "is");
    } catch {
      return false;
    }
    return results.every((r) => re.test(`${r.stdout ?? ""}\n${r.stderr ?? ""}`));
  }
  return results.every((r, i) => codes[i] === 0 && executedTestCount(r) > 0);
}

function hashFile(root: string, rel: string): string {
  const path = join(root, rel);
  if (!existsSync(path)) return "<missing>";
  const digest = createHash("sha256");
  digest.update(readFileSync(path));
  return digest.digest("hex");
}

export function hashFiles(root: string, files: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const f of files) out[f] = hashFile(root, f);
  return out;
}

function markdownLiteral(value: unknown, lineBreak = "<br>"): string {
  const safe = sanitizeText(String(value ?? ""))
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n");
  let escaped = safe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
  escaped = escaped.replace(/\|/g, "&#124;").replace(/`/g, "&#96;").replace(/\[/g, "&#91;").replace(/\]/g, "&#93;");
  return escaped.replace(/\n/g, lineBreak);
}

function markdownCode(value: unknown): string {
  return `<code>${markdownLiteral(value)}</code>`;
}

export interface EvidenceEntry {
  phase: string;
  status: string;
  recordedAt?: string;
  files: string[];
  projectWide?: boolean;
  commands: TestResult[];
  manualEvidence?: string;
  expectedFailure?: string;
  fileHashes?: Record<string, string>;
}

export interface EvidencePayload {
  schemaVersion: 1;
  task: string;
  createdAt?: string;
  updatedAt?: string;
  entries: EvidenceEntry[];
}

/** Render the evidence payload to a Markdown report. Mirrors render_test_evidence. */
export function renderTestEvidence(payload: Partial<EvidencePayload>): string {
  const lines = [
    "# 测试证据",
    "",
    `任务：${markdownCode(payload.task || "_未记录_")}`,
    "",
    `更新时间：${markdownCode(payload.updatedAt || "unknown")}`,
    "",
    "| 阶段 | 状态 | 命令/人工证据 | 文件范围 |",
    "| --- | --- | --- | --- |",
  ];
  for (const entry of payload.entries ?? []) {
    const commandText = entry.commands
      .map(
        (c) =>
          `${markdownCode(c.command)} → ${markdownLiteral(c.exitCode ?? 0)}（${markdownLiteral(
            c.executedCount ?? 0
          )} tests）`
      )
      .join("<br>");
    const cells = commandText || markdownLiteral(entry.manualEvidence || "_");
    const files = (entry.files ?? []).map((f) => markdownCode(f)).join("<br>") || (entry.projectWide ? "项目级" : "未记录");
    lines.push(`| ${markdownLiteral(entry.phase)} | ${markdownLiteral(entry.status)} | ${cells} | ${files} |`);
  }
  return lines.join("\n").replace(/\s+$/, "") + "\n";
}

/**
 * Evaluate whether the recorded evidence covers the given task + files with a
 * passing phase recorded after the latest source change. Mirrors evaluate_test_evidence.
 */
export function evaluateTestEvidence(
  root: string,
  task: string,
  files: string[],
  payload: Partial<EvidencePayload>
): { ready: boolean; reason: string; passingPhase: string | null; redObserved: boolean } {
  const status = {
    ready: files.length === 0,
    taskMatches: payload.task === task,
    redObserved: false,
    passingPhase: null as string | null,
    reason: files.length === 0 ? "没有源码变更，不要求测试证据。" : "未找到与当前任务匹配的通过证据。",
  };
  if (!files.length || payload.task !== task) return status;
  const selected = new Set(files);
  const latestMtime = Math.max(
    0,
    ...files.filter((f) => existsSync(join(root, f))).map((f) => statSync(join(root, f)).mtimeMs)
  );
  for (const entry of payload.entries ?? []) {
    const evidenceFiles = new Set(entry.files ?? []);
    const covers = Boolean(entry.projectWide) || (evidenceFiles.size > 0 && [...selected].every((f) => evidenceFiles.has(f)));
    if (entry.phase === "red" && entry.status === "passed" && covers) status.redObserved = true;
    if (!PASSING_PHASES.has(entry.phase) || entry.status !== "passed" || !covers) continue;
    if (entry.fileHashes && JSON.stringify(entry.fileHashes) !== JSON.stringify(hashFiles(root, [...evidenceFiles].sort()))) continue;
    const recorded = entry.recordedAt ? Date.parse(entry.recordedAt) : NaN;
    if (Number.isNaN(recorded) || recorded + 1 < latestMtime) continue;
    status.ready = true;
    status.passingPhase = entry.phase;
    status.reason = "已找到与当前任务、文件范围和源码时间匹配的通过证据。";
  }
  if (!status.ready && payload.entries?.length) {
    status.reason = "现有证据与当前任务、文件范围或源码更新时间不匹配。";
  }
  return status;
}
