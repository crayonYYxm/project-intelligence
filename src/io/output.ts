// UTF-8 output layer (phase 2.6).
//
// The Python CLI relies on `text=True`/`encoding="utf-8"` and, on Windows, the
// console code page. To guarantee Chinese error messages and JSON render
// correctly across platforms (AC-08), this module writes through
// `process.stdout`/`process.stderr` so that:
//   - in JSON mode the dispatcher can replace `process.stdout.write` to capture
//     all output into the envelope (P1 fix: previously `writeSync(fd, …)` bypassed
//     the capture, leaking non-JSON text before the envelope),
//   - in text mode the bytes are written directly to the fd as UTF-8 (Node.js
//     encodes strings as UTF-8; `ensureUtf8Console` sets Windows CP 65001).

import { spawnSync } from "node:child_process";

/** Print a line to stdout, UTF-8, with a trailing newline. */
export function print(text = ""): void {
  process.stdout.write(text + "\n");
}

/** Print a line to stderr, UTF-8, with a trailing newline. */
export function printError(text = ""): void {
  process.stderr.write(text + "\n");
}

/** Render a value as pretty JSON (UTF-8, no ASCII escaping) and print. */
export function printJson(value: unknown): void {
  process.stdout.write(JSON.stringify(value, null, 2) + "\n");
}

/**
 * Ensure stdout/stderr are treated as UTF-8. On Windows, configure the process
 * console to UTF-8 (CP 65001) when possible so inherited shells/children also
 * render Chinese correctly. Called once at process startup.
 */
export function ensureUtf8Console(): void {
  if (process.platform !== "win32") return;
  // chcp 65001 best-effort; ignore failures (non-Windows already UTF-8 capable).
  try {
    spawnSync("chcp", ["65001"], { shell: true, stdio: "ignore" });
  } catch {
    /* non-fatal */
  }
}
