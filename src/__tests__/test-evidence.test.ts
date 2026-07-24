import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { sanitizeText, manualEvidenceValid, COMMAND_ERROR_CODES } from "../testing/sanitize.js";
import {
  executedTestCount,
  inspectTestReport,
  phasePassed,
  renderTestEvidence,
  evaluateTestEvidence,
} from "../testing/render.js";
import { runTest } from "../commands/test.js";
import { loadRequirement } from "../requirements/state-machine.js";
import { beginWithBusinessChange, prepareDesignedRequirement } from "./helpers.js";

const noopGlobal = { project: null, jsonMode: false } as never;

describe("sanitizeText", () => {
  it("redacts header values (Authorization/Cookie)", () => {
    assert.equal(sanitizeText("Authorization: Bearer abc.def"), "Authorization: [REDACTED]");
    assert.equal(sanitizeText("Cookie: session=xyz"), "Cookie: [REDACTED]");
  });
  it("redacts key=value secrets", () => {
    assert.ok(sanitizeText("password=hunter2").includes("password=[REDACTED]") || sanitizeText("password=hunter2").includes("[REDACTED]"));
    assert.ok(sanitizeText("api_key: secret123").includes("[REDACTED]"));
  });
  it("redacts raw token formats", () => {
    assert.ok(!sanitizeText("ghp_" + "a".repeat(36)).includes("ghp_"));
    assert.ok(!sanitizeText("sk-" + "a".repeat(24)).includes("sk-"));
    assert.ok(!sanitizeText("xoxb-" + "a".repeat(12)).includes("xoxb-"));
    assert.ok(!sanitizeText("AIza" + "a".repeat(22)).includes("AIza"));
  });
  it("redacts database URLs and URL userinfo", () => {
    const out = sanitizeText("postgres://user:pass@host:5432/db");
    assert.ok(out.includes("[REDACTED]"));
    assert.ok(!out.includes("pass@"));
  });
  it("redacts PRC identity and mainland mobile", () => {
    const id = "11010119900307393X";
    assert.ok(!sanitizeText(`身份证 ${id}`).includes(id));
    const phone = "13812345678";
    assert.ok(!sanitizeText(`电话 ${phone}`).includes(phone));
  });
  it("preserves benign Chinese text", () => {
    assert.equal(sanitizeText("需求 LOCAL-1 测试通过"), "需求 LOCAL-1 测试通过");
  });
});

describe("manualEvidenceValid", () => {
  it("rejects generic phrases", () => {
    assert.equal(manualEvidenceValid("验证通过"), false);
    assert.equal(manualEvidenceValid("tested manually"), false);
  });
  it("accepts specific descriptions", () => {
    assert.equal(manualEvidenceValid("在 Chrome 120 上手动验证登录流程可正确跳转"), true);
  });});

describe("executedTestCount", () => {
  it("extracts unittest 'Ran N tests'", () => {
    assert.equal(executedTestCount({ stdout: "Ran 5 tests in 0.1s" }), 5);
  });
  it("extracts 'N passed'", () => {
    assert.equal(executedTestCount({ stdout: "3 passed" }), 3);
  });
  it("returns 0 for empty formatter output (AC-11)", () => {
    assert.equal(executedTestCount({ stdout: "all files formatted" }), 0);
  });
  it("extracts the Node test runner summary", () => {
    assert.equal(executedTestCount({ stdout: "ℹ tests 213\nℹ pass 213\nℹ fail 0" }), 213);
  });
});

describe("inspectTestReport", () => {
  it("accepts structured JSON and rejects free-form pass text", () => {
    assert.deepEqual(inspectTestReport('{"numTotalTests":3,"numFailedTests":0}'), {
      format: "json",
      executedCount: 3,
      failedCount: 0,
      passed: true,
    });
    assert.equal(inspectTestReport("3 passed"), null);
  });

  it("parses JUnit, TAP and unittest failures", () => {
    assert.equal(inspectTestReport('<testsuite tests="2" failures="0" errors="0"></testsuite>')?.passed, true);
    assert.equal(inspectTestReport("TAP version 13\nnot ok 1 - broken\n1..1\n# fail 1")?.passed, false);
    assert.equal(inspectTestReport("Ran 2 tests in 0.1s\n\nFAILED (failures=1)")?.passed, false);
  });
});

describe("phasePassed", () => {
  it("green requires exit 0 AND a real test count", () => {
    assert.equal(phasePassed("green", [{ exitCode: 0, stdout: "Ran 1 test" }]), true);
    assert.equal(phasePassed("green", [{ exitCode: 0, stdout: "formatted" }]), false); // no test count
    assert.equal(phasePassed("green", [{ exitCode: 1, stdout: "Ran 1 test" }]), false); // non-zero
  });
  it("red requires non-zero exit + expected-failure match", () => {
    assert.equal(phasePassed("red", [{ exitCode: 1, stdout: "AssertionError boom" }], "", "AssertionError"), true);
    assert.equal(phasePassed("red", [{ exitCode: 1, stdout: "other" }], "", "AssertionError"), false);
  });
  it("manual uses manualEvidenceValid", () => {
    assert.equal(phasePassed("manual", [], "在真机环境验证推送到达并点击跳转正确"), true);
    assert.equal(phasePassed("manual", [], "验证通过"), false);
  });
});

