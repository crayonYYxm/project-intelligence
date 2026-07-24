import { spawnSync } from "node:child_process";

// Node-only aggregate test gate. Python implementation tests were replaced by
// AC-10's method-level test map plus the TypeScript unit/e2e suite.

const skillResult = spawnSync(process.execPath, ["scripts/validate-skill-evals.mjs"], { stdio: "inherit" });
if (skillResult.error) {
  console.error(`Unable to validate skill contracts: ${skillResult.error.message}`);
  process.exit(1);
}
if ((skillResult.status ?? 1) !== 0) {
  process.exit(skillResult.status ?? 1);
}

// Node/TypeScript unit tests (migrated core). Aggregated here so `npm test`
// remains the single gate; `npm run test:unit` runs them in isolation.
const unitResult = spawnSync(process.execPath, ["scripts/run-unit-tests.mjs"], { stdio: "inherit" });
if (unitResult.error) {
  console.error(`Unable to run unit tests: ${unitResult.error.message}`);
  process.exit(1);
}
process.exit(unitResult.status ?? 1);
