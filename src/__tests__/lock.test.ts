import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, existsSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, basename, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { withLock } from "../fs/lock.js";
import { RequirementError } from "../errors.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
// Resolve the tsx binary so the child TS contender loads its TS imports reliably.
const TSX_BIN = join(ROOT, "node_modules", ".bin", "tsx");
const CONTENDER = join(ROOT, "src", "__tests__", "lock-contender.ts");

describe("withLock (in-process)", () => {
  it("blocks same-process re-entrant acquire (no deadlock)", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-lock-"));
    const order: string[] = [];
    withLock(dir, () => {
      order.push("outer");
      // Re-entrant acquire from the same process must fail fast rather than hang.
      assert.throws(
        () => withLock(dir, () => order.push("inner"), { timeoutMs: 60 }),
        RequirementError
      );
    });
    assert.deepEqual(order, ["outer"]);
  });

  it("releases the lockfile after the critical section", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-lock-"));
    withLock(dir, () => undefined);
    const lockPath = join(dir, "..", `.${basename(dir)}.manifest.lock`);
    assert.equal(existsSync(lockPath), false);
  });
});

describe("withLock (multi-process contention)", () => {
  // Spawn several Node child processes that contend for the same lock and append
  // START/END markers to a shared results file. Exclusivity holds when each id's
  // START immediately precedes its END (no interleaving from another process).
  it(
    "grants exclusive access across child processes",
    { timeout: 30_000 },
    () => {
      const tmp = mkdtempSync(join(tmpdir(), "pi-mp-"));
      const dir = join(tmp, "req");
      mkdirSync(dir, { recursive: true });
      const resultsPath = join(tmp, "results.txt");
      writeFileSync(resultsPath, "");

      const procs = 4;
      const children: ReturnType<typeof spawnSync>[] = [];
      for (let i = 0; i < procs; i++) {
        children.push(
          spawnSync(TSX_BIN, [CONTENDER, dir, resultsPath, String(i)], {
            cwd: ROOT,
            encoding: "utf8",
            timeout: 15_000,
          })
        );
      }
      const failures = children.filter((c) => (c.status ?? -1) !== 0);
      assert.equal(
        failures.length,
        0,
        `child failures: ${failures.map((f) => f.stderr).join("; ")}`
      );

      const lines = readFileSync(resultsPath, "utf8").trim().split("\n");
      assert.equal(lines.length, procs * 2, "each contender wrote START+END");
      for (let i = 0; i < lines.length; i += 2) {
        const startId = lines[i]!.split(" ")[0];
        const endId = lines[i + 1]!.split(" ")[0];
        assert.equal(startId, endId, "START/END pair must share an id (exclusivity violated)");
      }
    }
  );
});
