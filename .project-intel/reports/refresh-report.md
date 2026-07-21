# 项目智能报告

生成时间：`2026-07-21T10:46:36.799622+00:00`

项目根目录：`/Users/xumeng/Desktop/code/project-intelligence`

## 图谱来源

| 来源 | 状态 | 用途 | 路径 |
| --- | --- | --- | --- |
| GitNexus | present | 符号调用、影响、变更风险 | .gitnexus/meta.json |
| Understand-Anything | present | 架构、模块、领域流、入职 | .understand-anything/knowledge-graph.json |

## 前端概况

- 组件数：0
- Hooks 数：0
- API 模块数：0
- 冗余候选数：0

## 后端概况

- API / 入口模块数：3
- 服务数：2
- 数据类型数：0
- 仓库 / 映射器数：1
- 候选入口点数：0

## 质量命令

| 类型 | 命令 | 来源 |
| --- | --- | --- |
| test | npm run test | package.json |

## 推荐的工具操作

_None detected._

## 后续 Agent 步骤

| 工具 | 图谱命令 | 刷新命令 | 说明 |
| --- | --- | --- | --- |
| Understand-Anything | /understand . --language zh | /project-refresh | Understand-Anything 已安装到 Codex/Claude Code agent，但当前 shell 没有 `understand` 命令。如果是在 Claude Code 刚完成安装/启用，请先运行 /reload-plugins 重新加载插件，再在当前 agent 会话中运行 /understand . --language zh 或触发 Understand-Anything skill，生成图谱后立即执行 /project-refresh；如果不能触发 slash command，执行 project-intel refresh。 |
