// `test` command (phase 3.E.2), ported from application.run_project_test.
//
// Runs the given test commands via the shell layer, sanitizes output, records the
// evidence under `.project-intel/reports/test-evidence.{json,md}`, and — when a
// requirement id is supplied — calls the state machine's recordTestResult so the
// requirement lifecycle advances. Rejects forged pass-text without a real test
// count (AC-11).

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, realpathSync, statSync } from "node:fs";
import { isAbsolute, join, relative, resolve } from "node:path";
import { runShell } from "../process/exec-shell.js";
import { sanitizeText } from "../testing/sanitize.js";
import {
  phasePassed,
  executedTestCount,
  inspectTestReport,
  renderTestEvidence,
  type EvidencePayload,
  type EvidenceEntry,
  type TestResult,
} from "../testing/render.js";
import { writeJson, writeText, loadJson } from "../fs/atomic-write.js";
import { loadRequirement, mutate, recordTestResult, requirementDir } from "../requirements/state-machine.js";
import { artifactFilename } from "../requirements/artifacts.js";
import {
  captureRequirementScope,
  normalizeScopeFiles,
  sameScope,
  validateScopeSelection,
} from "../requirements/scope.js";
import { projectIntelDir } from "./init.js";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";

const VALID_PHASES = new Set(["red", "green", "regression", "verify", "manual"]);

interface TestArgs {
  task?: string;
  requirementId?: string;
  phase: string;
  testKind?: string;
  commands: string[];
  files: string[];
  acceptance?: string[];
  manualEvidence?: string;
  expectedFailure?: string;
  projectWide?: boolean;
  reportAction?: string;
  reportPath?: string;
  manualApproved?: boolean;
  manualCategory?: string;
  manualReason?: string;
  manualSteps?: string;
  manualInput?: string;
  manualObservation?: string;
  manualEvidencePath?: string;
}

interface CommandEvidenceResult extends TestResult {
  command: string;
  stdout: string;
  stderr: string;
  exitCode: number;
  executedCount: number;
}

function parseArgs(args: string[]): TestArgs {
  const phase = flag(args, "--phase");
  if (!phase || !VALID_PHASES.has(phase)) throw new UsageError(`--phase 必须是 red/green/regression/verify/manual：${phase ?? "(空)"}`);
  const opts: TestArgs = {
    phase,
    commands: multi(args, "--command"),
    files: multi(args, "--files"),
    acceptance: multi(args, "--acceptance"),
  };
  const tk = flag(args, "--test-kind");
  if (tk !== undefined) opts.testKind = tk;
  const task = flag(args, "--task");
  const requirementId = flag(args, "--requirement-id");
  const manualEvidence = flag(args, "--manual-evidence");
  const expectedFailure = flag(args, "--expect-failure");
  const reportAction = flag(args, "--report-action");
  const reportPath = flag(args, "--report-path");
  const manualCategory = flag(args, "--manual-category");
  const manualReason = flag(args, "--manual-reason");
  const manualSteps = flag(args, "--manual-steps");
  const manualInput = flag(args, "--manual-input");
  const manualObservation = flag(args, "--manual-observation");
  const manualEvidencePath = flag(args, "--manual-evidence-path");
  if (task !== undefined) opts.task = task;
  if (requirementId !== undefined) opts.requirementId = requirementId;
  if (manualEvidence !== undefined) opts.manualEvidence = manualEvidence;
  if (expectedFailure !== undefined) opts.expectedFailure = expectedFailure;
  if (args.includes("--project-wide")) opts.projectWide = true;
  if (reportAction !== undefined) opts.reportAction = reportAction;
  if (reportPath !== undefined) opts.reportPath = reportPath;
  if (args.includes("--manual-approved")) opts.manualApproved = true;
  if (manualCategory !== undefined) opts.manualCategory = manualCategory;
  if (manualReason !== undefined) opts.manualReason = manualReason;
  if (manualSteps !== undefined) opts.manualSteps = manualSteps;
  if (manualInput !== undefined) opts.manualInput = manualInput;
  if (manualObservation !== undefined) opts.manualObservation = manualObservation;
  if (manualEvidencePath !== undefined) opts.manualEvidencePath = manualEvidencePath;
  return opts;
}

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

