# LOCAL-20260721-144445 收口总结

## 验收标准

- AC-01：CLI 入口已迁移到 Node.js/TypeScript，`bin/project-intel.mjs` 直接加载编译产物。
- AC-02：命令、参数、退出码与 JSON 输出协议保持兼容。
- AC-03：`.project-intel` 文件模型保持兼容，未引入 schema 升级。
- AC-04：原子写入、锁、UTF-8 和路径处理由 Node 实现承接。
- AC-05：外部进程调用由 Node 层统一处理，不再依赖 Python 运行时。
- AC-06：版本源以 `package.json` 为准并同步插件清单与运行时版本。
- AC-07：项目扫描、项目事实、标准、知识图谱生成链路完成 Node 迁移。
- AC-08：需求生命周期状态机完成 Node 迁移并保留门禁语义。
- AC-09：测试证据、评审、finish、maintain 流程完成 Node 迁移。
- AC-10：旧 Python 测试已映射到 Node 测试清单，严格映射校验通过。
- AC-11：测试证据拒绝伪造通过文本，必须绑定真实报告或实际命令计数。
- AC-12：发布包不包含旧 Python 生产实现和 Python 测试源码。
- AC-13：干净安装冒烟通过 `--version`、`doctor`、`init --dry-run`。
- AC-14：0.6.1 回滚读取兼容验证通过。
- AC-15：性能与进程泄漏基准通过，未发现 Python 运行时引用。

## 收口说明

本次 Node.js/TypeScript 运行时迁移已完成。旧 Python 生产实现、旧 Python 测试和 Python 版文档校验脚本已从仓库发布范围移除，Node 版本保留当前 CLI、需求生命周期、测试证据、评审收口、项目扫描、适配器和发布校验能力。

已登记并通过的验收命令包括：`npm test`、`npm run check-release`、`node scripts/validate-test-map.mjs --strict`、`node scripts/check-dual-compat.mjs`、`node scripts/rollback-read.mjs`、`node scripts/bench.mjs`、`node scripts/scan-python-runtime-refs.mjs`、`node scripts/smoke-pack.mjs`。发布包验证显示安装产物内无 `.py` 文件，Node-only PATH 下核心命令退出码为 0。
