# 项目智能 (Project Intelligence)

Project Intelligence 是一个本地的 Codex/Claude 兼容项目插件，用于完成“需求号/名称 → 需求文档与 manifest 验收标准 → Bug 根因诊断（如适用） → 源码佐证的开发设计文档 → 可选实施计划 → readiness → 实施 → 测试报告 → 持久化 review → 收口总结 → finish → maintain”的需求级闭环，同时维护仓库级规范、知识和图谱上下文。

可用时优先使用 GitNexus 和 Understand-Anything 作为推荐的图谱来源。

完整项目说明、流程图、使用方式、Skill 介绍和触发词见 [docs/project-intelligence-guide.md](docs/project-intelligence-guide.md)。

## 安装

### npm（推荐）

需要 Node.js 18+ 和 Python 3.9+。npm 包会安装 `project-intel` CLI，但不会在安装阶段修改 Claude Code 或 Codex 配置。

```bash
npm install -g project-intelligence
project-intel --version
project-intel agent install --target all
```

`agent install` 是显式操作：它将当前 npm 包中的 marketplace 和插件注册到 Claude Code、Codex 或两者。完成后启动新的 Agent 会话加载 skills。

也可以直接运行，无需全局安装：

```bash
npx project-intelligence doctor --json
npx project-intelligence init --dry-run
```

### Claude Code

1. 先添加 marketplace：
   ```bash
   /plugin marketplace add crayonYYxm/project-intelligence
   ```

2. 然后安装插件：
   ```bash
   /plugin install project-intelligence@project-intelligence
   ```

3. 启动新的 Claude Code 会话以加载插件 skills。

### Codex CLI（不使用 npm 时）

```bash
codex plugin marketplace add crayonYYxm/project-intelligence
codex plugin add project-intelligence@project-intelligence
```

安装后启动新的 Codex 线程以加载插件 skills。

## CLI

常用命令：

```bash
project-intel --project /path/to/repo init
project-intel --project /path/to/repo init --dry-run
project-intel --project /path/to/repo graph-tools --json
project-intel --project /path/to/repo doctor --json
project-intel --project /path/to/repo intake --task "新需求"
project-intel --project /path/to/repo intake --requirement-id REQ-1001 --requirement-name "新需求" --ticket-kind requirement --external-api no --requirement-action generate --design-action generate
project-intel --project /path/to/repo requirement acceptance set --requirement-id REQ-1001 --criterion "AC-01:实现目标行为" --criterion "AC-02:相关回归测试通过"
project-intel --project /path/to/repo requirement add --requirement-id REQ-1001 --type requirement --path .project-intel/requirements/REQ-1001/requirement.md
# 仅 Bug 需要在 design/ready 前登记根因证据：
project-intel --project /path/to/repo requirement diagnose --requirement-id bug1001 --root-cause "已确认根因" --evidence "src/order/service.ts#submitOrder"
project-intel --project /path/to/repo requirement add --requirement-id REQ-1001 --type design --path .project-intel/requirements/REQ-1001/design.md
project-intel --project /path/to/repo requirement ready --requirement-id REQ-1001 --resolution "需求和验收已确认"
project-intel --project /path/to/repo requirement begin --requirement-id REQ-1001
project-intel --project /path/to/repo requirement test-contract set --requirement-id REQ-1001 --kind unit --report-action generate --acceptance AC-01,AC-02
project-intel --project /path/to/repo lifecycle --task "新需求"
project-intel --project /path/to/repo debug --bug "错误或异常行为"
project-intel --project /path/to/repo plan --requirement-id REQ-1001
project-intel --project /path/to/repo refresh
project-intel --project /path/to/repo refresh --with-graph
project-intel --project /path/to/repo refresh --with-graph --allow-repo-runner
project-intel --project /path/to/repo check
project-intel --project /path/to/repo test --requirement-id REQ-1001 --test-kind unit --report-action generate --phase red --command "npm test -- path/to/test" --expect-failure "expected failure" --files src/file.ts tests/file.test.ts --acceptance AC-01
project-intel --project /path/to/repo test --requirement-id REQ-1001 --test-kind unit --report-action generate --phase green --command "npm test -- path/to/test" --files src/file.ts tests/file.test.ts --acceptance AC-01,AC-02
project-intel --project /path/to/repo review --requirement-id REQ-1001 --result passed --summary "无阻塞问题" --files src/file.ts tests/file.test.ts
project-intel --project /path/to/repo requirement resolve-finding --requirement-id REQ-1001 --finding-id FINDING-01-01 --resolved-by "reviewer" --resolution "已修复并复核"
project-intel --project /path/to/repo requirement generate --requirement-id REQ-1001 --type closure
project-intel --project /path/to/repo finish --requirement-id REQ-1001 --files src/file.ts tests/file.test.ts
project-intel --project /path/to/repo maintain --requirement-id REQ-1001 --files src/file.ts tests/file.test.ts
project-intel --project /path/to/repo adapters status --json
project-intel --project /path/to/repo adapters preview --target both --json
project-intel --project /path/to/repo adapters apply --target both
project-intel --project /path/to/repo install --hooks
project-intel --project /path/to/repo query "表格"
project-intel --project /path/to/repo requirement query --file src/file.ts
project-intel --project /path/to/repo requirement migrate
```

