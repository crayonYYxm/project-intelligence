// `requirement` command family dispatcher (phase 3.D.2 + 3.D.3).
//
// Routes `requirement <subcommand> --requirement-id <id> ...` to the state-machine
// domain service. Query/registration subcommands (status/query/migrate/generate/
// add/acceptance/test-contract) and state-progression subcommands (ready/begin/
// reopen/amend) all call the service — no new top-level commands are introduced
// (review/finish/maintain are top-level commands in their own modules).

import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  realpathSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { extname, isAbsolute, join, relative, resolve } from "node:path";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import {
  loadRequirement,
  mutate,
  nowIso,
  normalizeTestEvidence,
  readyRequirement,
  beginRequirement,
  reopenRequirement,
  setAcceptanceCriteria,
  setTestContract,
  recordDiagnosis,
  recordLater,
  resolveReviewFindings,
  registerArtifact,
  generateArtifact,
  recordTestResult,
  requirementDir,
} from "../requirements/state-machine.js";
import { migrateLayout, artifactFilename } from "../requirements/layout.js";
import {
  captureRequirementScope,
  normalizeScopeFiles,
  validateScopeSelection,
} from "../requirements/scope.js";
import { inspectTestReport } from "../testing/render.js";
import { writeText } from "../fs/atomic-write.js";

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

function multi(args: string[], name: string): string[] {
  const out: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]!);
  }
  return out;
}

function requireId(args: string[]): string {
  const id = flag(args, "--requirement-id");
  if (!id) throw new UsageError("缺少 --requirement-id。");
  return id;
}

