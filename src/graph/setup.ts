import { readSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import { isAbsolutePathLike, expandUser } from "../fs/paths.js";
import { print } from "../io/output.js";
import { runShell } from "../process/exec-shell.js";
import { sanitizeText } from "../testing/sanitize.js";
import { detectGraphActions, type GraphAction } from "./actions.js";

export interface GraphSetupPermissions {
  allowRepoRunner?: boolean;
  allowEnvCommand?: boolean;
  allowExternalPath?: boolean;
}

export interface GraphSetupResult extends Record<string, unknown> {
  tool: unknown;
  status: "ok" | "failed" | "skipped" | "needs-agent";
}

export function graphTimeoutMs(): number {
  const seconds = Number.parseInt(process.env.PROJECT_INTEL_GRAPH_TIMEOUT_SECONDS?.trim() || "900", 10);
  const bounded = Number.isFinite(seconds) ? Math.min(7200, Math.max(30, seconds)) : 900;
  return bounded * 1000;
}

export function runGraphCommand(
  root: string,
  action: Record<string, unknown>,
  command: string
): GraphSetupResult {
  const timeoutMs = graphTimeoutMs();
  const tool = action.tool ?? "图谱工具";
  print(`${tool} 开始执行，超时上限 ${timeoutMs / 1000} 秒。`);
  const result = runShell(command, root, timeoutMs);
  return {
    tool,
    status: result.code === 0 ? "ok" : "failed",
    command: sanitizeText(command),
    exitCode: result.code,
    stdout: sanitizeText(result.stdout.slice(-4000)),
    stderr: sanitizeText(result.stderr.slice(-4000)),
    detail: result.code === 124
      ? `执行超过 ${timeoutMs / 1000} 秒后已终止。可通过 PROJECT_INTEL_GRAPH_TIMEOUT_SECONDS 调整。`
      : "",
  };
}

/** Split shell words while preserving Windows path separators on POSIX hosts. */
export function shellWords(command: string): string[] {
  const words: string[] = [];
  let current = "";
  let quote = "";
  for (let index = 0; index < command.length; index++) {
    const char = command[index]!;
    if (quote) {
      if (char === quote) quote = "";
      else if (char === "\\" && command[index + 1] === quote) current += command[++index]!;
      else current += char;
      continue;
    }
    if (char === "'" || char === '"') {
      quote = char;
    } else if (/\s/.test(char)) {
      if (current) {
        words.push(current);
        current = "";
      }
    } else if (char === "\\" && /\s/.test(command[index + 1] ?? "")) {
      current += command[++index]!;
    } else {
      current += char;
    }
  }
  if (current) words.push(current);
  return words;
}

export function commandUsesExternalPath(root: string, command: string): boolean {
  const rootResolved = resolve(root);
  for (const value of shellWords(command)) {
    let cleaned = value.replace(/^['"]|['"]$/g, "");
    const separator = cleaned.indexOf("=");
    if (separator > 0) {
      const option = cleaned.slice(0, separator);
      if (option.startsWith("-") || /^[A-Za-z_][A-Za-z0-9_]*$/.test(option)) {
        cleaned = cleaned.slice(separator + 1).replace(/^['"]|['"]$/g, "");
      }
    }
    cleaned = expandUser(cleaned);
    if (!isAbsolutePathLike(cleaned)) continue;
    // A Windows absolute path is external when evaluated on POSIX (and vice
    // versa) because it cannot resolve inside the current repository.
    if (!isAbsolute(cleaned)) return true;
    const rel = relative(rootResolved, resolve(cleaned));
    if (rel === ".." || rel.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`) || isAbsolute(rel)) {
      return true;
    }
  }
  return false;
}

export function graphCommandAuthorized(
  root: string,
  command: string,
  source: string,
  permissions: GraphSetupPermissions = {}
): { allowed: boolean; detail: string } {
  if (source === "repo-runner" && !permissions.allowRepoRunner) {
    return { allowed: false, detail: "仓库内 runner 需要显式使用 --allow-repo-runner。" };
  }
  if (source === "environment" && !permissions.allowEnvCommand) {
    return { allowed: false, detail: "环境变量提供的命令需要显式使用 --allow-env-command。" };
  }
  if (source !== "builtin" && /(?<!\\)(?:\$(?:\{|\(|[A-Za-z_])|%[^%\r\n]+%|`|[<>]\()/.test(command) && !permissions.allowExternalPath) {
    return { allowed: false, detail: "命令包含运行时 shell 展开，需要显式使用 --allow-external-path。" };
  }
  if (commandUsesExternalPath(root, command) && !permissions.allowExternalPath) {
    return { allowed: false, detail: "命令引用项目外绝对路径，需要显式使用 --allow-external-path。" };
  }
  return { allowed: true, detail: "" };
}

function installOptions(action: Record<string, unknown>): Record<string, unknown>[] {
  if (Array.isArray(action.installOptions) && action.installOptions.length) {
    return action.installOptions as Record<string, unknown>[];
  }
  return action.installCommand
    ? [{
        platform: "default",
        label: "默认安装命令",
        command: action.installCommand,
        commands: [action.installCommand],
        canRun: true,
      }]
    : [];
}

function chooseInstallOption(
  action: Record<string, unknown>,
  autoApprove: boolean
): Record<string, unknown> | null {
  const options = installOptions(action);
  if (!options.length) return null;
  const currentPlatform = String(action.currentPlatform ?? "codex");
  const preferred = options.find((option) => option.platform === currentPlatform) ?? options[0]!;
  if (autoApprove) return preferred;
  print(`\n检测到 ${action.tool}：${action.stateLabel ?? "需要准备后才能运行分析"}。`);
  print(`用途：${action.reason ?? ""}`);
  options.forEach((option, index) => print(`${index + 1}. ${option.label ?? option.platform}\n   命令：${option.command}`));
  print(`${options.length + 1}. 跳过，继续初始化 .project-intel`);
  try {
    const buffer = Buffer.alloc(64);
    const count = readSync(process.stdin.fd, buffer, 0, buffer.length, null);
    const choice = buffer.toString("utf8", 0, count).trim().toLowerCase();
    if (!choice || ["y", "yes", "是"].includes(choice)) return preferred;
    const index = Number.parseInt(choice, 10);
    return index >= 1 && index <= options.length ? options[index - 1]! : null;
  } catch {
    return null;
  }
}

export function setupGraphTools(
  root: string,
  actions: Record<string, unknown>[],
  autoApprove: boolean,
  permissions: GraphSetupPermissions = {}
): GraphSetupResult[] {
  const results: GraphSetupResult[] = [];
  for (const action of actions) {
    const tool = action.tool;
    const analyzeCommand = String(action.analyzeCommand ?? "");
    if (analyzeCommand) {
      const authorization = graphCommandAuthorized(
        root,
        analyzeCommand,
        String(action.analyzeCommandSource ?? "path"),
        permissions
      );
      if (!authorization.allowed) {
        print(`${tool}：${authorization.detail}`);
        results.push({
          tool,
          status: "skipped",
          command: sanitizeText(analyzeCommand),
          detail: authorization.detail,
        });
      } else {
        print(`${tool} 已安装，开始运行分析：${sanitizeText(analyzeCommand)}`);
        results.push(runGraphCommand(root, action, analyzeCommand));
      }
      continue;
    }

    const options = installOptions(action);
    if (tool === "Understand-Anything" && action.state === "agent-installed" && !options.length) {
      const detail =
        `Understand-Anything 已安装到 agent；当前 shell 不能直接分析。请运行 ${action.agentCommand} 生成图谱，` +
        "完成后立即执行 /project-refresh；不能触发 slash command 时执行 project-intel refresh。";
      print(detail);
      results.push({ tool, status: "skipped", detail });
      continue;
    }
    if (!options.length) {
      const detail = "未检测到可安装或可运行的命令。";
      print(`${tool}：${detail}`);
      results.push({ tool, status: "skipped", detail });
      continue;
    }
    const option = chooseInstallOption(action, autoApprove);
    if (!option) {
      results.push({ tool, status: "skipped", detail: "用户选择跳过。" });
      continue;
    }
    const installCommand = String(option.command ?? "");
    const authorization = graphCommandAuthorized(
      root,
      installCommand,
      String(option.commandSource ?? action.installCommandSource ?? "builtin"),
      permissions
    );
    if (!authorization.allowed) {
      print(`${tool}：${authorization.detail}`);
      results.push({
        tool,
        status: "skipped",
        command: sanitizeText(installCommand),
        detail: authorization.detail,
      });
      continue;
    }
    print(`开始准备并执行 ${tool}：${sanitizeText(installCommand)}`);
    const commands = Array.isArray(option.commands) ? option.commands.map(String) : [installCommand];
    let installOk = false;
    for (const command of commands.filter(Boolean)) {
      const result = runGraphCommand(root, action, command);
      results.push({ ...result, platform: option.platform });
      installOk = result.status === "ok";
      if (!installOk) break;
    }
    if (tool === "Understand-Anything" && installOk) {
      const refreshed = detectGraphActions(root).find((item) => item.tool === tool);
      const refreshedCommand = String(refreshed?.analyzeCommand ?? "");
      if (refreshedCommand) {
        results.push(runGraphCommand(root, action, refreshedCommand));
      } else {
        const detail =
          `Understand-Anything 已安装到 agent，但当前 shell 不能直接识别它；请触发 Understand-Anything skill 或运行 ${action.agentCommand}，` +
          "完成后立即执行 /project-refresh；不能触发 slash command 时执行 project-intel refresh。";
        print(detail);
        results.push({
          tool,
          status: "needs-agent",
          command: action.agentCommand,
          refreshCommand: "/project-refresh",
          fallbackRefreshCommand: "project-intel refresh",
          detail,
        });
      }
    }
  }
  return results;
}

export function handleToolingSetup(
  root: string,
  tooling: Record<string, unknown>,
  options: {
    interactive: boolean;
    setupMissing: boolean;
    withGraph: boolean;
  } & GraphSetupPermissions
): GraphSetupResult[] {
  if (!options.withGraph) return [];
  const actions = ((tooling.graphActions as GraphAction[] | undefined) ?? []) as Record<string, unknown>[];
  const installed = actions.filter((action) => Boolean(action.analyzeCommand));
  const pending = actions.filter((action) => !action.analyzeCommand);
  const permissions: GraphSetupPermissions = {
    allowRepoRunner: Boolean(options.allowRepoRunner),
    allowEnvCommand: Boolean(options.allowEnvCommand),
    allowExternalPath: Boolean(options.allowExternalPath),
  };
  const results = installed.length
    ? setupGraphTools(root, installed, true, permissions)
    : [];
  if (options.setupMissing && pending.length) {
    results.push(...setupGraphTools(root, pending, true, permissions));
  } else if (options.interactive && pending.length) {
    if (process.stdin.isTTY) {
      results.push(...setupGraphTools(root, pending, false, permissions));
    } else {
      print("当前不是交互终端，已跳过缺失图谱工具安装；可先运行 graph-tools --json 再确认安装。");
    }
  }
  return results;
}