说明：

- `init` 默认不运行图谱命令，只写项目事实；使用 `--with-graph` 才会运行已安装的图谱分析器。
- `init` 和普通 `refresh` 默认只写 `.project-intel` 项目事实，不修改根 `.gitignore`、`AGENTS.md` 或 `CLAUDE.md`；只有显式 `adapters apply`、`install` 或 `refresh --adapters` 才维护适配器。`adapters preview/status/remove` 可先预览、检查或移除 Project Intelligence 管理块。
- `init --interactive` 只在交互终端询问安装选择；`init --setup-missing` 只应在用户明确授权后使用。
- `refresh` 默认只刷新当前项目事实并读取已有图谱产物；`refresh --with-graph` 才重新运行已安装的图谱分析器，且不会安装缺失工具。仓库 runner、环境变量命令和项目外绝对路径还分别需要 `--allow-repo-runner`、`--allow-env-command`、`--allow-external-path`。
- `graph-tools --json` 可用于在非交互 agent 会话里先读取图谱工具状态，再由 agent 用中文向用户确认安装选择；当多个图谱动作可用时，应提供“全部”和组合选择。
- `intake` 将需求分为 `quick`、`standard`、`complex`，并输出 readiness、风险、缺失信息、必经阶段和复用候选；默认只打印，不生成文件。
- `lifecycle` 输出带 track/readiness 的任务影响分析，默认只打印，不写共享报告。
- `project-spec` 维护需求目录中的 `requirement.md` 和 manifest 验收标准；`project-plan` 仅在复杂任务或明确要求时生成同目录的可选 `plan.md`。未选择计划时不强制生成；一旦生成，必须补全、登记且保持哈希有效，才能通过 ready/begin。
- `project-design` 可以独立把本地 Bug/需求单转换为 `docs/requirements/` 下的源码佐证设计文档；独立调用不会初始化或修改 `.project-intel`。在生命周期模式中，设计统一归档为 `.project-intel/requirements/<id>/design.md`。
- `requirement` 将每个需求直接归档到 `.project-intel/requirements/<id>/`。四个必选文档是 `requirement.md`、`design.md`、`test-report.md`、`closure-summary.md`；`plan.md` 可选。manifest 保存状态、AC、测试/评审证据、变更文件、finish 和 maintenance 结果。纯数字编号按单据类型规范化为 `bug<数字>` 或 `req<数字>`。
- intake 选择的需求文档和设计文档动作及已有文件路径保存在 `manifest.workflowSelections`，后续会话和子任务从 `requirement status --json` 恢复，不重复询问或猜测。
- 项目级可覆盖状态统一写入 `.project-intel/project-status.md`。新流程不创建共享 `reports/specs/plans/maintenance`、`requirements/by-id` 或 `requirements/files`；旧结构可用 `requirement migrate` 先预览，再加 `--apply` 迁移。
- `requirement test-contract set` 把测试类型、报告动作和 AC 映射写入 manifest；`both` 只表示契约要求 unit 和 service 两类证据，单条 `test` 证据只能是 `unit`、`service` 或 `manual`。
- `test` 要求显式 `--files` 或 `--project-wide`；RED 还必须用 `--expect-failure` 匹配预期失败，退出码 2/3/4/5、命令不存在和超时都不会被误判为有效 RED。需求级 `test-report.md` 按执行追加命令、结果、覆盖文件、AC、commit 和 diff hash；登记已有报告时还会保留脱敏后的不可变证据副本。
- `review` 持久化结果、问题级别、完整 Git 范围和 diff hash；存在未解决的 critical/important 问题或评审后代码变化时不能 finish。修复后使用 `requirement resolve-finding` 按稳定 finding ID 写入解决人和解决说明，再执行新一轮 review。
- `finish` 检查需求/设计、测试策略、验收标准映射、评审、实际 Git 变更范围、证据 hash 和结构完整的收口总结。登记已有测试报告时会解析实际通过/失败结果并与声明结果核对；人工测试只能通过 `project-test` 的审批式 visual/device/hardware/configuration 例外登记，不能由 finish 一行文字绕过。它不会自动提交、推送、部署或发布。
- 图谱工具未准备好但有支持的 setup 命令时，只有显式 `--with-graph --interactive` 才会询问是否继续。GitNexus 通常是 `npx gitnexus analyze` 这种“下载并运行分析”；Understand-Anything 会按当前环境安装到 Codex 或 Claude Code。
- `init --setup-missing` 会跳过询问并直接运行支持的安装/初始化命令。
- Understand-Anything 的 Codex 安装使用官方 `install.sh codex`；Claude Code 安装使用 `claude plugin marketplace add Egonex-AI/Understand-Anything` 和 `claude plugin install understand-anything@understand-anything`。
- Understand-Anything 如果只能通过 agent slash command 使用，安装后需要重启 agent 并运行 `/understand . --language zh`，随后再运行 `refresh` 让 `.project-intel` 记录图谱元数据。
- `check` 会执行结构化 hard 规则；纯文本 hard 规则标记为 `manual-review`。退出码 `0` 表示自动检查通过，`1` 表示自动 hard/质量检查失败，`2` 表示未初始化、配置或路径无效。
- 可提交的 `.project-intel/config.json` 只保存团队规则、扫描范围和质量命令；本机工具状态与扫描缓存写入默认忽略的 `.project-intel/local/`。
- `--strict` 只接受可验证的 GitNexus 或 Understand-Anything 图谱，空 `.gitnexus/` 目录和损坏 JSON 不会通过。

