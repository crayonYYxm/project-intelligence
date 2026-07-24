import { describe, it } from "node:test";
import assert from "node:assert/strict";

// Smoke test: confirms the node:test + tsx unit-test harness runs TypeScript.
// Real module tests land in phases 2-3 as each TS module is migrated.
describe("typescript harness", () => {
  it("runs a TypeScript assertion", () => {
    const sum = (a: number, b: number): number => a + b;
    assert.equal(sum(1, 2), 3);
  });

  it("can import a source module", async () => {
    const mod = await import("../index.js");
    assert.equal(typeof mod.VERSION, "string");
    assert.ok(mod.VERSION.length > 0);
  });
});
