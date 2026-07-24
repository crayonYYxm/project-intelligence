# LOCAL-20260721-144445 Project Intelligence Node.js/TypeScript 运行时迁移 实施计划

- 需求号：`LOCAL-20260721-144445`
- 需求名称：Project Intelligence Node.js/TypeScript 运行时迁移
- Track：`complex`
- 源需求：`docs/node-typescript-migration-requirement.md`
- 设计文档：`.project-intel/requirements/LOCAL-20260721-144445/design.md`

## 实施范围

将 Project Intelligence 生产运行时从"Node.js 启动器 + Python 核心"渐进式等价迁移为"Node.js + TypeScript 核心"，发布包仅依赖 Node.js 18+。覆盖 CLI 与应用入口、项目初始化与诊断、项目事实层、需求生命周期、查询与图谱、适配与自动化（顶层 install、adapters、agent install、Git Hook）、文件与文档、外部进程、工程化九大能力域。

代码落位：新增 `src/` 承载 TypeScript 源码，编译输出 `dist/`；Python 代码迁移期保留作对照基线，生产运行路径不再引用时移除。

不涉及：新增业务命令、生命周期阶段、数据模型、`.project-intel` schema 升级、GitNexus/Understand-Anything 边界、界面改版、独立安全加固。

## 输入基线

- requirement.md：`docs/node-typescript-migration-requirement.md`（已登记为需求级 requirement 产物，含 15 条编号 AC）
- design.md：`.project-intel/requirements/LOCAL-20260721-144445/design.md`（已登记为需求级 design 产物，validator `ok: true`）
- 基线版本：project-intelligence 0.6.1，git tag `v0.6.1` 指向提交 `ad3f346`（不是 `d677a47`，后者仅多一条迁移需求文档提交）
- 已有备份分支：`codex/main-before-node-migration-20260721`（指向 `7fa1334`），不新建备份分支
- 全局 CLI 限制：`/opt/homebrew/bin/project-intel` 为旧版 0.1.16，不支持 `requirement` 子命令；迁移期所有 Project Intelligence CLI 调用必须用 `node bin/project-intel.mjs`（版本 0.6.1）

## 文件级变更

新增：`tsconfig.json`、`src/`（cli、fs、process、io、app、scanner、commands、requirements、testing、graph、rules、standards、version 等）、`dist/`（编译产物，加入 npm files）、`scripts/`（snapshot-cli、build-fixtures、validate-test-map、gen-version、dual-impl 对照、scan-python-runtime-refs、smoke-pack、bench、rollback-read）、`.baseline/`（worktree 子目录 gitignore；snapshot/fixtures/test-map 提交）。

修改：`package.json`（devDeps、scripts `build`/`typecheck`/`test:unit`、`files` 加 `dist` 阶段 4 移除 Python scripts、`engines`）、`bin/project-intel.mjs`（阶段 4.1 切到 dist）、`scripts/run-tests.mjs`（聚合 Node 单测）、`scripts/check-release.mjs`（版本单一源校验）、两个 `plugin.json`（构建期回填版本）、`.github/workflows/validate.yml`（Node 18 + Node-only job）、`.gitignore`（`.baseline/worktree/`）、README/CHANGELOG（移除 Python 要求）。

保留不动（迁移期对照基线）：`plugins/project-intelligence/scripts/project_intel_lib/`、`plugins/project-intelligence/tests/`、`plugins/project-intelligence/skills/`、`plugins/project-intelligence/.claude-plugin/`、`plugins/project-intelligence/.codex-plugin/`。

不创建：`.project-intel/plans/` 与 `.project-intel/specs/` 下的人工副本（legacy 索引保留指向本文件）。

## 实施步骤

### 全局约束