function multi(args: string[], name: string): string[] {
  const out: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === name) {
      // --files consumes subsequent non-flag tokens; --command takes the next one.
      if (name === "--files") {
        let j = i + 1;
        while (j < args.length && !args[j]!.startsWith("--")) {
          out.push(args[j]!);
          j++;
        }
      } else if (args[i + 1] !== undefined) {
        out.push(args[i + 1]!);
      }
    }
  }
  return out;
}

export function runTest(root: string, args: string[], global: GlobalOptions): CommandResult {
  const opts = parseArgs(args);
  const task = opts.task ?? opts.requirementId ?? "(未记录)";
  let requirementContext: ReturnType<typeof prepareRequirementTest> | undefined;
  if (opts.requirementId) requirementContext = prepareRequirementTest(root, opts.requirementId, opts);

  const results: CommandEvidenceResult[] = opts.commands.map((command) => {
    const r = runShell(command, root);
    return {
      command: sanitizeText(command),
      stdout: sanitizeText(r.stdout),
      stderr: sanitizeText(r.stderr),
      exitCode: r.code,
      executedCount: executedTestCount({ stdout: r.stdout, stderr: r.stderr }),
    };
  });
  if (opts.reportAction === "register") {
    results.push(registeredReportEvidence(root, opts.reportPath!));
  }

  const passed = phasePassed(opts.phase, results, opts.manualEvidence, opts.expectedFailure);
  const entry: EvidenceEntry = {
    phase: opts.phase,
    status: passed ? "passed" : "failed",
    recordedAt: new Date().toISOString(),
    files: [...new Set(opts.files)].sort(),
    commands: results,
  };
  if (opts.projectWide) entry.projectWide = true;
  if (opts.manualEvidence) entry.manualEvidence = sanitizeText(opts.manualEvidence);
  if (opts.expectedFailure) entry.expectedFailure = sanitizeText(opts.expectedFailure);

  if (opts.requirementId) {
    const context = requirementContext!;
    const currentManifest = loadRequirement(root, opts.requirementId);
    const afterCommands = captureRequirementScope(root, currentManifest);
    if (!sameScope(context.snapshot, afterCommands)) {
      throw new UsageError("测试执行期间业务文件或 Git 提交发生变化，证据已拒绝。");
    }
    const report = prepareRequirementReport(root, opts.requirementId, opts, entry, results, passed);
    const manual = opts.phase === "manual" ? structuredManual(root, opts) : undefined;
    const evidence = {
      phase: opts.phase,
      passed,
      acceptance: context.acceptanceIds,
      files: context.selectedFiles,
      gitCommit: afterCommands.gitCommit,
      diffHash: afterCommands.diffHash,
      evidenceDiffHash: afterCommands.evidenceDiffHash ?? afterCommands.diffHash,
      gitAvailable: afterCommands.gitAvailable,
      command: opts.commands.join("; "),
      reportPath: report.relativePath,
      reportSha256: report.sha256,
      ...(report.sourcePath ? { reportSourcePath: report.sourcePath, reportOriginalPath: report.sourcePath } : {}),
      projectWide: Boolean(opts.projectWide),
      testKind: opts.testKind!,
      ...(manual ? { manual } : {}),
    };
    const recorded = recordTestResult(root, opts.requirementId, evidence);
    writeRequirementTestReport(root, opts.requirementId, recorded);
  } else {
    const reportsDir = join(projectIntelDir(root), "reports");
    mkdirSync(reportsDir, { recursive: true });
    const jsonPath = join(reportsDir, "test-evidence.json");
    const mdPath = join(reportsDir, "test-evidence.md");
    const current = loadJson<EvidencePayload>(jsonPath, { schemaVersion: 1, task, entries: [] });
    const entries = current.task === task ? current.entries : [];
    const now = new Date().toISOString();
    const payload: EvidencePayload = {
      schemaVersion: 1,
      task,
      createdAt: current.task === task && current.createdAt ? current.createdAt : now,
      updatedAt: now,
      entries: [...entries, entry].slice(-50),
    };
    writeJson(jsonPath, payload);
    writeText(mdPath, renderTestEvidence(payload));
  }

  void global;
  if (!passed && opts.phase !== "red") {
    return { exitCode: 1, result: { passed, phase: opts.phase, task } };
  }
  return ok({ passed, phase: opts.phase, task });
}

