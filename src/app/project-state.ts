// Project-state assembly (phase 3.B), ported from application.collect_project_state
// + build_manifest + default_config. Produces the in-memory facts that init/refresh/
// doctor/check consume: discovered files, frontend/backend scan results, manifest,
// config, and the inferred standards.

import { spawnSync } from "node:child_process";
import { accessSync, constants, existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { discoverFiles, EXCLUDED_DIRS } from "../scanner/files.js";
import { scanFrontend } from "../scanner/frontend.js";
import { scanBackend } from "../scanner/backend.js";
import { detectPackage, detectQualityCommands, packageManager } from "../scanner/quality.js";
import { detectGraphSources, understandGraphSummary } from "../graph/sources.js";
import { detectGraphActions } from "../graph/actions.js";
import { commandExists } from "../process/spawn.js";
import { VERSION } from "../version.js";
import { captureScopeSnapshot } from "../requirements/scope.js";
import { inferStandards } from "../standards/infer.js";
import { projectDomainCandidates } from "../standards/domains.js";
import { IncrementalScanCache, fileSignature } from "../scanner/core.js";

export interface ProjectState {
  files: ReturnType<typeof discoverFiles>;
  frontend: ReturnType<typeof scanFrontend>;
  backend: ReturnType<typeof scanBackend>;
  package: ReturnType<typeof detectPackage>;
  manifest: Record<string, unknown>;
  config: Record<string, unknown>;
  graph: Record<string, unknown>;
  tooling: Record<string, unknown>;
  scanCache: ReturnType<IncrementalScanCache["payload"]>;
}

export function nowIso(): string {
  return new Date().toISOString();
}

/** Read git info (commit/branch/dirty) for the manifest, mirroring git_info. */
export function gitInfo(root: string): Record<string, unknown> {
  const run = (args: string[]): { ok: boolean; output: string } => {
    const r = spawnSync("git", args, { cwd: root, encoding: "utf8", timeout: 5000 });
    return { ok: r.status === 0, output: (r.stdout ?? "").trim() };
  };
  const commit = run(["rev-parse", "HEAD"]);
  const branch = run(["rev-parse", "--abbrev-ref", "HEAD"]);
  const status = run(["status", "--porcelain"]);
  return {
    commit: commit.ok && commit.output ? commit.output : null,
    branch: branch.ok && branch.output ? branch.output : null,
    dirty: status.ok ? status.output.length > 0 : null,
  };
}

/** Capture a Git snapshot (commit + diffHash) for evidence binding.
 *  Used by test/review/finish to record the code state at evidence time.
 *  diffHash hashes: tracked changes (excluding .project-intel/) + untracked files
 *  (excluding .project-intel/) + HEAD commit. This ensures:
 *  - Content changes to tracked files are detected
 *  - New untracked files are detected
 *  - Commit switches are detected (via the commit hash in the input)
 *  - Manifest writes (which happen during lifecycle ops) don't trigger staleness */
export function captureGitSnapshot(root: string): { gitCommit: string; diffHash: string; gitAvailable: boolean } {
  const snapshot = captureScopeSnapshot(root);
  return {
    gitCommit: snapshot.gitCommit,
    diffHash: snapshot.diffHash,
    gitAvailable: snapshot.gitAvailable,
  };
}

/** Build the manifest.json payload (mirrors build_manifest). */
export function buildManifest(
  files: ProjectState["files"],
  pkg: ReturnType<typeof detectPackage>,
  graphSources: unknown[],
  tooling: Record<string, unknown>,
  root: string = "."
): Record<string, unknown> {
  const suffixCounts = new Map<string, number>();
  for (const f of files) {
    const key = f.suffix || "<none>";
    suffixCounts.set(key, (suffixCounts.get(key) ?? 0) + 1);
  }
  const detectedSources = graphSources.length > 0 ? graphSources : detectGraphSources(root);
  const optional = (tooling.optional as Record<string, unknown>) ?? {};
  return {
    schemaVersion: 2,
    toolVersion: VERSION,
    projectRoot: ".",
    generatedAt: nowIso(),
    git: gitInfo(root),
    frameworks: pkg.frameworks,
    packageName: pkg.packageName,
    packages: (pkg.packages as Record<string, unknown>[]).map((item) => ({
      path: item.path,
      name: item.name,
      frameworks: item.frameworks ?? [],
    })),
    fileCount: files.length,
    suffixCounts: Object.fromEntries([...suffixCounts.entries()].sort((a, b) => b[1] - a[1])),
    graphSources: detectedSources,
    tooling: {
      node: (optional.node as Record<string, unknown> | undefined)?.status,
      gitnexus: (optional.gitnexus as Record<string, unknown> | undefined)?.status,
      understandAnything: (optional.understandAnything as Record<string, unknown> | undefined)?.status,
      recommendedActions: Array.isArray(tooling.recommendedActions) ? tooling.recommendedActions.length : 0,
    },
    notes: ["可用时优先使用 GitNexus 和 Understand-Anything 作为图谱来源。"],
  };
}

/** Build the default config.json payload (mirrors default_config). */
export function defaultConfig(root: string, pkg: ReturnType<typeof detectPackage>): Record<string, unknown> {
  return {
    schemaVersion: 2,
    scan: {
      include: ["**/*"],
      exclude: [...EXCLUDED_DIRS].sort(),
      excludeHidden: true,
    },
    quality: { commands: detectQualityCommands(root, pkg) },
    backend: {
      entrypointRules: [
        { type: "annotation", pattern: "@RestController|@Controller|@RequestMapping|@GetMapping|@PostMapping|@MessageListener|@Scheduled" },
        { type: "call", pattern: "router\\.(get|post|put|delete|use)|app\\.(get|post|put|delete|use)" },
        { type: "path", pattern: "**/{controller,handler,endpoint,facade,adapter}/**/*" },
      ],
    },
    rules: { hard: [], preferred: [], inferred: [], candidate: [] },
  };
}

/** Detect a minimal tooling report (node present, python absent in product runtime). */
export function detectTooling(root: string, pkg: ReturnType<typeof detectPackage>): Record<string, unknown> {
  const selectedManager = packageManager(root);
  const graphActions = detectGraphActions(root);
  const gitnexusAction = graphActions.find((action) => action.tool === "GitNexus")!;
  const understandAction = graphActions.find((action) => action.tool === "Understand-Anything")!;
  const qualityCommands = detectQualityCommands(root, pkg) as Record<string, unknown>[];
  const gitnexusIndex = existsSync(join(root, ".gitnexus"));
  const gitnexusRunner = existsSync(join(root, ".gitnexus", "run.cjs"));
  const understandGraph = existsSync(join(root, ".understand-anything", "knowledge-graph.json"));
  const recommendedActions: Record<string, unknown>[] = [];
  const followUpActions: Record<string, unknown>[] = [];
  if (gitnexusAction.state !== "installed") {
    recommendedActions.push({
      tool: "GitNexus",
      reason: gitnexusAction.reason,
      command: gitnexusAction.installCommand ?? gitnexusAction.analyzeCommand,
      canRun: Boolean(gitnexusAction.canInstall || gitnexusAction.canAnalyze),
    });
  }
  if (understandAction.state === "agent-installed" || understandAction.state === "partially-installed") {
    followUpActions.push({
      tool: "Understand-Anything",
      reason: understandAction.reason,
      command: understandAction.agentCommand,
      refreshCommand: "/project-refresh",
      fallbackRefreshCommand: "project-intel refresh",
      detail:
        "Understand-Anything 已安装到 Codex/Claude Code agent，但当前 shell 没有 `understand` 命令。" +
        "如果是在 Claude Code 刚完成安装/启用，请先运行 /reload-plugins 重新加载插件，" +
        "再在当前 agent 会话中运行 /understand . --language zh 或触发 Understand-Anything skill，" +
        "生成图谱后立即执行 /project-refresh；如果不能触发 slash command，执行 project-intel refresh。",
      canRun: false,
    });
  }
  if (understandAction.state === "installable" || understandAction.state === "partially-installed") {
    recommendedActions.push({
      tool: "Understand-Anything",
      reason: understandAction.reason,
      command: understandAction.installCommand ?? understandAction.agentCommand,
      installOptions: understandAction.installOptions ?? [],
      canRun: Boolean(understandAction.canInstall || understandAction.canAnalyze),
    });
  }
  return {
    schemaVersion: 1,
    required: [
      { name: "node>=18", status: Number(process.versions.node.split(".")[0]) >= 18 ? "present" : "missing" },
      { name: "project-write-access", status: writable(root) ? "present" : "missing" },
    ],
    optional: {
      git: { status: commandExists("git") ? "present" : "missing" },
      node: { status: "present" },
      packageManagers: ["pnpm", "npm", "yarn"].map((name) => ({
        name,
        status: commandExists(name) ? "present" : "missing",
        selected: name === selectedManager,
      })),
      gitnexus: {
        status: gitnexusIndex ? "present" : gitnexusAction.state,
        indexPath: gitnexusIndex ? ".gitnexus" : null,
        runnerPath: gitnexusRunner ? ".gitnexus/run.cjs" : null,
      },
      understandAnything: {
        status: understandGraph ? "present" : understandAction.state,
        graphPath: understandGraph ? ".understand-anything/knowledge-graph.json" : null,
        pluginRoots: understandAction.pluginRoots ?? [],
        claudeInstalls: understandAction.claudeInstalls ?? [],
      },
      qualityTools: qualityCommands.map((c) => ({
        kind: c.kind,
        status: c.source === "package.json"
          ? "configured"
          : commandExists(String(c.command ?? "").split(/\s+/)[0] ?? "")
            ? "available"
            : "missing",
        command: c.command,
        detail: c.source === "package.json"
          ? "使用项目的 package script；依赖归属保持在项目中。"
          : String(c.command ?? "").startsWith("npx ")
            ? "需要 npx，因为未找到项目 script。"
            : "从项目配置推断。",
      })),
    },
    graphActions,
    recommendedActions,
    followUpActions,
    generatedAt: nowIso(),
  };
}

function writable(root: string): boolean {
  try {
    accessSync(root, constants.W_OK);
    return true;
  } catch {
    return false;
  }
}

/**
 * Collect the full project state: discover files, scan frontend + backend, build
 * manifest + config. Mirrors collect_project_state (graph sources excluded in the
 * no-graph init path; added by the graph integration layer in phase 3.G).
 */
export function collectProjectState(root: string): ProjectState {
  // Read existing config first (if any) to respect user's scan settings.
  const configPath = join(root, ".project-intel", "config.json");
  let existingConfig: Record<string, unknown> | null = null;
  let configError: string | null = null;
  try {
    if (existsSync(configPath)) {
      existingConfig = JSON.parse(readFileSync(configPath, "utf8"));
      if (!existingConfig || typeof existingConfig !== "object" || Array.isArray(existingConfig)) {
        configError = "config.json is not a valid JSON object";
        existingConfig = null;
      }
    }
  } catch (err) {
    configError = String((err as Error).message);
  }
  if (configError) {
    throw new Error(`损坏的 config.json 无法解析：${configError}；请修复后重试。`);
  }
  const pkg = detectPackage(root);
  const defaultCfg = defaultConfig(root, pkg);
  const config = existingConfig
    ? {
        ...defaultCfg,
        ...existingConfig,
        scan: { ...(defaultCfg.scan as Record<string, unknown>), ...((existingConfig.scan as Record<string, unknown>) ?? {}) },
        backend: { ...(defaultCfg.backend as Record<string, unknown>), ...((existingConfig.backend as Record<string, unknown>) ?? {}) },
        rules: { ...(defaultCfg.rules as Record<string, unknown>), ...((existingConfig.rules as Record<string, unknown>) ?? {}) },
        quality: {
          ...(defaultCfg.quality as Record<string, unknown>),
          ...((existingConfig.quality as Record<string, unknown>) ?? {}),
          commands: mergeQualityCommands(
            (((existingConfig.quality as Record<string, unknown> | undefined)?.commands as Record<string, unknown>[] | undefined) ?? []),
            (((defaultCfg.quality as Record<string, unknown>).commands as Record<string, unknown>[] | undefined) ?? [])
          ),
        },
      }
    : defaultCfg;
  config.schemaVersion = 2;
  const scanConfig = (config.scan as Record<string, unknown> | undefined) ?? (defaultCfg.scan as Record<string, unknown>);
  const excludePatterns = (scanConfig.exclude as string[]) ?? (defaultCfg.scan as Record<string, unknown>).exclude as string[];
  const includePatterns = (scanConfig.include as string[]) ?? undefined;
  const excludeHidden = scanConfig.excludeHidden !== false;

  // Read .understandignore if it exists (additional exclude patterns).
  const understandignorePath = join(root, ".understandignore");
  let understandignorePatterns: string[] = [];
  try {
    if (existsSync(understandignorePath)) {
      understandignorePatterns = readFileSync(understandignorePath, "utf8")
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter((l) => l && !l.startsWith("#"));
    }
  } catch { /* ignore */ }

  const allExcludes = [...excludePatterns, ...understandignorePatterns];
  const files = discoverFiles(root, { exclude: allExcludes, excludeHidden, include: includePatterns });
  const scanCache = IncrementalScanCache.load(join(root, ".project-intel", "local", "scan-cache.json"));
  const frontendFiles = files
    .filter((f) => [".vue", ".tsx", ".jsx", ".ts", ".js", ".css", ".scss", ".sass", ".less"].includes(f.suffix))
    .map((f) => ({ path: f.path, readText: () => safeRead(f.absolute), signature: fileSignature(f.absolute) }));
  const backendFiles = files
    .filter((f) => [".java", ".kt", ".py", ".go", ".ts", ".js", ".yaml", ".yml", ".properties", ".xml"].includes(f.suffix))
    .map((f) => ({ path: f.path, readText: () => safeRead(f.absolute), signature: fileSignature(f.absolute) }));
  const frontend = scanFrontend(frontendFiles, scanCache);
  const backend = scanBackend(backendFiles, config, scanCache);
  const rules = config.rules as Record<string, unknown>;
  rules.inferred = inferStandards(frontend, backend);
  const tooling = detectTooling(root, pkg);
  const graphSources = detectGraphSources(root);
  const manifest = buildManifest(files, pkg, graphSources, tooling, root);
  const understandSummary = understandGraphSummary(root);
  const graph: Record<string, unknown> = {
    schemaVersion: 2,
    generatedAt: nowIso(),
    sources: graphSources,
    summary: {
      components: frontend.components.length,
      hooks: frontend.hooks.length,
      apis: backend.apis.length,
      services: backend.services.length,
      candidateEntrypoints: backend.candidateEntrypoints.length,
    },
    gitnexusSummary: graphSources.find((source) => source.name === "GitNexus") ?? {},
    understandSummary,
  };
  graph.projectDomains = projectDomainCandidates(frontend, backend, graph);
  return { files, frontend, backend, package: pkg, manifest, config, graph, tooling, scanCache: scanCache.payload() };
}

function mergeQualityCommands(
  manual: Record<string, unknown>[],
  detected: Record<string, unknown>[]
): Record<string, unknown>[] {
  const merged: Record<string, unknown>[] = [];
  const seen = new Set<string>();
  for (const item of [...manual, ...detected]) {
    const command = String(item.command ?? "");
    if (!command || seen.has(command)) continue;
    seen.add(command);
    merged.push(item);
  }
  return merged;
}

function safeRead(path: string): string {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}