1. 产品运行依赖 vs 扫描目标依赖：迁移后产品自身仅依赖 Node.js 18+；但扫描 Python 仓库时仍必须识别 pytest/ruff/mypy 等被扫描项目工具（3.A.4），不得用"改 npx"破坏 Python 项目扫描。
2. 入口切换时机：阶段 2-3 期间 `bin/project-intel.mjs` 保持指向 Python，用户路径始终走旧实现；Node 实现通过独立开发入口（`node --import tsx src/cli.ts`）自测。仅阶段 4.1 在全部公开命令迁移完成并通过双实现对照后切换 `bin`。
3. Shell 兼容：现有测试/质量/图谱命令经 `run_shell`（shell=True）执行，支持环境变量、引号、管道、重定向和复合命令（`application.py#run_shell`）。Node 子进程层必须保留 shell 形执行路径（`src/process/exec-shell.ts`），不得统一成 argv spawn 而破坏用户已配置命令。
4. Python 引用检测口径：阶段 4 检测实际运行依赖（`child_process` 对 python/python3/py 的 spawn/exec、动态 import Python 桥接库、生产入口对 .py 的运行时读取）；不做裸 .py 字符串扫描（扫描器必须保留 .py 后缀识别）。
5. 聚合测试门禁：`npm test` 迁移期始终 = Python 单测 + Skill 契约 + Node 单测（`test:unit`）三段；阶段 4 前不得删 Python 段。
6. 版本单一源：`package.json#version` 为唯一源；构建期生成 `dist/version.js` 并回填两个 `plugin.json#version`；`scripts/check-release.mjs` 校验。
7. 基线来源：对照脚本必须用 `git worktree add .baseline/worktree v0.6.1`（不可变 tag `ad3f346`）；禁止读迁移过程中可能变化的工作区 Python。
8. 收口粒度：整个需求 `LOCAL-20260721-144445` 只在阶段 5.6 一次性 finish + maintain；子任务只做 RED→GREEN + 里程碑 review。

### 阶段 0：迁移准备（在 main 推进，不新建分支）

1. 0.1（inline）确认备份分支 `codex/main-before-node-migration-20260721` 存在并指向 `7fa1334`；不新建分支。验证：`git rev-parse codex/main-before-node-migration-20260721` 返回 `7fa1334`。
2. 0.2（inline）固定 0.6.1 基线工作树：`.baseline/worktree/` 由 `git worktree add .baseline/worktree v0.6.1` 创建，`.gitignore` 忽略该子目录。验证：`git -C .baseline/worktree rev-parse HEAD` == `ad3f346`。
3. 0.3（inline）CLI 行为快照：`scripts/snapshot-cli.mjs` 调用基线工作树 Python 生成 `.baseline/cli-snapshot.json`（命令、子命令、参数、默认值、互斥、帮助、退出码、JSON 字段）。RED：快照为空 → GREEN：`node scripts/snapshot-cli.mjs --check` 通过。产物**提交**。
4. 0.4（inline）0.6.1 数据夹具：`scripts/build-fixtures.mjs` 在临时项目跑基线工作树生成 `.baseline/fixtures/`（config/manifest/knowledge/standards/requirements/test-evidence/review/maintain）。验证：`node scripts/build-fixtures.mjs --validate`。产物**提交**。
5. 0.5（inline）测试映射种子 `.baseline/test-map.json`（每个 Python 测试类 → 期望 Node 等价测试），人工维护，**提交**。验证：`node scripts/validate-test-map.mjs`（非 strict）。

### 阶段 1：TS 工程骨架（不动 bin）

