import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  sanitizeErrorText,
  extractGlobalJson,
  jsonEnvelope,
} from "../cli/json-envelope.js";
import { splitArgv, parseGlobal } from "../cli/parser.js";
import { UsageError } from "../errors.js";

describe("sanitizeErrorText", () => {
  it("redacts authorization bearer tokens", () => {
    assert.equal(
      sanitizeErrorText("Authorization: Bearer abc.def.ghi"),
      "Authorization: [REDACTED]"
    );
  });
  it("redacts cookies", () => {
    assert.equal(sanitizeErrorText("cookie: session=secret123"), "cookie: [REDACTED]");
  });
  it("redacts password/secret/token/api_key", () => {
    assert.equal(
      sanitizeErrorText("password=hunter2 secret=x token=abc"),
      "password=[REDACTED] secret=[REDACTED] token=[REDACTED]"
    );
  });
  it("redacts aws credentials", () => {
    assert.equal(
      sanitizeErrorText("aws_access_key_id=AKIA123 aws_secret_access_key=xyz"),
      "aws_access_key_id=[REDACTED] aws_secret_access_key=[REDACTED]"
    );
  });
  it("redacts URL userinfo", () => {
    assert.equal(
      sanitizeErrorText("https://user:pass@host/path"),
      "https://[REDACTED]:[REDACTED]@host/path"
    );
  });
  it("leaves benign text intact", () => {
    assert.equal(sanitizeErrorText("需求 LOCAL-100 失败"), "需求 LOCAL-100 失败");
  });
});

describe("extractGlobalJson", () => {
  it("strips --json and reports mode", () => {
    assert.deepEqual(extractGlobalJson(["--json", "init", "--no-graph"]), {
      argv: ["init", "--no-graph"],
      jsonMode: true,
    });
  });
  it("preserves argv when --json absent", () => {
    assert.deepEqual(extractGlobalJson(["init"]), { argv: ["init"], jsonMode: false });
  });
});

describe("jsonEnvelope", () => {
  it("shapes a success envelope", () => {
    const env = jsonEnvelope("version", 0, { version: "0.6.1" });
    assert.equal(env.ok, true);
    assert.equal(env.status, "ok");
    assert.equal(env.exitCode, 0);
    assert.equal(env.error, null);
    assert.deepEqual(env.result, { version: "0.6.1" });
  });
  it("classifies exit 2 as USAGE_ERROR with sanitized in-place error", () => {
    const env = jsonEnvelope("requirement", 2, {
      error: "cookie: leak=value",
    });
    assert.equal(env.ok, false);
    assert.equal(env.status, "failed");
    assert.equal(env.error!.code, "USAGE_ERROR");
    assert.equal(env.error!.message, "cookie: [REDACTED]");
    assert.deepEqual(env.result, { error: "cookie: [REDACTED]" });
  });
  it("classifies non-2 failure as COMMAND_FAILED with default message", () => {
    const env = jsonEnvelope("test", 1);
    assert.equal(env.error!.code, "COMMAND_FAILED");
    assert.equal(env.error!.message, "command failed");
  });
  it("trims the output field", () => {
    const env = jsonEnvelope("x", 0, null, "  line\n  ");
    assert.equal(env.output, "line");
  });
});

describe("parseGlobal / splitArgv", () => {
  it("parses --project value", () => {
    assert.deepEqual(parseGlobal(["--project", "/tmp/x", "init"]), {
      project: "/tmp/x",
      jsonMode: false,
    });
  });
  it("parses --project= form", () => {
    assert.deepEqual(parseGlobal(["--project=/tmp/x", "init"]), {
      project: "/tmp/x",
      jsonMode: false,
    });
  });
  it("parses --json", () => {
    assert.deepEqual(parseGlobal(["--json", "init"]), { project: null, jsonMode: true });
  });
  it("rejects unknown long option before subcommand with exit-2 UsageError", () => {
    try {
      parseGlobal(["--nope-nope-nope"]);
      assert.fail("expected UsageError");
    } catch (e) {
      assert.ok(e instanceof UsageError);
      assert.equal((e as UsageError).exitCode, 2);
    }
  });
  it("splitArgv separates global, command, and rest", () => {
    const parsed = splitArgv(["--json", "--project", "/p", "init", "--no-graph"]);
    assert.ok(parsed);
    assert.equal(parsed!.command, "init");
    assert.deepEqual(parsed!.args, ["--no-graph"]);
    assert.equal(parsed!.global.project, "/p");
    assert.equal(parsed!.global.jsonMode, true);
  });
  it("splitArgv returns null when no subcommand", () => {
    assert.equal(splitArgv(["--project", "/p"]), null);
  });
});
