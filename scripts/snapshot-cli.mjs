#!/usr/bin/env node
// Capture the 0.6.1 CLI behavior baseline (commands, subcommands, args, defaults,
// help text, exit codes, JSON envelope) into .baseline/cli-snapshot.json.
//
// Usage:
//   node scripts/snapshot-cli.mjs            # (re)generate the snapshot
//   node scripts/snapshot-cli.mjs --check    # fail if snapshot would change
//
// The snapshot is generated from an immutable v0.6.1 worktree (see plan 0.2),
// never from the live workspace Python, so it stays stable during the migration.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const BASELINE_CLI = resolve(ROOT, ".baseline/worktree/bin/project-intel.mjs");
const OUT = resolve(ROOT, ".baseline/cli-snapshot.json");

const checkMode = process.argv.includes("--check");

if (!existsSync(BASELINE_CLI)) {
  console.error(
    `Baseline CLI missing: ${BASELINE_CLI}\n` +
      "Run `git worktree add .baseline/worktree v0.6.1` first (plan 0.2)."
  );
  process.exit(1);
}

// Parse the top-level command list out of the `{a,b,c} ...` positional line.
function topLevelCommands(helpText) {
  const lines = helpText.split(/\r?\n/);
  const positional = lines.find((l) => l.includes("{") && l.includes("}"));
  if (!positional) return [];
  const inner = positional.slice(positional.indexOf("{") + 1, positional.lastIndexOf("}"));
  return inner
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function runCli(args, opts = {}) {
  const result = spawnSync(process.execPath, [BASELINE_CLI, ...args], {
    cwd: ROOT,
    encoding: "utf8",
    timeout: 30_000,
    ...opts,
  });
  return {
    args,
    exitCode: result.status ?? -1,
    stdout: (result.stdout ?? "").trimEnd(),
    stderr: (result.stderr ?? "").trimEnd(),
  };
}

function runJson(args) {
  // `--json` is a suppressed global flag that must precede the subcommand.
  const r = runCli(["--json", ...args]);
  let envelope = null;
  try {
    envelope = r.stdout ? JSON.parse(r.stdout) : null;
  } catch {
    envelope = null;
  }
  return { args, exitCode: r.exitCode, envelope };
}

function buildSnapshot() {
  const snapshot = {
    generatedFrom: "v0.6.1 worktree (.baseline/worktree)",
    bin: ".baseline/worktree/bin/project-intel.mjs",
    // NOTE: no timestamp — the snapshot must be deterministic so --check is stable.
    version: null,
    topHelp: null,
    commands: {},
    jsonEnvelopes: {},
  };

  const versionRun = runCli(["--version"]);
  snapshot.version = {
    exitCode: versionRun.exitCode,
    stdout: versionRun.stdout,
  };

  const topHelp = runCli(["--help"]);
  snapshot.topHelp = {
    exitCode: topHelp.exitCode,
    stdout: topHelp.stdout,
    commands: topLevelCommands(topHelp.stdout),
  };

  for (const cmd of snapshot.topHelp.commands) {
    const help = runCli([cmd, "--help"]);
    snapshot.commands[cmd] = {
      exitCode: help.exitCode,
      stdout: help.stdout,
      stderr: help.stderr,
    };
  }

  // JSON envelope shape probes: one success-ish, one usage error, one missing-project.
  // These pin the {ok, command, status, exitCode, error, result, output} contract.
  snapshot.jsonEnvelopes.version = runJson(["--version"]);
  snapshot.jsonEnvelopes.usageError = runJson(["--nope-nope-nope"]);
  // requirement status on a nonexistent id -> usage/gate error envelope
  snapshot.jsonEnvelopes.requirementMissing = runJson([
    "requirement",
    "status",
    "--requirement-id",
    "NONEXISTENT-SNAPSHOT-PROBE",
  ]);

  return snapshot;
}

function main() {
  const snapshot = buildSnapshot();
  const serialized = JSON.stringify(snapshot, null, 2) + "\n";

  if (checkMode) {
    if (!existsSync(OUT)) {
      console.error(`Snapshot missing: ${OUT}. Run without --check to generate.`);
      process.exit(1);
    }
    const current = readFileSync(OUT, "utf8");
    if (current !== serialized) {
      console.error(`Snapshot drift detected in ${OUT}. Regenerate without --check.`);
      process.exit(1);
    }
    console.log(
      `Snapshot OK (${snapshot.topHelp.commands.length} commands, ` +
        `version ${snapshot.version.stdout || "?"}).`
    );
    return;
  }

  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, serialized);
  console.log(
    `Wrote ${OUT} — ${snapshot.topHelp.commands.length} commands, ` +
      `version ${snapshot.version.stdout || "?"}.`
  );
}

main();