6. 1.1（inline）TypeScript 工程配置：`tsconfig.json`（target ES2022, module NodeNext, strict, outDir `./dist`）；`package.json` 加 devDeps（typescript, tsx, @types/node）、scripts（`build`/`typecheck`/`test:unit`）、**`files` 数组加入 `dist`**、构建前置（`build` 依赖 gen-version）。RED：`npm run typecheck` 无配置 → GREEN：空 `src/index.ts` 下通过；`npm pack --dry-run` 列出 `dist`（即使暂为空目录占位）。
7. 1.2（inline）测试框架接入：`package.json` 新增 `test:unit`（vitest 或 node:test + tsx）；`scripts/run-tests.mjs` 在 Python + Skill 之外追加 `npm run test:unit`，**保留** `npm test` 聚合语义。RED：`npm run test:unit` 无测试 → GREEN：smoke 通过；`npm test` 仍聚合三段。
8. 1.3（inline）版本单一源：`src/version.ts` 导出 `VERSION`；`scripts/gen-version.mjs` 读 `package.json#version` 生成 `dist/version.js` 并回填两个 `plugin.json#version`。RED：四处版本不一致 → GREEN：`npm run gen-version && npm run check-release` 通过。
9. 1.4（inline）双实现对照工具 `src/testing/dual-impl.ts`（同输入分别跑基线 Python 与 Node，diff 归一化）。验证：归一化器单测覆盖时间/临时路径/绝对路径归一。
10. 1.5（parallelizable-readonly）CLI 兼容测试骨架 `src/__tests__/cli-contract.test.ts` 读 `.baseline/cli-snapshot.json` 断言。验证：框架可运行（Node 实现未到位时 skip 并记录）。

### 阶段 2：基础设施迁移（不切 bin）

11. 2.1（inline）CLI 解析与 JSON 信封 `src/cli/parser.ts`、`src/cli/json-envelope.ts`（脱敏 bearer/cookie/secret/URL userinfo）。对齐 `plugins/project-intelligence/scripts/project_intel_lib/application.py#JsonArgumentParser`、`cli.py#json_envelope`。验证：退出码 0/1/2/124/127 与脱敏单测。
12. 2.2（inline）路径与项目根 `src/fs/paths.ts`（显式项目根、Windows 盘符/UNC/POSIX 归一）。验证：中文路径、空格、非 ASCII 固定样例。
13. 2.3（inline）原子写入 `src/fs/atomic-write.ts`（临时文件 + fsync + rename + 失败保留原文件）。对齐 `application.py#write_json`。验证：并发写 + 失败注入。
14. 2.4（inline）文件锁 `src/fs/lock.ts`（O_CREAT\|O_EXCL 等价、5s 超时、60s 陈旧回收、锁文件置需求目录父级）。对齐 `requirements.py#_RequirementLock`。验证：**多个 Node 子进程**竞争同一锁（不是 worker threads，需覆盖进程退出、陈旧锁、独立文件句柄）。
15. 2.5（inline）子进程层（两条路径）：`src/process/spawn.ts`（argv 形，工具缺失→127/超时→124/UTF-8 解码/脱敏截断）对齐 `application.py#run`；`src/process/exec-shell.ts`（shell 形，保留环境变量、引号、管道、重定向、复合命令）对齐 `application.py#run_shell`。验证：argv 缺失/超时；shell 形管道 `a | b` 与重定向 `> file` 等价。
16. 2.6（inline）UTF-8 输出层 `src/io/output.ts`（强制 UTF-8 stdout/stderr，Windows 控制台处理）。验证：非 UTF-8 控制台模拟下中文输出。
17. 2.7（inline）JSON/YAML/Markdown 读写 `src/io/json.ts`、`src/io/yaml.ts`（按需）、`src/io/markdown.ts`。验证：schemaVersion 2 config/manifest 往返。
18. 2.8（inline）命令分发器 `src/app/dispatcher.ts`（子命令注册表、`--project`/`--version`/`--json` 全局处理）。对齐 `application.py#build_parser`。验证：开发入口 `--version` 与单一源一致。

### 阶段 3：业务模块迁移（bin 仍走 Python）

模块顺序：扫描 → 项目事实层 → 顶层 install/Hook → 需求状态机（领域服务）→ 测试证据 → 评审收口（顶层命令调状态服务）→ 图谱集成。

#### 3.A 项目扫描

