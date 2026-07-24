import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// CLI contract test (AC-02).
//
// The 0.6.1 CLI behavior snapshot (.baseline/cli-snapshot.json) is the
// compatibility contract the Node.js implementation must reproduce. This test:
//   1. Validates the snapshot itself is well-formed and complete.
//   2. Pins the JSON envelope contract {ok, command, status, exitCode, error,
//      result, output} that every --json response must satisfy.
//   3. Runs the live Node CLI (dist/cli.js) and asserts each command's --help
//      exits 0, the version command prints a semver, and unknown flags exit 2.
//      This is the real dual-implementation comparison gate (AC-02/AC-10).

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SNAPSHOT_PATH = resolve(ROOT, ".baseline/cli-snapshot.json");
const NODE_CLI = resolve(ROOT, "dist", "cli.js");

interface CliSnapshot {
  generatedFrom: string;
  bin: string;
  version: { exitCode: number; stdout: string };
  topHelp: { exitCode: number; stdout: string; stderr?: string; commands: string[] };
  commands: Record<string, { exitCode: number; stdout: string; stderr: string }>;
  jsonEnvelopes: Record<string, { exitCode: number; envelope: unknown }>;
}

const REQUIRED_ENVELOPE_KEYS = [
  "ok",
  "command",
  "status",
  "exitCode",
  "error",
  "result",
  "output",
] as const;

function loadSnapshot(): CliSnapshot {
  const raw = readFileSync(SNAPSHOT_PATH, "utf8");
  return JSON.parse(raw) as CliSnapshot;
}

/** Run the live Node CLI with the given args, returning {status, stdout, stderr}. */
function runNodeCli(args: string[]): { status: number; stdout: string; stderr: string } {
  const r = spawnSync(process.execPath, [NODE_CLI, ...args], { encoding: "utf8", timeout: 10_000 });
  return { status: r.status ?? -1, stdout: r.stdout ?? "", stderr: r.stderr ?? "" };
}

/** Run the live Node CLI in --json mode and parse the envelope. */
function runNodeCliJson(args: string[]): { status: number; envelope: Record<string, unknown> | null } {
  const r = runNodeCli(["--json", ...args]);
  try {
    const env = JSON.parse(r.stdout);
    return { status: r.status, envelope: env };
  } catch {
    return { status: r.status, envelope: null };
  }
}

describe("cli snapshot contract (AC-02)", () => {
  let snapshot: CliSnapshot;
  it("loads a well-formed snapshot", () => {
    snapshot = loadSnapshot();
    assert.ok(Array.isArray(snapshot.topHelp.commands) && snapshot.topHelp.commands.length > 0);
    assert.ok(Object.keys(snapshot.commands).length > 0);
  });

  it("captured every top-level command's help", () => {
    snapshot = loadSnapshot();
    const missing = snapshot.topHelp.commands.filter(
      (cmd) => !snapshot.commands[cmd] || snapshot.commands[cmd].exitCode !== 0
    );
    assert.deepEqual(missing, [], `commands missing clean help: ${missing.join(", ")}`);
  });

  it("pins the JSON envelope shape on every probe", () => {
    snapshot = loadSnapshot();
    for (const [name, probe] of Object.entries(snapshot.jsonEnvelopes)) {
      const env = probe.envelope as Record<string, unknown> | null;
      if (!env) {
        assert.fail(`envelope probe '${name}' produced no JSON envelope`);
      }
      for (const key of REQUIRED_ENVELOPE_KEYS) {
        assert.ok(
          key in env,
          `envelope probe '${name}' missing key '${key}' (got ${Object.keys(env).join(",")})`
        );
      }
    }
  });

  it("the version command exits 0 and prints a semver", () => {
    snapshot = loadSnapshot();
    assert.equal(snapshot.version.exitCode, 0);
    assert.match(snapshot.version.stdout, /^\d+\.\d+\.\d+/);
  });

  it("usage errors exit non-zero with a non-ok envelope", () => {
    snapshot = loadSnapshot();
    const probe = snapshot.jsonEnvelopes.usageError;
    assert.ok(probe && probe.exitCode !== 0, "usage error should exit non-zero");
    const env = probe!.envelope as Record<string, unknown> | null;
    assert.ok(env && env.ok === false, "usage error envelope must have ok=false");
  });
});

