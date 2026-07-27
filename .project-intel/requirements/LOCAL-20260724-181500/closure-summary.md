# LOCAL-20260724-181500 修复 ZCode 兼容性并生成测试与收口文档 复盘收口总结

## 验收标准

- AC-01：通过 — ZCode 可从仓库根目录 marketplace 发现插件，并优先读取 .zcode-plugin/plugin.json；npm 包包含两份 ZCode 清单。
- AC-02：通过 — Git 跟踪文件和 npm 包内不存在符号链接，Windows/ZCode 克隆不再因链接权限失败。
- AC-03：通过 — 需求级测试命令每次记录证据后都会创建或更新 .project-intel/requirements/<id>/test-report.md，内容包含各次实际执行结果与验收标准映射。
- AC-04：通过 — 评审通过后直接执行 project-intel finish 会自动创建并登记 closure-summary.md；门禁失败时不会留下收口文档。
- AC-05：通过 — 现有 Claude Code、Codex、测试门禁、完整测试套件和发布包检查保持通过。

## 收口说明

当前实现、测试、评审和变更范围已经汇总；最终完成状态以当前 Git 快照的 finish 门禁为准。
