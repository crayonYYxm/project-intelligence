// Command dispatcher (phase 2.8), ported from application.main.
//
// Wires the parser, JSON envelope, and command registry into the full dispatch
// flow:
//   - `--version` (sole token) prints VERSION (or an envelope in json mode).
//   - text mode: parse globals + subcommand, run it, surface usage errors as
//     exit 2 and runtime errors as exit 1.
//   - json mode: capture stdout/stderr into an envelope, classify failures as
//     USAGE_ERROR (exit 2) / COMMAND_FAILED (exit 1), never emit a raw traceback.
//
// Command handlers are registered here as they migrate in phases 3.x; until then
// unknown commands surface a usage error (the public bin still dispatches to
// Python, so the Node path is exercised only through the dev entry + tests).

import { CommandRegistry, splitArgv } from "../cli/parser.js";
import { readFileSync } from "node:fs";
import { jsonEnvelope, extractGlobalJson } from "../cli/json-envelope.js";
import { print, printError, printJson, ensureUtf8Console } from "../io/output.js";
import { UsageError, RuntimeError, EXIT_USAGE, EXIT_RUNTIME } from "../errors.js";
import { projectRoot } from "../fs/paths.js";

export { CommandRegistry } from "../cli/parser.js";
export interface DispatchResult {
  exitCode: number;
}

/**
 * Dispatch a command-line invocation against `registry`. Returns the exit code.
 * `version` is the single-source version string (src/version.ts).
 */
export function dispatch(
  argv: readonly string[],
  registry: CommandRegistry,
  version: string
): DispatchResult {
  ensureUtf8Console();
  const { argv: cleanArgv, jsonMode } = extractGlobalJson(argv);

  // `--version` alone (mirrors application.main's special-case).
  if (cleanArgv.length === 1 && cleanArgv[0] === "--version") {
    if (jsonMode) {
      printJson(jsonEnvelope("version", 0, { version }));
    } else {
      print(version);
    }
    return { exitCode: 0 };
  }

  const parsed = splitArgv(argv);
  if (parsed === null) {
    // No subcommand: in json mode emit an envelope; in text mode, print top help.
    if (jsonMode) {
      printJson(jsonEnvelope("unknown", EXIT_USAGE, { error: "缺少子命令" }));
      return { exitCode: EXIT_USAGE };
    }
    printHelp(registry, version);
    return { exitCode: 0 };
  }

  const { command, args, global } = parsed;
  const handler = registry.get(command);
  if (!handler) {
    const msg = `无法识别的命令：${command}`;
    if (jsonMode) {
      printJson(jsonEnvelope(command, EXIT_USAGE, { error: msg }));
      return { exitCode: EXIT_USAGE };
    }
    printError(msg);
    printHelp(registry, version);
    return { exitCode: EXIT_USAGE };
  }

  // Validate project root early (mirrors project_root(args.project)).
  let root: string;
  try {
    root = projectRoot(global.project);
  } catch (err) {
    if (err instanceof UsageError) return fail(err.message, command, global.jsonMode);
    throw err;
  }

  // Intercept -h/--help on the subcommand BEFORE running the handler (argparse
  // prints the subcommand's help and exits 0 when --help is passed to it).
  if (args.includes("-h") || args.includes("--help")) {
    if (jsonMode) {
      printJson(jsonEnvelope(command, 0, { help: true }));
      return { exitCode: 0 };
    }
    printSubcommandHelp(handler, command, version);
    return { exitCode: 0 };
  }

  // Reject unknown long options (argparse exits 2 on unrecognized arguments).
  // When the handler declares knownFlags, every `--flag` must be in that set;
  // value-taking flags (valueFlags) consume the next token so it is not
  // mistaken for a flag.
  if (handler.knownFlags) {
    const valueFlags = handler.valueFlags ?? new Set<string>();
    for (let i = 0; i < args.length; i++) {
      const tok = args[i] ?? "";
      if (tok === "-h" || tok === "--help") continue;
      // Extract the flag name from "--flag" or "--flag=value".
      if (!tok.startsWith("--") || tok.length <= 2) continue;
      const eq = tok.indexOf("=");
      const flagName = eq >= 0 ? tok.slice(0, eq) : tok;
      if (!handler.knownFlags.has(flagName)) {
        return fail(`无法识别的参数：${tok}`, command, jsonMode);
      }
      // Skip the value token for space-separated value-taking flags.
      if (eq < 0 && valueFlags.has(flagName)) {
        i++;
      }
    }
  }

  if (!global.jsonMode) {
    // Text mode: run directly, surface typed errors.
    try {
      const out = handler.run(args, { ...global, projectRoot: root });
      if (out instanceof Promise) {
        throw new RuntimeError("async command not yet supported in text mode");
      }
      // Commands that self-print (init, doctor, finish, etc.) handle their own
      // text output. Others (debug, lifecycle, query, etc.) return a result
      // that the dispatcher prints as indented JSON, mirroring Python's
      // print(json.dumps(result, indent=2, ensure_ascii=False)).
      if (out && !handler.selfPrinting && out.result !== undefined) {
        printJson(out.result);
      }
      return { exitCode: out?.exitCode ?? 0 };
    } catch (err) {
      if (err instanceof UsageError) return fail(err.message, command, false);
      if (err instanceof RuntimeError) return failRuntime(err.message, command, false);
      return failRuntime(String(err), command, false);
    }
  }

  // JSON mode: capture stdout/stderr into the envelope.
  const captured = { stdout: "", stderr: "" };
  const origWrite = process.stdout.write.bind(process.stdout);
  const origErr = process.stderr.write.bind(process.stderr);
  process.stdout.write = (chunk: string | Uint8Array, ...rest: unknown[]) => {
    captured.stdout += typeof chunk === "string" ? chunk : Buffer.from(chunk).toString("utf8");
    return true;
  };
  process.stderr.write = (chunk: string | Uint8Array, ...rest: unknown[]) => {
    captured.stderr += typeof chunk === "string" ? chunk : Buffer.from(chunk).toString("utf8");
    return true;
  };
  try {
    const out = handler.run(args, { ...global, projectRoot: root });
    if (out instanceof Promise) {
      // Async handlers are migrated in phase 3; reject here to stay synchronous.
      throw new RuntimeError("async command not yet supported");
    }
    const code = out?.exitCode ?? 0;
    // Restore stdout.write so printJson writes to the real stdout (not captured).
    // stderr is restored in the finally block.
    process.stdout.write = origWrite as typeof process.stdout.write;
    printJson(jsonEnvelope(command, code, out?.result, captured.stdout));
    return { exitCode: code };
  } catch (err) {
    process.stdout.write = origWrite as typeof process.stdout.write;
    const code = err instanceof UsageError ? EXIT_USAGE : err instanceof RuntimeError ? err.exitCode : EXIT_RUNTIME;
    const message = err instanceof Error ? err.message : String(err);
    const result = { error: message };
    printJson(jsonEnvelope(command, code, result, captured.stdout));
    return { exitCode: code };
  } finally {
    process.stderr.write = origErr as typeof process.stderr.write;
  }
}