19. 3.A.1（inline）后端扫描器 `src/scanner/backend.ts`。对齐 `scanner/backend.py`。验证：Python/JS/TS/Java/Go 夹具字段级等价。
20. 3.A.2（inline）前端扫描器 `src/scanner/frontend.ts`（regex-fallback）。对齐 `scanner/frontend.py`。验证：Vue/TSX/JSX 夹具对照。
21. 3.A.3（inline）文件发现与增量缓存 `src/scanner/files.ts`、`src/scanner/cache.ts`（schemaVersion 1）。对齐 `core.py#IncrementalScanCache`。验证：增量命中/未命中。
22. 3.A.4（inline）包/质量命令识别 `src/scanner/quality.ts`：**Python 项目仍识别 pytest/ruff/mypy**（被扫描项目工具），仅改调用形式不硬编码 `python3 -m`（按被扫描项目 lockfile/可执行文件探测）。对齐 `quality.py#detect_quality_commands`。验证：Python 仓库夹具仍报 pytest/ruff/mypy；产品自身不因扫描引入 Python 依赖。

#### 3.B 项目事实层

23. 3.B.1（inline）init/refresh `src/commands/init.ts`、`src/commands/refresh.ts`。验证：`init --dry-run --no-graph` 与基线等价。
24. 3.B.2（inline）doctor `src/commands/doctor.ts`。验证：Node-only 环境 `doctor --json` 不报 Python 缺失。
25. 3.B.3（inline）check（hard 规则 + 可选 quality）`src/commands/check.ts`、`src/rules/hard.ts`。验证：规则违反非 0；生成 project-status.md。
26. 3.B.4（inline）standards 推断 `src/standards/infer.ts`。验证：推断结果对照。

#### 3.C 顶层 install + Hook（公开命令，不可被 adapters/agent install 替代）

27. 3.C.1（inline）顶层 `install` 命令 `src/commands/install.ts`：仅含 `--hooks`/`--activate-git-hooks`/`--allow-external-hooks`（**无 preview/status/remove**，这些属于 adapters）。对齐 `application.py#install_claude`。验证：三选项行为对照，幂等。
28. 3.C.2（inline）adapters 子命令族 `src/commands/adapters.ts`（status/preview/apply/remove + `--target {codex,claude,both}` + status 的 `--check`）。对齐 `application.py` adapter 块逻辑。验证：块标记保留、安全路径校验、四子命令对照。
29. 3.C.3（inline）`agent install` 子命令 `src/commands/agent-install.ts`：仅含 `--target {codex,claude,all}`（默认 all）和 `--dry-run`（**无 status/remove**）。对齐 `application.py#agent_install_commands`（application.py:5117）。验证：预览（dry-run）输出与实际安装命令对照、幂等、状态分类（present/ok/failed/missing）。
30. 3.C.4（inline）Git Hook 生成 `src/commands/hooks.ts`：hook 模板（`write_hook_templates` 等价）+ `activate_git_hooks` 等价；hook 体调用 npm 包 Node CLI，移除 python3。对齐 `application.py#hook_script_body`、`activate_git_hooks`。验证：三平台 hook 产物不含 `python`/`python3`/`py` 调用；symlink hooks 拒绝、core.hooksPath 外部目录需 `--allow-external-hooks`。

#### 3.D 需求状态机（领域服务，被顶层命令调用，不暴露新子命令）

