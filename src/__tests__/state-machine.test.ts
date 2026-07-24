import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, existsSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  createRequirement,
  loadRequirement,
  mutate,
  readyRequirement,
  recordReview,
  finishRequirement,
  closeRequirement,
  reopenRequirement,
  setAcceptanceCriteria,
  setTestContract,
  assertTransition,
  requirementDir,
  manifestPath,
  SCHEMA_VERSION,
  STATES,
} from "../requirements/state-machine.js";
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

  it("manifest is written under the v2 direct layout (no by-id)", () => {
    const root = freshProject();
    createRequirement(root, "REQ-8", "布局需求");
    const dir = requirementDir(root, "REQ-8");
    assert.ok(dir.endsWith(join(".project-intel", "requirements", "REQ-8")));
    assert.ok(!dir.includes("by-id"));
    assert.ok(existsSync(join(dir, "manifest.json")));
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
