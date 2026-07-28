import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, existsSync, readFileSync, mkdirSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  createRequirement,
  loadRequirement,
  mutate,
  readyRequirement,
  recordLater,
  recordReview,
  finishRequirement,
  closeRequirement,
  generateArtifact,
  reopenRequirement,
  setAcceptanceCriteria,
  setTestContract,
  assertTransition,
  requirementDir,
  manifestPath,
  SCHEMA_VERSION,
  STATES,
} from "../requirements/state-machine.js";
import {
  artifactFilename,
  normalizeVersionDate,
  requirementDirectoryName,
} from "../requirements/artifacts.js";
import { RequirementError } from "../errors.js";
import {
  prepareDesignedRequirement,
  prepareReviewedRequirement,
  prepareVerifiedRequirement,
} from "./helpers.js";

function freshProject(): string {
  return mkdtempSync(join(tmpdir(), "pi-sm-"));
}

/** Drive a manifest to a target state by directly setting state + AC (bypassing
 *  the artifact-registration no-ops), to exercise the gate logic. */
function setState(root: string, id: string, state: string, extra: Record<string, unknown> = {}): void {
  mutate(root, id, (m) => {
    m.state = state as never;
    Object.assign(m, extra);
  });
}

describe("requirement state machine", () => {
  it("createRequirement writes a v2 manifest at draft", () => {
    const root = freshProject();
    const m = createRequirement(root, "REQ-1", "示例需求", { track: "complex" });
    assert.equal(m.schemaVersion, SCHEMA_VERSION);
    assert.equal(m.state, "draft");
    assert.equal(m.requirementId, "REQ-1");
    assert.ok(existsSync(manifestPath(root, "REQ-1")));
    assert.equal((m.workflowSelections?.requirement as Record<string, unknown>).action, "generate");
    assert.equal((m.workflowSelections?.design as Record<string, unknown>).action, "generate");
  });

  it("createRequirement rejects later for mandatory lifecycle documents", () => {
    const root = freshProject();
    assert.throws(
      () => createRequirement(root, "REQ-LATER", "延期需求", {
        requirementAction: "later",
        designAction: "generate",
      }),
      /必选|later/
    );
  });

  it("createRequirement is idempotent on matching identity", () => {
    const root = freshProject();
    createRequirement(root, "REQ-1", "示例需求");
    const again = createRequirement(root, "REQ-1", "示例需求");
    assert.equal(again.revision, 1);
  });

  it("createRequirement rejects name mismatch on existing id", () => {
    const root = freshProject();
    createRequirement(root, "REQ-1", "A");
    assert.throws(() => createRequirement(root, "REQ-1", "B"), RequirementError);
  });

  it("createRequirement canonicalizes numeric ids by ticket kind", () => {
    const root = freshProject();
    assert.equal(createRequirement(root, "1234", "普通需求").requirementId, "req1234");
    assert.equal(createRequirement(root, "5678", "缺陷", { ticketKind: "bug" }).requirementId, "bug5678");
  });

  it("createRequirement rejects conflicting duplicate intake fields", () => {
    const root = freshProject();
    createRequirement(root, "REQ-CONFLICT", "冲突检测", {
      track: "complex",
      externalApi: false,
      ticketKind: "requirement",
    });
    assert.throws(
      () => createRequirement(root, "REQ-CONFLICT", "冲突检测", {
        track: "quick",
        externalApi: false,
        ticketKind: "requirement",
      }),
      /关键信息不同/
    );
  });

  it("assertTransition enforces legal transitions", () => {
    assert.throws(() => assertTransition("draft", "finished"), RequirementError);
    assert.throws(() => assertTransition("ready", "finished"), RequirementError);
    // legal ones do not throw
    assertTransition("designed", "ready");
    assertTransition("reviewed", "finished");
  });

  it("ready gate: requires designed state + non-empty resolution + AC", () => {
    const root = freshProject();
    prepareDesignedRequirement(root, "REQ-2");
    assert.throws(() => readyRequirement(root, "REQ-2", ""), RequirementError); // empty resolution
    setState(root, "REQ-2", "specified"); // wrong state
    assert.throws(() => readyRequirement(root, "REQ-2", "ok"), RequirementError);
    setState(root, "REQ-2", "designed");
    const m = readyRequirement(root, "REQ-2", "范围已确认");
    assert.equal(m.state, "ready");
  });

  it("ready revalidates requirement.md against the latest manifest acceptance criteria", () => {
    const root = freshProject();
    prepareDesignedRequirement(root, "REQ-2B");
    const path = manifestPath(root, "REQ-2B");
    const payload = JSON.parse(readFileSync(path, "utf8"));
    payload.acceptanceCriteria.push({ id: "AC-02", description: "新增边界验收", status: "pending" });
    writeFileSync(path, JSON.stringify(payload, null, 2));
    assert.throws(() => readyRequirement(root, "REQ-2B", "尝试使用旧文档"), /需求文档/);
  });

  it("full lifecycle: ready -> begin -> test -> review -> finish -> close", () => {
    const root = freshProject();
    const prepared = prepareReviewedRequirement(root, "REQ-3");
    assert.equal(loadRequirement(root, "REQ-3").state, "reviewed");
    finishRequirement(root, "REQ-3", prepared.files);
    assert.equal(loadRequirement(root, "REQ-3").state, "finished");
    closeRequirement(root, "REQ-3", true);
    assert.equal(loadRequirement(root, "REQ-3").state, "closed");
    assert.equal(loadRequirement(root, "REQ-3").finishResult?.status, "passed");
    assert.equal(loadRequirement(root, "REQ-3").maintenanceResult?.status, "passed");
  });

  it("finish gate rejects without passing test evidence", () => {
    const root = freshProject();
    const prepared = prepareDesignedRequirement(root, "REQ-4");
    setState(root, "REQ-4", "reviewed");
    assert.throws(() => finishRequirement(root, "REQ-4", prepared.files), RequirementError);
  });

  it("finish gate rejects without a passed review round", () => {
    const root = freshProject();
    const prepared = prepareVerifiedRequirement(root, "REQ-4B");
    setState(root, "REQ-4B", "reviewed", {
      reviewRounds: [{ result: "failed", summary: "有问题", findings: [], recordedAt: new Date().toISOString(), valid: true }],
    });
    assert.throws(() => finishRequirement(root, "REQ-4B", prepared.files), RequirementError);
  });

  it("finish gate rejects when the mandatory test document was deleted", () => {
    const root = freshProject();
    const prepared = prepareReviewedRequirement(root, "REQ-TEST-DOC-MISSING");
    const manifest = loadRequirement(root, "REQ-TEST-DOC-MISSING");
    const artifact = manifest.artifacts.find((item) => item.type === "test")!;
    unlinkSync(join(root, artifact.path));
    assert.throws(
      () => finishRequirement(root, "REQ-TEST-DOC-MISSING", prepared.files),
      /测试文档/
    );
  });

  it("finish gate rejects when the mandatory test document was tampered", () => {
    const root = freshProject();
    const prepared = prepareReviewedRequirement(root, "REQ-TEST-DOC-TAMPERED");
    const manifest = loadRequirement(root, "REQ-TEST-DOC-TAMPERED");
    const artifact = manifest.artifacts.find((item) => item.type === "test")!;
    writeFileSync(join(root, artifact.path), "# 篡改后的测试文档\n");
    assert.throws(
      () => finishRequirement(root, "REQ-TEST-DOC-TAMPERED", prepared.files),
      /测试文档/
    );
  });

  it("close gate revalidates the mandatory test document", () => {
    const root = freshProject();
    const prepared = prepareReviewedRequirement(root, "REQ-TEST-DOC-CLOSE");
    finishRequirement(root, "REQ-TEST-DOC-CLOSE", prepared.files);
    const manifest = loadRequirement(root, "REQ-TEST-DOC-CLOSE");
    const artifact = manifest.artifacts.find((item) => item.type === "test")!;
    writeFileSync(join(root, artifact.path), "# finish 后篡改\n");
    assert.throws(
      () => closeRequirement(root, "REQ-TEST-DOC-CLOSE", true),
      /测试文档/
    );
  });

  it("review failed does not advance to reviewed", () => {
    const root = freshProject();
    const prepared = prepareVerifiedRequirement(root, "REQ-5");
    recordReview(root, "REQ-5", { result: "failed", summary: "仍有问题", files: prepared.files });
    assert.equal(loadRequirement(root, "REQ-5").state, "verified");
  });

  it("reopen closed -> draft (returns to document state, not implementing)", () => {
    const root = freshProject();
    createRequirement(root, "REQ-6", "重开需求");
    setState(root, "REQ-6", "closed");
    reopenRequirement(root, "REQ-6", "发现问题");
    // reopen returns to the strongest reusable document state (draft when no
    // requirement doc registered), forcing ready/begin to be re-run.
    assert.equal(loadRequirement(root, "REQ-6").state, "draft");
  });

  it("reopen only reuses documents that still match their recorded digest", () => {
    const root = freshProject();
    const prepared = prepareReviewedRequirement(root, "REQ-6B");
    finishRequirement(root, "REQ-6B", prepared.files);
    const manifest = loadRequirement(root, "REQ-6B");
    const requirementArtifact = manifest.artifacts.find((artifact) => artifact.type === "requirement")!;
    writeFileSync(join(root, requirementArtifact.path), "# tampered\n");
    reopenRequirement(root, "REQ-6B", "发现问题");
    assert.equal(loadRequirement(root, "REQ-6B").state, "draft");
  });

  it("setAcceptanceCriteria + setTestContract persist", () => {
    const root = freshProject();
    createRequirement(root, "REQ-7", "AC 需求");
    setAcceptanceCriteria(root, "REQ-7", [{ id: "AC-01", description: "a" }, { id: "AC-02", description: "b" }]);
    setTestContract(root, "REQ-7", { kind: "both", reportAction: "generate", acceptanceIds: ["AC-01", "AC-02"] });
    const m = loadRequirement(root, "REQ-7");
    assert.equal(m.acceptanceCriteria.length, 2);
    assert.equal((m.testContract as Record<string, unknown>).kind, "both");
  });

  it("test contracts cannot defer the mandatory test document", () => {
    const root = freshProject();
    createRequirement(root, "REQ-TEST-LATER", "测试文档延期");
    setAcceptanceCriteria(root, "REQ-TEST-LATER", [{ id: "AC-01", description: "核心行为通过" }]);
    assert.throws(
      () => setTestContract(root, "REQ-TEST-LATER", {
        kind: "unit",
        reportAction: "later",
        acceptanceIds: ["AC-01"],
      }),
      /必选|later/
    );
  });

  it("recordLater rejects every mandatory lifecycle document", () => {
    const root = freshProject();
    for (const [type, state] of [
      ["requirement", "draft"],
      ["design", "specified"],
      ["test", "implementing"],
      ["closure", "reviewed"],
    ]) {
      const id = `REQ-NO-LATER-${type}`;
      createRequirement(root, id, `禁止延期 ${type}`);
      mutate(root, id, (manifest) => {
        manifest.state = state as never;
      });
      assert.throws(() => recordLater(root, id, type), /必选|不能延期|不支持 defer/);
    }
  });

  it("manifest is written under an id-title directory with a cross-platform safe title", () => {
    const root = freshProject();
    createRequirement(root, "REQ-8", "布局 / 标题: Win\\dows?\u0001\u0085 .");
    const dir = requirementDir(root, "REQ-8");
    assert.ok(dir.endsWith(join(".project-intel", "requirements", "REQ-8-布局-标题-Win-dows")));
    assert.equal(existsSync(join(root, ".project-intel", "requirements", "REQ-8")), false);
    assert.ok(!dir.includes("by-id"));
    assert.ok(existsSync(join(dir, "manifest.json")));
    assert.equal(loadRequirement(root, "REQ-8").requirementName, "布局 / 标题: Win\\dows?\u0001\u0085 .");
  });

  it("normalizes user supplied version dates and writes dated requirement directories", () => {
    assert.equal(normalizeVersionDate("2026-07-23"), "2026-07-23");
    assert.equal(normalizeVersionDate("2026.7.23"), "2026-07-23");
    assert.equal(normalizeVersionDate("7.23版本", new Date(2026, 0, 1)), "2026-07-23");
    assert.equal(normalizeVersionDate("7月23日", new Date(2026, 0, 1)), "2026-07-23");
    assert.throws(() => normalizeVersionDate("2026-02-30"), /版本日期/);

    const root = freshProject();
    const manifest = createRequirement(root, "CRM-req76637", "迁改价值聚合ES合并与优惠折扣字段新增", {
      versionDate: "2026-07-23",
    });
    assert.equal(manifest.versionDate, "2026-07-23");
    assert.ok(requirementDir(root, "CRM-req76637").endsWith(join(
      ".project-intel",
      "requirements",
      "2026-07-23-CRM-req76637-迁改价值聚合ES合并与优惠折扣字段新增"
    )));
    assert.equal(
      artifactFilename("requirement", manifest),
      "CRM-req76637-迁改价值聚合ES合并与优惠折扣字段新增-需求文档.md"
    );

    const bug = createRequirement(root, "76638", "优惠字段缺失", {
      ticketKind: "bug",
      versionDate: "2026-07-24",
    });
    assert.equal(bug.requirementId, "bug76638");
    assert.ok(requirementDir(root, "bug76638").endsWith(join(
      ".project-intel",
      "requirements",
      "2026-07-24-bug76638-优惠字段缺失"
    )));
  });

  it("limits id-title directories by UTF-8 byte length", () => {
    const root = freshProject();
    createRequirement(root, "REQ-LONG", "标题".repeat(200));
    const directory = requirementDir(root, "REQ-LONG").split(/[\\/]/).pop()!;
    assert.ok(Buffer.byteLength(directory) <= 240);
    assert.ok(existsSync(join(requirementDir(root, "REQ-LONG"), "manifest.json")));
  });

  it("includes the date prefix in the UTF-8 directory byte limit", () => {
    const directory = requirementDirectoryName("REQ-LONG", "标题".repeat(200), "2026-07-23");
    assert.ok(directory.startsWith("2026-07-23-REQ-LONG-"));
    assert.ok(Buffer.byteLength(directory) <= 240);
  });

  it("numeric bug ids use the canonical id together with the title", () => {
    const root = freshProject();
    const manifest = createRequirement(root, "123", "登录失败", { ticketKind: "bug" });
    assert.equal(manifest.requirementId, "bug123");
    assert.ok(requirementDir(root, "bug123").endsWith(
      join(".project-intel", "requirements", "bug123-登录失败")
    ));
  });

  it("generated lifecycle docs use id-title document filenames", () => {
    const root = freshProject();
    createRequirement(root, "REQ-DOC", "文件命名", { ticketKind: "requirement" });
    generateArtifact(root, "REQ-DOC", "requirement");
    assert.equal(
      existsSync(join(requirementDir(root, "REQ-DOC"), "REQ-DOC-文件命名-需求文档.md")),
      true
    );
    assert.equal(existsSync(join(requirementDir(root, "REQ-DOC"), "requirement.md")), false);

    createRequirement(root, "BUG-DOC", "登录失败", { ticketKind: "bug" });
    generateArtifact(root, "BUG-DOC", "requirement");
    assert.equal(
      existsSync(join(requirementDir(root, "BUG-DOC"), artifactFilename("requirement", loadRequirement(root, "BUG-DOC")))),
      true
    );
    assert.equal(
      artifactFilename("requirement", loadRequirement(root, "BUG-DOC")),
      "BUG-DOC-登录失败-Bug文档.md"
    );
  });

  it("generated requirement, design, and test docs follow the sample document standards", () => {
    const root = freshProject();
    createRequirement(root, "REQ-STD", "文档标准", { ticketKind: "requirement" });
    setAcceptanceCriteria(root, "REQ-STD", [{ id: "AC-01", description: "生成样例标准文档" }]);

    generateArtifact(root, "REQ-STD", "requirement");
    const requirement = readFileSync(join(requirementDir(root, "REQ-STD"), artifactFilename("requirement", loadRequirement(root, "REQ-STD"))), "utf8");
    assert.match(requirement, /^# 业务需求文档: 文档标准/m);
    for (const heading of ["背景与目标", "需求范围", "用户角色与使用场景", "业务流程", "功能需求", "业务规则", "数据口径与状态说明", "需拍板业务决策", "权限与可见性", "异常与边界场景", "验收标准", "待确认项"]) {
      assert.ok(requirement.includes(heading), `missing requirement heading: ${heading}`);
    }

    setState(root, "REQ-STD", "specified");
    generateArtifact(root, "REQ-STD", "design");
    const design = readFileSync(join(requirementDir(root, "REQ-STD"), artifactFilename("design", loadRequirement(root, "REQ-STD"))), "utf8");
    for (const heading of ["目录", "概述 / Overview", "架构设计 / Architecture", "核心模块 / Core Modules", "技术决策 / Key Decisions", "已知限制 / Known Limits", "扩展方向 / Extension Points", "相关资源 / References"]) {
      assert.ok(design.includes(`## ${heading}`), `missing design heading: ${heading}`);
    }

    setState(root, "REQ-STD", "implementing");
    generateArtifact(root, "REQ-STD", "test");
    const testDoc = readFileSync(join(requirementDir(root, "REQ-STD"), artifactFilename("test", loadRequirement(root, "REQ-STD"))), "utf8");
    assert.match(testDoc, /^# 测试文档：文档标准/m);
    for (const heading of ["测试环境与前置准备", "核心规则与用例总览", "功能用例", "边界与异常用例", "自动化与回归建议", "测试清单", "涉及代码索引"]) {
      assert.ok(testDoc.includes(heading), `missing test heading: ${heading}`);
    }
  });

  it("loadRequirement rejects ambiguous id-title directories", () => {
    const root = freshProject();
    const requirementsRoot = join(root, ".project-intel", "requirements");
    for (const directory of ["REQ-DUP-标题一", "2026-07-23-REQ-DUP-标题二"]) {
      const target = join(requirementsRoot, directory);
      mkdirSync(target, { recursive: true });
      writeFileSync(join(target, "manifest.json"), JSON.stringify({
        schemaVersion: 2,
        requirementId: "REQ-DUP",
        requirementName: directory,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }));
    }
    assert.throws(() => loadRequirement(root, "REQ-DUP"), /存在多个需求档案/);
  });

  it("createRequirement does not overwrite an unrecognized id-title manifest", () => {
    const root = freshProject();
    const target = join(root, ".project-intel", "requirements", "REQ-CORRUPT-损坏档案");
    mkdirSync(target, { recursive: true });
    writeFileSync(join(target, "manifest.json"), "{not-json");
    assert.throws(
      () => createRequirement(root, "REQ-CORRUPT", "损坏档案"),
      /档案身份无法识别/
    );
    assert.equal(readFileSync(join(target, "manifest.json"), "utf8"), "{not-json");
  });

  it("STATES includes the full v2 lifecycle", () => {
    for (const s of ["draft", "specified", "designed", "ready", "implementing", "verified", "reviewed", "finished", "closed"]) {
      assert.ok((STATES as readonly string[]).includes(s));
    }
  });

  it("loadRequirement raises on missing archive", () => {
    const root = freshProject();
    assert.throws(() => loadRequirement(root, "NOPE"), RequirementError);
  });

  it("revision increments on each mutate", () => {
    const root = freshProject();
    createRequirement(root, "REQ-9", "修订需求");
    setAcceptanceCriteria(root, "REQ-9", [{ id: "AC-01", description: "x" }]);
    setAcceptanceCriteria(root, "REQ-9", [{ id: "AC-01", description: "y" }]);
    const raw = JSON.parse(readFileSync(manifestPath(root, "REQ-9"), "utf8"));
    assert.ok(raw.revision >= 3, `revision ${raw.revision} should be >= 3`);
  });

  it("mutate keeps a legacy v1 manifest in the legacy by-id directory", () => {
    const root = freshProject();
    const legacy = join(root, ".project-intel", "requirements", "by-id", "REQ-V1", "manifest.json");
    mkdirSync(join(legacy, ".."), { recursive: true });
    writeFileSync(legacy, JSON.stringify({
      schemaVersion: 1,
      revision: 1,
      requirementId: "REQ-V1",
      requirementName: "旧版需求",
      state: "draft",
      externalApiImpact: { confirmed: true, value: false },
      acceptanceCriteria: [],
      artifacts: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }));
    mutate(root, "REQ-V1", (manifest) => {
      manifest.requirementName = "旧版需求已更新";
    });
    assert.equal(JSON.parse(readFileSync(legacy, "utf8")).requirementName, "旧版需求已更新");
    assert.equal(existsSync(manifestPath(root, "REQ-V1")), false);
  });
});
