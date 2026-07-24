import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  adaptersApply,
  adaptersRemove,
  adaptersStatus,
  adaptersPreview,
  runAdapters,
} from "../commands/adapters.js";
import {
  upsertAdapterManagedBlock,
  removeAdapterManagedBlock,
  replaceSingleManagedBlock,
  safeAdapterPath,
  PROJECT_INTEL_BLOCK_START,
  PROJECT_INTEL_BLOCK_END,
} from "../commands/adapter-blocks.js";
import { adapterTargets } from "../commands/agent-rules.js";
import { runInstall } from "../commands/install.js";
import { runAgentInstall, agentInstallCommands } from "../commands/agent-install.js";
import { hookScriptBody, writeHookTemplates } from "../commands/hooks.js";

const noopGlobal = { project: null, jsonMode: false } as never;

describe("adapter block management", () => {
  it("rejects paths outside the allowed set", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-ad-"));
    assert.throws(() => safeAdapterPath(tmp, "../etc/passwd"));
    assert.throws(() => safeAdapterPath(tmp, "docs/readme.md"));
  });

  it("replaceSingleManagedBlock creates then updates", () => {
    const start = PROJECT_INTEL_BLOCK_START;
    const end = PROJECT_INTEL_BLOCK_END;
    const created = replaceSingleManagedBlock("", `${start}\nbody\n${end}`, start, end, false);
    assert.equal(created.action, "created");
    const updated = replaceSingleManagedBlock(created.text, `${start}\nbody2\n${end}`, start, end, false);
    assert.equal(updated.action, "updated");
    assert.ok(updated.text.includes("body2"));
  });

  it("upsert then remove a managed block", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-ad-"));
    writeFileSync(join(tmp, "CLAUDE.md"), "existing content\n");
    upsertAdapterManagedBlock(tmp, "CLAUDE.md", "managed body", PROJECT_INTEL_BLOCK_START, PROJECT_INTEL_BLOCK_END, { prepend: true });
    let text = readFileSync(join(tmp, "CLAUDE.md"), "utf8");
    assert.ok(text.includes(PROJECT_INTEL_BLOCK_START));
    assert.ok(text.includes("managed body"));
    removeAdapterManagedBlock(tmp, "CLAUDE.md", PROJECT_INTEL_BLOCK_START, PROJECT_INTEL_BLOCK_END);
    text = readFileSync(join(tmp, "CLAUDE.md"), "utf8");
    assert.ok(!text.includes(PROJECT_INTEL_BLOCK_START));
    assert.ok(text.includes("existing content"));
  });
});

describe("adapters command family", () => {
  it("apply writes codex + claude blocks; status reports current", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-adv-"));
    const result = adaptersApply(tmp, "both", false);
    assert.equal(result.ok, true);
    assert.ok(existsSync(join(tmp, "AGENTS.md")));
    assert.ok(existsSync(join(tmp, "CLAUDE.md")));
    assert.ok(existsSync(join(tmp, ".claude", "CLAUDE.md")));
    const status = adaptersStatus(tmp, "both");
    assert.equal(status.ok, true, `entries: ${JSON.stringify(status.entries)}`);
  });

  it("preview is dry-run (no files written)", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-adv-"));
    adaptersPreview(tmp, "claude");
    assert.ok(!existsSync(join(tmp, "CLAUDE.md")));
  });

  it("remove clears blocks", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-adv-"));
    adaptersApply(tmp, "codex", false);
    assert.ok(readFileSync(join(tmp, "AGENTS.md"), "utf8").length > 0);
    adaptersRemove(tmp, "codex", false);
    // file may be emptied but block gone
    const text = readFileSync(join(tmp, "AGENTS.md"), "utf8");
    assert.ok(!text.includes("agent-project-intelligence"));
  });

  it("status --check returns non-zero when not current", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-adv-"));
    writeFileSync(join(tmp, "CLAUDE.md"), "no block here\n");
    const result = runAdapters(tmp, ["status", "--check"], noopGlobal);
    assert.notEqual(result.exitCode, 0);
  });

  it("adapterTargets both returns 3 targets (codex, claude, claude-nested)", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-adv-"));
    const targets = adapterTargets(tmp, "both");
    assert.equal(targets.length, 3);
    assert.deepEqual(targets.map((t) => t.name), ["codex", "claude", "claude-nested"]);
  });
});

describe("top-level install command", () => {
  it("creates .claude/ and applies adapters; --hooks writes templates", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-ins-"));
    const result = runInstall(tmp, ["--hooks"], noopGlobal);
    assert.equal(result.exitCode, 0);
    assert.ok(existsSync(join(tmp, ".claude")));
    assert.ok(existsSync(join(tmp, "CLAUDE.md")));
    assert.ok(existsSync(join(tmp, ".project-intel", "hooks", "post-commit.sh")));
  });
});

describe("agent install command", () => {
  it("agentInstallCommands builds codex+claude for all", () => {
    const cmds = agentInstallCommands("all", "crayonYYxm/project-intelligence");
    assert.ok(cmds.codex && cmds.codex.length === 2);
    assert.ok(cmds.claude && cmds.claude.length === 2);
    assert.deepEqual(cmds.codex![0], ["codex", "plugin", "marketplace", "add", "crayonYYxm/project-intelligence"]);
  });

  it("--dry-run classifies present when cli exists, missing otherwise", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-ai-"));
    const result = runAgentInstall(tmp, ["--target", "claude", "--dry-run"], noopGlobal);
    assert.equal(result.exitCode, 0);
    const results = (result.result as Record<string, unknown>).results as Record<string, unknown>[];
    // claude cli is unlikely present in CI; should be missing OR present depending on env
    assert.ok(results.length === 1);
    assert.ok(["present", "missing"].includes(results[0]!.status as string));
  });

  it("rejects invalid target", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-ai-"));
    assert.throws(() => runAgentInstall(tmp, ["--target", "bogus"], noopGlobal));
  });
});

describe("git hooks (AC-07: no python3)", () => {
  it("hook body calls project-intel (Node CLI), never python3", () => {
    const body = hookScriptBody("post-commit");
    assert.ok(body.includes("project-intel refresh"));
    assert.ok(body.includes("project-intel check"));
    assert.ok(!body.includes("python3"), "hook body must not reference python3");
    assert.ok(!body.includes("python "), "hook body must not reference python");
  });

  it("writeHookTemplates writes 3 hooks + README under .project-intel/hooks", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-hk-"));
    // init first so .project-intel exists
    writeFileSync(join(tmp, "package.json"), "{}");
    mkdirSync(join(tmp, ".project-intel"), { recursive: true });
    const written = writeHookTemplates(tmp);
    assert.equal(written.length, 3);
    for (const name of ["post-merge.sh", "post-commit.sh", "pre-push.sh"]) {
      assert.ok(existsSync(join(tmp, ".project-intel", "hooks", name)));
    }
  });
});
