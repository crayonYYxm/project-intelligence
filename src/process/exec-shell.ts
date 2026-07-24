// Shell-form execution (phase 2.5), mirroring application.run_shell (shell=True).
//
// Used for user-configured quality/test/graph commands that depend on shell
// features: environment variables, quoting, pipes, redirects, and compound
// commands (`&&`, `;`). Unlike the argv path, timeouts map to 124 (matching
// Python run_shell), and the command string is passed to the platform shell.

import { spawnSync } from "node:child_process";
import { EXIT_TIMEOUT } from "../errors.js";
import type { RunResult } from "./spawn.js";

/**
 * Run a shell command string. Mirrors application.run_shell: TimeoutExpired ->
 * exit 124, output captured and stripped. The shell is `sh -c` on POSIX and
 * `cmd /d /s /c` on Windows (Node's default when shell:true).
 */
export function runShell(command: string, cwd: string, timeoutMs = 120_000): RunResult {
  try {
    const proc = spawnSync(command, {
      cwd,
      encoding: "utf8",
      timeout: timeoutMs,
      shell: true,
      windowsHide: true,
    });
    if (proc.error) {
      const code = (proc.error as NodeJS.ErrnoException).code;
      return { code: code === "ETIMEDOUT" ? EXIT_TIMEOUT : 127, stdout: "", stderr: String(proc.error) };
    }
    // A timed-out spawn surfaces status null + signal 'SIGTERM' on most platforms.
    if (proc.signal === "SIGTERM" && proc.status === null) {
      return { code: EXIT_TIMEOUT, stdout: "", stderr: "command timed out" };
    }
    return {
      code: proc.status ?? -1,
      stdout: (proc.stdout ?? "").trim(),
      stderr: (proc.stderr ?? "").trim(),
    };
  } catch (err) {
    return { code: 127, stdout: "", stderr: String(err) };
  }
}
