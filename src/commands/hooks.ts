// Git Hook generation + activation (phase 3.C.4), ported from
// application.hook_script_body / write_hook_templates / activate_git_hooks.
//
// Per the migration requirement (AC-07): generated hook bodies call the npm
// package's Node CLI (via the bin name `project-intel`), NOT python3. The hook
// skips when PROJECT_INTEL_SKIP_HOOKS=1 and is best-effort (|| true).

import { existsSync, lstatSync, mkdirSync, readFileSync, writeFileSync, chmodSync, realpathSync } from "node:fs";
import { join } from "node:path";
import { run } from "../process/spawn.js";
import { projectIntelDir } from "./init.js";

export const PROJECT_INTEL_HOOK_MARKER = "# Project Intelligence hook";

const HOOK_NAMES = ["post-merge", "post-commit", "pre-push"];

/**
 * The hook body for `hook_name`. Calls the Node CLI `project-intel` (not python3)
 * for refresh + check, best-effort. Mirrors hook_script_body minus the python3
 * dependency.
 */
export function hookScriptBody(hookName: string): string {
  return [
    "#!/bin/sh",
    `${PROJECT_INTEL_HOOK_MARKER}: ${hookName}`,
    "",
    'if [ "${PROJECT_INTEL_SKIP_HOOKS:-0}" = "1" ]; then',
    "  exit 0",
    "fi",
    "",
    "if command -v project-intel >/dev/null 2>&1; then",
    "  PROJECT_INTEL_SKIP_HOOKS=1 project-intel refresh >/dev/null 2>&1 || true",
    "  PROJECT_INTEL_SKIP_HOOKS=1 project-intel check >/dev/null 2>&1 || true",
    "fi",
    "",
  ].join("\n");
}

/** Write optional hook templates under .project-intel/hooks/ (mirrors write_hook_templates). */
export function writeHookTemplates(root: string): string[] {
  const hooksDir = join(projectIntelDir(root), "hooks");
  mkdirSync(hooksDir, { recursive: true });
  const written: string[] = [];
  for (const name of HOOK_NAMES) {
    const path = join(hooksDir, `${name}.sh`);
    writeFileSync(path, hookScriptBody(name), "utf8");
    try {
      chmodSync(path, 0o755);
    } catch {
      /* chmod best-effort (no-op on some platforms) */
    }
    written.push(path);
  }
  writeFileSync(
    join(hooksDir, "README.md"),
    [
      "# 项目智能钩子",
      "",
      "这些钩子模板是可选的。只有在 `project-intel install --hooks --activate-git-hooks` 将包装器安装到 `.git/hooks` 后才会激活。",
      "",
      "设置 `PROJECT_INTEL_SKIP_HOOKS=1` 可跳过钩子执行。",
      "",
    ].join("\n"),
    "utf8"
  );
  return written;
}

/** Resolve the git hooks directory (mirrors git_hooks_path). */
export function gitHooksPath(root: string): string | null {
  const r = run(["git", "rev-parse", "--git-path", "hooks"], root, 20);
  if (r.code === 0 && r.stdout) {
    const p = r.stdout.replace(/^~/, process.env.HOME ?? "~");
    const resolved = existsSync(p) ? realpathSync(p) : join(root, p);
    return resolved;
  }
  const fallback = join(root, ".git", "hooks");
  return existsSync(fallback) ? fallback : null;
}

/** Activate hook wrappers into .git/hooks (mirrors activate_git_hooks). */
export function activateGitHooks(root: string, allowExternal = false): Record<string, unknown>[] {
  const gitHooks = gitHooksPath(root);
  if (!gitHooks || !existsSync(gitHooks)) {
    return [{ hook: "*", status: "skipped", detail: "未找到 .git/hooks 目录。" }];
  }
  if (lstatSync(gitHooks).isSymbolicLink()) {
    throw new Error("Git hooks 路径不能是符号链接。");
  }
  const gitDirRaw = run(["git", "rev-parse", "--git-dir"], root, 20).stdout;
  if (gitDirRaw) {
    const gitDir = existsSync(gitDirRaw) && !gitDirRaw.startsWith("/") ? join(root, gitDirRaw) : gitDirRaw;
    const expected = join(gitDir, "hooks");
    if (!allowExternal && realpathSync(gitHooks) !== realpathSafe(expected)) {
      throw new Error("Git core.hooksPath 指向仓库外目录；默认拒绝写入。若确实需要，请显式传入 --allow-external-hooks。");
    }
  }
  mkdirSync(gitHooks, { recursive: true });
  const results: Record<string, unknown>[] = [];
  for (const name of HOOK_NAMES) {
    const target = join(gitHooks, name);
    const body = hookScriptBody(name);
    if (existsSync(target)) {
      const existing = readFileSync(target, "utf8");
      if (!existing.includes(PROJECT_INTEL_HOOK_MARKER)) {
        const pending = join(projectIntelDir(root), "hooks", `${name}.pending.sh`);
        writeFileSync(pending, body, "utf8");
        try {
          chmodSync(pending, 0o755);
        } catch {
          /* ignore */
        }
        results.push({ hook: name, status: "conflict", detail: `已保留现有钩子；待安装的包装器已写入 ${pending}` });
        continue;
      }
    }
    writeFileSync(target, body, "utf8");
    try {
      chmodSync(target, 0o755);
    } catch {
      /* ignore */
    }
    results.push({ hook: name, status: "installed", detail: target });
  }
  return results;
}

function realpathSafe(p: string): string {
  try {
    return realpathSync(p);
  } catch {
    return p;
  }
}