31. 3.D.1（inline）状态机领域服务 `src/requirements/state-machine.ts`：状态枚举、SCHEMA_VERSION、RequirementError、状态迁移函数（ready/begin/record-test/record-review/finish/close/reopen/amend/defer/diagnose/resolve-finding）、锁集成。对齐 `requirements.py#STATES`、`SCHEMA_VERSION`。**不暴露 `requirement/record-review`、`requirement/finish` 等顶层子命令**（review/finish/maintain 是顶层命令，调用此服务）。验证：非法状态迁移被拒；状态转换全矩阵单测。
32. 3.D.2（inline）`requirement` 子命令族（查询与登记类）`src/commands/requirement/{status,query,migrate,generate,add,acceptance,test-contract}.ts`：仅迁移现有公开子命令，不新增。对齐 `application.py:4994-5083`。验证：各子命令参数对照。
33. 3.D.3（inline）`requirement` 子命令族（状态推进类，调 3.D.1 服务）`src/commands/requirement/{ready,begin,diagnose,defer,reopen,amend,resolve-finding}.ts`。对齐 `application.py:4994-5083`。验证：状态推进 + Bug 诊断 + 发现项处理对照。
34. 3.D.4（inline）scope snapshot/diff-hash `src/requirements/scope.ts`（git diff -z NUL 解析）。对齐 `requirements.py#capture_scope_snapshot`。验证：带空格/中文路径的 diff 解析。
35. 3.D.5（inline）0.6.1 布局兼容（v2 直目录，无 by-id）`src/requirements/layout.ts`。验证：0.6.1 数据夹具原地读写。
36. 3.D.6（inline）调度命令 `src/commands/{intake,spec,plan,lifecycle,debug}.ts`。验证：调度输出对照。

#### 3.E 测试证据（testing）

37. 3.E.1（inline）secret 脱敏 `src/testing/sanitize.ts`。对齐 `testing.py#sanitize_text`。验证：全模式脱敏单测。
38. 3.E.2（inline）顶层 `test` 命令 `src/commands/test.ts`（red/green/regression/verify/manual，调 3.D.1 record-test）。验证：故意失败时拒绝；伪造通过文本不被接受。
39. 3.E.3（inline）证据渲染与评估 `src/testing/render.ts`、`src/testing/evaluate.ts`（COMMAND_ERROR_CODES 映射）。对齐 `testing.py#render_test_evidence`。验证：错误码映射一致。

#### 3.F 评审收口（顶层命令，调 3.D.1 服务；与 3.D 无循环依赖）

40. 3.F.1（inline）顶层 `review` 命令 `src/commands/review.ts`：调 `state-machine.record-review`。验证：未 review 时 finish 拒绝。
41. 3.F.2（inline）顶层 `finish` 命令 `src/commands/finish.ts`：调 `state-machine.finish`，门禁 + closure-summary。验证：门禁未满足拒绝；生成收口报告。
42. 3.F.3（inline）顶层 `maintain` 命令 `src/commands/maintain.ts`：刷新事实 + 调 `state-machine.close`。验证：刷新事实 + 关闭需求。

#### 3.G 图谱集成

43. 3.G.1（inline）graph 摘要读取 `src/graph/sources.ts`。对齐 `graph.py`。验证：降级场景状态正确。
44. 3.G.2（inline）graph-tools/查询命令 `src/commands/{graph-tools,query,requirements}.ts`。验证：参数与结果结构兼容。

### 阶段 4：移除生产桥接（此时才切 bin）

45. 4.1（inline）切换 bin 到 Node：`bin/project-intel.mjs` 加载 `dist/cli.js`，移除 Python spawn 与环境变量回退开关。前置门：所有公开命令双实现对照通过、未迁移命令数为 0。验证：全公开命令对照基线等价。
46. 4.2（inline）运行时无 Python 依赖扫描 `scripts/scan-python-runtime-refs.mjs`（检测 child_process 对 python/python3/py 的 spawn/exec、动态 import Python 桥接库、生产入口对 .py 的运行时读取；**不扫描 .py 字符串**）。验证：dist/ + hook 产物扫描通过。
47. 4.3（inline）从 npm files 移除 Python scripts：`package.json#files` 删 `plugins/project-intelligence/scripts`，保留 `dist`。验证：`npm pack --dry-run` 不含 Python scripts。
48. 4.4（inline）测试映射全闭环：`.baseline/test-map.json` 每条有对应 Node 测试，skip=0。验证：`node scripts/validate-test-map.mjs --strict` 通过。

### 阶段 5：发布验证与正式发布