function prepareRequirementTest(root: string, requirementId: string, opts: TestArgs): {
  snapshot: ReturnType<typeof captureRequirementScope>;
  selectedFiles: string[];
  acceptanceIds: string[];
} {
  const manifest = loadRequirement(root, requirementId);
  if (manifest.state !== "implementing" && manifest.state !== "verified") {
    throw new UsageError("需求必须处于 implementing/verified 状态才能记录测试。");
  }
  const contract = manifest.testContract;
  if (!contract || contract.source !== "explicit" || contract.status !== "selected") {
    throw new UsageError("测试契约尚未显式确认。");
  }
  if (!opts.testKind || !["unit", "service", "manual"].includes(opts.testKind)) {
    throw new UsageError("需求级测试必须显式提供 --test-kind unit|service|manual。");
  }
  const channels = contract.kind === "both" ? ["unit", "service"] : [String(contract.kind ?? "")];
  if (!channels.includes(opts.testKind)) throw new UsageError("测试类型与已确认的测试契约不一致。");
  if (!opts.reportAction || opts.reportAction !== contract.reportAction) {
    throw new UsageError("必须显式提供与测试契约一致的 --report-action。");
  }
  if (opts.reportAction === "later") throw new UsageError("测试报告仍为 later，不能登记测试证据。");
  if (opts.reportAction === "register" && !opts.reportPath) {
    throw new UsageError("report-action=register 必须提供 --report-path。");
  }
  if (
    opts.reportAction === "register"
    && contract.reportPath
    && normalizeReportPath(opts.reportPath!) !== normalizeReportPath(String(contract.reportPath))
  ) {
    throw new UsageError("登记的测试报告路径与已确认的测试契约不一致。");
  }
  const acceptanceIds = [...new Set(
    (opts.acceptance ?? []).flatMap((value) => value.split(",")).map((value) => value.trim().toUpperCase()).filter(Boolean)
  )].sort();
  if (acceptanceIds.length === 0) throw new UsageError("需求级测试必须显式提供 --acceptance。");
  const contractAcceptance = new Set((contract.acceptanceIds as string[] | undefined) ?? []);
  const outsideContract = acceptanceIds.filter((id) => !contractAcceptance.has(id));
  if (outsideContract.length > 0) {
    throw new UsageError(`测试证据引用了契约外验收标准：${outsideContract.join(", ")}`);
  }
  if (opts.phase === "manual") structuredManual(root, opts);
  const snapshot = captureRequirementScope(root, manifest);
  let selectedFiles: string[];
  if (opts.projectWide) {
    selectedFiles = normalizeScopeFiles(root, opts.files);
  } else {
    if (opts.files.length === 0) throw new UsageError("需求级测试必须提供 --files 或 --project-wide。");
    selectedFiles = validateScopeSelection(root, opts.files, snapshot);
  }
  return { snapshot, selectedFiles, acceptanceIds };
}

