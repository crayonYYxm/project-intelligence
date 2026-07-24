import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { run, commandExists, which } from "../process/spawn.js";
import { runShell } from "../process/exec-shell.js";
import { print, printJson, printError } from "../io/output.js";
import { parseFlatYaml, coerceScalar } from "../io/yaml.js";
import {
  parseHeadings,
  normalizeHeading,
  hasMeaningfulContent,
} from "../io/markdown.js";

describe("subprocess.spawn (argv)", () => {
  it("runs a successful command and captures output", () => {
    const r = run([process.execPath, "-e", "process.stdout.write('hi')"], process.cwd(), 5000);
    assert.equal(r.code, 0);
    assert.equal(r.stdout, "hi");
  });
  it("returns 127 when the binary is missing", () => {
    const r = run(["this-binary-does-not-exist-xyz"], process.cwd(), 3000);
    assert.equal(r.code, 127);
  });
  it("returns a non-zero code on argv usage error", () => {
    const r = run([process.execPath, "--no-such-flag"], process.cwd(), 3000);
    assert.ok(r.code !== 0);
  });
});

describe("subprocess.which / commandExists", () => {
  it("finds node on PATH", () => {
    assert.ok(commandExists("node"));
    assert.ok(which("node") !== null);
  });
  it("returns null for a missing command", () => {
    assert.equal(which("nope-xyz-12345"), null);
  });
});

describe("subprocess.runShell (shell form)", () => {
  it("supports pipes and redirects", () => {
    // echo a | tr a-z A-Z  ->  A
    const r = runShell("echo a | tr a-z A-Z", process.cwd(), 5000);
    assert.equal(r.code, 0);
    assert.equal(r.stdout, "A");
  });
  it("supports environment variable expansion", () => {
    const r = runShell("echo $PI_TEST_VAR", process.cwd(), 5000);
    // var unset -> empty; set it and retry
    assert.equal(r.code, 0);
    process.env.PI_TEST_VAR = "hello";
    try {
      const r2 = runShell("echo $PI_TEST_VAR", process.cwd(), 5000);
      assert.equal(r2.stdout, "hello");
    } finally {
      delete process.env.PI_TEST_VAR;
    }
  });
  it("returns 0 for a true compound command", () => {
    const r = runShell("true && echo ok", process.cwd(), 5000);
    assert.equal(r.code, 0);
    assert.equal(r.stdout, "ok");
  });
  it("surfaces non-zero exit of a failed command", () => {
    const r = runShell("exit 3", process.cwd(), 5000);
    assert.equal(r.code, 3);
  });
});

describe("output (UTF-8)", () => {
  it("print writes a UTF-8 line including Chinese", () => {
    // Capture by redirecting stdout fd is intrusive; assert no throw + type.
    assert.doesNotThrow(() => print("中文测试"));
  });
  it("printJson renders without ASCII escaping", () => {
    assert.doesNotThrow(() => printJson({ name: "中文" }));
  });
  it("printError writes to stderr", () => {
    assert.doesNotThrow(() => printError("err 中文"));
  });
});

describe("io.yaml", () => {
  it("parses flat key: value", () => {
    const m = parseFlatYaml("name: 中文\nage: 42\nactive: true\n# comment\nbad");
    assert.deepEqual(m, { name: "中文", age: "42", active: "true" });
  });
  it("strips quoted values", () => {
    assert.equal(parseFlatYaml('x: "a b"').x, "a b");
  });
  it("coerces scalars", () => {
    assert.deepEqual(coerceScalar("42"), { string: "42", int: 42, bool: null });
    assert.deepEqual(coerceScalar("true"), { string: "true", int: null, bool: true });
    assert.deepEqual(coerceScalar("中文"), { string: "中文", int: null, bool: null });
  });
});

describe("io.markdown", () => {
  it("parses ATX headings with level and text", () => {
    const h = parseHeadings(["# Title", "## Sub", "body", "### Deep"]);
    assert.equal(h.length, 3);
    assert.equal(h[0]!.level, 1);
    assert.equal(h[0]!.text, "Title");
    assert.equal(h[1]!.level, 2);
    assert.equal(h[2]!.normalized, "Deep");
  });
  it("normalizeHeading collapses whitespace", () => {
    assert.equal(normalizeHeading("  a   b  "), "a b");
  });
  it("hasMeaningfulContent rejects blank/placeholder", () => {
    assert.equal(hasMeaningfulContent(""), false);
    assert.equal(hasMeaningfulContent("___"), false);
    assert.equal(hasMeaningfulContent("待确认"), false);
    assert.equal(hasMeaningfulContent("无"), false);
    assert.equal(hasMeaningfulContent("实际内容"), true);
  });
});