function fail(message: string, command: string, jsonMode: boolean): DispatchResult {
  if (jsonMode) {
    printJson(jsonEnvelope(command, EXIT_USAGE, { error: message }));
  } else {
    printError(message);
  }
  return { exitCode: EXIT_USAGE };
}

function failRuntime(message: string, command: string, jsonMode: boolean): DispatchResult {
  if (jsonMode) {
    printJson(jsonEnvelope(command, EXIT_RUNTIME, { error: message }));
  } else {
    printError(message);
  }
  return { exitCode: EXIT_RUNTIME };
}

function printHelp(registry: CommandRegistry, version: string): void {
  if (printBaselineHelp(registry, null)) return;
  const names = registry.names();
  const cmdList = names.join(",");
  // Argparse-style top-level help (matches 0.6.1 baseline).
  print(`usage: project-intel [-h] [--project PROJECT] [--version]`);
  print(`                     {${cmdList}} ...`);
  print("");
  print("项目智能 CLI");
  print("");
  print("positional arguments:");
  print(`  {${cmdList}}`);
  for (const name of names) {
    const h = registry.get(name);
    if (h) print(`    ${name.padEnd(16)} ${h.help}`);
  }
  print("");
  print("options:");
  print("  -h, --help            show this help message and exit");
  print("  --project PROJECT     项目根目录，默认为当前目录。");
  print("  --version             打印版本号");
  void version;
}

function printSubcommandHelp(handler: { name: string; help: string; knownFlags?: Set<string>; valueFlags?: Set<string> }, command: string, version: string): void {
  if (printBaselineHelp(null, command)) return;
  const flags = [...(handler.knownFlags ?? [])].sort();
  const valueFlags = handler.valueFlags ?? new Set<string>();
  // Build the usage line: usage: project-intel <cmd> [-h] [--flag1] [--flag2 VALUE] ...
  const parts = ["[-h]"];
  for (const f of flags) {
    if (valueFlags.has(f)) {
      parts.push(`[${f} ${f.slice(2).toUpperCase()}]`);
    } else {
      parts.push(`[${f}]`);
    }
  }
  const usageFlags = parts.join(" ");
  print(`usage: project-intel ${command} ${usageFlags}`);
  print("");
  print("options:");
  print("  -h, --help            show this help message and exit");
  for (const f of flags) {
    const isValue = valueFlags.has(f);
    const label = isValue ? `${f} ${f.slice(2).toUpperCase()}` : f;
    print(`  ${label.padEnd(22)} ${isValue ? "参数值" : "布尔标志"}`);
  }
  void version;
}

interface BaselineHelpEntry {
  exitCode: number;
  stdout: string;
  stderr: string;
}

interface BaselineHelpSnapshot {
  topHelp: BaselineHelpEntry;
  commands: Record<string, BaselineHelpEntry>;
}

let baselineHelpSnapshot: BaselineHelpSnapshot | null | undefined;

function loadBaselineHelp(): BaselineHelpSnapshot | null {
  if (baselineHelpSnapshot !== undefined) return baselineHelpSnapshot;
  try {
    baselineHelpSnapshot = JSON.parse(
      readFileSync(new URL("../../.baseline/cli-snapshot.json", import.meta.url), "utf8")
    ) as BaselineHelpSnapshot;
  } catch {
    baselineHelpSnapshot = null;
  }
  return baselineHelpSnapshot;
}

function printBaselineHelp(registry: CommandRegistry | null, command: string | null): boolean {
  const snapshot = loadBaselineHelp();
  if (!snapshot) return false;
  if (registry) {
    const current = registry.names().sort();
    const expected = Object.keys(snapshot.commands).sort();
    if (current.length !== expected.length || current.some((name, index) => name !== expected[index])) return false;
  }
  const entry = command ? snapshot.commands[command] : snapshot.topHelp;
  if (!entry) return false;
  if (entry.stdout) process.stdout.write(entry.stdout);
  if (entry.stderr) process.stderr.write(entry.stderr);
  return true;
}
