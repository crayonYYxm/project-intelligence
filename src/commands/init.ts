// `init` and `refresh` commands (phase 3.B.1), ported from application.init_project.
//
// Collects project state and writes the `.project-intel` layout: manifest.json,
// config.json, knowledge/{frontend,backend,files}.json, graph/project-graph.json,
// the standards docs, and project-status.md. `refresh` re-runs the same collection
// without the setup/adapters side effects. `--dry-run` returns the computed state
// without writing. `--no-graph` skips graph tool detection (deterministic, fast).

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import { collectProjectState, type ProjectState } from "../app/project-state.js";
import { writeJson, writeText } from "../fs/atomic-write.js";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import { print, printJson } from "../io/output.js";
import { standardsDocs } from "../standards/docs.js";
import { handleToolingSetup } from "../graph/setup.js";
import { runAdapters } from "./adapters.js";

const SUBDIRS = ["standards", "knowledge", "graph", "requirements", "hooks", "cache", "local", "tmp"];

/** Resolve the `.project-intel` directory for a project root. */
export function projectIntelDir(root: string): string {
  return join(root, ".project-intel");
}

interface InitOptions {
  dryRun?: boolean;
  noGraph?: boolean;
  withGraph?: boolean;
  strict?: boolean;
  interactive?: boolean;
  setupMissing?: boolean;
  adapters?: boolean;
  allowRepoRunner?: boolean;
  allowEnvCommand?: boolean;
  allowExternalPath?: boolean;
}

function parseArgs(args: string[], refresh: boolean): InitOptions {
  const noGraph = args.includes("--no-graph");
  return {
    dryRun: args.includes("--dry-run"),
    noGraph,
    withGraph: !noGraph && (args.includes("--with-graph") || !refresh),
    strict: args.includes("--strict"),
    interactive: args.includes("--interactive"),
    setupMissing: args.includes("--setup-missing"),
    adapters: args.includes("--adapters"),
    allowRepoRunner: args.includes("--allow-repo-runner"),
    allowEnvCommand: args.includes("--allow-env-command"),
    allowExternalPath: args.includes("--allow-external-path"),
  };
}

/**
 * Run the init/refresh collection + write flow. Returns the computed state.
 * Mirrors init_project's directory + knowledge + standards + status writes.
 */
export function runInit(root: string, args: string[], global: GlobalOptions, refresh = false): CommandResult {
  const opts = parseArgs(args, refresh);
  if (opts.strict && opts.noGraph) {
    throw new UsageError("--strict 不能与 --no-graph 同时使用。");
  }
  if ((opts.setupMissing || opts.interactive) && opts.noGraph) {
    throw new UsageError("--setup-missing/--interactive 不能与 --no-graph 同时使用。");
  }
  if (refresh && opts.adapters) {
    const result = runAdapters(root, ["apply", "--target", "both"], global);
    const entries = ((result.result as Record<string, unknown> | undefined)?.entries as Record<string, unknown>[] | undefined) ?? [];
    print("已维护项目级 Agent 入口：" + entries.map((item) => item.path).join(", "));
    return result;
  }
  let state = collectProjectState(root);
  let setupResults: Record<string, unknown>[] = [];
  if (!opts.dryRun) {
    setupResults = handleToolingSetup(root, state.tooling, {
      interactive: Boolean(opts.interactive || (!refresh && opts.withGraph && !opts.setupMissing)),
      setupMissing: Boolean(opts.setupMissing),
      withGraph: Boolean(opts.withGraph),
      allowRepoRunner: Boolean(opts.allowRepoRunner),
      allowEnvCommand: Boolean(opts.allowEnvCommand),
      allowExternalPath: Boolean(opts.allowExternalPath),
    });
    if (setupResults.length) state = collectProjectState(root);
  }
  const graphSources = state.manifest.graphSources as Record<string, unknown>[];
  if (opts.strict && opts.withGraph && !graphSources.some((source) => source.status === "present")) {
    throw new UsageError("请求了严格的图谱初始化，但没有有效的 GitNexus 或 Understand-Anything 图谱。");
  }
  if (opts.dryRun) {
    const graphActions = (state.tooling.graphActions as Record<string, unknown>[] | undefined) ?? [];
    const preview = {
      dryRun: true,
      manifest: state.manifest,
      config: state.config,
      graph: state.graph,
      wouldWrite: [
        ".project-intel/manifest.json",
        ".project-intel/config.json",
        ".project-intel/knowledge/*.json",
        ".project-intel/graph/project-graph.json",
        ".project-intel/standards/*.md",
        ".project-intel/project-status.md",
        ".project-intel/requirements/<requirement-id>/*.md",
      ],
      adapterWritesRequireExplicitFlag: true,
      wouldRunGraph: opts.withGraph
        ? graphActions.map((action) => action.analyzeCommand).filter(Boolean)
        : false,
    };
    printJson(preview);
    return ok(preview);
  }

  const pdir = projectIntelDir(root);
  for (const sub of SUBDIRS) mkdirSync(join(pdir, sub), { recursive: true });
  ensureProjectIntelGitignore(pdir);

  writeJson(join(pdir, "manifest.json"), state.manifest);
  writeJson(join(pdir, "config.json"), state.config);
  writeJson(join(pdir, "knowledge", "frontend.json"), state.frontend);
  writeJson(join(pdir, "knowledge", "backend.json"), state.backend);
  writeJson(join(pdir, "knowledge", "files.json"), fileIndex(state.files));
  writeJson(join(pdir, "graph", "project-graph.json"), state.graph);
  writeJson(join(pdir, "local", "tooling.json"), state.tooling);
  writeJson(join(pdir, "local", "scan-cache.json"), state.scanCache);
  for (const [name, content] of Object.entries(standardsDocs(state))) {
    writeText(join(pdir, "standards", name), content);
  }
  writeText(join(pdir, "project-status.md"), buildProjectStatus(root, state, setupResults));

  print(refresh ? `已刷新 .project-intel，索引了 ${state.files.length} 个文本文件。` : `已初始化 .project-intel，索引了 ${state.files.length} 个文本文件。`);
  return ok({
    manifest: state.manifest,
    frontend: state.frontend,
    backend: state.backend,
    config: state.config,
    tooling: state.tooling,
    setupResults,
    agentFiles: [],
    claude: null,
    legacyCleanup: [],
  });
}

