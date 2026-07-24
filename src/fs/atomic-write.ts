// Atomic file writes (phase 2.3), ported from application.write_text/write_json.
//
// Writes go to a same-directory temp file, fsync'd, then `os.replace`d onto the
// target so a crash or failure never leaves a half-written file (AC-13). The
// existing file mode is preserved; UTF-8 is enforced; a trailing newline is
// guaranteed.

import {
  chmodSync,
  closeSync,
  existsSync,
  fsyncSync,
  mkdirSync,
  openSync,
  readFileSync,
  renameSync,
  statSync,
  unlinkSync,
  writeSync,
} from "node:fs";
import { dirname, join, basename } from "node:path";

/** Read a UTF-8 file, returning `default` on any error (mirrors load_json). */
export function loadJson<T>(path: string, defaultValue: T): T {
  try {
    return JSON.parse(readFileSync(path, "utf8")) as T;
  } catch {
    return defaultValue;
  }
}

/** Atomic write of text with UTF-8 encoding and a guaranteed trailing newline. */
export function writeText(path: string, text: string): void {
  mkdirSync(dirname(path), { recursive: true });
  const content = text.replace(/\s+$/g, "") + "\n";
  const mode = existsSync(path) ? statSync(path).mode & 0o777 : 0o644;
  const tempPath = join(dirname(path), `.${basename(path)}.${process.pid}.${Date.now()}.tmp`);
  let fd: number | undefined;
  try {
    fd = openSync(tempPath, "w", 0o644);
    writeSync(fd, content, null, "utf8");
    fsyncSync(fd);
    closeSync(fd);
    fd = undefined;
    try {
      chmod(tempPath, mode);
    } catch {
      // chmod may be unsupported; best-effort, mirrors Python try/except OSError.
    }
    renameSync(tempPath, path); // atomic on POSIX and Windows
  } finally {
    if (fd !== undefined) {
      try {
        closeSync(fd);
      } catch {
        /* ignore */
      }
    }
    try {
      unlinkSync(tempPath);
    } catch {
      /* temp already renamed or removed */
    }
  }
}

/** Atomic write of JSON with UTF-8, no ASCII escaping, 2-space indent. */
export function writeJson(path: string, data: unknown): void {
  writeText(path, JSON.stringify(data, null, 2));
}

/**
 * Strict JSON read that raises a usage error on read/parse failure (mirrors
 * load_json_strict). The `label` is used in the error message.
 */
export function loadJsonStrict<T = Record<string, unknown>>(path: string, label: string): T {
  let payload: unknown;
  try {
    payload = JSON.parse(readFileSync(path, "utf8"));
  } catch {
    throw new StrictReadError(`${label}格式错误或无法读取，原文件未修改：${path}`);
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new StrictReadError(`${label}必须是 JSON 对象，原文件未修改：${path}`);
  }
  return payload as T;
}

export class StrictReadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "StrictReadError";
  }
}

// Best-effort chmod that tolerates platforms where it is a no-op.
function chmod(path: string, mode: number): void {
  try {
    chmodSync(path, mode);
  } catch {
    /* ignore */
  }
}