function structuredManual(root: string, opts: TestArgs): Record<string, unknown> {
  const fields = {
    approved: opts.manualApproved === true,
    category: opts.manualCategory ?? "",
    reason: opts.manualReason ?? "",
    steps: opts.manualSteps ?? "",
    input: opts.manualInput ?? "",
    observation: opts.manualObservation ?? "",
    evidencePath: opts.manualEvidencePath ?? "",
  };
  if (
    !fields.approved
    || !["visual", "device", "hardware", "configuration"].includes(fields.category)
    || [fields.reason, fields.steps, fields.input, fields.observation, fields.evidencePath].some((value) => value.trim().length < 3)
  ) {
    throw new UsageError("人工测试必须包含审批、类别、原因、步骤、输入、观察结果和截图/日志路径。");
  }
  if (!existsSync(isAbsolute(fields.evidencePath) ? resolve(fields.evidencePath) : resolve(root, fields.evidencePath))) {
    throw new UsageError("人工测试截图或日志不存在。");
  }
  return fields;
}

function prepareRequirementReport(
  root: string,
  requirementId: string,
  opts: TestArgs,
  entry: EvidenceEntry,
  results: CommandEvidenceResult[],
  passed: boolean
): { relativePath: string; sha256: string; sourcePath?: string } {
  const manifest = loadRequirement(root, requirementId);
  const sequence = String((manifest.testEvidence?.length ?? 0) + 1).padStart(2, "0");
  const reportPath = join(requirementDir(root, requirementId), "test-reports", `TEST-${sequence}-${opts.testKind}.md`);
  if (opts.reportAction === "register") {
    const resolved = resolveReportFile(root, opts.reportPath!);
    const content = readFileSync(resolved.path, "utf8");
    const inspected = inspectTestReport(content);
    if (!inspected) {
      throw new UsageError("登记的测试报告格式不受支持，必须是含真实测试计数的 JSON、JUnit XML、TAP 或 unittest 报告。");
    }
    const lines = [
      `# ${requirementId} 测试报告`,
      "",
      `- 测试类型：${opts.testKind}`,
      `- 阶段：${opts.phase}`,
      `- 结果：${passed ? "passed" : "failed"}`,
      `- 验收标准：${(opts.acceptance ?? []).join(", ")}`,
      `- 文件范围：${opts.projectWide ? "project-wide" : opts.files.join(", ")}`,
      `- 原始报告：${resolved.relativePath}`,
      `- 报告格式：${inspected.format}`,
      `- 测试数量：${inspected.executedCount}`,
      `- 失败数量：${inspected.failedCount}`,
      "",
      "## 原始报告摘要",
      "",
      "```text",
      sanitizeText(content).slice(0, 20_000),
      "```",
      "",
    ];
    writeText(reportPath, lines.join("\n"));
    return {
      relativePath: relative(root, reportPath).replaceAll("\\", "/"),
      sha256: hashFile(reportPath),
      sourcePath: resolved.relativePath,
    };
  }
  const lines = [
    `# ${requirementId} 测试报告`,
    "",
    `- 测试类型：${opts.testKind}`,
    `- 阶段：${opts.phase}`,
    `- 结果：${passed ? "passed" : "failed"}`,
    `- 验收标准：${(opts.acceptance ?? []).join(", ")}`,
    `- 文件范围：${opts.projectWide ? "project-wide" : opts.files.join(", ")}`,
    "",
    "## 执行结果",
    "",
  ];
  if (results.length === 0) {
    lines.push(`- 人工证据：${entry.manualEvidence ?? ""}`);
  }
  for (const result of results) {
    lines.push(`### ${result.command}`);
    lines.push("");
    lines.push(`- exitCode: ${result.exitCode}`);
    lines.push(`- executedCount: ${result.executedCount}`);
    lines.push("");
    lines.push("```text");
    lines.push(sanitizeText(`${result.stdout}\n${result.stderr}`).slice(0, 20_000));
    lines.push("```");
    lines.push("");
  }
  writeText(reportPath, lines.join("\n"));
  return { relativePath: relative(root, reportPath).replaceAll("\\", "/"), sha256: hashFile(reportPath) };
}

