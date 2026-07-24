// JSON envelope + error-text sanitization, ported from cli.py.
//
// Every `--json` response is wrapped in a fixed-shape envelope
// {ok, command, status, exitCode, error, result, output} so machine callers get
// a stable contract (AC-03). Error text is sanitized to redact credentials.

import { EXIT_SUCCESS, EXIT_USAGE } from "../errors.js";

interface ErrorPayload {
  code: string;
  message: string;
}

export interface JsonEnvelope {
  ok: boolean;
  command: string;
  status: "ok" | "failed";
  exitCode: number;
  error: ErrorPayload | null;
  result: unknown;
  output: string;
}

const SANITIZE_PATTERNS: ReadonlyArray<[RegExp, string]> = [
  [/(authorization\s*[:=]\s*)(bearer\s+)?[^\s,;]+/gi, "$1[REDACTED]"],
  [/(cookie\s*[:=]\s*)[^\n]+/gi, "$1[REDACTED]"],
  [/(token|access_token|refresh_token|password|secret|api_key)(\s*[:=]\s*)[^\s,;]+/gi, "$1$2[REDACTED]"],
  [/(aws_access_key_id|aws_secret_access_key)(\s*[:=]\s*)[^\s,;]+/gi, "$1$2[REDACTED]"],
  [/:\/\/([^:/\s]+):([^@\s]+)@/g, "://[REDACTED]:[REDACTED]@"],
];

/** Redact credentials/secrets from error text so they never reach JSON output. */
export function sanitizeErrorText(value: unknown): string {
  let text = String(value ?? "");
  for (const [pattern, replacement] of SANITIZE_PATTERNS) {
    text = text.replace(pattern, replacement);
  }
  return text;
}

/**
 * Strip the suppressed `--json` global flag from argv (it may appear before the
 * subcommand) and report whether json mode was requested. Mirrors
 * cli.extract_global_json.
 */
export function extractGlobalJson(argv: readonly string[]): { argv: string[]; jsonMode: boolean } {
  const jsonMode = argv.includes("--json");
  return { argv: argv.filter((item) => item !== "--json"), jsonMode };
}

/**
 * Build the response envelope. Mirrors cli.json_envelope, including the
 * USAGE_ERROR vs COMMAND_FAILED classification and in-place error sanitization
 * when result is a dict carrying an `error` key.
 */
export function jsonEnvelope(
  command: string,
  exitCode: number,
  result: unknown = null,
  output = ""
): JsonEnvelope {
  const ok = exitCode === EXIT_SUCCESS;
  let error: ErrorPayload | null = null;
  let normalizedResult = result;
  if (!ok) {
    if (result && typeof result === "object" && !Array.isArray(result) && "error" in (result as Record<string, unknown>)) {
      const dict = { ...(result as Record<string, unknown>) };
      const message = sanitizeErrorText(String(dict.error ?? "command failed"));
      dict.error = message;
      normalizedResult = dict;
      error = { code: exitCode === EXIT_USAGE ? "USAGE_ERROR" : "COMMAND_FAILED", message };
    } else {
      error = { code: exitCode === EXIT_USAGE ? "USAGE_ERROR" : "COMMAND_FAILED", message: "command failed" };
    }
  }
  return {
    ok,
    command,
    status: ok ? "ok" : "failed",
    exitCode,
    error,
    result: normalizedResult,
    output: output.trim(),
  };
}