结构化 hard 规则写在 `.project-intel/config.json`：

```json
{
  "rules": {
    "hard": [
      {
        "id": "no-direct-console",
        "rule": "业务源码禁止直接使用 console.log",
        "check": {
          "type": "forbid-regex",
          "pattern": "\\bconsole\\.log\\s*\\(",
          "include": ["src/**"],
          "exclude": ["**/*.test.*"]
        }
      }
    ]
  }
}
```

支持 `forbid-regex`、`require-regex`、`require-file`、`forbid-path`。没有 `check` 的 hard 规则保留为人工审查项。

## Skills

- `project-init`：首次创建 `.project-intel` 项目事实层，不用于普通新建页面或模块。
- `project-refresh`：刷新已存在的 `.project-intel`；首次初始化使用 `project-init`。
- `project-intake`：需求入口分流、readiness 和 quick/standard/complex 路由。
- `project-brainstorm`：塑造需求并比较实现方案，默认不创建正式需求档案。
- `project-spec`：在 intake 后、debug/design 前形成 `requirement.md`，并把同一组编号验收标准写入 manifest。
- `project-debug`：调查 Bug/错误；Bug 实现流程中还要在 design 前登记根因证据。
- `project-design`：分析本地 Bug/需求单和源码，生成或验证开发设计文档；可独立使用，也可接入需求生命周期。
- `project-plan`：复杂任务或用户明确要求时，将已确认设计转成可执行实施计划。
- `project-test`：在 ready 后询问测试类型和报告动作，begin 后记录 RED、GREEN、回归/验证或审批式人工证据。
- `project-task`：需求 ready 后进入实现，使用项目规范、知识库和复用点。
- `project-orchestrate`：在任务可拆分时编排子代理、任务级 review、最终 review 和验证证据。
- `project-review`：基于规范、图谱上下文、质量检查和复用风险审查代码。
- `project-finish`：任务完成前做验收证据、scope drift、发布/回滚风险和收口检查。
- `project-maintain`：仅在需求通过 finish、状态为 finished 后刷新项目事实、记录 maintenance 结果并关闭需求；git pull/merge 后的普通事实刷新使用 `project-refresh`。
- `project-knowledge`：回答组件、API、模块、服务和规范相关问题。
- `project-standards`：说明和管理规则等级。
- `project-quality`：运行和解读 lint/type/style/format 和冗余检查。

