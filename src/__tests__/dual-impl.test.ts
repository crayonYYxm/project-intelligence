import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  normalizeForCompare,
  compareJsonOutputs,
} from "../testing/dual-impl.js";

describe("normalizeForCompare", () => {
  it("masks ISO-8601 timestamps", () => {
    const out = normalizeForCompare({ at: "2026-07-21T12:30:00.000000+00:00", x: 1 });
    assert.deepEqual(out, { at: "<TIME>", x: 1 });
  });

  it("masks 40-char git hashes", () => {
    const out = normalizeForCompare({
      commit: "ad3f346a78fbbc29689e16e1c9002f7037381841",
      short: "ad3f346",
    });
    assert.deepEqual(out, { commit: "<GIT_HASH>", short: "ad3f346" });
  });

  it("masks epoch-second/milli integers", () => {
    const out = normalizeForCompare({ a: 1784770096, b: 1784770096000, c: 42 });
    assert.deepEqual(out, { a: "<EPOCH>", b: "<EPOCH>", c: 42 });
  });

  it("masks absolute repo roots (POSIX)", () => {
    const root = "/Users/xumeng/Desktop/code/project-intelligence";
    const out = normalizeForCompare(
      { path: `${root}/.project-intel/manifest.json` },
      [root]
    );
    assert.deepEqual(out, { path: "<ROOT>/.project-intel/manifest.json" });
  });

  it("normalizes Windows backslashes and masks sample root", () => {
    const sample = "C:\\tmp\\pi-sample";
    const out = normalizeForCompare(
      { path: `${sample}\\sub\\file.py`, raw: "a\\b" },
      [sample]
    );
    assert.deepEqual(out, { path: "<ROOT>/sub/file.py", raw: "a/b" });
  });

  it("collapses mtime integers regardless of value", () => {
    const out = normalizeForCompare({ files: [{ path: "a", mtime: 123 }, { path: "b", mtime: 456 }] });
    assert.deepEqual(out, {
      files: [{ path: "a", mtime: "<MTIME>" }, { path: "b", mtime: "<MTIME>" }],
    });
  });

  it("applies longest-root-first masking so nested roots win", () => {
    const inner = "/a/b/c";
    const outer = "/a/b";
    const out = normalizeForCompare(`x ${inner}/y ${outer}/z`, [outer, inner]);
    assert.equal(out, "x <ROOT>/y <ROOT1>/z");
  });
});

describe("compareJsonOutputs", () => {
  it("returns null for equal normalized values", () => {
    assert.equal(compareJsonOutputs({ a: 1, b: [1, 2] }, { a: 1, b: [1, 2] }), null);
  });

  it("reports the first differing path", () => {
    const diff = compareJsonOutputs({ a: { b: 1 } }, { a: { b: 2 } });
    assert.equal(diff, "a.b: 1 vs 2");
  });

  it("reports missing keys with direction", () => {
    assert.match(compareJsonOutputs({ a: 1 }, { a: 1, b: 2 }) ?? "", /b: missing in baseline/);
    assert.match(compareJsonOutputs({ a: 1, b: 2 }, { a: 1 }) ?? "", /b: missing in candidate/);
  });

  it("reports array length mismatches", () => {
    assert.match(compareJsonOutputs([1, 2], [1]) ?? "", /\[1\]: missing in candidate/);
  });
});
