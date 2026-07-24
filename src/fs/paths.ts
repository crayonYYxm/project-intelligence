// Path utilities: project-root resolution and cross-platform path normalization
// (phase 2.2). Mirrors Python application.project_root + PurePosixPath/PureWindows
// handling used to authorize paths across POSIX and Windows (AC-08).

import { resolve, isAbsolute, normalize, toNamespacedPath } from "node:path";
import { existsSync, statSync } from "node:fs";
import { UsageError } from "../errors.js";

/**
 * Resolve and validate the project root. Mirrors application.project_root:
 * default to cwd, expand ~, resolve to absolute, reject non-existent/non-dir.
 */
export function projectRoot(arg?: string | null): string {
  const root = resolve(expandUser(arg ?? process.cwd()));
  if (!existsSync(root) || !statSync(root).isDirectory()) {
    throw new UsageError(`项目路径不是目录：${root}`);
  }
  return root;
}

/** Expand a leading ~ to the home directory (Node has no built-in). */
export function expandUser(p: string): string {
  if (p === "~") return process.env.HOME ?? process.env.USERPROFILE ?? p;
  if (p.startsWith("~/") || p.startsWith("~\\")) {
    const home = process.env.HOME ?? process.env.USERPROFILE;
    return home ? home + p.slice(1) : p;
  }
  return p;
}

/** Convert any path separators (back- or forward slashes) to POSIX forward slashes,
 *  independent of the host platform. */
export function toPosix(p: string): string {
  return p.replace(/\\/g, "/");
}

/** Normalize a business path to forward slashes (matches requirements._business_path). */
export function normalizeBusinessPath(p: string): string {
  return toPosix(normalize(toNamespacedPath(p))).replace(/^\.\/+/, "");
}

/**
 * Detect whether a command string references an absolute path on either POSIX or
 * Windows (used to authorize graph/external commands). Mirrors
 * application.command_uses_external_path, preserving backslashes for Windows.
 */
export function isAbsolutePathLike(p: string): boolean {
  if (isAbsolute(p)) return true;
  // Windows drive: e.g. C:\ or C:/ — preserve detection across platforms.
  if (/^[a-zA-Z]:[\\/]/.test(p)) return true;
  // UNC \\server\share
  return p.startsWith("\\\\") || p.startsWith("//");
}

/**
 * Resolve a repository-relative path, rejecting path traversal outside root and
 * symlink hops for managed paths. Used by the data layer (phase 3) to keep
 * writes inside .project-intel.
 */
export function resolveInside(root: string, relative: string): string {
  const cleaned = relative.split("\\").join("/");
  const target = resolve(root, cleaned);
  const rootPosix = toPosix(root);
  const targetPosix = toPosix(target);
  if (targetPosix !== rootPosix && !targetPosix.startsWith(rootPosix + "/")) {
    throw new UsageError(`路径越界：${relative}`);
  }
  return target;
}