describe("test command (AC-11: rejects forged pass)", () => {
  it("records green evidence when a real test passes", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-tc-"));
    const r = runTest(root, ["--task", "demo", "--phase", "green", "--command", "echo 'Ran 1 test'"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.ok(existsSync(join(root, ".project-intel", "reports", "test-evidence.json")));
  });
  it("rejects a formatter pass as evidence (no test count)", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-tc-"));
    const r = runTest(root, ["--task", "demo", "--phase", "green", "--command", "echo 'all formatted'"], noopGlobal);
    assert.equal(r.exitCode, 1); // forged pass rejected
  });
  it("advances requirement state via recordTestResult", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-tc-"));
    const prepared = prepareDesignedRequirement(root, "REQ-T", { name: "测试需求" });
    beginWithBusinessChange(prepared);
    runTest(root, [
      "--requirement-id", "REQ-T",
      "--test-kind", "unit",
      "--report-action", "generate",
      "--phase", "green",
      "--acceptance", "AC-01",
      "--files", ...prepared.files,
      "--command", "echo 'Ran 2 tests'",
    ], noopGlobal);
    assert.equal(loadRequirement(root, "REQ-T").state, "verified");
  });

  it("registers a structured report without re-running a command", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-tc-"));
    const reportPath = ".project-intel/requirements/REQ-R/unit.json";
    mkdirSync(join(root, ".project-intel", "requirements", "REQ-R"), { recursive: true });
    writeFileSync(join(root, reportPath), '{"numTotalTests":2,"numFailedTests":0}');
    const prepared = prepareDesignedRequirement(root, "REQ-R", {
      name: "登记报告需求",
      reportAction: "register",
      reportPath,
    });
    beginWithBusinessChange(prepared);
    const result = runTest(root, [
      "--requirement-id", "REQ-R",
      "--test-kind", "unit",
      "--report-action", "register",
      "--report-path", reportPath,
      "--phase", "verify",
      "--acceptance", "AC-01",
      "--files", ...prepared.files,
    ], noopGlobal);
    assert.equal(result.exitCode, 0);
    const manifest = loadRequirement(root, "REQ-R");
    assert.equal(manifest.state, "verified");
    const evidence = manifest.testEvidence?.[0] as Record<string, unknown>;
    assert.equal(evidence.reportOriginalPath, reportPath);
    assert.match(String(evidence.reportPath ?? ""), /\.project-intel\/requirements\/REQ-R\/test-reports\/TEST-01-unit\.md$/);
    assert.ok(existsSync(join(root, String(evidence.reportPath))));
  });

  it("rejects a free-form registered pass report", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-tc-"));
    const reportPath = ".project-intel/requirements/REQ-R2/unit.txt";
    mkdirSync(join(root, ".project-intel", "requirements", "REQ-R2"), { recursive: true });
    writeFileSync(join(root, reportPath), '{"numTotalTests":2,"numFailedTests":0}');
    const prepared = prepareDesignedRequirement(root, "REQ-R2", {
      name: "拒绝伪造报告需求",
      reportAction: "register",
      reportPath,
    });
    beginWithBusinessChange(prepared);
    writeFileSync(join(root, reportPath), "2 passed");
    assert.throws(() => runTest(root, [
      "--requirement-id", "REQ-R2",
      "--test-kind", "unit",
      "--report-action", "register",
      "--report-path", reportPath,
      "--phase", "verify",
      "--acceptance", "AC-01",
      "--files", ...prepared.files,
    ], noopGlobal), /格式不受支持/);
  });
});

describe("evaluateTestEvidence", () => {
  it("ready=true when no files changed", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-ev-"));
    const s = evaluateTestEvidence(root, "demo", [], { schemaVersion: 1, task: "demo", entries: [] });
    assert.equal(s.ready, true);
  });
  it("ready=false when task mismatch", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-ev-"));
    writeFileSync(join(root, "a.ts"), "x");
    const s = evaluateTestEvidence(root, "demo", ["a.ts"], { schemaVersion: 1, task: "other", entries: [] });
    assert.equal(s.ready, false);
  });
});

describe("renderTestEvidence", () => {
  it("renders a markdown table with the task", () => {
    const md = renderTestEvidence({ task: "demo", updatedAt: "2026-01-01", entries: [] });
    assert.ok(md.includes("# 测试证据"));
    assert.ok(md.includes("demo"));
    assert.ok(md.includes("| 阶段 | 状态"));
  });
});

describe("COMMAND_ERROR_CODES", () => {
  it("includes the gate-relevant exit codes", () => {
    for (const c of [2, 3, 124, 127]) assert.ok(COMMAND_ERROR_CODES.has(c));
  });
});
