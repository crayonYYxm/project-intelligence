// Orchestration commands (phase 3.D.6): intake / spec / plan / lifecycle / debug,
// plus the per-source-file `requirements` command. These are read-mostly report
// generators that call the scanner + state machine; they complete the 21-command
// public surface so the bin can flip to the Node core (phase 4.1).

import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { ok, type CommandResult, type GlobalOptions } from "../cli/parser.js";
import { UsageError } from "../errors.js";
import { detectGraphSources } from "../graph/sources.js";
import { collectProjectState } from "../app/project-state.js";
import { createRequirement, setAcceptanceCriteria } from "../requirements/state-machine.js";
import { projectIntelDir } from "./init.js";
import { writeText } from "../fs/atomic-write.js";

function flag(args: string[], name: string): string | undefined {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}
function multi(args: string[], name: string): string[] {
  const out: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]!);
  }
  return out;
}

/**
 * `intake`: analyze a requirement task for track/readiness + optionally register.
 * Mirrors application.intake's analysis + requirement registration branches.
 */
export function runIntake(root: string, args: string[], global: GlobalOptions): CommandResult {
  const task = flag(args, "--task") ?? flag(args, "--requirement-name");
  if (!task) throw new UsageError("intake 必须提供 --task 或 --requirement-name。");
  const track = flag(args, "--track") ?? "auto";
  let requirementId = flag(args, "--requirement-id");
  const requirementName = flag(args, "--requirement-name") ?? task;
  const externalApi = flag(args, "--external-api");
  const ticketKind = (flag(args, "--ticket-kind") ?? "requirement") as "bug" | "requirement";

  // Lightweight track inference (mirrors analyze_task_intake's heuristics).
  const inferredTrack = inferTrack(task, track);

  // Generate LOCAL-* ID when not provided (mirrors Python's LOCAL timestamp ID).
  if (!requirementId) {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    requirementId = `LOCAL-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
  }

  // Register the requirement. Only pass externalApi when explicitly provided
  // (not passing it leaves confirmed=false in the manifest, matching Python).
  const createOpts: { track: string; ticketKind: string; externalApi?: boolean } = {
    track: inferredTrack,
    ticketKind,
  };
  if (externalApi !== undefined) createOpts.externalApi = externalApi === "yes";
  const requirementAction = flag(args, "--requirement-action");
  const requirementPath = flag(args, "--requirement-path");
  const designAction = flag(args, "--design-action");
  const designPath = flag(args, "--design-path");
  const documentOptions = {
    ...(requirementAction !== undefined ? { requirementAction } : {}),
    ...(requirementPath !== undefined ? { requirementPath } : {}),
    ...(designAction !== undefined ? { designAction } : {}),
    ...(designPath !== undefined ? { designPath } : {}),
  };
  const m = createRequirement(root, requirementId, requirementName, { ...createOpts, ...documentOptions });

  void global;
  return ok({
    task,
    track: inferredTrack,
    requirementId: m.requirementId,
    readiness: externalApi !== undefined ? "ready" : "needs-clarification",
    requirement: { requirementId: m.requirementId, state: m.state },
  });
}

function inferTrack(task: string, explicit: string): string {
  if (explicit !== "auto") return explicit;
  const complex = /跨|迁移|重构|安全|发布|兼容|async|auth|payment|cache/i.test(task);
  const standard = /新增|修改|调整|修复|增加/i.test(task);
  return complex ? "complex" : standard ? "standard" : "quick";
}

/** `spec`: set numbered acceptance criteria on a requirement (lightweight). */
export function runSpec(root: string, args: string[], global: GlobalOptions): CommandResult {
  const id = flag(args, "--requirement-id");
  const title = flag(args, "--title");
  const from = flag(args, "--from");
  const criteria = multi(args, "--criterion");
  if (id && criteria.length) {
    const manifest = setAcceptanceCriteria(root, id, criteria.map((c) => {
      const idx = c.indexOf(":");
      return { id: idx >= 0 ? c.slice(0, idx) : c, description: idx >= 0 ? c.slice(idx + 1) : "" };
    }));
    return ok({ requirementId: id, acceptanceCriteria: manifest.acceptanceCriteria });
  }
  // Legacy: generate a spec scaffold file.
  if (!title) throw new UsageError("spec 需要 --title 或 --requirement-id + --criterion。");
  const specsDir = join(projectIntelDir(root), "specs");
  mkdirSync(specsDir, { recursive: true });
  const safeTitle = title.replace(/[^\w\u4e00-\u9fff-]/g, "-");
  const date = new Date().toISOString().slice(0, 10);
  const path = join(specsDir, `${date}-${safeTitle}-spec.md`);
  writeText(path, `# ${title} 需求文档\n\n生成时间：\`${new Date().toISOString()}\`\n\nTrack：auto\n\n## 需求\n\n${from ?? "(待补充)"}\n`);
  void global;
  return ok({ path });
}

/** `plan`: generate a plan.md scaffold inside the requirement directory. */
export function runPlan(root: string, args: string[], global: GlobalOptions): CommandResult {
  const id = flag(args, "--requirement-id");
  const title = flag(args, "--title");
  if (!id) throw new UsageError("plan 需要 --requirement-id。");
  // Verify the requirement exists before generating (mirrors Python's gate).
  const reqDir = join(projectIntelDir(root), "requirements", id);
  const manifestPath = join(reqDir, "manifest.json");
  if (!existsSync(manifestPath)) {
    throw new UsageError(`未找到需求档案：${id}`);
  }
  mkdirSync(reqDir, { recursive: true });
  const path = join(reqDir, "plan.md");
  // Refuse to overwrite existing user content unless --replace is passed
  // (mirrors Python's requirement_generate --replace gate; AC-04/AC-13).
  if (existsSync(path) && !args.includes("--replace")) {
    throw new UsageError("plan.md 已存在；如需覆盖请显式传入 --replace。");
  }
  writeText(
    path,
    [
      `# ${id} ${title ?? ""} 实施计划`,
      "",
      `生成时间：\`${new Date().toISOString()}\``,
      "",
      "## 实施范围",
      "",
      "_待补充_",
      "",
      "## 实施步骤",
      "",
      "1. _待补充_",
      "",
      "## 风险与回滚",
      "",
      "_待补充_",
      "",
    ].join("\n")
  );
  void global;
  return ok({ requirementId: id, path });
}

/** `lifecycle`: output a read-only task-impact analysis. */
export function runLifecycle(root: string, args: string[], global: GlobalOptions): CommandResult {
  const task = flag(args, "--task");
  if (!task) throw new UsageError("lifecycle 需要 --task。");
  const state = collectProjectState(root);
  const impact = {
    task,
    track: inferTrack(task, flag(args, "--track") ?? "auto"),
    fileCount: state.files.length,
    frameworks: state.package.frameworks,
    backendApis: (state.backend.apis as unknown[]).length,
    frontendComponents: (state.frontend.components as unknown[]).length,
    graphSources: detectGraphSources(root).map((s) => ({ name: s.name, status: s.status })),
  };
  void global;
  return ok(impact);
}

/** `debug`: output systematic debugging context (read-only). */
export function runDebug(root: string, args: string[], global: GlobalOptions): CommandResult {
  const bug = flag(args, "--bug");
  if (!bug) throw new UsageError("debug 需要 --bug。");
  const state = collectProjectState(root);
  const manifest = existsSync(join(projectIntelDir(root), "manifest.json"))
    ? JSON.parse(readFileSync(join(projectIntelDir(root), "manifest.json"), "utf8"))
    : null;
  const context = {
    bug,
    projectRoot: ".",
    initialized: existsSync(join(projectIntelDir(root), "manifest.json")),
    manifest,
    backendApis: (state.backend.apis as unknown[]).length,
    frontendComponents: (state.frontend.components as unknown[]).length,
    hints: ["检查 .project-intel/manifest.json 的 git 提交与分支", "用 doctor 诊断运行时与图谱工具状态"],
  };
  void global;
  return ok(context);
}

/** `requirements`: per-source-file short Chinese requirement records. */
export function runRequirements(root: string, args: string[], global: GlobalOptions): CommandResult {
  const task = flag(args, "--task");
  const files = multi(args, "--files");
  if (!task) throw new UsageError("requirements 需要中文 --task 摘要。");
  const reqsDir = join(projectIntelDir(root), "requirements", "files");
  mkdirSync(reqsDir, { recursive: true });
  const records: string[] = [];
  for (const f of files) {
    const safe = f.replace(/[^\w.-]/g, "-");
    const path = join(reqsDir, `${safe}.md`);
    writeText(path, `# ${f}\n\n需求：${task}\n\n生成时间：\`${new Date().toISOString()}\`\n`);
    records.push(path);
  }
  void global;
  return ok({ task, files, records });
}
