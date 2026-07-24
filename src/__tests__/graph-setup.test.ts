import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  commandUsesExternalPath,
  graphCommandAuthorized,
  setupGraphTools,
  shellWords,
} from "../graph/setup.js";

describe("graph command authorization", () => {
  it("preserves and detects Windows absolute paths on POSIX", () => {
    assert.deepEqual(shellWords('C:\\Tools\\understand.exe analyze "."'), [
      "C:\\Tools\\understand.exe",
      "analyze",
      ".",
    ]);
    const root = mkdtempSync(join(tmpdir(), "pi-graph-auth-"));
    assert.equal(commandUsesExternalPath(root, "C:\\Tools\\understand.exe analyze"), true);
  });

  it("allows repository-contained absolute paths and rejects outside paths", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-graph-auth-"));
    assert.equal(commandUsesExternalPath(root, `${join(root, "tool")} analyze`), false);
    assert.equal(commandUsesExternalPath(root, "/opt/tools/understand analyze"), true);
  });

  it("requires explicit permission for repo runners and environment commands", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-graph-auth-"));
    assert.equal(graphCommandAuthorized(root, "node .gitnexus/run.cjs analyze", "repo-runner").allowed, false);
    assert.equal(graphCommandAuthorized(root, "understand .", "environment").allowed, false);
    assert.equal(
      graphCommandAuthorized(root, "node .gitnexus/run.cjs analyze", "repo-runner", { allowRepoRunner: true }).allowed,
      true
    );
  });
});

describe("graph setup execution", () => {
  it("executes an authorized installed analyzer and captures evidence", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-graph-run-"));
    const results = setupGraphTools(root, [{
      tool: "FixtureGraph",
      state: "installed",
      analyzeCommand: `${JSON.stringify(process.execPath)} -e "process.stdout.write('graph-ok')"`,
      analyzeCommandSource: "builtin",
    }], true, { allowExternalPath: true });
    assert.equal(results.length, 1);
    assert.equal(results[0]?.status, "ok");
    assert.equal(results[0]?.stdout, "graph-ok");
  });

  it("records a skipped result instead of executing an unauthorized runner", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-graph-run-"));
    const results = setupGraphTools(root, [{
      tool: "GitNexus",
      state: "installed",
      analyzeCommand: "node .gitnexus/run.cjs analyze",
      analyzeCommandSource: "repo-runner",
    }], true);
    assert.equal(results[0]?.status, "skipped");
    assert.match(String(results[0]?.detail), /allow-repo-runner/);
  });
});
