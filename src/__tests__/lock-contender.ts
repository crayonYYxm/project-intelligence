// Child-process contender for the multi-process lock test (lock.test.ts).
// Run via tsx: `tsx src/__tests__/lock-contender.ts <dir> <resultsPath> <id>`.
// Imported and executed only by spawned children; the test module orchestrates.

import { appendFileSync } from "node:fs";
import { withLock } from "../fs/lock.js";

export async function main(): Promise<void> {
  const dir = process.argv[2];
  const resultsPath = process.argv[3];
  const id = process.argv[4];
  if (!dir || !resultsPath) throw new Error("missing args");
  withLock(
    dir,
    () => {
      appendFileSync(resultsPath, `${id} START\n`);
      const end = Date.now() + 30;
      while (Date.now() < end) {
        /* hold the lock briefly */
      }
      appendFileSync(resultsPath, `${id} END\n`);
    },
    { timeoutMs: 4000 }
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