function writeRequirementTestReport(
  root: string,
  requirementId: string,
  manifest: ReturnType<typeof loadRequirement>
): void {
  const evidence = (manifest.testEvidence ?? []) as Record<string, unknown>[];
  const latest = evidence.at(-1);
  const currentCommit = String(latest?.gitCommit ?? latest?.evidenceCommit ?? "");
  const currentHash = String(latest?.evidenceDiffHash ?? latest?.diffHash ?? "");
  const currentEvidence = evidence.filter((item) =>
    item.valid !== false
    && String(item.gitCommit ?? item.evidenceCommit ?? "") === currentCommit
    && String(item.evidenceDiffHash ?? item.diffHash ?? "") === currentHash
  );
  const advancingPhases = new Set(["green", "regression", "verify", "manual"]);
  const contractKind = String(manifest.testContract?.kind ?? "unit");
  const requiredChannels = contractKind === "both" ? ["unit", "service"] : [contractKind];
  const channelsPassing = requiredChannels.every((channel) => {
    const channelLatest = [...currentEvidence].reverse().find((item) =>
      String(item.testKind ?? "") === channel
      && advancingPhases.has(String(item.phase ?? ""))
    );
    return Boolean(channelLatest && (channelLatest.passed === true || channelLatest.result === "passed"));
  });
  const passingEvidence = channelsPassing
    ? currentEvidence.filter((item) =>
        advancingPhases.has(String(item.phase ?? ""))
        && (item.passed === true || item.result === "passed")
      )
    : [];
  const coveredAcceptance = new Set(
    passingEvidence.flatMap((item) => (item.acceptanceIds as string[] | undefined) ?? [])
  );
  const affectedFiles = [...new Set(
    currentEvidence.flatMap((item) => (item.files as string[] | undefined) ?? [])
  )].sort();
  const lines = [
    `# 测试文档：${manifest.requirementName}`,
    "",
    `> feature-id: ${requirementId}`,
    `> 测试日期：${new Date().toISOString().slice(0, 10)}`,
    `> 关联文档：${artifactFilename("requirement", manifest)} | ${artifactFilename("design", manifest)}`,
    `> 测试范围：${manifest.requirementName}`,
    "",
    "## 1. 测试环境与前置准备",
    "",
    `- 执行方式：${[...new Set(evidence.map((item) => String(item.testKind ?? "unit")))].join("、") || "自动化测试"}`,
    `- 当前状态：${manifest.state}`,
    `- 当前快照证据：${currentEvidence.length}（历史总计 ${evidence.length}）`,
    `- 最近执行：${String(latest?.recordedAt ?? "尚无执行时间")}`,
    "",
    "## 2. 核心规则与用例总览",
    "",
    "| 用例 ID | 验收标准 | 描述 | 结果 |",
    "|---|---|---|---|",
    ...manifest.acceptanceCriteria.map((criterion, index) =>
      `| T${index + 1} | ${criterion.id} | ${criterion.description.replaceAll("|", "\\|")} | ${coveredAcceptance.has(criterion.id) ? "通过" : "未通过"} |`
    ),
    "",
    "## 3. 功能用例",
    "",
    `当前快照记录 ${currentEvidence.length} 条测试证据，其中 ${passingEvidence.length} 条为有效通过证据；完整历史命令、计数和输出见“执行记录”。`,
    "",
    "## 4. 边界与异常用例",
    "",
    currentEvidence.some((item) => item.phase === "red")
      ? "已记录预期失败（RED）证据，用于证明实现前缺失行为或回归复现。"
      : "本轮未单列 RED 证据；边界与异常行为由已登记的验证或回归命令覆盖。",
    "",
    "## 5. 自动化与回归建议",
    "",
    "后续修改关联文件时，应按当前测试合同重新执行对应 unit/service 回归并刷新 Git 快照证据。",
    "",
    "## 6. 测试清单",
    "",
    ...manifest.acceptanceCriteria.map((criterion) =>
      `- [${coveredAcceptance.has(criterion.id) ? "x" : " "}] ${criterion.id} ${criterion.description}`
    ),
    "",
    "## 7. 涉及代码索引",
    "",
    ...(affectedFiles.length > 0 ? affectedFiles.map((path) => `- \`${path}\``) : ["- 本轮测试证据声明为项目级覆盖。"]),
    "",
    "## 执行记录",
    "",
  ];
  for (const item of evidence) {
    const reportPath = String(item.reportPath ?? "");
    const phase = String(item.phase ?? "");
    const evidencePassed = item.passed === true || item.result === "passed";
    const resultLabel = phase === "red"
      ? (evidencePassed ? "预期失败已复现" : "RED 复现无效")
      : (evidencePassed ? "passed" : "failed");
    const detail = reportPath && existsSync(join(root, reportPath))
      ? readFileSync(join(root, reportPath), "utf8").replace(/\s+$/g, "")
      : "";
    lines.push(`### ${String(item.id ?? "TEST")} · ${String(item.testKind ?? "unit")}`);
    lines.push("");
    lines.push(`- 阶段：${phase}`);
    lines.push(`- 结果：${resultLabel}`);
    lines.push(`- 验收标准：${((item.acceptanceIds as string[] | undefined) ?? []).join(", ")}`);
    lines.push(`- 文件范围：${((item.files as string[] | undefined) ?? []).join(", ")}`);
    lines.push(`- 明细报告：\`${reportPath}\``);
    lines.push("");
    if (detail) {
      lines.push("#### 执行明细");
      lines.push("");
      lines.push(...detail.split(/\r?\n/).map((line) => `    ${line}`));
      lines.push("");
    }
  }
  const path = join(requirementDir(root, requirementId), artifactFilename("test", manifest));
  writeText(path, `${lines.join("\n").replace(/\s+$/g, "")}\n`);
  const sha256 = hashFile(path);
  const advancing = latest
    ? ["green", "regression", "verify", "manual"].includes(String(latest.phase ?? ""))
    : false;
  const passed = latest?.passed === true || latest?.result === "passed";
  mutate(root, requirementId, (current) => {
    current.artifacts ??= [];
    const artifact = current.artifacts.find((item) => item.type === "test");
    const record = {
      type: "test",
      path: relative(root, path).replaceAll("\\", "/"),
      sha256,
      source: "generated",
      status: advancing ? (passed ? "passed" : "failed") : "recorded",
      validation: {
        ok: evidence.length > 0,
        schema: "test-report-v1",
        evidenceCount: evidence.length,
      },
      recordedAt: new Date().toISOString(),
    };
    if (artifact) Object.assign(artifact, record);
    else current.artifacts.push(record);
  });
}