function fileIndex(files: ProjectState["files"]): unknown[] {
  return files.map((f) => ({ path: f.path, size: f.size, mtime: f.mtimeMs, suffix: f.suffix || "<none>" }));
}

function buildProjectStatus(
  root: string,
  state: ProjectState,
  setupResults: Record<string, unknown>[]
): string {
  const graphSources = (state.manifest.graphSources as Record<string, unknown>[] | undefined) ?? [];
  const quality = (((state.config.quality as Record<string, unknown> | undefined)?.commands as Record<string, unknown>[] | undefined) ?? []);
  const table = (headers: string[], rows: unknown[][]): string => {
    if (!rows.length) return "_None detected._";
    const clean = (value: unknown) => String(value || "").replace(/\r?\n/g, " ").replace(/\|/g, "\\|");
    return [
      `| ${headers.join(" | ")} |`,
      `| ${headers.map(() => "---").join(" | ")} |`,
      ...rows.map((row) => `| ${row.map(clean).join(" | ")} |`),
    ].join("\n");
  };
  return `# 项目状态

更新时间：\`${new Date().toISOString()}\`

## 项目事实

- 项目：${state.manifest.name ?? basename(root)}
- 索引文件数：${state.manifest.fileCount ?? 0}
- 框架：${((state.manifest.frameworks as string[] | undefined) ?? ["未识别"]).join(", ") || "未识别"}
- 前端组件：${state.frontend.components.length}
- Hooks：${state.frontend.hooks.length}
- 后端 API：${state.backend.apis.length}
- 服务：${state.backend.services.length}
- 前端冗余候选：${state.frontend.redundancyCandidates.length}
- 后端候选入口：${state.backend.candidateEntrypoints.length}

## 图谱来源

${table(["来源", "状态", "路径"], graphSources.map((item) => [item.name, item.status, item.path]))}

## 质量命令

${table(["类型", "命令", "来源"], quality.map((item) => [item.kind, item.command, item.source]))}

## 工具准备

${setupResults.length
    ? table(["工具", "状态", "说明"], setupResults.map((item) => [item.tool, item.status, item.detail]))
    : "_本次没有执行工具安装或初始化。_"}

## 最近质量检查

_尚未单独运行项目质量检查。_

## 需求档案

每个需求的需求文档、设计文档、可选计划、测试报告、收口总结和历史状态均位于 \`.project-intel/requirements/<需求号>/\`；本文件只表示可覆盖的项目级当前状态。
`;
}

/** Ensure `.project-intel/.gitignore` excludes local-only files. */
export function ensureProjectIntelGitignore(pdir: string): void {
  const path = join(pdir, ".gitignore");
  let existingText = "";
  try {
    existingText = readFileSync(path, "utf8");
  } catch {
    existingText = "";
  }
  const existingRules = new Set(
    existingText.split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !l.trim().startsWith("#"))
  );
  const required = ["cache/", "local/", "tmp/", "**/.manifest.lock", "**/.*.tmp"];
  const missing = required.filter((r) => !existingRules.has(r));
  if (!missing.length) return;
  const block = "# Project Intelligence local-only files\n" + missing.join("\n") + "\n";
  const body = existingText.replace(/\s+$/, "") + (existingText.trim() ? "\n\n" : "") + block;
  writeFileSync(path, body, "utf8");
}
