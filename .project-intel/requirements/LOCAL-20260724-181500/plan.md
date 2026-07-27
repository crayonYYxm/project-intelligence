# LOCAL-20260724-181500 修复 ZCode 兼容性并生成测试与收口文档 实施计划

## 实施范围

补齐 ZCode 原生分发清单，统一测试主报告生成，并让 finish 在完整门禁通过后自动生成收口总结。

## 输入基线

- `requirement.md`
- `design.md`

## 文件级变更

| 仓库相对路径 | 符号或区域 | 修改目的 | 对应 AC |
| --- | --- | --- | --- |
| marketplace.json | ZCode marketplace 清单 | 支持 ZCode 从仓库根目录发现插件 | AC-01, AC-02 |
| plugins/project-intelligence/.zcode-plugin/plugin.json | ZCode 插件清单 | 提供 ZCode 优先识别的原生 manifest | AC-01 |
| package.json | files | 将 ZCode 清单纳入 npm 包 | AC-01, AC-05 |
| scripts/check-release.mjs | 版本一致性检查 | 校验 ZCode/Claude/Codex 版本一致 | AC-01, AC-05 |
| scripts/check-package.mjs | 包内容检查 | 校验 ZCode 清单存在且包内无符号链接 | AC-01, AC-02 |
| src/commands/test.ts | runTest、测试报告聚合 | 每次真实测试后维护 test-report.md | AC-03 |
| src/requirements/state-machine.ts | validateFinishRequirement | 支持收口生成前的无副作用门禁预检 | AC-04 |
| src/commands/finish.ts | runFinish | 门禁通过后自动生成并登记 closure-summary.md | AC-04 |
| src/__tests__/test-evidence.test.ts | 需求级测试用例 | 验证测试主文档生成和累计 | AC-03 |
| src/__tests__/review-finish-graph.test.ts | finish 用例 | 验证自动收口及失败无残留 | AC-04 |
| src/__tests__/zcode-compat.test.ts | ZCode 分发用例 | 验证清单、版本和无符号链接 | AC-01, AC-02 |

## 实施步骤

1. 先添加失败回归测试，覆盖缺少 ZCode 清单、缺少测试主文档和 finish 不自动收口。
2. 添加 ZCode 原生清单并更新发布检查。
3. 实现测试主报告聚合与 manifest 产物登记。
4. 实现 finish 预检后自动生成 closure 的流程。
5. 运行定向测试、完整测试、类型检查和发布包检查。

## 测试与验收映射

| 验收标准 | 说明 | 测试类型 | 命令或人工步骤 |
| --- | --- | --- | --- |
| AC-01 | ZCode 可从仓库根目录 marketplace 发现插件，并优先读取 .zcode-plugin/plugin.json；npm 包包含两份 ZCode 清单。 | unit | node --import tsx --test src/__tests__/zcode-compat.test.ts |
| AC-02 | Git 跟踪文件和 npm 包内不存在符号链接，Windows/ZCode 克隆不再因链接权限失败。 | unit | node --import tsx --test src/__tests__/zcode-compat.test.ts |
| AC-03 | 需求级测试命令每次记录证据后都会创建或更新 .project-intel/requirements/<id>/test-report.md，内容包含各次实际执行结果与验收标准映射。 | unit | node --import tsx --test src/__tests__/test-evidence.test.ts |
| AC-04 | 评审通过后直接执行 project-intel finish 会自动创建并登记 closure-summary.md；门禁失败时不会留下收口文档。 | unit | node --import tsx --test src/__tests__/review-finish-graph.test.ts |
| AC-05 | 现有 Claude Code、Codex、测试门禁、完整测试套件和发布包检查保持通过。 | unit | npm test && npm run check-release |

## 风险与回滚

- 风险：测试主报告写入时机或 closure 预检顺序错误，可能造成证据与状态不同步。
- 回滚：回退命令逻辑与 ZCode 清单；原有 test-reports 明细和 Claude/Codex 清单不受影响。