49. 5.1（inline）npm pack 冒烟 `scripts/smoke-pack.mjs`（干净临时目录安装 + 核心流程 + 子进程监测）。验证：无 Python 子进程；不读包外源码。
50. 5.2（inline）三平台 + Node 18/20 CI：`.github/workflows/validate.yml` cli-smoke 矩阵增 Node 18；新增 Node-only job（不装 Python）测 `--version`/`doctor`/`init --dry-run`；保留 Python 矩阵至阶段 4 完成。验证：三平台 × Node 18/20 全绿；Node-only job 全绿。
51. 5.3（inline）性能与稳定性基准 `scripts/bench.mjs`（固定中型仓库启动/init 预览/refresh 中位耗时 + 句柄/僵尸进程检查）。验证：中位耗时 ≤ 基线 1.25 倍；无句柄增长。
52. 5.4（inline）回滚读取验证 `scripts/rollback-read.mjs`（Node 写入的兼容 schema 数据由 0.6.1 基线读取）。验证：0.6.1 可读、无损坏文件。
53. 5.5（inline）文档更新：README/CHANGELOG/安装文档移除 Python 要求。验证：文档不含 Python 安装要求。
54. 5.6（inline）正式发布与最终版本门禁：版本号升级（`package.json#version` bump，如 0.7.0）→ `npm run gen-version` 回填 → `npm run check-release` 通过 → `npm run build` → `npm publish`（或 `npm publish --dry-run` 预演）→ 打 git tag（如 `v0.7.0`）并推送 → 远端校验（干净环境 `npm i -g` 安装 + `--version`/`doctor`/`init --dry-run` 冒烟）→ 失败恢复（发布失败则 `npm unpublish`/发补丁版本/tag 回退）。完成后收口整个需求：`node bin/project-intel.mjs finish` + `maintain`，中文摘要"Project Intelligence Node.js/TypeScript 运行时迁移"。验证：发布产物版本与 `package.json`/`doctor`/`--version` 一致；`requirement status` state 变 finished/closed。

## 测试与验收映射

本节列出每条验收标准的完整描述（与 manifest 一致）与覆盖任务。

