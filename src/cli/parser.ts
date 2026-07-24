// CLI parser + dispatcher framework (phase 2.1).
//
// The Python CLI uses argparse with a JsonArgumentParser subclass that exits 2 on
// usage errors. This module provides an equivalent, command-registry-based parser
// that handles the global options (--project, --version, --json) and subcommand
// dispatch, surfacing usage errors as exit code 2 (AC-03).
//
// Per-flag help/mutual-exclusion fidelity is layered in as each subcommand is
// registered in phases 3.x; the parser here is the shared backbone.

import { EXIT_SUCCESS, EXIT_USAGE, UsageError } from "../errors.js";

/** Result of parsing global options that precede the subcommand. */
export interface GlobalOptions {
  project: string | null;
  /** Resolved absolute project root (filled in by the dispatcher). */
  projectRoot?: string;
  jsonMode: boolean;
}

export interface ParsedCommand {
  command: string;
  args: string[];
  global: GlobalOptions;
}

/**
 * Parse the leading global options. The Python CLI accepts --project anywhere
 * (argparse parses it at the top-level parser), and --json is suppressed and
 * stripped before parsing. --version is handled by the dispatcher when it is the
 * sole token. Unknown top-level options that look like flags are left for the
 * subcommand parser; a bare unknown long option before a subcommand is a usage
 * error.
 */
export function parseGlobal(argv: readonly string[]): GlobalOptions {
  let project: string | null = null;
  let jsonMode = false;
  const known = new Set(["--project", "--version", "--json", "-h", "--help"]);
  for (let i = 0; i < argv.length; i++) {
    const tok = argv[i];
    if (tok === undefined) continue;
    if (tok === "--json") {
      jsonMode = true;
      continue;
    }
    if (tok === "--project") {
      const next = argv[i + 1];
      if (next === undefined) throw new UsageError("--project 需要一个参数");
      project = next;
      i++;
      continue;
    }
    if (tok.startsWith("--project=")) {
      project = tok.slice("--project=".length);
      continue;
    }
    // Stop scanning global options once we reach the first positional (subcommand).
    if (!tok.startsWith("-")) break;
    // An unknown long option before the subcommand is a usage error, matching
    // argparse's top-level rejection (e.g. --nope -> exit 2).
    if (tok.startsWith("--") && !known.has(tok)) {
      throw new UsageError(`无法识别的参数：${tok}`);
    }
  }
  return { project, jsonMode };
}

/**
 * Split argv into global options + (command, rest). Returns null when no
 * subcommand was given (the caller renders help and exits 0, or errors).
 */
export function splitArgv(argv: readonly string[]): ParsedCommand | null {
  const global = parseGlobal(argv);
  // Find the first positional (the subcommand name).
  let command: string | null = null;
  let rest: string[] = [];
  let seenCommand = false;
  for (let i = 0; i < argv.length; i++) {
    const tok = argv[i];
    if (tok === undefined || tok === "--json") continue;
    if (tok === "--project") {
      i++; // skip value
      continue;
    }
    if (tok.startsWith("--project=")) continue;
    if (!tok.startsWith("-") && !seenCommand) {
      command = tok;
      seenCommand = true;
      rest = argv.slice(i + 1).filter((t) => t !== "--json");
      break;
    }
  }
  if (command === null) return null;
  return { command, args: rest, global };
}

/** A registered subcommand handler. */
export interface CommandHandler {
  /** Canonical command name. */
  name: string;
  /** One-line help summary. */
  help: string;
  /**
   * Accepted long flags for this command (e.g. `--requirement-id`). When
   * present, the dispatcher rejects any unrecognized `--flag` with exit 2,
   * matching argparse's behavior. Subcommand positionals (the first non-`--`
   * token) are always allowed.
   */
  knownFlags?: Set<string>;
  /**
   * Flags that consume the next token as their value (e.g.
   * `--requirement-id <id>`). The dispatcher skips these values during
   * unknown-flag validation so they are not mistaken for flags.
   */
  valueFlags?: Set<string>;
  /**
   * When true, the handler prints its own text-mode output (via print/console).
   * When false (default), the dispatcher prints the returned `result` as
   * indented JSON in text mode. This mirrors Python: each command prints its
   * own output; the result dict is only surfaced in the JSON envelope.
   */
  selfPrinting?: boolean;
  /** Parse + run the command; return an exit code. Throws UsageError/RuntimeError. */
  run(args: string[], global: GlobalOptions): Promise<CommandResult> | CommandResult;
}

export interface CommandResult {
  exitCode: number;
  /** Structured result, surfaced in the JSON envelope's `result` field. */
  result?: unknown;
}

/** Registry of top-level commands (populated in phases 3.x). */
export class CommandRegistry {
  private readonly commands = new Map<string, CommandHandler>();

  register(handler: CommandHandler): void {
    this.commands.set(handler.name, handler);
  }

  get(name: string): CommandHandler | undefined {
    return this.commands.get(name);
  }

  names(): string[] {
    return [...this.commands.keys()].sort();
  }

  has(name: string): boolean {
    return this.commands.has(name);
  }
}

/** Exit code helper for the success path. */
export function ok(result?: unknown): CommandResult {
  return { exitCode: EXIT_SUCCESS, result };
}

/** Render a usage-error message and return the code (callers may throw instead). */
export function usageFailure(): number {
  return EXIT_USAGE;
}
