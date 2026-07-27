# LOCAL-20260727-141720 需求与 Bug 目录使用编号加标题 实施计划

生成时间：`2026-07-27T06:20:51.912Z`

## 实施范围

- track：complex；外部 API：不影响。
- 修改 `src/requirements/state-machine.ts`，集中实现安全目录名生成和按编号解析新旧档案。
- 修改 `src/commands/requirement.ts`、`src/requirements/layout.ts`、`src/requirements/scope.ts` 中依赖目录段等于需求编号的逻辑。
- 更新 `src/__tests__/state-machine.test.ts`、`src/__tests__/requirement-command.test.ts` 及相关测试，覆盖 AC-01 至 AC-04。
- 更新 CLI/技能中的 `.project-intel/requirements/<id>/` 用户说明为 `<id>-<title>/`，并注明历史兼容。

## 全局约束

- CLI 身份参数继续使用 `--requirement-id`，manifest 的 `requirementId` 和 `requirementName` 字段不变。
- 不自动重命名或删除历史需求目录，不覆盖同编号档案。
- 目录段必须兼容 Windows、macOS 和 Linux，并限制在常见文件系统单段长度以内。
- 目录解析必须通过 manifest 身份校验；重复匹配必须失败。
- 所有代码任务均在当前会话内顺序完成，不使用子代理。

## 实施步骤

1. `inline`：先在 `src/__tests__/state-machine.test.ts` 增加新建目录、标题清洗、新旧目录解析和歧义阻断测试。执行 `node --test --import tsx src/__tests__/state-machine.test.ts`，RED 预期为目录仍只包含编号或无法按编号加载新目录；对应 AC-01、AC-02、AC-03。
2. `inline`：在 `src/requirements/state-machine.ts` 实现目录段清洗、创建路径和按编号查找，保持 legacy fallback。GREEN 执行同一 state-machine 定向测试；复查 `requirementDir` 的全部直接调用方。
3. `inline`：在 `src/__tests__/requirement-command.test.ts` 增加 query、migrate 与 artifact 路径回归，执行 `node --test --import tsx src/__tests__/requirement-command.test.ts`，RED 预期为查询返回目录段或迁移仍生成仅编号目录；对应 AC-03、AC-04。
4. `inline`：修改 `src/commands/requirement.ts`、`src/requirements/layout.ts` 和 `src/requirements/scope.ts`，让查询、迁移和证据范围使用实际目录。GREEN 执行 requirement-command、scope、test-evidence、review-finish-graph 定向测试。
5. `inline`：更新用户可见说明并运行 `npm test`、`npm run typecheck`、`project-intel check`、`git diff --check`。记录 unit/generate 的 GREEN、regression 和 verify 证据。
6. `inline`：检查完整 diff，运行 GitNexus `detect_changes`，完成 `project-intel review`、`finish` 和 `maintain`。

## 风险与回滚

- 风险：公共路径解析改变会波及测试、finish、maintain 和历史档案。通过 manifest 身份校验、旧布局兼容及全生命周期回归控制。
- 风险：过长或非法标题导致跨平台创建失败。通过字符清洗、尾随字符处理、保留编号长度预算和稳定截断控制。
- 回滚：回退本次代码提交即可；本次不批量迁移历史目录，用户数据无需反向迁移。
