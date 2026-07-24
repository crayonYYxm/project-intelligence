import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import {
  beginRequirement,
  createRequirement,
  loadRequirement,
  readyRequirement,
  registerArtifact,
  requirementDir,
  setAcceptanceCriteria,
  setTestContract,
} from "../requirements/state-machine.js";
import { runTest } from "../commands/test.js";
import { runReview } from "../commands/review.js";
import { runInit } from "../commands/init.js";

export const noopGlobal = { project: null, jsonMode: false } as never;

export interface PreparedRequirement {
  root: string;
  id: string;
  name: string;
  files: string[];
  acceptanceIds: string[];
}

export function initGitProject(root: string): void {
  runGit(root, ["init", "-q"]);
  runGit(root, ["config", "user.email", "tests@example.com"]);
  runGit(root, ["config", "user.name", "Project Intelligence Tests"]);
  writeFileSync(join(root, "package.json"), JSON.stringify({ name: "fixture", version: "1.0.0" }));
  writeFileSync(join(root, "README.md"), "# Fixture\n");
  mkdirSync(join(root, "src"), { recursive: true });
  writeFileSync(join(root, "src", "existing.ts"), "export function existingBehavior(): boolean { return true; }\n");
  runGit(root, ["add", "."]);
  runGit(root, ["commit", "-qm", "fixture baseline"]);
}

export function prepareDesignedRequirement(
  root: string,
  id: string,
  options: {
    name?: string;
    externalApi?: boolean;
    contractKind?: "unit" | "service" | "both" | "manual";
    reportAction?: "generate" | "register" | "later";
    reportPath?: string;
    criteria?: { id: string; description: string }[];
  } = {}
): PreparedRequirement {
  initGitProject(root);
  runInit(root, ["--no-graph"], noopGlobal, false);
  const name = options.name ?? "生命周期需求";
  const criteria = options.criteria ?? [{ id: "AC-01", description: "核心行为通过自动测试验证" }];
  createRequirement(root, id, name, { externalApi: options.externalApi ?? false });
  setAcceptanceCriteria(root, id, criteria);
  const docs = join(root, "docs");
  mkdirSync(docs, { recursive: true });
  const requirementPath = join(docs, `${id}-requirement.md`);
  writeFileSync(requirementPath, requirementDocument(id, name, options.externalApi ?? false, criteria));
  registerArtifact(root, id, "requirement", requirementPath);
  const designPath = join(docs, `${id}-design.md`);
  writeFileSync(designPath, designDocument(id, name));
  registerArtifact(root, id, "design", designPath);
  setTestContract(root, id, {
    kind: options.contractKind ?? "unit",
    reportAction: options.reportAction ?? "generate",
    ...(options.reportPath ? { reportPath: options.reportPath } : {}),
    acceptanceIds: criteria.map((criterion) => criterion.id),
  });
  return { root, id, name, files: ["src/feature.ts"], acceptanceIds: criteria.map((criterion) => criterion.id) };
}

export function beginWithBusinessChange(prepared: PreparedRequirement): void {
  readyRequirement(prepared.root, prepared.id, "需求、设计、测试范围均已确认");
  beginRequirement(prepared.root, prepared.id);
  mkdirSync(join(prepared.root, "src"), { recursive: true });
  writeFileSync(join(prepared.root, prepared.files[0]!), "export const migrated = true;\n");
}

export function recordPassingTest(
  prepared: PreparedRequirement,
  testKind: "unit" | "service" = "unit"
): void {
  const result = runTest(
    prepared.root,
    [
      "--requirement-id", prepared.id,
      "--test-kind", testKind,
      "--report-action", "generate",
      "--phase", "verify",
      "--acceptance", prepared.acceptanceIds.join(","),
      "--files", ...prepared.files,
      "--command", "node -e \"console.log('Ran 2 tests')\"",
    ],
    noopGlobal
  );
  if (result.exitCode !== 0) throw new Error(`fixture test evidence failed: ${JSON.stringify(result.result)}`);
}

