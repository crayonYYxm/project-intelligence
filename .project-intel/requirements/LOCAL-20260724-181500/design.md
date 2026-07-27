# LOCAL-20260724-181500_修复 ZCode 兼容性并生成测试与收口文档_设计文档

## bug现象

仓库被 ZCode 作为 marketplace 导入时，只能依赖 Claude 兼容格式，缺少 ZCode 推荐的根目录 marketplace.json 和插件内 .zcode-plugin/plugin.json。需求生命周期中，测试执行只留下分阶段明细，finish 又要求调用者预先生成 closure 产物，导致用户在需求目录看不到流程承诺的测试主文档和收口文档。

## 原因分析

1. `package.json` 的发布文件和 `.claude-plugin/marketplace.json` 只覆盖 Claude/Codex 分发，没有 ZCode 原生清单。
2. 测试报告逻辑位于 `src/commands/test.ts#prepareRequirementReport`。该函数每次只写入 test-reports/TEST-*.md，没有生成或刷新 test-report.md 聚合入口。
3. 收口入口位于 `src/commands/finish.ts#runFinish`。该函数直接调用 finish 门禁；状态机要求 closure artifact 已存在，但命令本身没有生成它，和“任务完成后生成收口报告”的 CLI 描述不一致。

## 修复方案

补齐 ZCode 原生 marketplace 与插件清单，并纳入版本、npm 包内容和无符号链接检查。测试命令在写入分阶段报告后同步重建 test-report.md，使用 manifest 中的当前证据组织摘要。finish 命令先执行不写状态的完整门禁校验，通过后再创建并登记 closure，最后执行正式 finish；失败时不生成收口文件。

## 改造思路

1. 根目录新增 marketplace.json，插件目录新增 .zcode-plugin/plugin.json，字段与现有 Claude 插件保持一致。
2. 在测试报告函数完成明细报告后，调用聚合函数写入 canonical test-report.md 并登记当前 test artifact。
3. 在 finish 命令中先做无副作用门禁预检，成功后通过现有 artifact 生成能力创建 closure，再执行状态迁移。
4. 更新打包、版本一致性和 lifecycle 单元测试，保持 Claude/Codex 行为不变。

## 新旧代码对照

旧逻辑：测试命令只返回 test-reports/TEST-*.md；finish 假设 closure-summary.md 已经存在。

新逻辑：测试命令同时维护 test-report.md；finish 在全部门禁满足时自动生成并登记 closure-summary.md，失败路径不落收口产物。

## 逻辑变更说明

- ZCode 导入优先命中原生插件清单，仍可继续读取 Claude 兼容格式。
- 每次需求级 RED/GREEN/回归/验证都会刷新测试主文档，历史明细继续保留。
- finish 的测试、评审、变更范围和 diff hash 门禁不放宽，仅把原本需要手工执行的 closure 生成步骤收进命令。
- 已存在 closure 时沿用已登记产物，不覆盖用户内容。

## 影响范围

修改插件分发清单、npm 打包校验、需求级测试报告生成和 finish 命令。受影响入口为 `project-intel test`、`project-intel finish` 与 ZCode marketplace 安装；init、refresh、Claude/Codex 技能内容和外部接口不变。

## 风险评估

**风险等级**：中

**极端预测**：若聚合报告与 manifest 证据不同步，finish 会拒绝完成；若 ZCode 清单版本漏同步，发布检查会阻断打包。

**紧急举措**：回退本次命令与清单改动即可恢复旧流程；测试明细仍保存在 test-reports/，不会丢失既有证据。
