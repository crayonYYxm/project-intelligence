import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { dispatch, CommandRegistry } from "../app/dispatcher.js";
import type { CommandHandler, GlobalOptions } from "../cli/parser.js";
import { UsageError, RuntimeError } from "../errors.js";

const VERSION = "0.6.1-test";

function registry(): CommandRegistry {
  const reg = new CommandRegistry();
  const echo: CommandHandler = {
    name: "echo",
    help: "echo a message",
    knownFlags: new Set(["--msg"]),
    valueFlags: new Set(["--msg"]),
    run: (args: string[], _global: GlobalOptions) => ({ exitCode: 0, result: { echoed: args } }),
  };
  const fail: CommandHandler = {
    name: "fail",
    help: "always fails",
    run: () => {
      throw new UsageError("boom");
    },
  };
  const boom: CommandHandler = {
    name: "boom",
    help: "runtime error",
    run: () => {
      throw new RuntimeError("kaboom");
    },
  };
  reg.register(echo);
  reg.register(fail);
  reg.register(boom);
  return reg;
}

describe("dispatch", () => {
  it("prints --version alone", () => {
    const r = dispatch(["--version"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("prints --version envelope in json mode", () => {
    const r = dispatch(["--json", "--version"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("runs a registered command (text mode)", () => {
    const r = dispatch(["echo", "hi"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("runs a registered command (json mode) with envelope", () => {
    const r = dispatch(["--json", "echo", "hi"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("rejects unknown command with exit 2 (text)", () => {
    const r = dispatch(["nope"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });
  it("rejects unknown command with exit 2 (json envelope)", () => {
    const r = dispatch(["--json", "nope"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });
  it("surfaces usage errors as exit 2", () => {
    const r = dispatch(["fail"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });
  it("surfaces runtime errors as exit 1", () => {
    const r = dispatch(["boom"], registry(), VERSION);
    assert.equal(r.exitCode, 1);
  });
  it("rejects missing subcommand (json exit 2)", () => {
    const r = dispatch(["--json"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });

  it("subcommand --help is intercepted and exits 0 (text)", () => {
    const r = dispatch(["echo", "--help"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("subcommand -h is intercepted and exits 0 (json)", () => {
    const r = dispatch(["--json", "echo", "-h"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("rejects unknown long flag with exit 2 (text)", () => {
    const r = dispatch(["echo", "--definitely-invalid"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });
  it("rejects unknown long flag with exit 2 (json envelope)", () => {
    const r = dispatch(["--json", "echo", "--definitely-invalid"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });
  it("accepts known value flag and its value (not mistaken for a flag)", () => {
    const r = dispatch(["echo", "--msg", "--definitely-invalid"], registry(), VERSION);
    assert.equal(r.exitCode, 0);
  });
  it("rejects unknown flag even after a valid value flag", () => {
    const r = dispatch(["echo", "--msg", "hello", "--nope"], registry(), VERSION);
    assert.equal(r.exitCode, 2);
  });
});
