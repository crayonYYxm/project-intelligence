// `query` command (phase 3.G.2). Searches project-intel artifacts (standards,
// knowledge, reports) by text, mirroring application.query.

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { projectIntelDir } from "./init.js";
import { UsageError } from "../errors.js";
import { print } from "../io/output.js";

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

export function runQuery(root: string, args: string[], global: GlobalOptions): CommandResult {
  const needle = flag(args, "--search") ?? flag(args, "--query") ?? args[args.indexOf("query") + 1];
  const pdir = projectIntelDir(root);
  if (!existsSync(join(pdir, "manifest.json"))) {
    throw new UsageError("未找到 .project-intel。请先运行 project-intel init。");
  }
  const matches: { path: string; snippet: string; line: number }[] = [];
  for (const path of queryFiles(pdir)) {
    const text = safeRead(path);
    const index = needle ? text.toLowerCase().indexOf(needle.toLowerCase()) : -1;
    if (index >= 0) {
      const line = text.slice(0, index).split("\n").length;
      matches.push({
        path: relative(root, path),
        snippet: text.slice(Math.max(0, index - 80), index + Math.max(needle?.length ?? 0, 160)).trim(),
        line,
      });
    }
  }
  if (matches.length === 0) {
    print("未找到直接匹配的项目智能结果。请尝试更宽泛的关键词或刷新知识库。");
  } else {
    for (const match of matches.slice(0, 10)) {
      print(`\n## ${match.path}:${match.line}\n`);
      print(match.snippet);
    }
  }
  void global;
  return ok({ query: needle ?? "" });
}

function queryFiles(dir: string): string[] {
  const out: string[] = [];
  const walk = (current: string): void => {
    for (const name of readdirSafe(current)) {
      if (["cache", "local", "tmp"].includes(name)) continue;
      const path = join(current, name);
      try {
        const stat = statSync(path);
        if (stat.isDirectory()) walk(path);
        else if (stat.isFile() && /\.(json|md|txt)$/i.test(name)) out.push(path);
      } catch {
        // Ignore files that disappear during a concurrent refresh.
      }
    }
  };
  walk(dir);
  return out.sort();
}

function readdirSafe(dir: string): string[] {
  try {
    return readdirSync(dir);
  } catch {
    return [];
  }
}

function safeRead(path: string): string {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}

function relative(root: string, path: string): string {
  return path.split(root).pop()!.replace(/^[/\\]/, "");
}
