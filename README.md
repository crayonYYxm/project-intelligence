# 项目智能 (Project Intelligence)

Project Intelligence 是一个本地的 Codex/Claude 兼容项目插件，用于完成仓库级“需求入口分流 → spec/plan → 实施前项目理解 → RED/GREEN/回归测试证据 → review/quality → finish 收口 → maintain 知识沉淀”的完整链路。

可用时优先使用 GitNexus 和 Understand-Anything 作为推荐的图谱来源。

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
project-intel --project /path/to/repo lifecycle --task "新需求"
project-intel --project /path/to/repo debug --bug "错误或异常行为"
project-intel --project /path/to/repo spec --title "功能" --from "需求" --track auto
project-intel --project /path/to/repo plan --title "功能" --from-spec .project-intel/specs/... --track auto
project-intel --project /path/to/repo refresh
project-intel --project /path/to/repo refresh --with-graph
project-intel --project /path/to/repo check
project-intel --project /path/to/repo test --task "中文摘要" --phase red --command "npm test -- path/to/test" --files src/file.ts tests/file.test.ts
project-intel --project /path/to/repo test --task "中文摘要" --phase green --command "npm test -- path/to/test" --files src/file.ts tests/file.test.ts
project-intel --project /path/to/repo test --task "中文摘要" --phase verify --files src/file.ts tests/file.test.ts
project-intel --project /path/to/repo finish --task "中文摘要" --files src/page.vue
project-intel --project /path/to/repo maintain --task "摘要"
project-intel --project /path/to/repo install --hooks
project-intel --project /path/to/repo query "表格"
```

说明：

- `init` 默认会检查 GitNexus 和 Understand-Anything。已安装且有可执行分析命令时会自动分析；缺失工具只输出建议，不会在非交互环境等待输入。
- `init --interactive` 只在交互终端询问安装选择；`init --setup-missing` 只应在用户明确授权后使用。
- `refresh` 默认只刷新当前项目事实并读取已有图谱产物；`refresh --with-graph` 才重新运行已安装的图谱分析器，且不会安装缺失工具。
- `graph-tools --json` 可用于在非交互 agent 会话里先读取图谱工具状态，再由 agent 用中文向用户确认安装选择；当多个图谱动作可用时，应提供“全部”和组合选择。
- `intake` 将需求分为 `quick`、`standard`、`complex`，并输出 readiness、风险、缺失信息、必经阶段和复用候选；默认只打印，不生成文件。
- `lifecycle` 输出带 track/readiness 的任务影响分析；默认只打印，`--write` 才覆盖 `.project-intel/reports/task-impact.md`。
- `spec` 和 `plan` 支持 `--track auto|quick|standard|complex`，复杂需求会写入行为契约、readiness gate、验收到证据映射。
- `test` 将 RED、GREEN、回归、完整验证或人工验证记录到固定的 `.project-intel/reports/test-evidence.json` 和 `.md`；RED 只有在测试因预期行为缺失而失败时才算有效，命令不存在或超时不会被误判为有效 RED。
- `finish` 在维护前生成固定收口报告 `.project-intel/reports/finish-report.md`，用于检查 diff、验收证据、scope drift 和发布风险。源码有变更但缺少与当前任务、文件范围和源码更新时间匹配的通过证据时返回非零；无法合理自动化时可用 `--manual-evidence` 记录可复现步骤。它不会自动提交、推送、部署或发布。
- 图谱工具未准备好但有支持的 setup 命令时，`init` 会询问是否继续。GitNexus 通常是 `npx gitnexus analyze` 这种“下载并运行分析”；Understand-Anything 会按当前环境安装到 Codex 或 Claude Code。
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

- `project-task`：实现前使用项目规范和知识库。
- `project-intake`：需求入口分流、readiness 和 quick/standard/complex 路由。
- `project-brainstorm`：塑造需求并比较实现方案。
- `project-spec`：基于项目事实编写需求文档和影响说明。
- `project-plan`：将需求文档转化为实施计划。
- `project-debug`：基于项目上下文和根因纪律调查 bug。
- `project-test`：规划并记录目标测试 RED、GREEN、回归/验证或可复现人工证据，为 finish 提供机器可检查的任务证据。
- `project-orchestrate`：在任务可拆分时编排子代理、任务级 review、最终 review 和验证证据。
- `project-finish`：任务完成前做验收证据、scope drift、发布/回滚风险和收口检查。
- `project-maintain`：任务或变更后刷新项目知识库。
- `project-review`：基于规范、图谱上下文、质量检查和复用风险审查代码。
- `project-knowledge`：回答组件、API、模块、服务和规范相关问题。
- `project-refresh`：初始化或刷新 `.project-intel`。
- `project-standards`：说明和管理规则等级。
- `project-quality`：运行和解读 lint/type/style/format 和冗余检查。

## 执行纪律

Project Intelligence 内置了完整的任务分流、测试、审查和收口纪律：

- 实现意图的需求默认按 `project-intake → project-test → project-task` 同轮接力；即使用户要求暂不改文件，也完成前置 Skill 路由后再停在编辑前。只有计划任务能清晰拆分、文件边界明确、可单独验证时才用 `project-orchestrate`。
- 功能、Bug 修复和行为变更在生产代码前进入 `project-test`：先记录目标测试 RED，再记录 GREEN 和受影响回归；遗留、视觉、设备或配置场景可记录明确的人工证据，不要求删除已经存在的有效代码。
- 实现类子代理默认顺序执行，避免同一工作区并发改代码；并行代理主要用于只读影响分析、失败排查或互不相干的调查。
- `project-plan` 必须写清文件、接口、约束、复用点、验证命令和预期证据，但默认只保留在上下文里，不主动生成 plan 文件。
- `project-review` 对反馈先验证再修改，避免盲目接受不符合当前项目现实的建议。
- 完成、修复、通过、可发布这类结论必须有本轮新鲜验证证据；`project-intel check`、lint、type-check、build 或 Agent 自述都不能自动替代改变行为的测试证据。
- `project-finish` 在实现、review 和 `project-test` 证据之后执行一次，默认覆盖 `reports/finish-report.md`；证据门禁通过后再执行 `project-maintain`，默认覆盖 `maintenance/latest.md`，并维护每个源码文件一份简短中文需求历史。

## Skill 行为评测

普通 CI 会验证 Skill 场景契约，不调用外部模型：

```bash
npm test
```

需要验证 Claude 是否真的从朴素需求触发正确 Skill 链时，显式运行可计费的 headless eval：

```bash
npm run test:skills:dry-run
npm run test:skills
```

行为评测以实际 `Skill` 工具调用和顺序为断言；只开放 Skill 与只读工具，禁止 Bash/Edit/Write。如目标调用链出现后才触达预算上限，runner 会保留预算终态提示，但不会把已观测到的 Skill 路由误判为缺失。

Codex live eval 使用当前配置的插件，只有把当前工作树安装进隔离的 Codex profile 后才应设置 `PROJECT_INTEL_CODEX_EVAL_READY=1` 并运行 `node scripts/run-skill-evals.mjs --agent codex`，避免误测旧的云端缓存版本。
