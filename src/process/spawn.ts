// Subprocess layer (phase 2.5).
//
// Two execution paths, mirroring application.run (argv form) and run_shell
// (shell form). The argv path is used for tools invoked with explicit argument
// arrays (git, npm package commands); the shell path preserves compatibility
// with user-configured quality/test/graph commands that rely on env vars,
// quotes, pipes, redirects, and compound commands (run_shell, shell=True).
//
// Exit-code contract (AC-03): tool-missing -> 127, timeout -> 124 (shell) /
// 127 (argv, matching Python run which catches both FileNotFoundError and
// TimeoutExpired as 127). Output is captured as UTF-8 and stripped.

import { spawnSync } from "node:child_process";
import { accessSync, constants } from "node:fs";
import { delimiter, dirname, isAbsolute, join } from "node:path";
import { EXIT_NOT_FOUND, EXIT_TIMEOUT } from "../errors.js";

export interface RunResult {
  code: number;
  stdout: string;
  stderr: string;
}

/**
 * Run an argv-form command. Mirrors application.run: FileNotFoundError and
 * TimeoutExpired both map to 127, output stripped.
 */
export function run(cmd: readonly string[], cwd: string, timeoutMs = 30_000): RunResult {
  try {
    const proc = spawnSync(cmd[0] ?? "", cmd.slice(1), {
      cwd,
      encoding: "utf8",
      timeout: timeoutMs,
      windowsHide: true,
    });
    if (proc.error) {
      // ENOENT (binary not found) -> 127, matching Python FileNotFoundError.
      return { code: EXIT_NOT_FOUND, stdout: "", stderr: String(proc.error) };
    }
    return {
      code: proc.status ?? -1,
      stdout: (proc.stdout ?? "").trim(),
      stderr: (proc.stderr ?? "").trim(),
    };
  } catch (err) {
    // Synchronous spawn failures (incl. timeout surfaced as an error on some
    // platforms) collapse to 127 to match Python run's combined except clause.
    return { code: EXIT_NOT_FOUND, stdout: "", stderr: String(err) };
  }
}

/**
 * Check whether a command is resolvable on PATH (mirrors shutil.which). On
 * Windows, PATHEXT is honored so `npm` resolves to `npm.cmd`.
 */
export function commandExists(name: string): boolean {
  return which(name) !== null;
}

/**
 * Return the absolute path of `name` on PATH, or null when not found. Mirrors
 * shutil.which including Windows PATHEXT extension probing.
 */
export function which(name: string): string | null {
  if (name.includes("\0")) return null;
  // Absolute or relative path with a directory component: check directly.
  if (isAbsolute(name) || name.includes("/") || name.includes("\\")) {
    try {
      accessSync(name, constants.X_OK);
      return name;
    } catch {
      return tryWithExtensions(name);
    }
  }
  const pathEnv = process.env.PATH ?? "";
  const exts = process.platform === "win32" ? (process.env.PATHEXT ?? ".EXE;.CMD;.BAT").split(";") : [""];
  for (const dir of pathEnv.split(delimiter)) {
    if (!dir) continue;
    for (const ext of exts) {
      const candidate = join(dir, name + ext);
      try {
        accessSync(candidate, constants.X_OK);
        return candidate;
      } catch {
        /* try next */
      }
    }
  }
  return null;
}

function tryWithExtensions(base: string): string | null {
  if (process.platform !== "win32") return null;
  const exts = (process.env.PATHEXT ?? ".EXE;.CMD;.BAT").split(";");
  for (const ext of exts) {
    const candidate = base + ext;
    try {
      accessSync(candidate, constants.X_OK);
      return candidate;
    } catch {
      /* next */
    }
  }
  return null;
}

/** Resolve the parent directory of a path (helper used by callers). */
export function parentDir(p: string): string {
  return dirname(p);
}

export { EXIT_TIMEOUT };