## 执行纪律

Project Intelligence 内置了完整的任务分流、测试、审查和收口纪律：

- 实现意图默认按 `project-intake → project-spec → project-debug（仅 Bug）→ project-design → project-plan（complex 或明确要求）→ requirement ready → project-test（先选测试方案）→ project-task（begin 后执行测试和实现）` 接力。即使用户要求暂不改文件，也完成适用的前置 Skill 路由后再停在编辑前。
- intake 询问需求号/名称、单据类型、对外接口影响以及需求/设计文档动作；`project-spec` 维护 `requirement.md` 和 manifest AC，`project-design` 维护源码佐证 `design.md`。Bug 还必须由 `project-debug` 通过 `requirement diagnose` 登记根因证据，全部满足后才能 ready/begin。进入 `project-test` 时必须询问测试类型与测试报告动作。
- 实现类子代理默认顺序执行，避免同一工作区并发改代码；并行代理主要用于只读影响分析、失败排查或互不相干的调查。
- `project-plan` 必须写清文件、接口、约束、复用点、验证命令和预期证据，但默认只保留在上下文里，不主动生成 plan 文件。
- `project-review` 对反馈先验证再修改，避免盲目接受不符合当前项目现实的建议。
- 完成、修复、通过、可发布这类结论必须有本轮新鲜验证证据；`project-intel check`、lint、type-check、build 或 Agent 自述都不能自动替代改变行为的测试证据。
- `project-finish` 在实现、review 和 `project-test` 证据之后执行一次，把结果写入当前需求 manifest；证据门禁通过后再执行 `project-maintain`，刷新 `project-status.md`、记录维护结果并关闭需求。

## Skill 行为评测

普通 CI 会静态验证 Skill 场景契约，包括 feature/Bug 顺序、独立设计边界以及“写个方案”“开始修复”“收尾吧”“继续”“git pull 后刷新”等中文正/负触发场景，不调用外部模型：

```bash
npm test
```

需要验证 Agent 是否真的从朴素需求触发正确 Skill 链时，显式运行可计费的 headless eval：

```bash
npm run test:skills:dry-run
npm run test:skills
# Codex dry-run 不需要密钥；实际运行时需要 OPENAI_API_KEY。
node scripts/run-skill-evals.mjs --agent codex --dry-run
```

行为评测不再在 prompt 中要求 Agent 调用指定 Skill 或输出 `WORKFLOW`，只使用自然请求和只读限制。runner 仅从 Agent JSON 流中可观测的 Skill/tool invocation 事件断言名称和顺序，不从最终回答中搜索 Skill 名称；进程错误、超时或预算中止一律 fail-closed。

Codex live eval 会创建临时 `CODEX_HOME`，在其中注册并安装当前工作树，执行后立即清理，不读取或修改用户日常插件配置；需要通过 `OPENAI_API_KEY` 为隔离 profile 提供认证。Claude eval 继续使用 `--plugin-dir` 直接加载当前工作树。
