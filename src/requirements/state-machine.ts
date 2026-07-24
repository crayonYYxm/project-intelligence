// Requirement lifecycle state machine — domain service (phase 3.D.1), ported
// from requirements.py. This is a pure domain service: it owns the state machine,
// manifest persistence (lock + atomic write), and transition gates. It is called
// by the top-level `test`/`review`/`finish`/`maintain` commands and the
// `requirement` subcommand family. It does NOT register new top-level commands.
//
// States: draft -> specified -> designed -> ready -> implementing -> verified ->
// reviewed -> finished -> closed (with reopen/amend/defer side transitions).
// schemaVersion 2. AC-05 / AC-13.

import { existsSync, readFileSync, mkdirSync, realpathSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { withLock } from "../fs/lock.js";
import { writeJson, loadJson, writeText } from "../fs/atomic-write.js";
import { RequirementError } from "../errors.js";
import {
  captureRequirementScope,
  captureScopeSnapshot,
  sameScope,
  validateScopeSelection,
  type ScopeSnapshot,
} from "./scope.js";
import {
  readValidatedDocument,
  resolveRepositoryFile,
  validateDeliveryDocument,
  validateDeliveryDocumentInRepository,
  validateSourceEvidenceEntries,
  type DocumentValidation,
} from "./documents.js";
import { inspectTestReport } from "../testing/render.js";
import { sanitizeText } from "../testing/sanitize.js";

export const SCHEMA_VERSION = 2;
export const LEGACY_SCHEMA_VERSION = 1;
export const STATES = [
  "draft", "specified", "designed", "ready", "implementing", "verified", "reviewed", "finished", "closed",
  "documented", // schema v1 compat; not written under v2
] as const;
export type RequirementState = (typeof STATES)[number];

const VALID_NEXT: Record<string, RequirementState[]> = {
  draft: ["specified"],
  specified: ["designed"],
  designed: ["ready"],
  ready: ["implementing"],
  implementing: ["verified", "reviewed"],
  verified: ["reviewed"],
  reviewed: ["finished"],
  finished: ["closed", "implementing"], // reopen -> implementing
  closed: ["implementing"], // reopen
};

export interface RequirementManifest {
  schemaVersion: number;
  revision: number;
  requirementId: string;
  requirementName: string;
  ticketKind: string;
  track: string;
  state: RequirementState;
  externalApiImpact: { confirmed: boolean; value: boolean; source?: string };
  sourceTickets: unknown[];
  changedFiles: unknown[];
  diagnosis?: { status: string; rootCause: string; evidence: { path: string; symbol?: string; sha256?: string }[]; recordedAt: string } | null;
  acceptanceCriteria: { id: string; description: string; status?: string }[];
  testContract?: Record<string, unknown>;
  workflowSelections?: Record<string, unknown>;
  readiness?: { resolutions?: { resolution: string; recordedAt: string }[]; blockers?: { id: string; artifactType: string; reason: string; recordedAt: string; resolution: string | null; resolvedAt: string | null }[] };
  testEvidence?: Record<string, unknown>[];
  review?: Record<string, unknown>;
  reviewRounds?: {
    id?: string;
    result: string;
    summary: string;
    findings?: Record<string, unknown>[];
    recordedAt: string;
    valid?: boolean;
    files?: string[];
    diffHash?: string;
    evidenceDiffHash?: string;
    gitCommit?: string;
    [key: string]: unknown;
  }[];
  artifacts?: {
    type: string;
    path: string;
    sha256?: string;
    status?: string;
    result?: string;
    source?: string;
    sourcePath?: string;
    reportSha256?: string;
    validation?: DocumentValidation | Record<string, unknown>;
    documentKind?: string;
    registeredAt?: string;
    recordedAt?: string;
    updatedAt?: string;
    [key: string]: unknown;
  }[];
  scopeSnapshots?: (ScopeSnapshot & { kind?: string; selectedFiles?: string[] })[];
  baselineScope?: { diffHash?: string; gitCommit?: string; entries?: ScopeSnapshot["entries"] } | null;
  baselineDiffHash?: string | null;
  baselineCommit?: string | null;
  currentDiffHash?: string | null;
  finishResult?: Record<string, unknown> | null;
  maintenanceResult?: Record<string, unknown> | null;
  stateTimestamps?: Record<string, string>;
  history?: { action: string; recordedAt: string; [key: string]: unknown }[];
  createdAt: string;
  updatedAt: string;
}

/** Resolve the `.project-intel/requirements/<id>` directory (v2 direct layout). */
export function requirementDir(root: string, requirementId: string): string {
  return join(root, ".project-intel", "requirements", normalizeId(requirementId));
}

export function manifestPath(root: string, requirementId: string): string {
  return join(requirementDir(root, requirementId), "manifest.json");
}

/** Legacy by-id layout (read-only fallback for v0.6.1 compat). */
export function legacyManifestPath(root: string, requirementId: string): string {
  return join(root, ".project-intel", "requirements", "by-id", normalizeId(requirementId), "manifest.json");
}

export function activeManifestPath(root: string, requirementId: string): string {
  const current = manifestPath(root, requirementId);
  if (existsSync(current)) return current;
  const legacy = legacyManifestPath(root, requirementId);
  return existsSync(legacy) ? legacy : current;
}

export function normalizeId(id: string): string {
  // Pure numeric ids get a bug/req prefix; otherwise return as-is (sanitized).
  const trimmed = (id ?? "").trim();
  if (/^\d+$/.test(trimmed)) return trimmed; // canonicalize at the command layer
  return trimmed.replace(/[^A-Za-z0-9._-]/g, "-");
}

/** Read + validate a requirement manifest (raises RequirementError on problems). */
export function loadRequirement(root: string, requirementId: string): RequirementManifest {
  const path = activeManifestPath(root, requirementId);
  if (!existsSync(path)) {
    throw new RequirementError(`未找到需求档案：${normalizeId(requirementId)}`);
  }
  const payload = loadJson<RequirementManifest>(path, {} as RequirementManifest);
  if (!payload || typeof payload !== "object" || ![SCHEMA_VERSION, LEGACY_SCHEMA_VERSION].includes(payload.schemaVersion)) {
    throw new RequirementError(`不支持的需求档案格式：${path}`);
  }
  payload.ticketKind ??= "requirement";
  payload.sourceTickets ??= [];
  payload.changedFiles ??= [];
  payload.diagnosis ??= null;
  payload.acceptanceCriteria ??= [];
  payload.acceptanceCriteria = payload.acceptanceCriteria.map((criterion) => ({
    ...criterion,
    status: criterion.status ?? "pending",
  }));
  payload.artifacts ??= [];
  payload.testEvidence = normalizeTestEvidence(payload.testEvidence);
  payload.reviewRounds ??= [];
  payload.scopeSnapshots ??= [];
  payload.finishResult ??= null;
  payload.maintenanceResult ??= null;
  payload.baselineScope ??= null;
  return payload;
}

/** Persist a manifest atomically under the requirement lock. */
export function writeManifest(root: string, requirementId: string, manifest: RequirementManifest): void {
  const dir = requirementDir(root, requirementId);
  mkdirSync(dir, { recursive: true });
  manifest.updatedAt = nowIso();
  const path = join(dir, "manifest.json");
  // Lock lives in the parent of the requirement dir (not under by-id/, for Windows).
  withLock(dir, () => {
    writeJson(path, manifest);
  });
}

/**
 * Apply a mutation to a requirement manifest under its lock. Raises
 * RequirementError on invalid transitions. Mirrors requirements._mutate.
 */
export function mutate(
  root: string,
  requirementId: string,
  fn: (manifest: RequirementManifest) => void
): RequirementManifest {
  const path = activeManifestPath(root, requirementId);
  const dir = dirname(path);
  return withLock(dir, () => {
    const manifest = loadRequirement(root, requirementId);
    fn(manifest);
    manifest.revision = (manifest.revision ?? 1) + 1;
    manifest.updatedAt = nowIso();
    writeJson(path, manifest);
    return manifest;
  });
}

/** Enforce a state transition is legal; raise RequirementError otherwise. */
export function assertTransition(from: RequirementState, to: RequirementState): void {
  const allowed = VALID_NEXT[from];
  if (!allowed || !allowed.includes(to)) {
    throw new RequirementError(`非法状态迁移：${from} -> ${to}`);
  }
}

function setState(manifest: RequirementManifest, next: RequirementState): void {
  assertTransition(manifest.state as RequirementState, next);
  manifest.state = next;
  manifest.stateTimestamps ??= {};
  manifest.stateTimestamps[next] = nowIso();
}

/** Create a new requirement manifest (idempotent on matching identity). */
export function createRequirement(
  root: string,
  requirementId: string,
  requirementName: string,
  options: {
    track?: string;
    externalApi?: boolean;
    ticketKind?: string;
    requirementAction?: string;
    requirementPath?: string;
    designAction?: string;
    designPath?: string;
  } = {}
): RequirementManifest {
  const track = options.track ?? "standard";
  if (!["quick", "standard", "complex", "auto"].includes(track)) {
    throw new RequirementError("track 只能是 auto、quick、standard 或 complex。");
  }
  const name = (requirementName ?? "").replace(/\s+/g, " ").trim();
  if (!name) throw new RequirementError("需求名称不能为空。");
  const ticketKind = options.ticketKind ?? "requirement";
  if (!["bug", "requirement"].includes(ticketKind)) {
    throw new RequirementError("ticket kind 只能是 bug 或 requirement。");
  }
  const rawId = String(requirementId ?? "").trim();
  if (!rawId) throw new RequirementError("需求号不能为空。");
  const identifier = normalizeId(/^\d+$/.test(rawId)
    ? `${ticketKind === "bug" ? "bug" : "req"}${rawId}`
    : rawId);
  const selections: Record<string, Record<string, unknown>> = {};
  for (const [key, actionValue, pathValue] of [
    ["requirement", options.requirementAction, options.requirementPath],
    ["design", options.designAction, options.designPath],
  ] as const) {
    if (actionValue === undefined) {
      if (pathValue) throw new RequirementError("只有 action=register 时才能提供已有文档路径。");
      continue;
    }
    if (!["generate", "register", "later"].includes(actionValue)) {
      throw new RequirementError("文档动作只能是 generate、register 或 later。");
    }
    if (actionValue === "register" && !pathValue) {
      throw new RequirementError(`文档动作 register 必须提供 ${key} 路径。`);
    }
    if (actionValue !== "register" && pathValue) {
      throw new RequirementError("只有文档动作 register 可以提供已有文件路径。");
    }
    const normalizedPath = pathValue ? resolveRepositoryFile(root, pathValue).relativePath : null;
    selections[key] = {
      action: actionValue,
      path: normalizedPath,
      status: "selected",
      selectedAt: nowIso(),
    };
  }
  const path = activeManifestPath(root, identifier);
  const dir = dirname(path);
  mkdirSync(dir, { recursive: true });

  if (existsSync(path)) {
    const current = loadRequirement(root, identifier);
    if (current.requirementName !== name) {
      throw new RequirementError(`需求号 ${identifier} 已绑定其他需求名称；如需修改请使用 requirement amend。`);
    }
    const currentExternal = current.externalApiImpact ?? { confirmed: false, value: false };
    if (
      current.track !== track
      || current.ticketKind !== ticketKind
      || Boolean(currentExternal.confirmed) !== (options.externalApi !== undefined)
      || Boolean(currentExternal.value) !== Boolean(options.externalApi)
    ) {
      throw new RequirementError(`需求号 ${identifier} 已存在且关键信息不同；如需修改请使用 requirement amend。`);
    }
    for (const [key, selection] of Object.entries(selections)) {
      const existing = current.workflowSelections?.[key] as Record<string, unknown> | undefined;
      if (!existing || existing.action !== selection.action || existing.path !== selection.path) {
        throw new RequirementError(`需求号 ${identifier} 已存在且文档动作不同；如需修改请使用 requirement amend。`);
      }
    }
    return current;
  }
  const created = nowIso();
  const baseline = captureScopeSnapshot(root);
  const manifest: RequirementManifest = {
    schemaVersion: SCHEMA_VERSION,
    revision: 1,
    requirementId: identifier,
    requirementName: name,
    ticketKind,
    track,
    state: "draft",
    externalApiImpact: { confirmed: options.externalApi !== undefined, value: Boolean(options.externalApi), source: "user" },
    sourceTickets: [],
    changedFiles: [],
    diagnosis: null,
    acceptanceCriteria: [],
    readiness: { blockers: [], resolutions: [] },
    artifacts: [],
    testContract: {
      kind: null,
      reportAction: null,
      acceptanceIds: [],
      reportPath: null,
      status: "pending",
      recordedAt: created,
      source: "pending",
    },
    testEvidence: [],
    reviewRounds: [],
    scopeSnapshots: [],
    workflowSelections: selections,
    baselineDiffHash: baseline.diffHash || null,
    baselineCommit: baseline.gitCommit || null,
    baselineScope: {
      diffHash: baseline.diffHash,
      gitCommit: baseline.gitCommit,
      entries: baseline.entries,
    },
    currentDiffHash: null,
    finishResult: null,
    maintenanceResult: null,
    history: [],
    stateTimestamps: { draft: created },
    createdAt: created,
    updatedAt: created,
  };
  writeManifest(root, identifier, manifest);
  return manifest;
}

/** Transition: designed -> ready (requires non-empty resolution + readiness inputs). */
export function readyRequirement(root: string, requirementId: string, resolution: string): RequirementManifest {
  const clean = (resolution ?? "").trim();
  if (!clean) throw new RequirementError("进入 ready 必须记录非空的确认或阻塞解决说明。");
  return mutate(root, requirementId, (m) => {
    if (m.state !== "designed" && m.state !== "documented") {
      throw new RequirementError("只有需求文档和设计文档均完成的 designed 状态可以进入 ready。");
    }
    assertReadinessInputs(root, m);
    m.readiness ??= { resolutions: [] };
    (m.readiness.resolutions ??= []).push({ resolution: clean, recordedAt: nowIso() });
    setState(m, "ready");
  });
}

/** Transition: ready -> implementing (requires external-api confirmation). */
export function beginRequirement(root: string, requirementId: string): RequirementManifest {
  return mutate(root, requirementId, (m) => {
    if (m.state !== "ready") {
      throw new RequirementError("需求必须先通过 ready 门禁才能开始实现。");
    }
    assertReadinessInputs(root, m);
    if (!m.externalApiImpact?.confirmed) {
      throw new RequirementError("开始实现前必须明确确认是否影响对外接口。");
    }
    setState(m, "implementing");
  });
}

/** Normalize testEvidence to an array. Handles:
 *  - undefined → []
 *  - single object (legacy Node or Python v1) → [object]
 *  - array (Python v2) → array */
export function normalizeTestEvidence(raw: unknown): Record<string, unknown>[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw as Record<string, unknown>[];
  if (typeof raw === "object") return [raw as Record<string, unknown>];
  return [];
}

/** Check if a test evidence entry represents a pass. Handles both Node
 *  (passed: true) and Python (result: "passed") field names. */
function isPassingEvidence(e: Record<string, unknown>): boolean {
  if (e.passed === true) return true;
  if (e.result === "passed") return true;
  return false;
}

/** Check if a test evidence entry is from an advancing phase. Handles both Node
 *  (phase: "green"/"regression"/"verify") and Python (testKind: "unit"/"service"/"manual")
 *  field names. In Python, any testKind with result="passed" is advancing. */
function isAdvancingEvidence(e: Record<string, unknown>): boolean {
  const ADVANCING_PHASES = new Set(["green", "regression", "verify"]);
  const phase = String(e.phase ?? "");
  if (phase && ADVANCING_PHASES.has(phase)) return true;
  // Python schema: testKind is unit/service/manual, result is passed/failed.
  // All testKinds are "advancing" in the sense that a pass advances the state.
  const testKind = String(e.testKind ?? "");
  if (testKind && ["unit", "service", "manual"].includes(testKind)) return true;
  return false;
}

function evidenceHash(evidence: Record<string, unknown>): string {
  return String(evidence.evidenceDiffHash ?? evidence.diffHash ?? "");
}

function reportIsCurrent(root: string, evidence: Record<string, unknown>): boolean {
  const reportPath = String(evidence.reportPath ?? "").replaceAll("\\", "/");
  const expected = String(evidence.reportSha256 ?? "");
  if (!reportPath || !expected || reportPath.startsWith("../") || reportPath.includes("/../")) return false;
  const path = join(root, reportPath);
  if (!existsSync(path)) return false;
  return createHash("sha256").update(readFileSync(path)).digest("hex") === expected;
}

function assertCurrentTestGate(
  root: string,
  manifest: RequirementManifest,
  snapshot: ScopeSnapshot,
  selectedFiles: string[]
): void {
  if (!snapshot.gitAvailable || !snapshot.gitCommit || !snapshot.diffHash) {
    throw new RequirementError("无法读取 Git 状态，不能验证测试证据。");
  }
  const contract = manifest.testContract;
  if (!contract || contract.source !== "explicit" || contract.status !== "selected") {
    throw new RequirementError("测试契约尚未显式确认。");
  }
  const hash = snapshot.evidenceDiffHash ?? snapshot.diffHash;
  const records = normalizeTestEvidence(manifest.testEvidence).filter((evidence) =>
    evidence.valid !== false
    && evidenceHash(evidence) === hash
    && String(evidence.gitCommit ?? evidence.evidenceCommit ?? "") === snapshot.gitCommit
  );
  const channels = contract.kind === "both"
    ? ["unit", "service"]
    : [String(contract.kind ?? "")];
  for (const channel of channels) {
    const latest = [...records].reverse().find((evidence) => String(evidence.testKind ?? "") === channel);
    if (!latest || !isPassingEvidence(latest) || !reportIsCurrent(root, latest)) {
      throw new RequirementError(`当前快照缺少有效且通过的 ${channel} 测试报告。`);
    }
  }
  const covered = new Set<string>();
  for (const evidence of records) {
    if (!isPassingEvidence(evidence) || !reportIsCurrent(root, evidence)) continue;
    for (const id of (evidence.acceptanceIds as string[] | undefined) ?? []) covered.add(id);
  }
  const missingAcceptance = manifest.acceptanceCriteria
    .map((criterion) => criterion.id)
    .filter((id) => !covered.has(id));
  if (missingAcceptance.length > 0) {
    throw new RequirementError(`以下验收标准缺少通过证据：${missingAcceptance.join(", ")}`);
  }
  const actualFiles = new Set(snapshot.evidenceFiles ?? snapshot.files);
  if (actualFiles.size > 0) {
    const hasCoveringEvidence = records.some((evidence) => {
      if (!isPassingEvidence(evidence) || !reportIsCurrent(root, evidence)) return false;
      if (evidence.projectWide === true) return true;
      const files = new Set((evidence.files as string[] | undefined) ?? []);
      return [...actualFiles].every((pathValue) => files.has(pathValue));
    });
    if (!hasCoveringEvidence) {
      throw new RequirementError("测试证据文件范围未覆盖全部实际 Git 变更。");
    }
  }
  const selected = new Set(selectedFiles);
  const omitted = [...actualFiles].filter((pathValue) => !selected.has(pathValue));
  if (omitted.length > 0) {
    throw new RequirementError(`提交的文件范围遗漏实际 Git 变更：${omitted.join(", ")}`);
  }
}

/** Transition: implementing -> verified (records a test evidence result).
 *  Only green/regression/verify phases can advance to verified; RED and manual
 *  record evidence but do NOT advance the state (mirrors Python record_test_result).
 *  testEvidence is an ARRAY — new entries are appended, not overwritten.
 *  Handles legacy single-object and Python result="passed" field formats. */
export function recordTestResult(
  root: string,
  requirementId: string,
  evidence: {
    phase: string;
    passed: boolean;
    acceptance?: string[];
    testKind?: string;
    files?: string[];
    gitCommit?: string;
    diffHash?: string;
    evidenceDiffHash?: string;
    gitAvailable?: boolean;
    command?: string;
    reportPath?: string;
    reportSha256?: string;
    reportSourcePath?: string;
    reportOriginalPath?: string;
    projectWide?: boolean;
    manual?: Record<string, unknown>;
  }
): RequirementManifest {
  const current = loadRequirement(root, requirementId);
  const contract = current.testContract;
  if (!contract || contract.source !== "explicit" || contract.status !== "selected") {
    throw new RequirementError("测试契约尚未显式确认，不能登记需求级测试证据。");
  }
  const testKind = evidence.testKind
    ?? (evidence.phase === "manual" ? "manual" : "unit");
  if (!["unit", "service", "manual"].includes(testKind)) {
    throw new RequirementError("test-kind 只能是 unit、service 或 manual；both 只能用于测试契约。");
  }
  const channels = contract.kind === "both" ? ["unit", "service"] : [String(contract.kind ?? "")];
  if (!channels.includes(testKind)) {
    throw new RequirementError("测试证据类型与已确认的测试契约不一致。");
  }
  const acceptance = [...new Set((evidence.acceptance ?? []).map((id) => id.trim().toUpperCase()).filter(Boolean))].sort();
  if (acceptance.length === 0) {
    throw new RequirementError("需求级测试必须显式传入 --acceptance 映射。");
  }
  const known = new Set(current.acceptanceCriteria.map((criterion) => criterion.id));
  const unknown = acceptance.filter((id) => !known.has(id));
  if (unknown.length > 0) throw new RequirementError(`测试证据引用了未知验收标准：${unknown.join(", ")}`);
  if (!evidence.gitAvailable || !evidence.gitCommit || !evidence.diffHash) {
    throw new RequirementError("无法读取 Git 状态，不能登记需求级测试证据。");
  }
  if (evidence.passed) {
    const reportPath = String(evidence.reportPath ?? "");
    const reportSha256 = String(evidence.reportSha256 ?? "");
    if (!reportPath || !reportSha256 || !existsSync(join(root, reportPath))) {
      throw new RequirementError("通过测试必须登记当前有效的测试报告文件。");
    }
    const actual = createHash("sha256").update(readFileSync(join(root, reportPath))).digest("hex");
    if (actual !== reportSha256) throw new RequirementError("测试报告内容与登记摘要不一致。");
  }
  return mutate(root, requirementId, (m) => {
    if (m.state !== "implementing" && m.state !== "verified") {
      throw new RequirementError("只有 implementing/verified 状态可以记录测试证据。");
    }
    const ADVANCING_PHASES = new Set(["green", "regression", "verify", "manual"]);
    const isAdvancing = ADVANCING_PHASES.has(evidence.phase);

    // Normalize testEvidence to an array (handles legacy single-object format).
    m.testEvidence = normalizeTestEvidence(m.testEvidence);
    const arr = m.testEvidence as Record<string, unknown>[];

    // Write a record compatible with BOTH Node and Python schemas.
    const entryId = `TEST-${String(arr.length + 1).padStart(2, "0")}`;
    const entry: Record<string, unknown> = {
      id: entryId,
      // Node fields:
      phase: evidence.phase,
      passed: evidence.passed,
      acceptance,
      // Python-compatible fields:
      testKind,
      result: evidence.passed ? "passed" : "failed",
      acceptanceIds: acceptance,
      files: evidence.files ?? [],
      projectWide: Boolean(evidence.projectWide),
      // Git snapshot binding (for freshness checks at review/finish time):
      gitCommit: evidence.gitCommit ?? "",
      evidenceCommit: evidence.gitCommit ?? "",
      diffHash: evidence.diffHash ?? "",
      evidenceDiffHash: evidence.evidenceDiffHash ?? evidence.diffHash ?? "",
      command: evidence.command ?? "",
      reportPath: evidence.reportPath ?? "",
      reportSha256: evidence.reportSha256 ?? "",
      reportSourcePath: evidence.reportSourcePath ?? evidence.reportOriginalPath ?? "",
      reportOriginalPath: evidence.reportOriginalPath ?? evidence.reportSourcePath ?? "",
      recordedAt: nowIso(),
      valid: true,
    };
    if (evidence.manual) entry.manual = evidence.manual;
    arr.push(entry);
    m.scopeSnapshots ??= [];
    m.scopeSnapshots.push({
      kind: "test",
      capturedAt: nowIso(),
      gitAvailable: true,
      gitCommit: evidence.gitCommit ?? "",
      diffHash: evidence.diffHash ?? "",
      evidenceDiffHash: evidence.evidenceDiffHash ?? evidence.diffHash ?? "",
      files: evidence.files ?? [],
      evidenceFiles: evidence.files ?? [],
      entries: [],
    });
    m.currentDiffHash = evidence.diffHash ?? "";
    if (evidence.reportPath) {
      m.artifacts ??= [];
      const artifactType = `${testKind}-test`;
      const existing = m.artifacts.find((artifact) => artifact.type === artifactType);
      const artifact = {
        type: artifactType,
        path: evidence.reportPath,
        sha256: String(evidence.reportSha256 ?? ""),
        status: evidence.passed ? "passed" : "failed",
        result: evidence.passed ? "passed" : "failed",
        source: "generated",
        ...(evidence.reportSourcePath || evidence.reportOriginalPath
          ? { sourcePath: evidence.reportSourcePath ?? evidence.reportOriginalPath }
          : {}),
        testKind,
        acceptanceIds: acceptance,
        recordedAt: nowIso(),
      };
      if (existing) Object.assign(existing, artifact);
      else m.artifacts.push(artifact);
    }
    for (const blocker of m.readiness?.blockers ?? []) {
      if (blocker.artifactType === "test" && !blocker.resolvedAt) {
        blocker.resolution = "测试报告和证据已登记。";
        blocker.resolvedAt = nowIso();
      }
    }

    // Determine whether to advance to verified. The testContract determines
    // which test kinds are required. Only advance when ALL required kinds have
    // valid passing evidence AND all acceptance criteria are covered.
    if (!evidence.passed) {
      m.state = "implementing";
      m.stateTimestamps ??= {};
      m.stateTimestamps.implementing = nowIso();
    } else if (m.state === "implementing") {
        const contractKind = String(m.testContract?.kind ?? "");
        const requiredKinds = new Set<string>();
        if (contractKind === "unit" || contractKind === "") requiredKinds.add("unit");
        if (contractKind === "service") requiredKinds.add("service");
        if (contractKind === "manual") requiredKinds.add("manual");
        if (contractKind === "both") { requiredKinds.add("unit"); requiredKinds.add("service"); }
        // Check that each required kind has at least one valid passing entry.
        const evidenceHash = evidence.evidenceDiffHash ?? evidence.diffHash;
        const allSatisfied = [...requiredKinds].every((kind) => {
          const latest = [...arr].reverse().find((item) =>
            item.valid !== false
            && String(item.testKind) === kind
            && String(item.evidenceDiffHash ?? item.diffHash ?? "") === evidenceHash
          );
          return Boolean(latest && (latest.passed === true || latest.result === "passed"));
        });
        // Check acceptance coverage: the union of acceptanceIds across all
        // valid passing evidence must cover all acceptance criteria.
        const allAcIds = new Set(m.acceptanceCriteria.map((ac) => ac.id));
        const coveredAcIds = new Set<string>();
        for (const e of arr) {
          if (
            e.valid !== false
            && (e.passed === true || e.result === "passed")
            && String(e.evidenceDiffHash ?? e.diffHash ?? "") === evidenceHash
          ) {
            for (const id of (e.acceptanceIds as string[]) ?? (e.acceptance as string[]) ?? []) {
              coveredAcIds.add(id);
            }
          }
        }
        const allAcCovered = allAcIds.size === 0 || [...allAcIds].every((id) => coveredAcIds.has(id));
        if (allSatisfied && allAcCovered) {
          setState(m, "verified");
        }
    }
  });
}

/** Transition: verified -> reviewed (records a review result). Mirrors record_review:
 *  result="passed" advances to reviewed; result="failed" stays at verified.
 *  Unresolved critical/important findings force effective_result="failed" even when
 *  the caller passes result="passed" (mirrors Python's BLOCKING_FINDINGS gate). */
export function validateReviewRequirement(
  root: string,
  requirementId: string,
  result: "passed" | "failed",
  files: string[],
  currentSnapshot?: ScopeSnapshot
): { manifest: RequirementManifest; snapshot: ScopeSnapshot; selectedFiles: string[] } {
  const manifest = loadRequirement(root, requirementId);
  if (manifest.state !== "verified" && manifest.state !== "reviewed") {
    throw new RequirementError("只有 verified/reviewed 状态可以登记评审。");
  }
  const snapshot = currentSnapshot ?? captureRequirementScope(root, manifest);
  const selectedFiles = validateScopeSelection(root, files, snapshot);
  if (result === "passed") assertCurrentTestGate(root, manifest, snapshot, selectedFiles);
  return { manifest, snapshot, selectedFiles };
}

export function recordReview(
  root: string,
  requirementId: string,
  review: {
    result: "passed" | "failed";
    summary: string;
    findings?: { severity: string; text: string }[];
    files: string[];
    snapshot?: ScopeSnapshot;
  }
): RequirementManifest {
  const validated = validateReviewRequirement(root, requirementId, review.result, review.files, review.snapshot);
  const { snapshot, selectedFiles } = validated;
  return mutate(root, requirementId, (m) => {
    if (m.state !== "verified" && m.state !== "reviewed") {
      throw new RequirementError("只有 verified/reviewed 状态可以登记评审。");
    }
    const lockedSnapshot = captureRequirementScope(root, m);
    if (!sameScope(snapshot, lockedSnapshot)) {
      throw new RequirementError("登记评审期间代码或 Git 提交发生变化，请重新测试和评审。");
    }
    if (review.result === "passed") {
      assertCurrentTestGate(root, m, lockedSnapshot, selectedFiles);
    }

    m.reviewRounds ??= [];
    const roundNumber = m.reviewRounds.length + 1;
    // Assign stable finding IDs (FINDING-<round>-<index>) and check for unresolved
    // blocking findings from previous rounds.
    const BLOCKING_FINDINGS = new Set(["critical", "important"]);
    const normalizedFindings = (review.findings ?? []).map((f, i) => ({
      id: `FINDING-${String(roundNumber).padStart(2, "0")}-${String(i + 1).padStart(2, "0")}`,
      severity: f.severity,
      text: sanitizeText(f.text),
      resolved: false,
    }));
    // Check for unresolved blocking findings from ALL previous valid rounds.
    const unresolved: string[] = [];
    for (const round of m.reviewRounds) {
      if (!round.valid) continue;
      for (const finding of round.findings ?? []) {
        const f = finding as Record<string, unknown>;
        if (BLOCKING_FINDINGS.has(String(f.severity)) && !f.resolved) {
          unresolved.push(String(f.id ?? "(unknown)"));
        }
      }
    }
    // Also check findings in THIS round — if result="passed" but there are
    // unresolved blocking findings, force effective_result="failed".
    const newUnresolved = normalizedFindings.filter((f) => BLOCKING_FINDINGS.has(f.severity));
    const effectiveResult = (unresolved.length > 0 || newUnresolved.length > 0) ? "failed" : review.result;

    m.reviewRounds.push({
      id: `REVIEW-${String(roundNumber).padStart(2, "0")}`,
      result: effectiveResult,
      summary: sanitizeText(review.summary),
      findings: normalizedFindings,
      files: selectedFiles,
      diffHash: lockedSnapshot.diffHash,
      evidenceDiffHash: lockedSnapshot.evidenceDiffHash ?? lockedSnapshot.diffHash,
      gitCommit: lockedSnapshot.gitCommit,
      recordedAt: nowIso(),
      valid: true,
    });
    m.scopeSnapshots ??= [];
    m.scopeSnapshots.push({ kind: "review", ...lockedSnapshot, selectedFiles });
    m.currentDiffHash = lockedSnapshot.diffHash;
    if (effectiveResult === "passed") {
      setState(m, "reviewed");
    } else {
      m.state = "verified";
    }
  });
}

/** Transition: reviewed -> finished (gate: valid advancing testEvidence + passed review + no unresolved findings + code freshness). */
export function validateFinishRequirement(
  root: string,
  requirementId: string,
  files: string[],
  currentSnapshot?: ScopeSnapshot
): { manifest: RequirementManifest; snapshot: ScopeSnapshot; selectedFiles: string[] } {
  const manifest = loadRequirement(root, requirementId);
  if (manifest.state !== "reviewed") {
    throw new RequirementError("只有 reviewed 状态可以 finish。");
  }
  const snapshot = currentSnapshot ?? captureRequirementScope(root, manifest);
  const selectedFiles = validateScopeSelection(root, files, snapshot);
  assertReadinessInputs(root, manifest);
  assertCurrentTestGate(root, manifest, snapshot, selectedFiles);
  const evidenceHash = snapshot.evidenceDiffHash ?? snapshot.diffHash;
  const reviews = (manifest.reviewRounds ?? []).filter((round) => round.valid !== false);
  const latestReview = reviews.at(-1) as Record<string, unknown> | undefined;
  if (
    !latestReview
    || latestReview.result !== "passed"
    || String(latestReview.evidenceDiffHash ?? latestReview.diffHash ?? "") !== evidenceHash
    || String(latestReview.gitCommit ?? "") !== snapshot.gitCommit
  ) {
    throw new RequirementError("评审证据与当前 Git 变更不一致，必须重新评审。");
  }
  const reviewedFiles = new Set((latestReview.files as string[] | undefined) ?? []);
  const missingReviewFiles = selectedFiles.filter((pathValue) => !reviewedFiles.has(pathValue));
  if (missingReviewFiles.length > 0) {
    throw new RequirementError(`评审证据文件范围不完整：${missingReviewFiles.join(", ")}`);
  }
  const unresolved = reviews.flatMap((round) =>
    (round.findings ?? []).filter((finding) =>
      ["critical", "important"].includes(String(finding.severity))
      && !finding.resolved
    )
  );
  if (unresolved.length > 0) {
    throw new RequirementError("finish 门禁：仍有未解决的 critical/important 评审问题。");
  }
  if (!hasCurrentArtifact(root, manifest, "closure")) {
    throw new RequirementError("缺少当前有效的复盘收口总结文件。");
  }
  return { manifest, snapshot, selectedFiles };
}

export function finishRequirement(
  root: string,
  requirementId: string,
  files: string[],
  currentSnapshot?: ScopeSnapshot
): RequirementManifest {
  const validated = validateFinishRequirement(root, requirementId, files, currentSnapshot);
  return mutate(root, requirementId, (m) => {
    const lockedSnapshot = captureRequirementScope(root, m);
    if (!sameScope(validated.snapshot, lockedSnapshot)) {
      throw new RequirementError("完成需求期间代码或 Git 提交发生变化，请重新测试和评审。");
    }
    validateScopeSelection(root, files, lockedSnapshot);
    m.currentDiffHash = lockedSnapshot.diffHash;
    m.scopeSnapshots ??= [];
    m.scopeSnapshots.push({ kind: "finish", ...lockedSnapshot, selectedFiles: validated.selectedFiles });
    const selected = new Set(validated.selectedFiles);
    m.changedFiles = lockedSnapshot.entries
      .filter((entry) => selected.has(entry.path) || (entry.oldPath && selected.has(entry.oldPath)))
      .map((entry) => ({ ...entry, recordedAt: nowIso() }));
    m.finishResult = {
      status: "passed",
      diffHash: lockedSnapshot.diffHash,
      evidenceDiffHash: lockedSnapshot.evidenceDiffHash ?? lockedSnapshot.diffHash,
      gitCommit: lockedSnapshot.gitCommit,
      files: validated.selectedFiles,
      recordedAt: nowIso(),
    };
    for (const criterion of m.acceptanceCriteria) criterion.status = "passed";
    setState(m, "finished");
  });
}

/** Transition: finished -> closed. */
export function validateFinishedFreshness(root: string, requirementId: string): ScopeSnapshot {
  const manifest = loadRequirement(root, requirementId);
  if (manifest.state !== "finished") throw new RequirementError("只有 finished 状态可以执行维护和关闭。");
  const snapshot = captureRequirementScope(root, manifest);
  if (!snapshot.gitAvailable || !snapshot.diffHash) {
    throw new RequirementError("无法读取 Git 状态，不能关闭需求。");
  }
  const finishResult = manifest.finishResult ?? {};
  if (
    finishResult.status !== "passed"
    || finishResult.diffHash !== snapshot.diffHash
    || finishResult.gitCommit !== snapshot.gitCommit
  ) {
    throw new RequirementError("finish 后代码或 Git 提交发生变化，必须重新测试、评审和 finish。");
  }
  if (manifest.acceptanceCriteria.some((criterion) => criterion.status !== "passed")) {
    throw new RequirementError("仍有验收标准未通过，不能关闭需求。");
  }
  assertReadinessInputs(root, manifest);
  assertCurrentTestGate(root, manifest, snapshot, (finishResult.files as string[] | undefined) ?? []);
  if (!hasCurrentArtifact(root, manifest, "closure")) {
    throw new RequirementError("复盘收口总结已删除、篡改或失效，不能关闭需求。");
  }
  return snapshot;
}

export function closeRequirement(root: string, requirementId: string, checkSucceeded: boolean): RequirementManifest {
  if (!checkSucceeded) throw new RequirementError("维护检查失败，需求保持 finished 状态。");
  const expected = validateFinishedFreshness(root, requirementId);
  return mutate(root, requirementId, (m) => {
    if (m.state !== "finished") throw new RequirementError("只有 finished 状态可以 maintain/close。");
    const locked = captureRequirementScope(root, m);
    if (!sameScope(expected, locked)) {
      throw new RequirementError("finish 后代码或 Git 提交发生变化，必须重新测试、评审和 finish。");
    }
    m.maintenanceResult = {
      status: "passed",
      diffHash: locked.diffHash,
      evidenceDiffHash: locked.evidenceDiffHash ?? locked.diffHash,
      gitCommit: locked.gitCommit,
      recordedAt: nowIso(),
    };
    setState(m, "closed");
  });
}

/** Transition: closed/finished -> implementing (reopen).
 *  Mirrors Python reopen_requirement: invalidates test evidence, review rounds,
 *  and closure artifacts; records reopen history; returns to the strongest
 *  reusable document state (not directly to implementing). */
export function reopenRequirement(root: string, requirementId: string, reason: string): RequirementManifest {
  const clean = (reason ?? "").trim();
  if (!clean) throw new RequirementError("重开需求必须记录原因。");
  return mutate(root, requirementId, (m) => {
    if (m.state !== "closed" && m.state !== "finished") {
      throw new RequirementError("只有 closed/finished 状态可以 reopen。");
    }
    // Invalidate test evidence (normalize to array first, then invalidate).
    m.testEvidence = normalizeTestEvidence(m.testEvidence);
    for (const entry of (m.testEvidence ?? []) as Record<string, unknown>[]) {
      entry.valid = false;
      entry.invalidatedAt = nowIso();
      entry.invalidatedReason = "需求已重新打开。";
    }
    // Invalidate all review rounds.
    for (const round of m.reviewRounds ?? []) {
      round.valid = false;
      (round as Record<string, unknown>).invalidatedAt = nowIso();
      (round as Record<string, unknown>).invalidatedReason = "需求已重新打开。";
    }
    // Mark closure artifacts as stale.
    for (const artifact of m.artifacts ?? []) {
      if (artifact.type === "closure" && artifact.status !== "stale") {
        artifact.status = "stale";
        (artifact as Record<string, unknown>).invalidatedAt = nowIso();
        (artifact as Record<string, unknown>).invalidatedReason = "需求已重新打开。";
      }
    }
    // Clear finish/maintenance results.
    (m as unknown as Record<string, unknown>).finishResult = null;
    (m as unknown as Record<string, unknown>).maintenanceResult = null;
    // Record reopen history.
    m.history ??= [];
    m.history.push({ action: "reopen", reason: clean, recordedAt: nowIso() });
    // Return to the strongest reusable document state. Mirrors Python's
    // _best_document_state: designed if both requirement + design exist and are
    // valid; specified if only requirement exists; draft otherwise.
    const hasRequirementDoc = hasCurrentArtifact(root, m, "requirement");
    const hasDesignDoc = hasCurrentArtifact(root, m, "design");
    if (hasRequirementDoc && hasDesignDoc) {
      m.state = "designed";
    } else if (hasRequirementDoc) {
      m.state = "specified";
    } else {
      m.state = "draft";
    }
  });
}

/** Amend acceptance criteria (atomic replace). */
export function setAcceptanceCriteria(root: string, requirementId: string, criteria: { id: string; description: string }[]): RequirementManifest {
  const normalized: { id: string; description: string; status: string }[] = [];
  const seen = new Set<string>();
  for (const criterion of criteria) {
    const id = String(criterion.id ?? "").trim().toUpperCase();
    const description = String(criterion.description ?? "").replace(/\s+/g, " ").trim();
    if (!/^AC-\d{2,}$/.test(id)) {
      throw new RequirementError("验收标准 ID 必须使用 AC-01 形式。");
    }
    if (seen.has(id)) throw new RequirementError(`验收标准 ID 重复：${id}`);
    if (!description) throw new RequirementError(`验收标准说明不能为空：${id}`);
    seen.add(id);
    normalized.push({ id, description, status: "pending" });
  }
  if (normalized.length === 0) throw new RequirementError("至少需要一项验收标准。");
  return mutate(root, requirementId, (m) => {
    if (m.state !== "draft" && m.state !== "specified") {
      throw new RequirementError("只有 draft/specified 状态可以设置验收标准；下游需求请先 reopen。");
    }
    m.acceptanceCriteria = normalized;
  });
}

/** Set the pre-implementation test contract. */
export function setTestContract(root: string, requirementId: string, contract: Record<string, unknown>): RequirementManifest {
  const kind = String(contract.kind ?? "").trim();
  const reportAction = String(contract.reportAction ?? "").trim();
  if (!["unit", "service", "manual", "both"].includes(kind)) {
    throw new RequirementError("测试契约类型只能是 unit、service、manual 或 both。");
  }
  if (!["generate", "register", "later"].includes(reportAction)) {
    throw new RequirementError("测试报告动作只能是 generate、register 或 later。");
  }
  const reportPath = String(contract.reportPath ?? "").trim();
  if (reportAction === "register" && !reportPath) {
    throw new RequirementError("report-action=register 必须提供 report path。");
  }
  const registeredReport = reportAction === "register" ? resolveTestContractReport(root, reportPath) : null;
  return mutate(root, requirementId, (m) => {
    if (!["draft", "specified", "designed", "documented", "ready"].includes(m.state)) {
      throw new RequirementError("测试契约只能在实现前设置；下游需求请先 reopen。");
    }
    if (m.externalApiImpact?.value && !["service", "both"].includes(kind)) {
      throw new RequirementError("对外接口需求必须选择 service 或 both 测试契约。");
    }
    const known = new Set(m.acceptanceCriteria.map((criterion) => criterion.id));
    const acceptanceIds = [...new Set(
      ((contract.acceptanceIds ?? contract.acceptance ?? []) as unknown[])
        .flatMap((value) => String(value ?? "").split(","))
        .map((value) => value.trim().toUpperCase())
        .filter(Boolean)
    )].sort();
    const unknown = acceptanceIds.filter((id) => !known.has(id));
    if (unknown.length > 0) {
      throw new RequirementError(`测试契约引用了未知验收标准：${unknown.join(", ")}`);
    }
    if (acceptanceIds.length === 0) {
      throw new RequirementError("测试契约必须显式映射至少一项验收标准。");
    }
    m.testContract = {
      kind,
      reportAction,
      acceptanceIds,
      reportPath: registeredReport?.relativePath ?? null,
      ...(registeredReport
        ? {
            reportSha256: registeredReport.sha256,
            reportFormat: registeredReport.format,
            reportExecutedCount: registeredReport.executedCount,
            reportPassed: registeredReport.passed,
          }
        : {}),
      status: reportAction === "later" ? "deferred" : "selected",
      recordedAt: nowIso(),
      source: "explicit",
    };
    m.readiness ??= { blockers: [], resolutions: [] };
    m.readiness.blockers ??= [];
    if (reportAction === "later") {
      m.readiness.blockers.push({
        id: `BLOCK-${String(m.readiness.blockers.length + 1).padStart(2, "0")}`,
        artifactType: "test",
        reason: "测试报告动作选择稍后处理。",
        recordedAt: nowIso(),
        resolution: null,
        resolvedAt: null,
      });
    } else {
      for (const blocker of m.readiness.blockers) {
        if (blocker.artifactType === "test" && !blocker.resolvedAt) {
          blocker.resolution = "测试契约已确认。";
          blocker.resolvedAt = nowIso();
        }
      }
    }
  });
}

function resolveTestContractReport(
  root: string,
  value: string
): { relativePath: string; sha256: string; format: string; executedCount: number; passed: boolean } {
  if (value.includes("\0")) throw new RequirementError("测试报告路径不能为空。");
  const rootReal = realpathSync(root);
  const candidate = isAbsolute(value) ? resolve(value) : resolve(root, value);
  if (!existsSync(candidate)) throw new RequirementError(`测试报告不存在：${value}`);
  const path = realpathSync(candidate);
  const relativePath = relative(rootReal, path).replaceAll("\\", "/");
  if (relativePath === ".." || relativePath.startsWith("../") || isAbsolute(relativePath)) {
    throw new RequirementError(`测试报告必须位于项目目录内：${value}`);
  }
  const stat = statSync(path);
  if (!stat.isFile() || stat.size <= 0) throw new RequirementError(`测试报告不存在或为空：${value}`);
  const content = readFileSync(path, "utf8");
  const inspected = inspectTestReport(content);
  if (!inspected) {
    throw new RequirementError("登记的测试报告格式不受支持，必须是含真实测试计数的 JSON、JUnit XML、TAP 或 unittest 报告。");
  }
  return {
    relativePath,
    sha256: createHash("sha256").update(content).digest("hex"),
    format: inspected.format,
    executedCount: inspected.executedCount,
    passed: inspected.passed,
  };
}

/**
 * Record a Bug root cause with source-backed evidence. Mirrors
 * record_diagnosis: requires ticketKind=bug, state in {specified, designed,
 * documented}; if the diagnosis arrives after design, the design artifact is
 * marked stale and the state rolls back to specified.
 */
export function recordDiagnosis(
  root: string,
  requirementId: string,
  diagnosis: { rootCause: string; evidence: string[] }
): RequirementManifest {
  const cleanCause = (diagnosis.rootCause ?? "").replace(/\s+/g, " ").trim();
  if (cleanCause.length < 12) {
    throw new RequirementError("Bug 根因必须提供至少 12 个有效字符的可验证说明。");
  }
  const rawEvidence: { path: string; symbol?: string }[] = [];
  for (const raw of diagnosis.evidence ?? []) {
    const [pathPart, symbolPart] = String(raw ?? "").split("#");
    const relative = (pathPart ?? "").trim();
    if (!relative) continue;
    const entry: { path: string; symbol?: string } = { path: relative };
    const sym = (symbolPart ?? "").trim();
    if (sym) entry.symbol = sym;
    rawEvidence.push(entry);
  }
  const normalized = validateSourceEvidenceEntries(root, rawEvidence, "Bug 根因源码证据");
  return mutate(root, requirementId, (m) => {
    if (m.ticketKind !== "bug") {
      throw new RequirementError("只有 Bug 需求需要登记 diagnosis。");
    }
    if (m.state !== "specified" && m.state !== "designed" && m.state !== "documented") {
      throw new RequirementError("必须先完成 requirement.md，才能登记 Bug 根因。");
    }
    if (m.state === "designed" || m.state === "documented") {
      for (const artifact of m.artifacts ?? []) {
        if ((artifact.type === "design" || artifact.type === "requirement-design") && artifact.status !== "stale") {
          artifact.status = "stale";
        }
      }
      m.state = "specified";
    }
    m.diagnosis = { status: "confirmed", rootCause: cleanCause, evidence: normalized, recordedAt: nowIso() };
    m.history ??= [];
    m.history.push({ action: "record-diagnosis", rootCause: cleanCause, evidence: normalized, recordedAt: nowIso() });
  });
}

/**
 * Defer an artifact to later, adding a readiness blocker. Mirrors record_later:
 * requirement/design/test/closure are allowed; the workflow selection is marked
 * `later` for document types.
 */
export function recordLater(root: string, requirementId: string, artifactType: string): RequirementManifest {
  const normalized = artifactType === "requirement-design" ? "design" : artifactType;
  if (!["requirement", "design", "test", "closure"].includes(normalized)) {
    throw new RequirementError("later 只支持 requirement、design、test 或 closure。");
  }
  const allowed: Record<string, RequirementState[]> = {
    requirement: ["draft", "specified"],
    design: ["draft", "specified", "designed", "documented"],
    test: ["implementing", "verified"],
    closure: ["reviewed"],
  };
  return mutate(root, requirementId, (m) => {
    if (!allowed[normalized]?.includes(m.state as RequirementState)) {
      throw new RequirementError(`当前状态不能将 ${normalized} 记录为稍后处理。`);
    }
    const selected = m.workflowSelections?.[normalized] as Record<string, unknown> | undefined;
    if (selected && selected.action !== "later") {
      throw new RequirementError(`${normalized} 已选择 ${String(selected.action)}；如需改为 later，请先使用 requirement amend。`);
    }
    m.readiness ??= {};
    m.readiness.blockers ??= [];
    const blockers = m.readiness.blockers;
    blockers.push({
      id: `BLOCK-${String(blockers.length + 1).padStart(2, "0")}`,
      artifactType: normalized,
      reason: `${normalized} 选择稍后处理。`,
      recordedAt: nowIso(),
      resolution: null,
      resolvedAt: null,
    });
    if (normalized === "requirement" || normalized === "design") {
      m.workflowSelections ??= {};
      const sel = m.workflowSelections as Record<string, Record<string, unknown>>;
      sel[normalized] = { action: "later", status: "deferred" };
    }
  });
}

/**
 * Resolve review findings by stable ID. Mirrors resolve_review_findings: marks
 * each finding resolved, records history, and rolls reviewed back to verified.
 */
export function resolveReviewFindings(
  root: string,
  requirementId: string,
  findingIds: string[],
  resolution: { resolvedBy: string; resolution: string }
): RequirementManifest {
  const identifiers = [...new Set((findingIds ?? []).map((s) => String(s ?? "").trim()).filter(Boolean))].sort();
  if (identifiers.length === 0) {
    throw new RequirementError("至少提供一个需要解决的 finding ID。");
  }
  const cleanBy = (resolution.resolvedBy ?? "").trim();
  const cleanRes = (resolution.resolution ?? "").trim();
  if (!cleanBy || !cleanRes) {
    throw new RequirementError("解决 finding 必须记录 resolved-by 和 resolution。");
  }
  return mutate(root, requirementId, (m) => {
    if (m.state !== "verified" && m.state !== "reviewed") {
      throw new RequirementError("只有 verified 或 reviewed 状态可以解决评审问题。");
    }
    const indexed = new Map<string, Record<string, unknown>>();
    for (const round of m.reviewRounds ?? []) {
      if (!round.valid) continue;
      for (const finding of round.findings ?? []) {
        const f = finding as Record<string, unknown>;
        const id = f.id as string | undefined;
        if (id) indexed.set(id, f);
      }
    }
    const missing = identifiers.filter((id) => !indexed.has(id));
    if (missing.length > 0) {
      throw new RequirementError("未找到有效的评审问题：" + missing.join(", "));
    }
    const resolvedAt = nowIso();
    for (const id of identifiers) {
      const finding = indexed.get(id);
      if (!finding) continue;
      finding.resolved = true;
      finding.resolvedBy = cleanBy;
      finding.resolution = cleanRes;
      finding.resolvedAt = resolvedAt;
    }
    m.history ??= [];
    m.history.push({ action: "resolve-review-findings", findingIds: identifiers, resolvedBy: cleanBy, resolution: cleanRes, recordedAt: resolvedAt });
    if (m.state === "reviewed") {
      m.state = "verified";
    }
  });
}

const GENERATED_ARTIFACT_FILES: Record<string, string> = {
  requirement: "requirement.md",
  design: "design.md",
  plan: "plan.md",
  test: "test-report.md",
  closure: "closure-summary.md",
};

function generatedArtifactText(manifest: RequirementManifest, type: string): string {
  if (type === "requirement") {
    const criteria = manifest.acceptanceCriteria
      .map((criterion) => `- ${criterion.id}：${criterion.description}`)
      .join("\n");
    return `# ${manifest.requirementId} ${manifest.requirementName} 需求文档

## 文档信息

- 需求号：${manifest.requirementId}
- 需求名称：${manifest.requirementName}
- 单据类型：${manifest.ticketKind === "bug" ? "Bug" : "Requirement"}

## 背景与现状

待补充。

## 目标

待补充。

## 业务场景

待补充。

## 范围

待补充。

## 非目标

待补充。

## 业务规则与异常边界

待补充。

## 验收标准

${criteria || "- 待补充。"}

## 外部接口影响

待补充。

## 待确认事项

待补充。
`;
  }
  if (type === "design") {
    const sections = manifest.ticketKind === "bug"
      ? ["Bug现象", "原因分析", "修复方案", "改造思路", "新旧代码对照", "逻辑变更说明", "影响范围", "风险评估"]
      : [
          "需求问题概述", "需求描述", "需求提出部门及联系人", "电信需求负责人", "需求适用范围",
          "需求期望完成时间", "设计相关选项", "场景分析", "风险考虑", "实现方案", "数据模型",
          "表结构设计", "新增模型汇总", "表结构描述", "建表语句", "表数据转储策略", "界面设计",
        ];
    return [
      `# ${manifest.requirementId}_${manifest.requirementName}_设计文档`,
      "",
      ...sections.flatMap((sectionName) => [`## ${sectionName}`, "", "待补充。", ""]),
    ].join("\n");
  }
  if (type === "plan") {
    const mapping = manifest.acceptanceCriteria
      .map((criterion) => `| ${criterion.id} | ${criterion.description} | [待补充测试类型] | [待补充命令或步骤] |`)
      .join("\n");
    return `# ${manifest.requirementId} ${manifest.requirementName} 实施计划

## 实施范围

待补充。

## 输入基线

- \`requirement.md\`
- \`design.md\`

## 文件级变更

| 仓库相对路径 | 符号或区域 | 修改目的 | 对应 AC |
| --- | --- | --- | --- |
| [待补充路径] | [待补充符号] | [待补充目的] | [待补充 AC] |

## 实施步骤

1. 待补充。

## 测试与验收映射

| 验收标准 | 说明 | 测试类型 | 命令或人工步骤 |
| --- | --- | --- | --- |
${mapping || "| [待补充 AC] | [待补充说明] | [待补充类型] | [待补充步骤] |"}

## 风险与回滚

- 风险：待补充。
- 回滚：待补充。
`;
  }
  if (type === "test") {
    const criteria = manifest.acceptanceCriteria
      .map((criterion) => `- ${criterion.id}：计划验证，尚未执行。`)
      .join("\n");
    return `# ${manifest.requirementName} · 测试报告

- 需求号：\`${manifest.requirementId}\`
- 当前状态：计划中

## 测试计划

${criteria || "- 等需求验收标准登记后补充测试映射。"}

## 执行记录

尚未执行。只有写入实际命令、结果和验收标准映射后，本文档才可作为完成证据。
`;
  }
  const criteria = manifest.acceptanceCriteria
    .map((criterion) => `- ${criterion.id}：通过 — ${criterion.description}`)
    .join("\n");
  return `# ${manifest.requirementId} ${manifest.requirementName} 复盘收口总结

## 验收标准

${criteria}

## 收口说明

当前实现、测试、评审和变更范围已经汇总；最终完成状态以当前 Git 快照的 finish 门禁为准。
`;
}

/** Generate a canonical lifecycle artifact without silently overwriting user content. */
export function generateArtifact(
  root: string,
  requirementId: string,
  artifactType: string,
  replace = false
): RequirementManifest {
  const type = artifactType === "requirement-design" ? "design"
    : artifactType === "test-report" ? "test"
      : artifactType;
  if (!Object.hasOwn(GENERATED_ARTIFACT_FILES, type)) {
    throw new RequirementError("可生成的产物类型只能是 requirement、design、plan、test 或 closure。");
  }
  const current = loadRequirement(root, requirementId);
  const allowed: Record<string, RequirementState[]> = {
    requirement: ["draft", "specified"],
    design: ["specified", "designed"],
    plan: ["designed", "ready"],
    test: ["implementing", "verified"],
    closure: ["reviewed", "finished"],
  };
  if (current.state === "closed") {
    throw new RequirementError("需求已 closed；如需修改产物请先 reopen。");
  }
  if (!allowed[type]!.includes(current.state)) {
    throw new RequirementError(`当前状态不能生成 ${type} 产物。`);
  }
  const selected = current.workflowSelections?.[type] as Record<string, unknown> | undefined;
  if ((type === "requirement" || type === "design") && selected && selected.action !== "generate") {
    throw new RequirementError(`${type} 已选择 ${String(selected.action)}；如需改为 generate，请先使用 requirement amend。`);
  }
  const path = join(requirementDir(root, requirementId), GENERATED_ARTIFACT_FILES[type]!);
  const existed = existsSync(path);
  const backup = existed ? readFileSync(path) : null;
  if (type !== "test" && existed && readFileSync(path).length > 0 && !replace) {
    throw new RequirementError(`${GENERATED_ARTIFACT_FILES[type]} 已存在；确需覆盖请显式使用 --replace。`);
  }
  if (type === "test" && existed && readFileSync(path).length > 0) {
    return current;
  }
  const content = generatedArtifactText(current, type);
  try {
    return mutate(root, requirementId, (manifest) => {
      writeText(path, content);
      const relative = relativePath(root, path);
      const digest = createHash("sha256").update(readFileSync(path)).digest("hex");
      const status = type === "closure" ? "registered" : "draft";
      const validation: DocumentValidation | Record<string, unknown> = type === "closure"
        ? validateDeliveryDocument(manifest, type, readFileSync(path, "utf8"))
        : { ok: false, scaffold: true, errors: [`${type} 脚手架必须补全并重新登记。`] };
      manifest.artifacts ??= [];
      const existing = [...manifest.artifacts].reverse().find((artifact) => artifact.type === type);
      const record = {
        type,
        path: relative,
        sha256: digest,
        source: "generated",
        status,
        validation,
        ...(["requirement", "design"].includes(type) ? { documentKind: manifest.ticketKind } : {}),
        recordedAt: nowIso(),
      };
      if (existing) Object.assign(existing, record);
      else manifest.artifacts.push(record);
      if (type === "requirement") manifest.state = "draft";
      if (type === "design") manifest.state = "specified";
      if (type === "closure") {
        for (const blocker of manifest.readiness?.blockers ?? []) {
          if (blocker.artifactType === "closure" && !blocker.resolvedAt) {
            blocker.resolution = "复盘收口总结已生成。";
            blocker.resolvedAt = nowIso();
          }
        }
      }
      if (type === "requirement" || type === "design") {
        manifest.workflowSelections ??= {};
        manifest.workflowSelections[type] = {
          action: "generate",
          status: "generated",
          artifactPath: relative,
          updatedAt: nowIso(),
        };
      }
    });
  } catch (error) {
    if (backup) writeFileSync(path, backup);
    else {
      try {
        unlinkSync(path);
      } catch {
        // The generated file may not have been created.
      }
    }
    throw error;
  }
}

/**
 * Register a delivery document artifact (requirement/design/plan/closure) into
 * the manifest. Validates the file exists, computes sha256, and advances the
 * state machine: requirement → specified, design → designed (mirrors Python's
 * _register_delivery_document). */
export function registerArtifact(
  root: string,
  requirementId: string,
  artifactType: string,
  pathValue: string
): RequirementManifest {
  const normalized = artifactType === "requirement-design" ? "design" : artifactType;
  if (!["requirement", "design", "plan", "closure"].includes(normalized)) {
    throw new RequirementError("不支持的产物类型。");
  }
  const current = loadRequirement(root, requirementId);
  const allowed: Record<string, RequirementState[]> = {
    requirement: ["draft", "specified"],
    design: ["specified", "designed", "documented"],
    plan: ["designed", "ready"],
    closure: ["reviewed", "finished"],
  };
  if (!allowed[normalized]!.includes(current.state)) {
    throw new RequirementError(`当前状态不能登记 ${normalized}；下游需求请先 reopen。`);
  }
  const selected = current.workflowSelections?.[normalized] as Record<string, unknown> | undefined;
  if (
    (normalized === "requirement" || normalized === "design")
    && selected
    && !["generate", "register"].includes(String(selected.action))
  ) {
    throw new RequirementError(`${normalized} 已选择 ${String(selected.action)}；如需登记文档，请先使用 requirement amend。`);
  }
  if (normalized === "design" && !hasCurrentArtifact(root, current, "requirement")) {
    throw new RequirementError("必须先登记当前有效的 requirement.md，才能登记设计文档。");
  }
  const source = readValidatedDocument(root, current, normalized, pathValue);
  if (
    selected?.action === "register"
    && selected.path
    && selected.path !== source.relativePath
  ) {
    throw new RequirementError(
      `${normalized} 已选择登记路径 ${String(selected.path)}；如需改用 ${source.relativePath}，请先使用 requirement amend。`
    );
  }
  const filename = {
    requirement: "requirement.md",
    design: "design.md",
    plan: "plan.md",
    closure: "closure-summary.md",
  }[normalized]!;
  const canonicalPath = join(requirementDir(root, requirementId), filename);
  const copyRequired = source.sourcePath !== canonicalPath;
  const canonicalExisted = existsSync(canonicalPath);
  const canonicalBackup = canonicalExisted ? readFileSync(canonicalPath) : null;
  if (copyRequired) writeText(canonicalPath, source.content);
  const canonicalContent = readFileSync(canonicalPath);
  const sha256 = createHash("sha256").update(canonicalContent).digest("hex");
  const canonicalRelative = relativePath(root, canonicalPath);
  try {
    return mutate(root, requirementId, (m) => {
      m.artifacts ??= [];
      const existing = m.artifacts.find((a) => a.type === normalized);
      if (existing) {
        existing.path = canonicalRelative;
        existing.status = "registered";
        existing.sha256 = sha256;
        existing.source = "registered";
        existing.sourcePath = source.relativePath;
        existing.validation = source.validation;
        existing.documentKind = m.ticketKind;
        existing.registeredAt = nowIso();
      } else {
        m.artifacts.push({
          type: normalized,
          path: canonicalRelative,
          sourcePath: source.relativePath,
          sha256,
          source: "registered",
          status: "registered",
          validation: source.validation,
          documentKind: m.ticketKind,
          registeredAt: nowIso(),
        });
      }
      if (normalized === "requirement" && m.state === "draft") {
        setState(m, "specified");
      }
      if (normalized === "design" && m.state === "specified") {
        setState(m, "designed");
      }
      m.workflowSelections ??= {};
      if (normalized === "requirement" || normalized === "design") {
        m.workflowSelections[normalized] = {
          action: "register",
          path: source.relativePath,
          status: "completed",
          artifactPath: canonicalRelative,
          updatedAt: nowIso(),
        };
      }
      for (const blocker of m.readiness?.blockers ?? []) {
        if (blocker.artifactType === normalized && !blocker.resolvedAt) {
          blocker.resolution = `${normalized} 已登记。`;
          blocker.resolvedAt = nowIso();
        }
      }
    });
  } catch (error) {
    if (copyRequired) {
      if (canonicalBackup) writeFileSync(canonicalPath, canonicalBackup);
      else {
        try {
          unlinkSync(canonicalPath);
        } catch {
          // The copy may already have been removed by a concurrent cleanup.
        }
      }
    }
    throw error;
  }
}

function artifactDigest(root: string, artifact: { path: string; sha256?: string }): boolean {
  const path = join(root, artifact.path);
  if (!artifact.sha256 || !existsSync(path)) return false;
  return createHash("sha256").update(readFileSync(path)).digest("hex") === artifact.sha256;
}

function hasCurrentArtifact(root: string, m: RequirementManifest, type: string): boolean {
  const aliases = type === "design" ? new Set(["design", "requirement-design"]) : new Set([type]);
  const artifact = [...(m.artifacts ?? [])].reverse().find((candidate) =>
    aliases.has(candidate.type)
    && !["draft", "stale", "failed"].includes(String(candidate.status ?? ""))
  );
  if (!artifact || !artifactDigest(root, artifact)) return false;
  if (
    m.schemaVersion === LEGACY_SCHEMA_VERSION
    && type === "design"
    && (!artifact.validation || typeof artifact.validation !== "object")
  ) {
    return true;
  }
  try {
    const path = join(root, artifact.path);
    validateDeliveryDocumentInRepository(root, m, type, readFileSync(path, "utf8"));
    return true;
  } catch {
    return false;
  }
}

function relativePath(root: string, path: string): string {
  const prefix = root.endsWith("/") ? root : `${root}/`;
  return path.replaceAll("\\", "/").startsWith(prefix.replaceAll("\\", "/"))
    ? path.replaceAll("\\", "/").slice(prefix.length)
    : path.replaceAll("\\", "/");
}

function assertReadinessInputs(root: string, m: RequirementManifest): void {
  if (!m.acceptanceCriteria?.length) {
    throw new RequirementError("ready 门禁：缺少验收标准。");
  }
  if (m.schemaVersion === SCHEMA_VERSION && !hasCurrentArtifact(root, m, "requirement")) {
    throw new RequirementError("缺少当前有效且验证通过的需求文档。");
  }
  if (!hasCurrentArtifact(root, m, "design")) {
    throw new RequirementError("缺少当前有效且验证通过的设计文档。");
  }
  const plan = (m.artifacts ?? []).find((artifact) => artifact.type === "plan");
  if (plan && (!artifactDigest(root, plan) || (plan.validation as Record<string, unknown> | undefined)?.ok !== true)) {
    throw new RequirementError("已选择生成实施计划，但 plan.md 尚未有效登记。");
  }
  if (m.ticketKind === "bug") {
    if (m.diagnosis?.status !== "confirmed" || !m.diagnosis.rootCause || !m.diagnosis.evidence?.length) {
      throw new RequirementError("Bug 必须先确认根因并登记 diagnosis。");
    }
  }
  const contract = m.testContract;
  if (!contract || contract.source !== "explicit" || contract.status !== "selected") {
    throw new RequirementError("缺少有效的实现前测试契约。");
  }
  if (!Array.isArray(contract.acceptanceIds) || contract.acceptanceIds.length === 0) {
    throw new RequirementError("测试契约必须显式映射验收标准。");
  }
  if (m.externalApiImpact?.value && !["service", "both"].includes(String(contract.kind ?? ""))) {
    throw new RequirementError("对外接口需求必须选择 service 或 both 测试契约。");
  }
  const unresolved = (m.readiness?.blockers ?? []).filter((blocker) => !blocker.resolvedAt);
  if (unresolved.length > 0) {
    throw new RequirementError(`仍有未解决的 readiness 阻塞项：${unresolved.map((item) => item.id).join(", ")}`);
  }
}

export function nowIso(): string {
  return new Date().toISOString();
}
