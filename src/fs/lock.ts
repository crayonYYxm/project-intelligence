// Cross-process file lock for requirement archives (phase 2.4), ported from
// requirements._RequirementLock.
//
// Uses an exclusive-create lockfile (O_CREAT|O_EXCL equivalent: openSync with
// "x" flag) written in the requirement directory's PARENT (not under by-id/, so
// Windows can move a legacy directory while the requirement stays locked). Holds
// the lock with a 5s timeout and a 60s stale-lock reaper. Contention raises
// RequirementError (exit 2) — same as Python.

import { closeSync, mkdirSync, openSync, statSync, unlinkSync, writeSync } from "node:fs";
import { dirname, join, basename } from "node:path";
import { RequirementError } from "../errors.js";

const DEFAULT_TIMEOUT_MS = 5000;
const STALE_MS = 60_000;
const POLL_MS = 20;

export interface LockOptions {
  /** Acquire timeout in milliseconds (default 5000). */
  timeoutMs?: number;
  /** Lockfile name suffix (default ".manifest.lock"). */
  filename?: string;
}

/**
 * Acquire an exclusive lock on `directory` for the duration of `fn`, then release.
 * The lockfile lives in the directory's grandparent when the parent is `by-id`
 * (mirrors Python exactly, for Windows move semantics).
 */
export function withLock<T>(directory: string, fn: () => T, options: LockOptions = {}): T {
  const timeout = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const filename = options.filename ?? ".manifest.lock";
  const parent = dirname(directory);
  const lockParent = basename(parent) === "by-id" ? dirname(parent) : parent;
  const lockPath = join(lockParent, `.${basename(directory)}${filename}`);

  mkdirSync(lockParent, { recursive: true });

  const deadline = Date.now() + timeout;
  let fd: number | undefined;
  // Exclusive create loop with stale-lock reaping.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      // O_CREAT | O_EXCL | O_WRONLY, mode 0o600 — the "wx" flag is exclusive.
      fd = openSync(lockPath, "wx", 0o600);
      writeSync(fd, `${process.pid}\n`, null, "ascii");
      break;
    } catch (err) {
      const code = (err as NodeJS.ErrnoException).code;
      if (code !== "EEXIST") {
        throw err;
      }
      // Stale-lock reaper: if the lockfile is older than STALE_MS, remove & retry.
      try {
        if (Date.now() - statSync(lockPath).mtimeMs > STALE_MS) {
          unlinkSync(lockPath);
          continue;
        }
      } catch {
        // lockfile vanished between stat and unlink; retry
        continue;
      }
      if (Date.now() >= deadline) {
        throw new RequirementError(`需求档案正被其他任务更新：${basename(lockParent)}`);
      }
      // Busy-wait POLL_MS. Atomics.wait is not available in the main thread, so
      // sleep via a synchronous spin against Date.now().
      sleepSync(POLL_MS);
    }
  }
  try {
    return fn();
  } finally {
    if (fd !== undefined) {
      try {
        closeSync(fd);
      } catch {
        /* ignore */
      }
    }
    try {
      unlinkSync(lockPath);
    } catch {
      /* already removed */
    }
  }
}

/** Synchronous sleep (used by the lock poll loop). */
function sleepSync(ms: number): void {
  const target = Date.now() + ms;
  while (Date.now() < target) {
    /* spin */
  }
}
