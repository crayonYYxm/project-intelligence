// Per-command flag specifications (phase 3.H / P1 fix).
//
// Mirrors the Python argparse definitions in application.py so the dispatcher
// can reject unrecognized `--flag` arguments with exit 2, matching argparse's
// behavior. Each command maps to:
//   - knownFlags: every accepted long option (including value-taking ones).
//   - valueFlags: the subset that consumes the next token as a value
//     (so the dispatcher skips it during validation).
//
// Boolean flags (store_true) appear only in knownFlags; value flags appear in
// both sets. Commands not listed here are not validated (the handler is trusted
// to surface its own usage errors), which keeps the migration incremental.

function set(...flags: string[]): Set<string> {
  return new Set(flags);
}

/** Flags that take a value as the next token. */
export const VALUE_FLAGS: Record<string, Set<string>> = {
  intake: set("--task", "--requirement-id", "--requirement-name", "--ticket-kind", "--external-api", "--requirement-action", "--requirement-path", "--design-action", "--design-path", "--track"),
  spec: set("--requirement-id", "--criterion", "--title", "--from", "--track"),
  plan: set("--requirement-id", "--title", "--from-spec", "--track"),
  lifecycle: set("--task", "--requirement-id", "--track", "--test-kind", "--report-action", "--report-path", "--acceptance"),
  debug: set("--bug"),
  test: set("--task", "--requirement-id", "--test-kind", "--report-action", "--report-path", "--acceptance", "--phase", "--command", "--files", "--expect-failure", "--manual-evidence", "--manual-category", "--manual-reason", "--manual-steps", "--manual-input", "--manual-observation", "--manual-evidence-path"),
  review: set("--requirement-id", "--result", "--summary", "--finding", "--files"),
  finish: set("--task", "--requirement-id", "--files", "--manual-evidence"),
  maintain: set("--task", "--requirement-id", "--files"),
  requirements: set("--task", "--files"),
  query: set("--search", "--query"),
  "graph-tools": set(),
  doctor: set(),
  init: set(),
  refresh: set(),
  check: set(),
  install: set(),
  adapters: set("--target"),
  agent: set("--target"),
};

/** Boolean (store_true) flags that take no value. */
export const BOOL_FLAGS: Record<string, Set<string>> = {
  intake: set("--write", "--legacy"),
  spec: set("--legacy"),
  plan: set("--replace", "--legacy"),
  lifecycle: set("--write", "--legacy"),
  debug: set("--write", "--legacy"),
  test: set("--project-wide", "--manual-approved", "--legacy"),
  review: set("--dry-run"),
  finish: set("--run-quality", "--dry-run", "--legacy"),
  maintain: set("--run-quality", "--archive", "--dry-run", "--legacy"),
  requirements: set("--legacy"),
  query: set(),
  "graph-tools": set(),
  doctor: set(),
  init: set("--interactive", "--setup-missing", "--with-graph", "--no-graph", "--allow-repo-runner", "--allow-env-command", "--allow-external-path", "--strict", "--dry-run"),
  refresh: set("--with-graph", "--allow-repo-runner", "--allow-env-command", "--allow-external-path", "--adapters"),
  check: set("--run-quality", "--dry-run"),
  install: set("--hooks", "--activate-git-hooks", "--allow-external-hooks"),
  adapters: set("--check"),
  agent: set("--dry-run"),
};

/** Build the complete knownFlags set (value + boolean) for a command. */
export function knownFlagsFor(command: string): Set<string> | undefined {
  const value = VALUE_FLAGS[command];
  const bool = BOOL_FLAGS[command];
  if (!value && !bool) return undefined;
  return new Set([...(value ?? []), ...(bool ?? [])]);
}

/** The value-taking flags for a command (for the dispatcher's skip logic). */
export function valueFlagsFor(command: string): Set<string> {
  return VALUE_FLAGS[command] ?? new Set();
}