export function prepareVerifiedRequirement(
  root: string,
  id: string,
  options: Parameters<typeof prepareDesignedRequirement>[2] = {}
): PreparedRequirement {
  const prepared = prepareDesignedRequirement(root, id, options);
  beginWithBusinessChange(prepared);
  const contractKind = options.contractKind ?? "unit";
  if (contractKind === "both") {
    recordPassingTest(prepared, "unit");
    recordPassingTest(prepared, "service");
  } else if (contractKind === "unit" || contractKind === "service") {
    recordPassingTest(prepared, contractKind);
  } else {
    throw new Error("manual fixture not implemented");
  }
  if (loadRequirement(root, id).state !== "verified") throw new Error("fixture did not reach verified");
  return prepared;
}

export function prepareReviewedRequirement(
  root: string,
  id: string,
  options: Parameters<typeof prepareDesignedRequirement>[2] = {}
): PreparedRequirement {
  const prepared = prepareVerifiedRequirement(root, id, options);
  runReview(
    root,
    [
      "--requirement-id", id,
      "--result", "passed",
      "--summary", "代码、测试报告和变更范围均已复核",
      "--files", ...prepared.files,
    ],
    noopGlobal
  );
  const closurePath = join(requirementDir(root, id), "closure-summary.md");
  writeFileSync(closurePath, closureDocument(id, prepared.name, prepared.acceptanceIds));
  registerArtifact(root, id, "closure", closurePath);
  return prepared;
}

export function requirementDocument(
  id: string,
  name: string,
  externalApi: boolean,
  criteria: { id: string; description: string }[]
): string {
  const criterionText = criteria.map((criterion) => `- ${criterion.id}：${criterion.description}`).join("\n");
  return `# ${id} ${name} 需求文档

## 文档信息

- 需求号：${id}
- 需求名称：${name}
- 单据类型：Requirement

## 背景与现状

现有行为需要迁移并保持兼容。

## 目标

在 Node.js 环境中提供等价且可验证的行为。

## 业务场景

用户执行项目命令并获得稳定结果。

## 范围

覆盖命令、生命周期和测试证据。

## 非目标

无，本需求边界已经明确。

## 业务规则与异常边界

所有状态推进必须有当前 Git 快照和真实测试报告。

## 验收标准

${criterionText}

## 外部接口影响

${externalApi ? "确认影响对外接口，需要 service 测试。" : "确认不影响对外接口，仅调整内部实现。"}

## 待确认事项

无，全部事项已经确认。
`;
}

export function designDocument(id: string, name: string): string {
  const sections = [
    "需求问题概述",
    "需求描述",
    "需求提出部门及联系人",
    "电信需求负责人",
    "需求适用范围",
    "需求期望完成时间",
    "设计相关选项",
    "场景分析",
    "风险考虑",
    "实现方案",
    "数据模型",
    "表结构设计",
    "新增模型汇总",
    "表结构描述",
    "建表语句",
    "表数据转储策略",
    "界面设计",
  ];
  return [
    `# ${id}_${name}_设计文档`,
    "",
    ...sections.flatMap((section) => [
      `## ${section}`,
      "",
      `${id} ${name} 在本章节采用 Node.js 等价实现；不适用项已确认无变更。`,
      ...(section === "实现方案"
        ? ["", "源码依据：`src/existing.ts` 中的 `existingBehavior`。"]
        : []),
      "",
    ]),
  ].join("\n");
}

export function closureDocument(id: string, name: string, acceptanceIds: string[]): string {
  return `# ${id} ${name} 复盘收口总结

## 验收标准

${acceptanceIds.map((acceptanceId) => `- ${acceptanceId}：测试、评审和范围证据均已通过。`).join("\n")}

## 收口说明

Node.js 实现已经完成真实命令验证、变更范围评审和发布前检查。
`;
}

function runGit(root: string, args: string[]): void {
  const result = spawnSync("git", args, { cwd: root, encoding: "utf8" });
  if (result.status !== 0) throw new Error(`git ${args.join(" ")} failed: ${result.stderr}`);
}