function resolveReportFile(root: string, value: string): { path: string; relativePath: string } {
  const rootReal = realpathSync(root);
  const candidate = isAbsolute(value) ? resolve(value) : resolve(root, value);
  if (!existsSync(candidate) || !statSync(candidate).isFile() || statSync(candidate).size <= 0) {
    throw new UsageError(`测试报告不存在或为空：${value}`);
  }
  const path = realpathSync(candidate);
  const relativePath = relative(rootReal, path).replaceAll("\\", "/");
  if (relativePath === ".." || relativePath.startsWith("../") || isAbsolute(relativePath)) {
    throw new UsageError(`测试报告必须位于项目目录内：${value}`);
  }
  return { path, relativePath };
}

function normalizeReportPath(value: string): string {
  return value.replaceAll("\\", "/").replace(/^\.\//, "");
}

function registeredReportEvidence(root: string, value: string): CommandEvidenceResult {
  const report = resolveReportFile(root, value);
  const content = readFileSync(report.path, "utf8");
  const inspected = inspectTestReport(content);
  if (!inspected) {
    throw new UsageError("登记的测试报告格式不受支持，必须是含真实测试计数的 JSON、JUnit XML、TAP 或 unittest 报告。");
  }
  return {
    command: `report:${report.relativePath}`,
    stdout: sanitizeText(content).slice(0, 20_000),
    stderr: "",
    exitCode: inspected.passed ? 0 : 1,
    executedCount: inspected.executedCount,
  };
}

function hashFile(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}
