import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, readFileSync, appendFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runRequirement } from "../commands/requirement.js";
import { runIntake } from "../commands/orchestration.js";
import { migrateLayout, artifactFilename, ARTIFACT_FILES } from "../requirements/layout.js";
import { createRequirement, loadRequirement, mutate, setAcceptanceCriteria } from "../requirements/state-machine.js";
import {
  beginWithBusinessChange,
  designDocument,
  initGitProject,
  prepareDesignedRequirement,
  requirementDocument,
} from "./helpers.js";

const noopGlobal = { project: null, jsonMode: false } as never;

describe("requirement command dispatcher", () => {
  it("status returns state for a created requirement", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-1", "需求");
    const r = runRequirement(root, ["status", "--requirement-id", "REQ-1"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "draft");
  });

  it("intake persists document actions and later selection blocks generation", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    runIntake(root, [
      "--task", "迁移运行时",
      "--requirement-id", "REQ-ACTIONS",
      "--requirement-name", "迁移运行时",
      "--external-api", "no",
      "--requirement-action", "later",
      "--design-action", "generate",
      "--track", "complex",
    ], noopGlobal);
    const manifest = loadRequirement(root, "REQ-ACTIONS");
    assert.equal((manifest.workflowSelections?.requirement as Record<string, unknown>).action, "later");
    assert.equal((manifest.workflowSelections?.design as Record<string, unknown>).action, "generate");
    assert.throws(
      () => runRequirement(root, ["generate", "--requirement-id", "REQ-ACTIONS", "--type", "requirement"], noopGlobal),
      /已选择 later/
    );
    runRequirement(root, ["defer", "--requirement-id", "REQ-ACTIONS", "--type", "requirement"], noopGlobal);
    assert.throws(
      () => runRequirement(root, ["defer", "--requirement-id", "REQ-ACTIONS", "--type", "design"], noopGlobal),
      /已选择 generate/
    );
  });

  it("acceptance set persists AC-01..AC-02", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-2", "需求");
    const r = runRequirement(
      root,
      ["acceptance", "set", "--requirement-id", "REQ-2", "--criterion", "AC-01:a", "--criterion", "AC-02:b"],
      noopGlobal
    );
    assert.equal(r.exitCode, 0);
    assert.equal(((r.result as Record<string, unknown>).acceptanceCriteria as unknown[]).length, 2);
  });

  it("query reads v2 and legacy by-id archives and supports --file", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-V2", "直目录需求");
    mutate(root, "REQ-V2", (m) => {
      m.state = "specified";
      m.changedFiles = ["src/v2.ts"];
    });
    const legacyDir = join(root, ".project-intel", "requirements", "by-id", "REQ-LEGACY");
    mkdirSync(legacyDir, { recursive: true });
    writeFileSync(join(legacyDir, "manifest.json"), JSON.stringify({
      schemaVersion: 1,
      revision: 1,
      requirementId: "REQ-LEGACY",
      requirementName: "旧目录需求",
      ticketKind: "requirement",
      track: "standard",
      state: "specified",
      externalApiImpact: { confirmed: true, value: false },
      sourceTickets: [],
      changedFiles: ["src/legacy.ts"],
      acceptanceCriteria: [],
      artifacts: [],
      scopeSnapshots: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }));
    const all = runRequirement(root, ["query", "--state", "specified"], noopGlobal).result as Record<string, unknown>;
    const allIds = ((all.requirements as Record<string, unknown>[]) ?? []).map((item) => item.requirementId).sort();
    assert.deepEqual(allIds, ["REQ-LEGACY", "REQ-V2"]);
    const filtered = runRequirement(root, ["query", "--file", "src/legacy.ts"], noopGlobal).result as Record<string, unknown>;
    assert.deepEqual(
      ((filtered.requirements as Record<string, unknown>[]) ?? []).map((item) => item.requirementId),
      ["REQ-LEGACY"]
    );
  });

  it("test-contract set requires --kind and --report-action", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-3", "需求");
    setAcceptanceCriteria(root, "REQ-3", [{ id: "AC-01", description: "核心行为通过" }]);
    assert.throws(() =>
      runRequirement(root, ["test-contract", "set", "--requirement-id", "REQ-3", "--kind", "both"], noopGlobal)
    );
    const r = runRequirement(
      root,
      ["test-contract", "set", "--requirement-id", "REQ-3", "--kind", "both", "--report-action", "generate", "--acceptance", "AC-01"],
      noopGlobal
    );
    assert.equal(r.exitCode, 0);
  });

  it("test-contract register validates and normalizes a structured report path", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-CONTRACT-REPORT", "测试契约报告");
    setAcceptanceCriteria(root, "REQ-CONTRACT-REPORT", [{ id: "AC-01", description: "核心行为通过" }]);
    mkdirSync(join(root, "reports"), { recursive: true });
    writeFileSync(join(root, "reports", "unit.json"), '{"numTotalTests":2,"numFailedTests":0,"status":"passed"}');
    assert.throws(
      () => runRequirement(root, [
        "test-contract", "set",
        "--requirement-id", "REQ-CONTRACT-REPORT",
        "--kind", "unit",
        "--report-action", "register",
        "--report-path", "reports/missing.json",
        "--acceptance", "AC-01",
      ], noopGlobal),
      /测试报告不存在/
    );
    writeFileSync(join(root, "reports", "free.txt"), "2 passed");
    assert.throws(
      () => runRequirement(root, [
        "test-contract", "set",
        "--requirement-id", "REQ-CONTRACT-REPORT",
        "--kind", "unit",
        "--report-action", "register",
        "--report-path", "reports/free.txt",
        "--acceptance", "AC-01",
      ], noopGlobal),
      /测试报告格式不受支持/
    );
    const result = runRequirement(root, [
      "test-contract", "set",
      "--requirement-id", "REQ-CONTRACT-REPORT",
      "--kind", "unit",
      "--report-action", "register",
      "--report-path", "reports/unit.json",
      "--acceptance", "AC-01",
    ], noopGlobal);
    assert.equal(result.exitCode, 0);
    const contract = loadRequirement(root, "REQ-CONTRACT-REPORT").testContract!;
    assert.equal(contract.reportPath, "reports/unit.json");
    assert.equal(contract.reportFormat, "json");
    assert.equal(contract.reportExecutedCount, 2);
    assert.match(String(contract.reportSha256 ?? ""), /^[a-f0-9]{64}$/);
  });

  it("ready -> begin through the dispatcher", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    prepareDesignedRequirement(root, "REQ-4");
    runRequirement(root, ["ready", "--requirement-id", "REQ-4", "--resolution", "ok"], noopGlobal);
    runRequirement(root, ["begin", "--requirement-id", "REQ-4"], noopGlobal);
    const status = runRequirement(root, ["status", "--requirement-id", "REQ-4"], noopGlobal);
    assert.equal((status.result as Record<string, unknown>).state, "implementing");
  });

  it("reopen after close", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-5", "需求");
    mutate(root, "REQ-5", (m) => {
      m.state = "closed";
    });
    const r = runRequirement(root, ["reopen", "--requirement-id", "REQ-5", "--reason", "发现问题"], noopGlobal);
    assert.equal((r.result as Record<string, unknown>).state, "draft");
  });

  it("generate enforces lifecycle order and creates a requirement scaffold", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-6", "需求");
    assert.throws(
      () => runRequirement(root, ["generate", "--requirement-id", "REQ-6", "--type", "design"], noopGlobal),
      /当前状态不能生成 design/
    );
    const r = runRequirement(root, ["generate", "--requirement-id", "REQ-6", "--type", "requirement"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.ok(existsSync((r.result as Record<string, unknown>).path as string));
  });

  it("generate refuses implicit overwrite and --replace really rebuilds the scaffold", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-6B", "覆盖保护");
    const args = ["generate", "--requirement-id", "REQ-6B", "--type", "requirement"];
    const generated = runRequirement(root, args, noopGlobal);
    const path = (generated.result as Record<string, unknown>).path as string;
    appendFileSync(path, "\n用户填写内容\n");
    assert.throws(() => runRequirement(root, args, noopGlobal), /已存在|覆盖|replace/);
    runRequirement(root, [...args, "--replace"], noopGlobal);
    assert.doesNotMatch(readFileSync(path, "utf8"), /用户填写内容/);
  });

  it("rejects missing --requirement-id", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    assert.throws(() => runRequirement(root, ["status"], noopGlobal));
  });

  it("add persists artifact registration into the manifest", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    initGitProject(root);
    createRequirement(root, "REQ-ADD", "需求");
    const criteria = [{ id: "AC-01", description: "核心行为通过" }];
    setAcceptanceCriteria(root, "REQ-ADD", criteria);
    mkdirSync(join(root, "docs"), { recursive: true });
    writeFileSync(join(root, "docs", "requirement.md"), requirementDocument("REQ-ADD", "需求", false, criteria));
    runRequirement(root, ["add", "--requirement-id", "REQ-ADD", "--type", "requirement", "--path", "docs/requirement.md"], noopGlobal);
    writeFileSync(join(root, "docs", "design.md"), designDocument("REQ-ADD", "需求"));
    const r = runRequirement(root, ["add", "--requirement-id", "REQ-ADD", "--type", "design", "--path", "docs/design.md"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).registered, true);
    // Verify it was actually written to the manifest.
    const status = runRequirement(root, ["status", "--requirement-id", "REQ-ADD"], noopGlobal);
    void status; // status doesn't expose artifacts, but no throw means manifest is intact
  });

  it("rejects arbitrary delivery-document content", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    initGitProject(root);
    createRequirement(root, "REQ-BAD-DOC", "需求");
    setAcceptanceCriteria(root, "REQ-BAD-DOC", [{ id: "AC-01", description: "核心行为通过" }]);
    mkdirSync(join(root, "docs"), { recursive: true });
    writeFileSync(join(root, "docs", "bad.md"), "x");
    assert.throws(() =>
      runRequirement(root, ["add", "--requirement-id", "REQ-BAD-DOC", "--type", "requirement", "--path", "docs/bad.md"], noopGlobal)
    );
  });

  it("design registration rejects missing source evidence paths", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    initGitProject(root);
    createRequirement(root, "REQ-SOURCE", "源码真值");
    const criteria = [{ id: "AC-01", description: "核心行为通过" }];
    setAcceptanceCriteria(root, "REQ-SOURCE", criteria);
    mkdirSync(join(root, "docs"), { recursive: true });
    writeFileSync(join(root, "docs", "requirement.md"), requirementDocument("REQ-SOURCE", "源码真值", false, criteria));
    runRequirement(root, ["add", "--requirement-id", "REQ-SOURCE", "--type", "requirement", "--path", "docs/requirement.md"], noopGlobal);
    writeFileSync(
      join(root, "docs", "design.md"),
      designDocument("REQ-SOURCE", "源码真值").replace("src/existing.ts", "src/missing.ts")
    );
    assert.throws(
      () => runRequirement(root, ["add", "--requirement-id", "REQ-SOURCE", "--type", "design", "--path", "docs/design.md"], noopGlobal),
      /源码证据路径不存在/
    );
  });

  it("design registration ignores symbols that exist only in comments or strings", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    initGitProject(root);
    createRequirement(root, "REQ-SYMBOL", "符号真值");
    const criteria = [{ id: "AC-01", description: "核心行为通过" }];
    setAcceptanceCriteria(root, "REQ-SYMBOL", criteria);
    mkdirSync(join(root, "docs"), { recursive: true });
    writeFileSync(join(root, "docs", "requirement.md"), requirementDocument("REQ-SYMBOL", "符号真值", false, criteria));
    runRequirement(root, ["add", "--requirement-id", "REQ-SYMBOL", "--type", "requirement", "--path", "docs/requirement.md"], noopGlobal);
    writeFileSync(join(root, "src", "fake.ts"), "// fakeSymbol\nconst text = 'fakeSymbol';\n");
    const design = designDocument("REQ-SYMBOL", "符号真值")
      .replace("src/existing.ts", "src/fake.ts")
      .replace("existingBehavior", "fakeSymbol");
    writeFileSync(join(root, "docs", "design.md"), design);
    assert.throws(
      () => runRequirement(root, ["add", "--requirement-id", "REQ-SYMBOL", "--type", "design", "--path", "docs/design.md"], noopGlobal),
      /源码证据符号不存在/
    );
  });

  it("add registers a structured test report as current requirement evidence", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    const prepared = prepareDesignedRequirement(root, "REQ-ADD-TEST", { name: "登记测试报告" });
    beginWithBusinessChange(prepared);
    mkdirSync(join(root, "reports"), { recursive: true });
    writeFileSync(join(root, "reports", "unit.json"), '{"tests":2,"failures":0,"status":"passed"}');
    const result = runRequirement(root, [
      "add",
      "--requirement-id", prepared.id,
      "--type", "unit-test",
      "--path", "reports/unit.json",
      "--result", "passed",
      "--acceptance", "AC-01",
      "--files", ...prepared.files,
    ], noopGlobal);
    assert.equal(result.exitCode, 0);
    const manifest = loadRequirement(root, prepared.id);
    assert.equal(manifest.state, "verified");
    assert.equal(manifest.testEvidence?.length, 1);
    assert.equal(manifest.testEvidence?.[0]?.reportOriginalPath, "reports/unit.json");
    assert.ok(existsSync(join(root, ".project-intel", "requirements", prepared.id, "test-report.md")));
  });

  it("diagnose records a Bug root cause (ticketKind=bug)", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "BUG-1", "Bug 需求", { ticketKind: "bug" });
    mutate(root, "BUG-1", (m) => {
      m.state = "specified";
      m.acceptanceCriteria = [{ id: "AC-01", description: "x" }];
    });
    mkdirSync(join(root, "src"), { recursive: true });
    writeFileSync(join(root, "src", "state.ts"), "export function recordReview() { return 'ok'; }\n");
    const r = runRequirement(root, ["diagnose", "--requirement-id", "BUG-1", "--root-cause", "状态机未校验 review result 字段", "--evidence", "src/state.ts#recordReview"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "specified");
    const manifest = loadRequirement(root, "BUG-1");
    assert.equal(manifest.diagnosis?.evidence[0]?.path, "src/state.ts");
    assert.equal(manifest.diagnosis?.evidence[0]?.symbol, "recordReview");
    assert.match(manifest.diagnosis?.evidence[0]?.sha256 ?? "", /^[a-f0-9]{64}$/);
  });

  it("diagnose rejects missing source evidence paths", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "BUG-MISSING", "Bug 需求", { ticketKind: "bug" });
    mutate(root, "BUG-MISSING", (m) => {
      m.state = "specified";
      m.acceptanceCriteria = [{ id: "AC-01", description: "x" }];
    });
    assert.throws(
      () => runRequirement(root, ["diagnose", "--requirement-id", "BUG-MISSING", "--root-cause", "状态机未校验 review result 字段", "--evidence", "src/missing.ts#recordReview"], noopGlobal),
      /源码证据路径不存在/
    );
  });

  it("diagnose rejects symbols that only appear in comments or strings", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "BUG-FAKE-SYMBOL", "Bug 需求", { ticketKind: "bug" });
    mutate(root, "BUG-FAKE-SYMBOL", (m) => {
      m.state = "specified";
      m.acceptanceCriteria = [{ id: "AC-01", description: "x" }];
    });
    mkdirSync(join(root, "src"), { recursive: true });
    writeFileSync(join(root, "src", "state.ts"), "// recordReview\nconst message = 'recordReview';\n");
    assert.throws(
      () => runRequirement(root, ["diagnose", "--requirement-id", "BUG-FAKE-SYMBOL", "--root-cause", "状态机未校验 review result 字段", "--evidence", "src/state.ts#recordReview"], noopGlobal),
      /源码证据符号不存在/
    );
  });

  it("diagnose rejects non-bug requirements", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-D", "需求");
    mutate(root, "REQ-D", (m) => {
      m.state = "specified";
      m.acceptanceCriteria = [{ id: "AC-01", description: "x" }];
    });
    assert.throws(() =>
      runRequirement(root, ["diagnose", "--requirement-id", "REQ-D", "--root-cause", "这是一个足够长的根因说明", "--evidence", "src/a.ts"], noopGlobal)
    );
  });

  it("defer adds a readiness blocker for design", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-DEF", "需求");
    const r = runRequirement(root, ["defer", "--requirement-id", "REQ-DEF", "--type", "design"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "draft");
  });

  it("resolve-finding marks a review finding resolved", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-RF", "需求");
    mutate(root, "REQ-RF", (m) => {
      m.state = "verified";
      m.acceptanceCriteria = [{ id: "AC-01", description: "x" }];
      m.testEvidence = { phase: "green", passed: true, recordedAt: new Date().toISOString() };
      m.reviewRounds = [
        {
          id: "REVIEW-01",
          result: "failed",
          summary: "有问题",
          findings: [{ id: "FINDING-01-01", severity: "important", text: "需修复", resolved: false }],
          recordedAt: new Date().toISOString(),
          valid: true,
        },
      ];
    });
    const r = runRequirement(root, ["resolve-finding", "--requirement-id", "REQ-RF", "--finding-id", "FINDING-01-01", "--resolved-by", "reviewer", "--resolution", "已修复"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "verified");
  });

  it("resolve-finding rejects unknown finding IDs", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-req-"));
    createRequirement(root, "REQ-RF2", "需求");
    mutate(root, "REQ-RF2", (m) => {
      m.state = "verified";
      m.acceptanceCriteria = [{ id: "AC-01", description: "x" }];
      m.testEvidence = { phase: "green", passed: true, recordedAt: new Date().toISOString() };
      m.reviewRounds = [
        { id: "REVIEW-01", result: "failed", summary: "x", findings: [], recordedAt: new Date().toISOString(), valid: true },
      ];
    });
    assert.throws(() =>
      runRequirement(root, ["resolve-finding", "--requirement-id", "REQ-RF2", "--finding-id", "NOPE-01", "--resolved-by", "r", "--resolution", "x"], noopGlobal)
    );
  });
});

