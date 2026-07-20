import { spawnSync } from "node:child_process";

const pythonCandidates = process.platform === "win32"
  ? [["py", ["-3"]], ["python", []], ["python3", []]]
  : [["python3", []], ["python", []]];

let pythonResult;
for (const [command, prefix] of pythonCandidates) {
  const result = spawnSync(command, [
    ...prefix,
    "-m",
    "unittest",
    "discover",
    "-s",
    "plugins/project-intelligence/tests",
    "-p",
    "test_*.py",
  ], { stdio: "inherit" });
  if (result.error?.code === "ENOENT" || result.status === 9009) {
    continue;
  }
  if (result.error) {
    console.error(`Unable to start ${command}: ${result.error.message}`);
    process.exit(1);
  }
  pythonResult = result;
  break;
}

if (!pythonResult) {
  console.error("Python 3.9 or newer was not found.");
  process.exit(1);
}
if (pythonResult.status !== 0) {
  process.exit(pythonResult.status ?? 1);
}

const skillResult = spawnSync(process.execPath, ["scripts/validate-skill-evals.mjs"], { stdio: "inherit" });
if (skillResult.error) {
  console.error(`Unable to validate skill contracts: ${skillResult.error.message}`);
  process.exit(1);
}
process.exit(skillResult.status ?? 1);
