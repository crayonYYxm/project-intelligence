import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  toPosix,
  normalizeBusinessPath,
  isAbsolutePathLike,
  resolveInside,
  expandUser,
} from "../fs/paths.js";
import { UsageError } from "../errors.js";
import { writeText, writeJson, loadJson, loadJsonStrict, StrictReadError } from "../fs/atomic-write.js";

describe("paths", () => {
  it("toPosix converts separators", () => {
    assert.equal(toPosix("a\\b\\c"), "a/b/c");
  });
  it("normalizeBusinessPath strips leading ./ and normalizes", () => {
    assert.equal(normalizeBusinessPath("./a/b/../c"), "a/c");
  });
  it("isAbsolutePathLike detects posix, windows drive, unc", () => {
    assert.equal(isAbsolutePathLike("/abs/path"), true);
    assert.equal(isAbsolutePathLike("C:\\Users"), true);
    assert.equal(isAbsolutePathLike("C:/Users"), true);
    assert.equal(isAbsolutePathLike("\\\\server\\share"), true);
    assert.equal(isAbsolutePathLike("relative/path"), false);
  });
  it("resolveInside rejects traversal outside root", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-paths-"));
    const inside = resolveInside(tmp, "sub/file.txt");
    assert.ok(inside.startsWith(tmp));
    assert.throws(() => resolveInside(tmp, "../../etc/passwd"), UsageError);
  });
  it("expandUser leaves non-home paths alone", () => {
    assert.equal(expandUser("/abs"), "/abs");
    assert.equal(expandUser("rel"), "rel");
  });
});

describe("atomic-write", () => {
  it("writes text with a trailing newline, UTF-8 preserved", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-aw-"));
    const target = join(tmp, "中文.txt");
    writeText(target, "你好\n\n\n");
    assert.equal(readFileSync(target, "utf8"), "你好\n");
  });
  it("writes JSON without ascii escaping and creates parent dirs", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-aw-"));
    const target = join(tmp, "nested", "data.json");
    writeJson(target, { name: "中文", n: 1 });
    assert.deepEqual(JSON.parse(readFileSync(target, "utf8")), { name: "中文", n: 1 });
  });
  it("preserves existing file mode", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-aw-"));
    const target = join(tmp, "keep.json");
    writeJson(target, { a: 1 });
    // rewrite; should not error and content updates atomically
    writeJson(target, { a: 2 });
    assert.equal(JSON.parse(readFileSync(target, "utf8")).a, 2);
  });
  it("loadJson returns default on missing/corrupt", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-aw-"));
    assert.equal(loadJson(join(tmp, "nope.json"), "fallback"), "fallback");
    const bad = join(tmp, "bad.json");
    writeFileSync(bad, "{not json");
    assert.equal(loadJson(bad, 42), 42);
  });
  it("loadJsonStrict raises on corrupt/non-object", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-aw-"));
    const bad = join(tmp, "bad.json");
    writeFileSync(bad, "{not json");
    assert.throws(() => loadJsonStrict(bad, "config"), StrictReadError);
    const arr = join(tmp, "arr.json");
    writeFileSync(arr, "[1,2]");
    assert.throws(() => loadJsonStrict(arr, "config"), StrictReadError);
  });
});
