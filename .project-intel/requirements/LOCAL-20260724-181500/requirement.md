# LOCAL-20260724-181500 修复 ZCode 兼容性并生成测试与收口文档 需求文档

## 文档信息

- 需求号：LOCAL-20260724-181500
- 需求名称：修复 ZCode 兼容性并生成测试与收口文档
- 单据类型：Bug

## 背景与现状

当前仓库同时面向 Claude Code、Codex 和 ZCode 分发。仓库已经提供 Claude/Codex 清单，但缺少 ZCode 原生清单与根目录 marketplace 清单；生命周期命令虽然保存了分阶段测试明细，也具备收口门禁，却没有按用户可见流程稳定生成约定的 `test-report.md` 和 `closure-summary.md`。

## 复现条件

1. 在 ZCode 中以 `crayonYYxm/project-intelligence` 导入 marketplace，或检查仓库的 ZCode 原生插件清单。
2. 对一个 implementing 状态需求执行 `project-intel test --report-action generate`。
3. 对一个 reviewed 状态需求直接执行 `project-intel finish`，不额外手工生成 closure 产物。

## 当前行为

ZCode 只能尝试 Claude 兼容回退，仓库根目录没有 ZCode 推荐的 marketplace 文件；测试只生成 `test-reports/TEST-*.md`，没有更新约定的测试主文档；finish 直接要求调用者预先生成并登记收口文档。

## 预期行为

ZCode 能按原生格式发现并安装插件；测试执行后自动维护测试主文档；finish 在门禁满足时自动生成并登记收口总结。

## 目标

补齐 ZCode 原生插件与 marketplace 兼容，并让测试和 finish 命令自动维护同一需求目录下的测试主文档与收口文档。

## 业务场景

1. ZCode 用户通过 GitHub 仓库或本地目录导入 marketplace，能够识别并安装 `project-intelligence` 插件。
2. 开发人员记录 RED/GREEN/回归/验证证据后，能够直接查看当前需求的 `test-report.md`。
3. 评审通过后执行 `project-intel finish`，流程自动生成有效的 `closure-summary.md` 并完成门禁。

## 范围

- ZCode marketplace 和插件清单。
- npm 打包内容与版本一致性检查。
- 需求级测试报告聚合逻辑。
- finish 收口文档生成逻辑及对应单元测试。

## 非目标

- 不修改现有 Claude Code、Codex 插件的技能内容和触发规则。
- 不新增外部 API、MCP 服务或远程依赖。
- 不改变既有测试证据、评审和 finish 的安全门禁。

## 业务规则与异常边界

- ZCode 原生清单与现有插件清单使用相同语义化版本。
- Git 仓库和 npm 包不得包含符号链接，避免 Windows 克隆或缓存复制失败。
- `test-report.md` 必须由真实测试执行结果生成或更新，不得把空计划当作通过证据。
- `finish` 只能在测试证据和评审均通过后生成收口文档；门禁失败时不得留下伪完成文档。

## 验收标准

- AC-01：ZCode 可从仓库根目录 marketplace 发现插件，并优先读取 `.zcode-plugin/plugin.json`；npm 包包含两份 ZCode 清单。
- AC-02：Git 跟踪文件和 npm 包内不存在符号链接，Windows/ZCode 克隆不再因链接权限失败。
- AC-03：需求级测试命令每次记录证据后都会创建或更新 `.project-intel/requirements/<id>/test-report.md`，内容包含各次实际执行结果与验收标准映射。
- AC-04：评审通过后直接执行 `project-intel finish` 会自动创建并登记 `closure-summary.md`；门禁失败时不会留下收口文档。
- AC-05：现有 Claude Code、Codex、测试门禁、完整测试套件和发布包检查保持通过。

## 外部接口影响

不影响外部接口。仅调整本地 CLI 生命周期产物与插件分发清单。

## 待确认事项

无。