function manifestMentionsFile(value: unknown, file: string): boolean {
  if (typeof value === "string") {
    const normalized = value.replaceAll("\\", "/").replace(/^\.\//, "");
    return normalized === file || normalized.endsWith(`/${file}`);
  }
  if (Array.isArray(value)) return value.some((item) => manifestMentionsFile(item, file));
  if (value && typeof value === "object") {
    return Object.values(value as Record<string, unknown>).some((item) => manifestMentionsFile(item, file));
  }
  return false;
}

export function runRequirement(root: string, args: string[], global: GlobalOptions): CommandResult {
  const sub = args[0];
  const rest = args.slice(1);
  switch (sub) {
    case "status": {
      const id = requireId(rest);
      const manifest = loadRequirement(root, id);
      return ok({ requirementId: manifest.requirementId, state: manifest.state, revision: manifest.revision });
    }
    case "query": {
      const state = flag(rest, "--state");
      const file = flag(rest, "--file")?.replaceAll("\\", "/").replace(/^\.\//, "");
      const reqsDir = join(root, ".project-intel", "requirements");
      const ids = new Set<string>();
      if (existsSync(reqsDir)) {
        for (const d of readdirSafe(reqsDir)) {
          if (d !== "by-id" && existsSync(join(reqsDir, d, "manifest.json"))) ids.add(d);
        }
      }
      const legacyDir = join(reqsDir, "by-id");
      if (existsSync(legacyDir)) {
        for (const d of readdirSafe(legacyDir)) {
          if (existsSync(join(legacyDir, d, "manifest.json"))) ids.add(d);
        }
      }
      const matches = [...ids]
        .map((id) => loadRequirement(root, id))
        .filter((m) => !state || m.state === state)
        .filter((m) => !file || manifestMentionsFile(m as unknown as Record<string, unknown>, file))
        .map((m) => ({ requirementId: m.requirementId, requirementName: m.requirementName, state: m.state }));
      return ok({ requirements: matches });
    }
    case "migrate": {
      const apply = rest.includes("--apply");
      const reqsDir = join(root, ".project-intel", "requirements", "by-id");
      const legacy = existsSync(reqsDir) ? readdirSafe(reqsDir) : [];
      const results = legacy.map((id) => ({ id, ...migrateLayout(root, id, apply) }));
      return ok({ migrated: results, applied: apply });
    }
    case "generate": {
      const id = requireId(rest);
      const type = flag(rest, "--type") ?? "requirement";
      const manifest = generateArtifact(root, id, type, rest.includes("--replace"));
      const path = join(requirementDir(root, id), artifactFilename(type));
      return ok({ requirementId: manifest.requirementId, type, path, state: manifest.state });
    }
    case "add": {
      const id = requireId(rest);
      const type = flag(rest, "--type");
      const path = flag(rest, "--path");
      if (!type || !path) throw new UsageError("requirement add 需要 --type 和 --path。");
      const manifest = type.endsWith("-test")
        ? registerTestReport(root, id, type, path, rest)
        : registerArtifact(root, id, type, path);
      return ok({ requirementId: id, type, path, registered: true, state: manifest.state });
    }
    case "diagnose": {
      const id = requireId(rest);
      const rootCause = flag(rest, "--root-cause");
      if (!rootCause) throw new UsageError("requirement diagnose 需要 --root-cause。");
      const evidence = multi(rest, "--evidence");
      if (evidence.length === 0) throw new UsageError("requirement diagnose 需要 --evidence。");
      const manifest = recordDiagnosis(root, id, { rootCause, evidence });
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    case "defer": {
      const id = requireId(rest);
      const type = flag(rest, "--type");
      if (!type) throw new UsageError("requirement defer 需要 --type。");
      const manifest = recordLater(root, id, type);
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    case "resolve-finding": {
      const id = requireId(rest);
      const findingIds = multi(rest, "--finding-id");
      if (findingIds.length === 0) throw new UsageError("requirement resolve-finding 需要 --finding-id。");
      const resolvedBy = flag(rest, "--resolved-by");
      const resolution = flag(rest, "--resolution");
      if (!resolvedBy || !resolution) throw new UsageError("requirement resolve-finding 需要 --resolved-by 和 --resolution。");
      const manifest = resolveReviewFindings(root, id, findingIds, { resolvedBy, resolution });
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    case "acceptance": {
      const action = rest[0];
      if (action !== "set") throw new UsageError("requirement acceptance 只支持 set。");
      const id = requireId(rest);
      const criteria = multi(rest, "--criterion").map((c) => {
        const idx = c.indexOf(":");
        if (idx < 0) throw new UsageError(`--criterion 必须使用 AC-XX:说明 格式：${c}`);
        const acId = c.slice(0, idx).trim();
        const description = c.slice(idx + 1).trim();
        if (!/^AC-\d+$/i.test(acId)) throw new UsageError(`验收标准 ID 格式应为 AC-XX：${acId}`);
        if (!description) throw new UsageError(`验收标准描述不能为空：${c}`);
        return { id: acId, description };
      });
      if (criteria.length === 0) throw new UsageError("acceptance set 至少需要一个 --criterion。");
      const manifest = setAcceptanceCriteria(root, id, criteria);
      return ok({ requirementId: manifest.requirementId, acceptanceCriteria: manifest.acceptanceCriteria });
    }
    case "test-contract": {
      const action = rest[0];
      if (action !== "set") throw new UsageError("requirement test-contract 只支持 set。");
      const id = requireId(rest);
      const kind = flag(rest, "--kind");
      const reportAction = flag(rest, "--report-action");
      const reportPath = flag(rest, "--report-path");
      const acceptance = multi(rest, "--acceptance");
      if (!kind || !reportAction) throw new UsageError("test-contract set 需要 --kind 和 --report-action。");
      if (!["unit", "service", "manual", "both"].includes(kind)) {
        throw new UsageError("test-contract kind 只能是 unit、service、manual 或 both。");
      }
      if (!["generate", "register", "later"].includes(reportAction)) {
        throw new UsageError("test-contract report-action 只能是 generate、register 或 later。");
      }
      if (reportAction === "register" && !reportPath) {
        throw new UsageError("report-action=register 时必须提供 --report-path。");
      }
      const manifest = setTestContract(root, id, {
        kind,
        reportAction,
        acceptanceIds: acceptance,
        reportPath: reportPath ?? null,
      });
      return ok({ requirementId: manifest.requirementId, testContract: manifest.testContract });
    }
    case "ready": {
      const id = requireId(rest);
      const resolution = flag(rest, "--resolution") ?? "";
      const manifest = readyRequirement(root, id, resolution);
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    case "begin": {
      const id = requireId(rest);
      const manifest = beginRequirement(root, id);
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    case "reopen": {
      const id = requireId(rest);
      const reason = flag(rest, "--reason") ?? "";
      const manifest = reopenRequirement(root, id, reason);
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    case "amend": {
      const id = requireId(rest);
      const requirementName = flag(rest, "--requirement-name");
      const track = flag(rest, "--track");
      const ticketKind = flag(rest, "--ticket-kind");
      const externalApi = flag(rest, "--external-api");
      const reason = flag(rest, "--reason");
      if (!reason) throw new UsageError("requirement amend 需要 --reason。");
      // Validate enum values before writing.
      if (track !== undefined && !["quick", "standard", "complex", "auto"].includes(track)) {
        throw new UsageError("track 只能是 auto、quick、standard 或 complex。");
      }
      if (ticketKind !== undefined && !["bug", "requirement"].includes(ticketKind)) {
        throw new UsageError("ticket-kind 只能是 bug 或 requirement。");
      }
      if (externalApi !== undefined && !["yes", "no"].includes(externalApi)) {
        throw new UsageError("external-api 只能是 yes 或 no。");
      }
      // Check that at least one field is being changed (no-op amend is rejected).
      if (requirementName === undefined && track === undefined && ticketKind === undefined && externalApi === undefined) {
        throw new UsageError("amend 必须至少修改一个字段（--requirement-name / --track / --ticket-kind / --external-api）。");
      }
      // Apply the amendment via mutate, mirroring Python's amend_requirement:
      // - Invalidate all testEvidence and reviewRounds (set valid=false)
      // - Mark design artifacts as stale if design-affecting fields changed
      // - Roll back state to draft/specified for downstream states
      const manifest = mutate(root, id, (m) => {
        const before = {
          requirementName: m.requirementName,
          ticketKind: m.ticketKind,
          track: m.track,
          externalApiImpact: m.externalApiImpact,
        };
        if (requirementName !== undefined) m.requirementName = requirementName;
        if (track !== undefined) m.track = track;
        if (ticketKind !== undefined) m.ticketKind = ticketKind;
        if (externalApi !== undefined) {
          m.externalApiImpact = { confirmed: true, value: externalApi === "yes", source: "user" };
        }
        const after = {
          requirementName: m.requirementName,
          ticketKind: m.ticketKind,
          track: m.track,
          externalApiImpact: m.externalApiImpact,
        };
        // Reject no-op amend: if before and after are identical, no actual change
        // was made (mirrors Python's "amend 没有产生任何变化").
        if (JSON.stringify(before) === JSON.stringify(after)) {
          throw new UsageError("amend 没有产生任何变化。");
        }
        const designAffecting =
          before.requirementName !== after.requirementName ||
          before.ticketKind !== after.ticketKind ||
          JSON.stringify(before.externalApiImpact) !== JSON.stringify(after.externalApiImpact);

        // Invalidate all test evidence (normalize to array first, then invalidate).
        m.testEvidence = normalizeTestEvidence(m.testEvidence);
        for (const entry of (m.testEvidence ?? []) as Record<string, unknown>[]) {
          entry.valid = false;
          entry.invalidatedAt = nowIso();
          entry.invalidatedReason = "需求关键信息已修改。";
        }
        // Invalidate all review rounds.
        for (const round of m.reviewRounds ?? []) {
          round.valid = false;
          (round as Record<string, unknown>).invalidatedAt = nowIso();
          (round as Record<string, unknown>).invalidatedReason = "需求关键信息已修改。";
        }
        // Clear finish/maintenance results.
        (m as unknown as Record<string, unknown>).finishResult = null;
        (m as unknown as Record<string, unknown>).maintenanceResult = null;

        // Mark design artifacts as stale if design-affecting fields changed.
        if (designAffecting) {
          for (const artifact of m.artifacts ?? []) {
            const kind = artifact.type;
            if (kind === "design" || kind === "requirement-design" || kind === "requirement") {
              artifact.status = "stale";
              (artifact as Record<string, unknown>).invalidatedAt = nowIso();
              (artifact as Record<string, unknown>).invalidatedReason = "需求名称、类型或接口影响已修改。";
            }
          }
          m.diagnosis = null;
        }

        m.history ??= [];
        m.history.push({ action: "amend", reason, before, after, recordedAt: nowIso() });

        // Roll back state for downstream states.
        if (designAffecting) {
          m.state = "draft";
        } else if (["verified", "reviewed", "finished", "closed"].includes(m.state)) {
          m.state = "specified";
        }
      });
      return ok({ requirementId: manifest.requirementId, state: manifest.state });
    }
    default:
      throw new UsageError(`requirement 子命令不支持：${sub ?? "(空)"}`);
  }
}

function readdirSafe(dir: string): string[] {
  try {
    return readdirSync(dir);
  } catch {
    return [];
  }
}

function filesFlag(args: string[]): string[] {
  const index = args.indexOf("--files");
  if (index < 0) return [];
  const values: string[] = [];
  for (let cursor = index + 1; cursor < args.length && !args[cursor]!.startsWith("--"); cursor++) {
    values.push(args[cursor]!);
  }
  return values;
}

function resolveReport(root: string, value: string): { path: string; relativePath: string; content: Buffer } {
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
  return { path, relativePath, content: readFileSync(path) };
}

function manualEvidence(root: string, args: string[]): Record<string, unknown> {
  const evidence = {
    approved: args.includes("--manual-approved"),
    category: flag(args, "--manual-category") ?? "",
    reason: flag(args, "--manual-reason") ?? "",
    steps: flag(args, "--manual-steps") ?? "",
    input: flag(args, "--manual-input") ?? "",
    observation: flag(args, "--manual-observation") ?? "",
    evidencePath: flag(args, "--manual-evidence-path") ?? "",
  };
  if (
    !evidence.approved
    || !["visual", "device", "hardware", "configuration"].includes(evidence.category)
    || [evidence.reason, evidence.steps, evidence.input, evidence.observation, evidence.evidencePath]
      .some((value) => value.trim().length < 3)
  ) {
    throw new UsageError("人工测试必须包含审批、类别、原因、步骤、输入、观察结果和截图/日志路径。");
  }
  resolveReport(root, evidence.evidencePath);
  return evidence;
}

function archiveRegisteredReport(
  root: string,
  requirementId: string,
  testKind: string,
  report: { relativePath: string; content: Buffer },
  result: string,
  acceptanceIds: string[],
  files: string[],
  projectWide: boolean,
  sequence: number,
  executedCount: number
): { relativePath: string; sha256: string } {
  const directory = requirementDir(root, requirementId);
  const reportsDir = join(directory, "test-reports");
  mkdirSync(reportsDir, { recursive: true });
  const suffix = extname(report.relativePath).toLowerCase() || ".txt";
  const archivedPath = join(reportsDir, `TEST-${String(sequence).padStart(2, "0")}-${testKind}${suffix}`);
  writeFileSync(archivedPath, report.content);
  const canonicalPath = join(directory, "test-report.md");
  const existing = existsSync(canonicalPath)
    ? readFileSync(canonicalPath, "utf8").replace(/\s+$/g, "")
    : `# ${requirementId} 测试报告`;
  const entry = [
    "",
    `## TEST-${String(sequence).padStart(2, "0")} · ${testKind}`,
    "",
    `- 结果：${result}`,
    `- 已执行测试数：${executedCount}`,
    `- 验收标准：${acceptanceIds.join(", ")}`,
    `- 覆盖范围：${projectWide ? "全项目" : files.map((file) => `\`${file}\``).join(", ")}`,
    `- 来源文件：\`${report.relativePath}\``,
    `- 归档证据：\`${relative(root, archivedPath).replaceAll("\\", "/")}\``,
    "",
  ].join("\n");
  writeText(canonicalPath, `${existing}\n${entry}`);
  return {
    relativePath: relative(root, archivedPath).replaceAll("\\", "/"),
    sha256: createHash("sha256").update(readFileSync(archivedPath)).digest("hex"),
  };
}

function registerTestReport(
  root: string,
  requirementId: string,
  artifactType: string,
  pathValue: string,
  args: string[]
) {
  const testKind = artifactType.replace(/-test$/, "");
  if (!["unit", "service", "manual"].includes(testKind)) {
    throw new UsageError("测试产物类型只能是 unit-test、service-test 或 manual-test。");
  }
  const result = flag(args, "--result");
  if (!result || !["passed", "failed"].includes(result)) {
    throw new UsageError("测试产物必须通过 --result 登记 passed 或 failed。");
  }
  const report = resolveReport(root, pathValue);
  const inspected = inspectTestReport(report.content.toString("utf8"));
  if (!inspected) {
    throw new UsageError("登记的测试报告格式不受支持，必须包含真实且非零的测试执行计数。");
  }
  if (inspected.passed !== (result === "passed")) {
    throw new UsageError("测试报告实际结果与 --result 不一致。");
  }
  const acceptanceIds = [...new Set(
    multi(args, "--acceptance")
      .flatMap((value) => value.split(","))
      .map((value) => value.trim().toUpperCase())
      .filter(Boolean)
  )].sort();
  if (acceptanceIds.length === 0) throw new UsageError("登记测试报告必须提供 --acceptance。");
  const manifest = loadRequirement(root, requirementId);
  if (!["implementing", "verified"].includes(manifest.state)) {
    throw new UsageError("测试报告只能在 implementing 或 verified 状态登记。");
  }
  const contract = manifest.testContract;
  if (!contract || contract.source !== "explicit" || contract.status !== "selected") {
    throw new UsageError("测试契约尚未显式确认，不能登记测试报告。");
  }
  const contractKinds = contract.kind === "both" ? ["unit", "service"] : [String(contract.kind ?? "")];
  if (!contractKinds.includes(testKind)) {
    throw new UsageError("测试报告类型与已确认的测试契约不一致。");
  }
  const knownAcceptance = new Set(manifest.acceptanceCriteria.map((criterion) => criterion.id));
  const unknownAcceptance = acceptanceIds.filter((id) => !knownAcceptance.has(id));
  if (unknownAcceptance.length > 0) {
    throw new UsageError(`测试报告引用了未知验收标准：${unknownAcceptance.join(", ")}`);
  }
  const synthetic = {
    ...manifest,
    artifacts: [
      ...(manifest.artifacts ?? []),
      { type: artifactType, path: report.relativePath, sourcePath: report.relativePath },
    ],
  };
  const snapshot = captureRequirementScope(root, synthetic);
  const requestedFiles = filesFlag(args);
  const projectWide = args.includes("--project-wide");
  if (!projectWide && requestedFiles.length === 0) {
    throw new UsageError("登记测试报告必须提供 --files，或显式使用 --project-wide。");
  }
  const selectedFiles = projectWide
    ? normalizeScopeFiles(root, requestedFiles)
    : validateScopeSelection(root, requestedFiles, snapshot);
  if (!snapshot.gitAvailable || !snapshot.gitCommit || !snapshot.diffHash) {
    throw new UsageError("无法读取 Git 状态，不能登记需求级测试报告。");
  }
  const manual = testKind === "manual" ? manualEvidence(root, args) : undefined;
  const archived = archiveRegisteredReport(
    root,
    requirementId,
    testKind,
    report,
    result,
    acceptanceIds,
    selectedFiles,
    projectWide,
    (manifest.testEvidence?.length ?? 0) + 1,
    inspected.executedCount
  );
  return recordTestResult(root, requirementId, {
    phase: testKind === "manual" ? "manual" : "verify",
    passed: result === "passed",
    testKind,
    acceptance: acceptanceIds,
    files: selectedFiles,
    gitCommit: snapshot.gitCommit,
    diffHash: snapshot.diffHash,
    evidenceDiffHash: snapshot.evidenceDiffHash ?? snapshot.diffHash,
    gitAvailable: snapshot.gitAvailable,
    command: `register ${report.relativePath}`,
    reportPath: archived.relativePath,
    reportSha256: archived.sha256,
    reportSourcePath: report.relativePath,
    reportOriginalPath: report.relativePath,
    projectWide,
    ...(manual ? { manual } : {}),
  });
}

void global;
