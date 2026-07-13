# 项目智能 (Project Intelligence)

Project Intelligence 是一个本地的 Codex/Claude 兼容项目插件，用于生成和使用仓库级的需求文档、实施计划、规范、知识库、图谱上下文、系统化调试、任务编排、质量检查、生命周期维护和审查指导。

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
project-intel --project /path/to/repo lifecycle --task "新需求"
project-intel --project /path/to/repo debug --bug "错误或异常行为"
project-intel --project /path/to/repo spec --title "功能" --from "需求"
project-intel --project /path/to/repo plan --title "功能" --from-spec .project-intel/specs/...
project-intel --project /path/to/repo refresh
project-intel --project /path/to/repo refresh --with-graph
project-intel --project /path/to/repo check
project-intel --project /path/to/repo maintain --task "摘要"
project-intel --project /path/to/repo install --hooks
project-intel --project /path/to/repo query "表格"
```

说明：

- `init` 默认会检查 GitNexus 和 Understand-Anything。已安装且有可执行分析命令时会自动分析；缺失工具只输出建议，不会在非交互环境等待输入。
- `init --interactive` 只在交互终端询问安装选择；`init --setup-missing` 只应在用户明确授权后使用。
- `refresh` 默认只刷新当前项目事实并读取已有图谱产物；`refresh --with-graph` 才重新运行已安装的图谱分析器，且不会安装缺失工具。
- `graph-tools --json` 可用于在非交互 agent 会话里先读取图谱工具状态，再由 agent 用中文向用户确认安装选择；当多个图谱动作可用时，应提供“全部”和组合选择。
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
- `project-brainstorm`：塑造需求并比较实现方案。
- `project-spec`：基于项目事实编写需求文档和影响说明。
- `project-plan`：将需求文档转化为实施计划。
- `project-debug`：基于项目上下文和根因纪律调查 bug。
- `project-orchestrate`：在任务可拆分时编排子代理、任务级 review、最终 review 和验证证据。
- `project-maintain`：任务或变更后刷新项目知识库。
- `project-review`：基于规范、图谱上下文、质量检查和复用风险审查代码。
- `project-knowledge`：回答组件、API、模块、服务和规范相关问题。
- `project-refresh`：初始化或刷新 `.project-intel`。
- `project-standards`：说明和管理规则等级。
- `project-quality`：运行和解读 lint/type/style/format 和冗余检查。

## 执行纪律

Project Intelligence 借鉴了 Superpowers 的执行纪律，但不依赖或接入 Superpowers：

- 默认用 `project-task` 处理普通需求；只有计划任务能清晰拆分、文件边界明确、可单独验证时才用 `project-orchestrate`。
- 实现类子代理默认顺序执行，避免同一工作区并发改代码；并行代理主要用于只读影响分析、失败排查或互不相干的调查。
- `project-plan` 必须写清文件、接口、约束、复用点、验证命令和预期证据，但默认只保留在上下文里，不主动生成 plan 文件。
- `project-review` 对反馈先验证再修改，避免盲目接受不符合当前项目现实的建议。
- 完成、修复、通过、可发布这类结论必须有本轮新鲜验证证据；`project-intel check` 只证明项目智能规则，不自动证明业务行为。
- `project-maintain` 在实现、review 和验证之后执行一次，默认覆盖 `maintenance/latest.md`，并维护每个源码文件一份简短中文需求历史。
