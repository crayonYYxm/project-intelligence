import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runReview } from "../commands/review.js";
import { runFinish } from "../commands/finish.js";
import { runMaintain } from "../commands/maintain.js";
import { runGraphTools } from "../commands/graph-tools.js";
import { runQuery } from "../commands/query.js";
import { gitnexusSummary, understandSummary, detectGraphSources, understandGraphSummary } from "../graph/sources.js";
import { loadRequirement, mutate } from "../requirements/state-machine.js";
import { prepareReviewedRequirement, prepareVerifiedRequirement } from "./helpers.js";

const noopGlobal = { project: null, jsonMode: false } as never;

describe("review / finish / maintain commands (3.F)", () => {
  it("review passed advances verified -> reviewed", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-3f-"));
    const prepared = prepareVerifiedRequirement(root, "REQ-R");
    const r = runReview(root, ["--requirement-id", "REQ-R", "--result", "passed", "--summary", "代码评审通过", "--files", ...prepared.files], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "reviewed");
  });

  it("review failed stays verified", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-3f-"));
    const prepared = prepareVerifiedRequirement(root, "REQ-R2");
    const r = runReview(root, ["--requirement-id", "REQ-R2", "--result", "failed", "--summary", "仍有问题", "--files", ...prepared.files], noopGlobal);
    assert.equal((r.result as Record<string, unknown>).state, "verified");
  });

  it("review sanitizes summary and finding text before persisting", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-3f-"));
    const prepared = prepareVerifiedRequirement(root, "REQ-R-SAFE");
    runReview(
      root,
      [
        "--requirement-id", "REQ-R-SAFE",
        "--result", "failed",
        "--summary", "Authorization: Bearer abc.def.ghi 手机 13800138000",
        "--finding", "minor:token=secret123",
        "--files", ...prepared.files,
      ],
      noopGlobal
    );
    const round = loadRequirement(root, "REQ-R-SAFE").reviewRounds?.at(-1) as Record<string, unknown>;
    const persisted = JSON.stringify(round);
    assert.ok(!persisted.includes("abc.def.ghi"));
    assert.ok(!persisted.includes("13800138000"));
    assert.ok(!persisted.includes("secret123"));
    assert.ok(persisted.includes("[REDACTED]"));
  });

  it("finish writes closure-summary and advances reviewed -> finished", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-3f-"));
    const prepared = prepareReviewedRequirement(root, "REQ-F");
    const r = runFinish(root, ["--requirement-id", "REQ-F", "--files", ...prepared.files], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "finished");
    assert.ok(existsSync(join(root, ".project-intel", "requirements", "REQ-F", "closure-summary.md")));
  });

  it("finish rejects without passed review (AC-11 gate)", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-3f-"));
    const prepared = prepareVerifiedRequirement(root, "REQ-F2");
    mutate(root, "REQ-F2", (m) => {
      m.state = "reviewed"; // simulate reviewed but no passed review round
    });
    assert.throws(() => runFinish(root, ["--requirement-id", "REQ-F2", "--files", ...prepared.files], noopGlobal));
  });

  it("maintain refreshes facts and closes the requirement", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-3f-"));
    const prepared = prepareReviewedRequirement(root, "REQ-M");
    runFinish(root, ["--requirement-id", "REQ-M", "--files", ...prepared.files], noopGlobal);
    const r = runMaintain(root, ["--requirement-id", "REQ-M", "--files", ...prepared.files], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.equal((r.result as Record<string, unknown>).state, "closed");
  });
});

describe("graph sources (3.G.1)", () => {
  it("gitnexusSummary missing when no .gitnexus", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-g-"));
    assert.equal(gitnexusSummary(root).status, "missing");
  });

  it("gitnexusSummary present with valid meta", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-g-"));
    mkdirSync(join(root, ".gitnexus"), { recursive: true });
    writeFileSync(
      join(root, ".gitnexus", "meta.json"),
      JSON.stringify({ schemaVersion: 5, lastCommit: "abc", stats: { files: 10, nodes: 100, edges: 200 }, capabilities: { graph: { status: "available" } } })
    );
    const s = gitnexusSummary(root);
    assert.equal(s.status, "present");
    assert.equal((s.stats as Record<string, number>).nodes, 100);
  });

  it("understandSummary present with non-empty nodes", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-g-"));
    mkdirSync(join(root, ".understand-anything"), { recursive: true });
    writeFileSync(
      join(root, ".understand-anything", "knowledge-graph.json"),
      JSON.stringify({ nodes: [{ id: "a", name: "A", filePath: "src/orders/a.ts" }], edges: [] })
    );
    const s = understandSummary(root);
    assert.equal(s.status, "present");
    assert.equal(s.nodes, 1);
  });

  it("detectGraphSources returns both names", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-g-"));
    const sources = detectGraphSources(root);
    assert.deepEqual(sources.map((s) => s.name), ["GitNexus", "Understand-Anything"]);
  });

  it("understandGraphSummary aggregates domains", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-g-"));
    mkdirSync(join(root, ".understand-anything"), { recursive: true });
    writeFileSync(
      join(root, ".understand-anything", "knowledge-graph.json"),
      JSON.stringify({
        nodes: [
          { id: "1", filePath: "src/orders/a.ts", name: "a" },
          { id: "2", filePath: "src/orders/b.ts", name: "b" },
          { id: "3", filePath: "src/pay/c.ts", name: "c" },
        ],
        edges: [],
      })
    );
    const summary = understandGraphSummary(root);
    assert.equal(summary.status, "present");
    const domains = summary.domains as { name: string; count: number }[];
    assert.ok(domains.some((d) => d.name === "orders" && d.count === 2));
  });
});

describe("graph-tools + query commands (3.G.2)", () => {
  it("graph-tools reports source statuses", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-cmd-"));
    const r = runGraphTools(root, [], noopGlobal);
    assert.equal(r.exitCode, 0);
    const actions = r.result as Record<string, unknown>[];
    assert.deepEqual(actions.map((action) => action.tool), ["GitNexus", "Understand-Anything"]);
  });

  it("query searches standards text", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-cmd-"));
    const stdDir = join(root, ".project-intel", "standards");
    mkdirSync(stdDir, { recursive: true });
    writeFileSync(join(root, ".project-intel", "manifest.json"), "{}");
    writeFileSync(join(stdDir, "api.md"), "# API 标准\n\n所有接口必须返回 JSON。\n");
    const r = runQuery(root, ["--search", "JSON"], noopGlobal);
    assert.equal(r.exitCode, 0);
    assert.deepEqual(r.result, { query: "JSON" });
  });

  it("query rejects an uninitialized project", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-cmd-"));
    assert.throws(() => runQuery(root, ["--search", "JSON"], noopGlobal), /请先运行 project-intel init/);
  });
});
