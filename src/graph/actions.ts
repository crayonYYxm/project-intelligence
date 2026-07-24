import { existsSync, readFileSync, readdirSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { commandExists } from "../process/spawn.js";

const UNDERSTAND_AGENT_COMMAND = "/understand . --language zh";
const UNDERSTAND_CLAUDE_MARKETPLACE = "claude plugin marketplace add Egonex-AI/Understand-Anything";
const UNDERSTAND_CLAUDE_INSTALL = "claude plugin install understand-anything@understand-anything";
const UNDERSTAND_CLAUDE_ENABLE = "claude plugin enable understand-anything@understand-anything";
const UNDERSTAND_CLAUDE_INSTALL_HINT =
  "claude plugin marketplace add Egonex-AI/Understand-Anything && " +
  "claude plugin install understand-anything@understand-anything && " +
  "claude plugin enable understand-anything@understand-anything";
const UNDERSTAND_CODEX_INSTALL =
  "curl -fsSL https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.sh | bash -s codex";

export interface GraphAction extends Record<string, unknown> {
  tool: "GitNexus" | "Understand-Anything";
  state: string;
  canAnalyze: boolean;
  canInstall: boolean;
}

export function detectGraphActions(root: string): GraphAction[] {
  const runner = join(root, ".gitnexus", "run.cjs");
  const gitnexusCommand = existsSync(runner)
    ? "node .gitnexus/run.cjs analyze"
    : commandExists("gitnexus")
      ? "gitnexus analyze"
      : null;
  const gitnexusSource = existsSync(runner) ? "repo-runner" : gitnexusCommand ? "path" : null;
  const gitnexusInstall = commandExists("npx") ? "npx gitnexus analyze" : null;

  const claudeInstalls = claudeUnderstandInstalls();
  const pluginRoots = understandPluginRoots();
  const installedPlatforms = new Set<string>();
  for (const path of pluginRoots) {
    const lower = path.toLowerCase();
    if (
      lower.endsWith("/.understand-anything-plugin") ||
      lower.includes("/.understand-anything/repo/understand-anything-plugin") ||
      lower.includes("/.codex/understand-anything/") ||
      lower.includes("/.agents/skills/")
    ) {
      installedPlatforms.add("codex");
    }
  }
  if (claudeInstalls.some(claudeInstallReady)) installedPlatforms.add("claude");
  const understandCommand = process.env.PROJECT_INTEL_UNDERSTAND_COMMAND?.trim()
    || (commandExists("understand") ? "understand ." : null);
  const currentPlatform = currentAgentPlatform();
  const installedForCurrent = installedPlatforms.has(currentPlatform);
  const allInstallOptions: Record<string, unknown>[] = [];
  const customInstall = process.env.PROJECT_INTEL_UNDERSTAND_INSTALL_COMMAND?.trim();
  if (customInstall) {
    allInstallOptions.push({
      platform: "custom",
      label: "自定义安装命令",
      command: customInstall,
      commands: [customInstall],
      canRun: true,
      commandSource: "environment",
    });
  } else {
    if (commandExists("claude")) {
      allInstallOptions.push({
        platform: "claude",
        label: "Claude Code 插件安装/修复",
        command: UNDERSTAND_CLAUDE_INSTALL_HINT,
        commands: [UNDERSTAND_CLAUDE_MARKETPLACE, UNDERSTAND_CLAUDE_INSTALL, UNDERSTAND_CLAUDE_ENABLE],
        canRun: true,
        postInstall: "/reload-plugins",
      });
    }
    if (process.platform !== "win32" && commandExists("curl") && commandExists("bash")) {
      allInstallOptions.push({
        platform: "codex",
        label: "Codex skills 安装",
        command: UNDERSTAND_CODEX_INSTALL,
        commands: [UNDERSTAND_CODEX_INSTALL],
        canRun: true,
      });
    }
  }
  const installOptions = allInstallOptions.filter((option) =>
    option.platform === "custom" || !installedPlatforms.has(String(option.platform))
  );
  const preferredInstall = installOptions.find((option) => option.platform === currentPlatform) ?? installOptions[0];
  const understandState = understandCommand
    ? "installed"
    : installedForCurrent && installOptions.length
      ? "partially-installed"
      : installedForCurrent
      ? "agent-installed"
      : installOptions.length
        ? "installable"
        : "missing";
  const installCommand = preferredInstall ? String(preferredInstall.command) : null;

  return [
    {
      tool: "GitNexus",
      reason: "符号级调用、影响分析、PR/变更风险",
      state: gitnexusCommand ? "installed" : gitnexusInstall ? "installable" : "missing",
      stateLabel: gitnexusCommand ? "已安装，可直接分析" : gitnexusInstall ? "可下载并运行分析" : "不可用",
      analyzeCommand: gitnexusCommand,
      analyzeCommandSource: gitnexusSource,
      installCommand: gitnexusInstall,
      canAnalyze: Boolean(gitnexusCommand),
      canInstall: Boolean(gitnexusInstall),
    },
    {
      tool: "Understand-Anything",
      reason: "架构概览、模块关系、领域流、入职图谱",
      state: understandState,
      stateLabel: {
        installed: "已安装，可直接分析",
        "partially-installed": "当前 agent 已安装；其他平台可选安装",
        "agent-installed": "已安装到 agent；当前 shell 不能直接分析",
        installable: "未安装，可选择安装",
        missing: "未安装且未找到可执行安装命令",
      }[understandState],
      analyzeCommand: understandCommand,
      analyzeCommandSource: understandCommand
        ? (process.env.PROJECT_INTEL_UNDERSTAND_COMMAND?.trim() ? "environment" : "path")
        : null,
      installCommand,
      installOptions,
      agentCommand: UNDERSTAND_AGENT_COMMAND,
      claudeInstallCommand: UNDERSTAND_CLAUDE_INSTALL_HINT,
      canAnalyze: Boolean(understandCommand),
      canInstall: Boolean(installCommand),
      pluginRoots,
      claudeInstalls,
      installedPlatforms: [...installedPlatforms].sort(),
      currentPlatform,
    },
  ];
}

function understandPluginRoots(): string[] {
  const home = homedir();
  const candidates = [
    join(home, ".understand-anything-plugin"),
    join(home, ".understand-anything", "repo", "understand-anything-plugin"),
    join(home, ".codex", "understand-anything", "understand-anything-plugin"),
    join(home, ".opencode", "understand-anything", "understand-anything-plugin"),
    join(home, ".pi", "understand-anything", "understand-anything-plugin"),
    join(home, "understand-anything", "understand-anything-plugin"),
  ];
  const configured = process.env.CLAUDE_PLUGIN_ROOT?.trim();
  if (configured) candidates.unshift(configured);
  const claudeCache = join(home, ".claude", "plugins", "cache");
  try {
    for (const marketplace of readdirSync(claudeCache)) {
      const base = join(claudeCache, marketplace, "understand-anything");
      if (!existsSync(base)) continue;
      candidates.push(base);
      for (const version of readdirSync(base)) candidates.push(join(base, version));
    }
  } catch {
    // no Claude cache
  }
  return candidates.filter((path) =>
    existsSync(join(path, "package.json")) && existsSync(join(path, "pnpm-workspace.yaml"))
  ).map((path) => {
    try {
      return realpathSync(path);
    } catch {
      return path;
    }
  });
}

function currentAgentPlatform(): string {
  const configured = process.env.PROJECT_INTEL_AGENT?.trim().toLowerCase();
  if (configured === "codex" || configured === "claude") return configured;
  if (process.env.CODEX_THREAD_ID || process.env.CODEX_CI || process.env.CODEX_HOME) return "codex";
  if (process.env.CLAUDE_PLUGIN_ROOT || process.env.CLAUDECODE) return "claude";
  return "codex";
}

function claudeInstallReady(install: Record<string, unknown>): boolean {
  const status = String(install.listStatus ?? "").toLowerCase();
  if (status.includes("failed") || status.includes("disabled")) return false;
  if (status.includes("enabled")) return true;
  return Boolean(install.enabled);
}

function claudeUnderstandInstalls(): Record<string, unknown>[] {
  const path = join(homedir(), ".claude", "plugins", "installed_plugins.json");
  try {
    const payload = JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
    const plugins = payload.plugins as Record<string, unknown> | undefined;
    const installs = plugins?.["understand-anything@understand-anything"];
    if (!Array.isArray(installs)) return discoverClaudeCache();
    return installs
      .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
      .map((item) => ({
        id: "understand-anything@understand-anything",
        enabled: true,
        listStatus: "✔ enabled",
        ...item,
      }));
  } catch {
    return discoverClaudeCache();
  }
}

function discoverClaudeCache(): Record<string, unknown>[] {
  const base = join(homedir(), ".claude", "plugins", "cache", "understand-anything", "understand-anything");
  try {
    return readdirSync(base)
      .filter((version) => existsSync(join(base, version)))
      .sort()
      .map((version) => ({
        id: "understand-anything@understand-anything",
        enabled: true,
        listStatus: "✔ enabled",
        scope: "user",
        installPath: join(base, version),
        version,
      }));
  } catch {
    return [];
  }
}
