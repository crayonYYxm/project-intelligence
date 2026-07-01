# 项目智能 (Project Intelligence)

Project Intelligence 是一个本地的 Codex/Claude 兼容项目插件，用于生成和使用仓库级的需求文档、实施计划、规范、知识库、图谱上下文、系统化调试、质量检查、生命周期维护和审查指导。

有意不集成 cgraphx。可用时优先使用 GitNexus 和 Understand-Anything 作为推荐的图谱来源。

## 安装

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

### Codex CLI

```bash
git clone https://github.com/crayonYYxm/project-intelligence.git
cd project-intelligence
codex plugin marketplace add .
codex plugin add project-intelligence@project-intelligence
```

安装后启动新的 Codex 线程以加载插件 skills。

## CLI

插件 CLI 位于：

```bash
plugins/project-intelligence/scripts/project-intel
```

常用命令：

```bash
plugins/project-intelligence/scripts/project-intel --project /path/to/repo init
plugins/project-intelligence/scripts/project-intel --project /path/to/repo init --interactive
plugins/project-intelligence/scripts/project-intel --project /path/to/repo lifecycle --task "新需求"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo debug --bug "错误或异常行为"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo spec --title "功能" --from "需求"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo plan --title "功能" --from-spec .project-intel/specs/...
plugins/project-intelligence/scripts/project-intel --project /path/to/repo refresh
plugins/project-intelligence/scripts/project-intel --project /path/to/repo check
plugins/project-intelligence/scripts/project-intel --project /path/to/repo maintain --task "摘要"
plugins/project-intelligence/scripts/project-intel --project /path/to/repo install --hooks
plugins/project-intelligence/scripts/project-intel --project /path/to/repo query "表格"
```

## Skills

- `project-task`：实现前使用项目规范和知识库。
- `project-brainstorm`：塑造需求并比较实现方案。
- `project-spec`：基于项目事实编写需求文档和影响说明。
- `project-plan`：将需求文档转化为实施计划。
- `project-debug`：基于项目上下文和根因纪律调查 bug。
- `project-maintain`：任务或变更后刷新项目知识库。
- `project-review`：基于规范、图谱上下文、质量检查和复用风险审查代码。
- `project-knowledge`：回答组件、API、模块、服务和规范相关问题。
- `project-refresh`：初始化或刷新 `.project-intel`。
- `project-standards`：说明和管理规则等级。
- `project-quality`：运行和解读 lint/type/style/format 和冗余检查。
