# 工具报告

生成时间：`2026-07-21T10:46:36.779129+00:00`

## 必需工具

| 工具 | 状态 |
| --- | --- |
| python3 | present |
| project-write-access | present |

## 可选运行时

- Git：`present`
- Node：`present`
- GitNexus：`present`
- Understand-Anything：`present`

## 包管理器

| 名称 | 状态 | 已选 |
| --- | --- | --- |
| pnpm | present |  |
| npm | present | yes |
| yarn | missing |  |

## 质量命令

| 类型 | 状态 | 命令 |
| --- | --- | --- |
| test | configured | npm run test |

## 推荐操作

_None detected._

## 后续 Agent 步骤

| 工具 | 图谱命令 | 刷新命令 | 说明 |
| --- | --- | --- | --- |
| Understand-Anything | /understand . --language zh | /project-refresh | Understand-Anything 已安装到 Codex/Claude Code agent，但当前 shell 没有 `understand` 命令。如果是在 Claude Code 刚完成安装/启用，请先运行 /reload-plugins 重新加载插件，再在当前 agent 会话中运行 /understand . --language zh 或触发 Understand-Anything skill，生成图谱后立即执行 /project-refresh；如果不能触发 slash command，执行 project-intel refresh。 |

## 安装结果

_None detected._

`init` 会检查图谱工具。已检测到可执行分析命令时会自动运行分析；未检测到时会询问是否安装/初始化，选择跳过时继续初始化 `.project-intel`。使用 `--setup-missing` 可跳过询问并直接运行支持的安装/初始化命令。对于只能在 agent 会话里执行的图谱工具，CLI 会把它们列到“后续 Agent 步骤”，但不会把初始化视为失败或反复要求重跑。