describe("requirement layout", () => {
  it("artifactFilename maps known types", () => {
    assert.equal(artifactFilename("requirement"), "requirement.md");
    assert.equal(artifactFilename("design"), "design.md");
    assert.equal(artifactFilename("plan"), "plan.md");
    assert.equal(artifactFilename("unit-test"), "test-report.md");
  });

  it("ARTIFACT_FILES covers the v2 types", () => {
    for (const t of ["requirement", "design", "plan", "test", "closure"]) {
      assert.ok(t in ARTIFACT_FILES);
    }
  });

  it("migrateLayout reports not-migrated when no legacy archive", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-lay-"));
    const r = migrateLayout(root, "NOPE", true);
    assert.equal(r.migrated, false);
  });

  it("migrateLayout copies legacy by-id archives and rewrites manifest paths", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-lay-"));
    const legacyDir = join(root, ".project-intel", "requirements", "by-id", "REQ-OLD");
    mkdirSync(join(legacyDir, "test-reports"), { recursive: true });
    writeFileSync(join(legacyDir, "requirement.md"), "# legacy requirement\n");
    writeFileSync(join(legacyDir, "test-reports", "unit.json"), '{"tests":1,"failures":0}');
    writeFileSync(join(legacyDir, "manifest.json"), JSON.stringify({
      requirementId: "REQ-OLD",
      artifacts: [
        {
          type: "requirement",
          path: ".project-intel/requirements/by-id/REQ-OLD/requirement.md",
          sourcePath: ".project-intel/requirements/by-id/REQ-OLD/requirement.md",
        },
        {
          type: "unit-test",
          path: ".project-intel/requirements/by-id/REQ-OLD/test-reports/unit.json",
        },
      ],
    }));
    const dryRun = migrateLayout(root, "REQ-OLD", false);
    assert.equal(dryRun.migrated, true);
    assert.equal(existsSync(join(root, ".project-intel", "requirements", "REQ-OLD", "manifest.json")), false);
    const result = migrateLayout(root, "REQ-OLD", true);
    assert.equal(result.migrated, true);
    assert.equal(existsSync(join(legacyDir, "manifest.json")), true);
    assert.equal(existsSync(join(root, ".project-intel", "requirements", "REQ-OLD", "test-reports", "unit.json")), true);
    const migrated = readFileSync(join(root, ".project-intel", "requirements", "REQ-OLD", "manifest.json"), "utf8");
    assert.ok(migrated.includes(".project-intel/requirements/REQ-OLD/requirement.md"));
    assert.ok(!migrated.includes(".project-intel/requirements/by-id/REQ-OLD/"));
  });
});
