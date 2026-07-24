#!/usr/bin/env node
// Dev entry for the Node.js/TypeScript core.
//
// During phases 2-3 the public bin/project-intel.mjs still dispatches to Python.
// This entry exercises the TS core via tsx (`tsx src/cli.ts ...`) so migrated
// commands can be developed and tested before phase 4.1 flips the bin.

import { dispatch, CommandRegistry } from "./app/dispatcher.js";
import { VERSION } from "./version.js";
import { ok, type GlobalOptions, type CommandHandler } from "./cli/parser.js";
import { print } from "./io/output.js";
import { runInit } from "./commands/init.js";
import { runDoctor } from "./commands/doctor.js";
import { runCheck } from "./commands/check.js";
import { runInstall } from "./commands/install.js";
import { runAdapters } from "./commands/adapters.js";
import { runAgentInstall } from "./commands/agent-install.js";
import { runRequirement } from "./commands/requirement.js";
import { runTest } from "./commands/test.js";
import { runReview } from "./commands/review.js";
import { runFinish } from "./commands/finish.js";
import { runMaintain } from "./commands/maintain.js";
import { runGraphTools } from "./commands/graph-tools.js";
import { runQuery } from "./commands/query.js";
import { runIntake, runSpec, runPlan, runLifecycle, runDebug, runRequirements } from "./commands/orchestration.js";
import { UsageError } from "./errors.js";
import { knownFlagsFor, valueFlagsFor } from "./cli/command-flags.js";

const registry = new CommandRegistry();

/** Attach the argparse-derived flag whitelist to a handler spec. */
function withFlags(name: string, help: string, run: (args: string[], global: GlobalOptions) => unknown, selfPrinting = false): CommandHandler {
  const knownFlags = knownFlagsFor(name);
  const valueFlags = valueFlagsFor(name);
  const handler: CommandHandler = {
    name,
    help,
    run: run as CommandHandler["run"],
    valueFlags,
    selfPrinting,
  };
  if (knownFlags) handler.knownFlags = knownFlags;
  return handler;
}

// `version` prints the version line in text mode (mirrors Python: print(VERSION)),
// and returns the structured result for the JSON envelope in json mode.
registry.register({
  name: "version",
  help: "打印版本号",
  selfPrinting: true,
  run: (_args, global) => {
    if (!global.jsonMode) print(VERSION);
    return ok({ version: VERSION });
  },
});

registry.register(withFlags("init", "初始化 .project-intel", (args, global) => runInit(global.projectRoot ?? process.cwd(), args, global, false), true));
registry.register(withFlags("refresh", "从当前工作区刷新 .project-intel", (args, global) => runInit(global.projectRoot ?? process.cwd(), args, global, true), true));
registry.register(withFlags("doctor", "诊断运行时、项目和图谱工具状态", (args, global) => runDoctor(global.projectRoot ?? process.cwd(), args, global), true));
registry.register(withFlags("check", "运行项目智能检查", (args, global) => runCheck(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("install", "安装 Claude 兼容的项目入口", (args, global) => runInstall(global.projectRoot ?? process.cwd(), args, global), true));
registry.register(withFlags("adapters", "预览、应用或移除 Codex/Claude 根入口适配器", (args, global) => runAdapters(global.projectRoot ?? process.cwd(), args, global), true));

registry.register(withFlags("agent", "显式安装 Claude/Codex 插件", (args, _global) => {
  // `agent install` — subcommand parsed inside the handler.
  if (args[0] !== "install") throw new UsageError("agent 子命令只支持 install。");
  return runAgentInstall(process.cwd(), args.slice(1), _global);
}));

// `requirement` has its own subcommand parser; flag validation happens inside
// each subcommand's run function (matching Python's nested argparse).
registry.register({
  name: "requirement",
  help: "维护需求级档案和状态机",
  run: (args, global) => runRequirement(global.projectRoot ?? process.cwd(), args, global),
});

registry.register(withFlags("test", "运行并记录 RED/GREEN/回归/验证测试证据", (args, global) => runTest(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("review", "登记需求级代码评审结果", (args, global) => runReview(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("finish", "任务完成后生成收口报告", (args, global) => runFinish(global.projectRoot ?? process.cwd(), args, global), true));
registry.register(withFlags("maintain", "任务完成后刷新项目智能", (args, global) => runMaintain(global.projectRoot ?? process.cwd(), args, global), true));
registry.register(withFlags("graph-tools", "查询可选图谱工具的状态与命令", (args, global) => runGraphTools(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("query", "搜索项目智能产物", (args, global) => runQuery(global.projectRoot ?? process.cwd(), args, global), true));
registry.register(withFlags("intake", "分析需求入口、任务分流和 readiness", (args, global) => runIntake(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("spec", "为需求档案设置编号验收标准", (args, global) => runSpec(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("plan", "按需在需求目录生成 plan.md", (args, global) => runPlan(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("lifecycle", "输出任务影响分析", (args, global) => runLifecycle(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("debug", "输出系统化调试上下文", (args, global) => runDebug(global.projectRoot ?? process.cwd(), args, global)));
registry.register(withFlags("requirements", "按源码文件维护简短中文需求记录", (args, global) => runRequirements(global.projectRoot ?? process.cwd(), args, global)));

const result = dispatch(process.argv.slice(2), registry, VERSION);
process.exit(result.exitCode);