describe("live Node CLI contract (AC-02/AC-10)", () => {
  // These tests run the actual built Node CLI (dist/cli.js) and verify it
  // matches the baseline behavior. They are the real dual-implementation gate.

  it("dist/cli.js exists and is runnable", () => {
    assert.ok(existsSync(NODE_CLI), `dist/cli.js not found at ${NODE_CLI}`);
  });

  it("version command exits 0 and prints a semver", () => {
    const r = runNodeCli(["version"]);
    assert.equal(r.status, 0);
    assert.match(r.stdout, /^\d+\.\d+\.\d+/);
  });

  it("--version flag exits 0 and prints a semver", () => {
    const r = runNodeCli(["--version"]);
    assert.equal(r.status, 0);
    assert.match(r.stdout, /^\d+\.\d+\.\d+/);
  });

  it("every baseline command's --help is byte-for-byte compatible", () => {
    const snapshot = loadSnapshot();
    for (const cmd of snapshot.topHelp.commands) {
      const r = runNodeCli([cmd, "--help"]);
      const expected = snapshot.commands[cmd]!;
      assert.equal(r.status, expected.exitCode, `--help exit mismatch for '${cmd}'`);
      assert.equal(r.stdout, expected.stdout, `--help stdout mismatch for '${cmd}'`);
      assert.equal(r.stderr, expected.stderr ?? "", `--help stderr mismatch for '${cmd}'`);
    }
  });

  it("top-level --help is byte-for-byte compatible", () => {
    const snapshot = loadSnapshot();
    const r = runNodeCli(["--help"]);
    assert.equal(r.status, snapshot.topHelp.exitCode);
    assert.equal(r.stdout, snapshot.topHelp.stdout);
    assert.equal(r.stderr, snapshot.topHelp.stderr ?? "");
  });

  it("top-level --help output contains all baseline commands", () => {
    const snapshot = loadSnapshot();
    const r = runNodeCli(["--help"]);
    // The Node help must list every command the baseline lists.
    for (const cmd of snapshot.topHelp.commands) {
      assert.ok(
        r.stdout.includes(cmd),
        `top-level --help output must mention command '${cmd}'`
      );
    }
  });

  it("subcommand --help output contains usage line and key flags", () => {
    const snapshot = loadSnapshot();
    // Spot-check a few commands for structural compatibility.
    const checks: Record<string, string[]> = {
      init: ["usage: project-intel init", "--dry-run", "--no-graph"],
      review: ["usage: project-intel review", "--requirement-id", "--result", "--summary"],
      doctor: ["usage: project-intel doctor", "-h, --help"],
    };
    for (const [cmd, expected] of Object.entries(checks)) {
      const r = runNodeCli([cmd, "--help"]);
      for (const substr of expected) {
        assert.ok(
          r.stdout.includes(substr),
          `${cmd} --help output must contain '${substr}', got:\n${r.stdout}`
        );
      }
    }
  });

  it("unknown command exits 2", () => {
    const r = runNodeCli(["nope"]);
    assert.equal(r.status, 2);
  });

  it("unknown flag exits 2", () => {
    const r = runNodeCli(["review", "--definitely-invalid"]);
    assert.equal(r.status, 2);
  });

  it("version --json produces a valid envelope with version field", () => {
    const { status, envelope } = runNodeCliJson(["version"]);
    assert.equal(status, 0);
    assert.ok(envelope, "envelope must be valid JSON");
    assert.equal(envelope!.ok, true);
    const result = envelope!.result as Record<string, unknown>;
    assert.ok(result && typeof result.version === "string");
    assert.match(result.version as string, /^\d+\.\d+\.\d+/);
  });

  it("doctor --json produces a valid envelope with runtime=node", () => {
    const { status, envelope } = runNodeCliJson(["doctor"]);
    assert.equal(status, 0);
    assert.ok(envelope, "doctor envelope must be valid JSON");
    assert.equal(envelope!.ok, true);
    const result = envelope!.result as Record<string, unknown>;
    const runtime = result?.runtime as Record<string, unknown>;
    assert.equal(runtime?.name, "node");
  });

  it("usage error --json produces ok=false envelope", () => {
    const { status, envelope } = runNodeCliJson(["nope"]);
    assert.notEqual(status, 0);
    assert.ok(envelope, "error envelope must be valid JSON");
    assert.equal(envelope!.ok, false);
  });
});
