import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { captureScopeSnapshot } from "../requirements/scope.js";
import { initGitProject } from "./helpers.js";

describe("Git scope snapshot", () => {
  it("changes when an existing untracked file's content changes", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-scope-"));
    initGitProject(root);
    mkdirSync(join(root, "src"), { recursive: true });
    writeFileSync(join(root, "src", "untracked.ts"), "export const value = 1;\n");
    const before = captureScopeSnapshot(root);
    writeFileSync(join(root, "src", "untracked.ts"), "export const value = 2;\n");
    const after = captureScopeSnapshot(root);
    assert.equal(before.gitAvailable, true);
    assert.notEqual(before.diffHash, after.diffHash);
    assert.notEqual(before.entries[0]?.sha256, after.entries[0]?.sha256);
  });

  it("excludes .project-intel lifecycle writes from business scope", () => {
    const root = mkdtempSync(join(tmpdir(), "pi-scope-"));
    initGitProject(root);
    const before = captureScopeSnapshot(root);
    mkdirSync(join(root, ".project-intel"), { recursive: true });
    writeFileSync(join(root, ".project-intel", "manifest.json"), "{}");
    const after = captureScopeSnapshot(root);
    assert.equal(before.diffHash, after.diffHash);
  });
});