- AC-01：在仅安装 Node.js 18 及以上版本、PATH 中不存在 Python 的干净环境中，npm 安装成功，且 project-intel --version、project-intel doctor --json 和 project-intel init --dry-run --no-graph 均可正常执行。→ 1.3, 2.8, 3.B.1, 3.B.2, 4.1, 5.2, 5.6
- AC-02：以 0.6.1 为基线生成公开 CLI 快照，Node.js 实现的命令、子命令、全局参数、子命令参数、默认值、互斥关系和帮助信息全部通过兼容性测试；任何有意差异均须另立需求批准。→ 0.3, 1.5, 2.1, 4.1
- AC-03：成功、用法错误、项目状态错误、外部工具错误和内部运行错误五类固定场景的退出码、JSON 顶层字段、状态值和错误分类与基线兼容。→ 2.1, 2.5, 3.B.3
- AC-04：至少使用包含初始化配置、项目事实、需求生命周期、测试证据、评审结果和维护记录的 0.6.1 数据夹具验证升级；Node.js 实现无需人工转换即可读取、查询和更新，且更新前后没有未授权的数据丢失或 schema 变化。→ 0.4, 2.7, 3.D.2, 3.D.5, 3.F.3
- AC-05：init → intake → spec → requirement ready → begin → test → review → finish → maintain 主流程及诊断、延期、重开、修订和发现项处理分支均有端到端测试，并保持现有状态门禁和失败原因。→ 3.D.1-3.D.6, 3.E.2, 3.F.1-3.F.3
- AC-06：针对 Python、JavaScript/TypeScript、Java 和混合仓库固定夹具，项目扫描、框架识别、包识别、质量命令识别和归一化事实输出达到字段级等价；时间、临时路径等非确定字段在比较前按书面规则归一化。→ 1.4, 3.A.1-3.A.4, 3.B.4, 3.G.1
- AC-07：adapters 和 agent install 的预览、应用、状态和移除流程通过测试；生成的 Git Hook 调用 npm 包提供的 Node.js CLI，在 Windows、macOS 和 Linux 上均不依赖 python 或 python3。→ 3.C.2, 3.C.3, 3.C.4
- AC-08：Windows、macOS 和 Linux CI 全部通过；每个平台均覆盖中文项目路径、中文需求内容、带空格路径、长输出和非 UTF-8 控制台环境下的 UTF-8 结果验证。→ 2.2, 2.5, 2.6, 3.D.4, 5.2
- AC-09：对 npm pack 产物执行全新临时目录安装和核心流程冒烟测试；测试期间监测子进程，确认没有查找、启动或动态导入 Python，且运行时不读取 npm 包之外的仓库源码。→ 4.2, 4.3, 5.1
- AC-10：现有 Python 自动化测试逐项建立“原测试 → Node.js 测试或等价端到端场景”的映射清单，所有当前有效测试均有对应覆盖；未获批准的测试删除、跳过或弱化会导致验收失败。→ 0.5, 1.2, 4.4
- AC-11：故意制造真实测试失败时，test、review 和 finish 门禁必须拒绝通过；仅包含伪造通过文本但没有受支持测试报告或可验证命令结果的证据不得被判定为成功。→ 3.E.1-3.E.3, 3.F.1, 3.F.2
- AC-12：project-intel --version、project-intel doctor --json、package.json 和打包产物报告同一版本；发布校验能够在版本不一致时失败。→ 1.3, 5.6（版本单一源 + 发布门禁；不再是仅文档的 5.5）
- AC-13：由 Node.js 实现更新后的兼容 schema 数据，可由 0.6.1 基线读取；执行失败和版本回滚场景不会留下损坏的 JSON、YAML、Markdown 或锁文件。→ 2.3, 2.4, 5.4
- AC-14：最终 npm 包的安装文档不再要求 Python，运行依赖清单不包含 Python，生产入口及生成的 Hook 不引用 Python，仓库发布检查可自动阻止上述依赖重新出现。→ 3.A.4, 3.C.4, 4.2, 4.3, 5.5, 5.6
- AC-15：在固定中型仓库上记录 0.6.1 与 Node.js 实现的启动、初始化预览和刷新基准；Node.js 实现不存在无限等待、僵尸进程或持续增长的句柄，三个场景的中位耗时均不高于基线的 1.25 倍。→ 5.3

## 风险与回滚

- 双实现漂移：阶段 3 每模块必须先过双实现对照（1.4）再进入阶段 4。
- CLI 兼容回归：任何命令参数/帮助/退出码/JSON 字段变更需另立需求批准（AC-02）。
- 入口切换前置门：阶段 4.1 切 bin 前，所有公开命令必须双实现对照通过；未迁移命令数必须为 0。
- Shell 兼容回归：2.5 的 shell 形执行必须保留管道/重定向/复合命令；若误改成 argv-only 会破坏用户已配置的 quality/test 命令（AC-03/AC-06 回归）。
- Python 项目扫描保真：3.A.4 完成后必须验证 Python 仓库仍正确识别 pytest/ruff/mypy（AC-06）。
- Windows 编码：2.6 必须在三平台 CI（5.2）前完成。
- schema 误升级：2.7 严禁提升 schemaVersion；AC-13 回滚读取为发布前硬门禁。
- 聚合测试门禁：`npm test` 迁移期始终含 Python 单测 + Skill 契约 + Node 单测；阶段 4 前不得删 Python 段。
- 发布失败恢复：5.6 若 `npm publish` 后发现严重问题，按 `npm unpublish`（72h 内）/发补丁版本/tag 回退三档处理，并通过 `codex/main-before-node-migration-20260721` 分支保障源码可回退。

回滚预案：任意阶段失败均可回退至 `codex/main-before-node-migration-20260721`（`7fa1334`）或 `v0.6.1`（`ad3f346`）；Node 写入的兼容 schema 数据保证 0.6.1 可读，用户侧 `npm install -g project-intelligence@0.6.1` 可回滚。
