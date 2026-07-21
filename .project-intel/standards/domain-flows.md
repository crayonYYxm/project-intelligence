# 业务流与图谱规范

## 业务域候选

以下内容来自 Understand-Anything 图谱摘要和项目轻量扫描，默认是 `inferred/candidate`，用于需求前影响分析：

| 业务域 | 节点/文件数 | 关键路径 | 图谱摘要 |
| --- | --- | --- | --- |
| project_intel_lib | 290 | plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py, plugins/project-intelligence/scripts/project_intel_lib/application.py | 规范化 finish/test 阶段传入的测试文件列表。；读取项目配置中的测试命令列表。 |
| tests | 39 | plugins/project-intelligence/tests/design_fixtures.py, plugins/project-intelligence/tests/design_fixtures.py, plugins/project-intelligence/tests/design_fixtures.py, plugins/project-intelligence/tests/design_fixtures.py, plugins/project-intelligence/tests/test_document_truth_validation.py, plugins/project-intelligence/tests/test_document_truth_validation.py, plugins/project-intelligence/tests/test_document_truth_validation.py, plugins/project-intelligence/tests/test_document_truth_validation.py | 为需求/Bug 测试用例提供统一的文档与设计脚手架文本生成器，是 tests 目录下多个 unittest 模块共享的 fixture 工厂。；生成符合规范的需求文档模板文本，支持 requirement 与 bug 两种 kind，包含验收标准与外部接口影响章节。 |
| scanner | 35 | plugins/project-intelligence/scripts/project_intel_lib/scanner/__init__.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py, plugins/project-intelligence/scripts/project_intel_lib/scanner/frontend.py | scanner 子包入口，re-export scan_backend/scan_frontend/extract_emits/extract_vue_props 四个对外扫描 API。；前端扫描器：从 Vue/React/TS/JS 源码中提取组件 props/emits/slots/expose、依赖、API 端点、service 前缀与路由模块信息，供 infer_standards 与 manifest 使用。 |
| scripts | 20 | scripts/run-skill-evals.mjs, scripts/skill-eval-events.mjs, scripts/validate-skill-evals.mjs, scripts/run-skill-evals.mjs, scripts/run-skill-evals.mjs, scripts/run-skill-evals.mjs, scripts/skill-eval-events.mjs, scripts/skill-eval-events.mjs | 针对 Claude 或 Codex 代理运行 skill 行为评测的脚手架脚本，按场景构造提示词、spawn 代理 CLI 并校验实际触发的 skill 路由是否符合预期。；纯函数工具模块，从代理 stdout 中解析 skill 工具调用事件，并评估实际触发的 skill 路由是否匹配场景的期望、禁止与顺序约束。 |
| standards | 19 | .project-intel/standards/api.md, .project-intel/standards/backend-api.md, .project-intel/standards/backend-async.md, .project-intel/standards/backend-config.md, .project-intel/standards/backend-errors.md, .project-intel/standards/backend-models.md, .project-intel/standards/backend-remote-calls.md, .project-intel/standards/backend-repository.md | 前端 API 与请求规范，约定接口放置位置、请求封装复用、服务前缀与接口路径热点，禁止页面/组件直接调用 uni.request、axios 或裸 fetch。；后端 API 与入口规范，记录框架入口分布、API/入口清单、路径热点与非标准入口候选，指导新增 API 的入口声明方式。 |
| configuration | 7 | package.json, .claude-plugin/marketplace.json, .npmignore, .project-intel/config.json, .project-intel/manifest.json, .ua/.understandignore, .ua/config.json | Project Intelligence 的 npm 包清单，声明包名、版本、ESM 模块类型、CLI bin 入口、发布文件列表、Node 引擎要求及构建/发布脚本，是包发布与本地开发的核心配置。；Claude Code 插件市场清单，引用 Anthropic marketplace schema，声明 project-intelligence 插件的名称、描述、分类与 GitHub 主页。 |
| documentation | 5 | AGENTS.md, CHANGELOG.md, CLAUDE.md, README.md, .claude/CLAUDE.md | 面向 Codex/通用 Agent 的项目级指令文件，汇总 Project Intelligence 与 GitNexus 的工作守则、资源清单、CLI 用法及技能调用规则，供 Agent 在仓库内自动加载遵循。；Project Intelligence 的版本发布日志，按版本号倒序记录从 0.1.13 到 0.6.1 的功能新增、修复与变更，是项目演进历史的单一事实来源。 |
| reports | 4 | .project-intel/reports/frontend-quality.md, .project-intel/reports/init-report.md, .project-intel/reports/redundancy-report.md, .project-intel/reports/tooling-report.md | 前端质量报告，记录 Hard 规范检测、质量命令、命令输出与冗余候选情况；本次检测中各项目均为空或未执行。；Project Intelligence 初始化生成的总览报告，汇总图谱来源、前后端概况、质量命令与后续 Agent 步骤，并指引用户补全 Understand-Anything 图谱。 |
| knowledge | 3 | .project-intel/knowledge/backend.json, .project-intel/knowledge/files.json, .project-intel/knowledge/frontend.json | 项目后端知识库快照，由 project-intelligence 扫描器生成，汇总 13 个维度的后端结构信号：API、服务、仓储、配置、权限校验、事务、远程调用、消息任务、错误码等，覆盖 application.py、scanner/backend.py 及相关测试文件，扫描模式为 python-ast 与 regex-fallback。；项目文件清单索引，记录 49 个项目文件的路径、大小、修改时间与后缀，作为 backend.json / frontend.json 知识扫描的输入清单，涵盖文档、Python 脚本、SKILL.md、测试与配置文件。 |
| project-intelligence | 2 | plugins/project-intelligence/.claude-plugin/plugin.json, plugins/project-intelligence/.codex-plugin/plugin.json | Claude Code 插件清单，声明 project-intelligence 插件的名称、版本、描述与作者，供 .claude-plugin/marketplace.json 引用与安装。；Codex CLI 插件清单，声明 project-intelligence 插件的名称、版本、描述、作者，并指向 skills 目录与 OpenAI/Claude agent 接口配置，供 .agents/plugins/marketplace.json 引用与安装。 |
| references | 2 | plugins/project-intelligence/skills/project-design/references/bug-design-template.md, plugins/project-intelligence/skills/project-design/references/requirement-design-template.md | Bug 开发设计文档精简模板：五段式结构（现象/原因/修复/影响/验证），正文控制在 120 行内，禁用需求型元数据、源码证据表与 AC 列表。；Requirement 开发设计文档模板：CRM 风格中文业务设计结构，含场景分析、实现方案、字段流转与相对路径#符号依据，要求最多 3 个关键代码块与必要的 Mermaid 图。 |
| workflows | 2 | .github/workflows/live-skill-evals.yml, .github/workflows/validate.yml | GitHub Actions 定时工作流，每周一 02:30 UTC 或手动触发，分别针对 Claude 与 Codex 两个 agent 运行隔离的 skill 评测，缺少对应 API Key 时安全跳过。；GitHub Actions 校验工作流，在 push 与 pull_request 时触发；test job 矩阵跑 Python 3.9/3.10/3.12 的单元测试与多脚本校验，cli-smoke job 在 ubuntu/macos/windows 三平台执行冒烟测试。 |
| agents | 1 | plugins/project-intelligence/skills/project-design/agents/openai.yaml | project-design 技能的 OpenAI/Claude agent 接口配置，定义展示名称、简短描述与默认提示语，用于把本地工单与仓库分析转化为已校验的开发设计文档。 |
| bin | 1 | bin/project-intel.mjs | Node CLI 入口 shim，定位包内 plugins/project-intelligence/scripts/project_intel.py，按平台候选 python3/python/py 依次 spawnSync 调用并透传参数与退出码，缺失或无 Python 时报错退出。 |
| gitnexus-cli | 1 | .claude/skills/gitnexus/gitnexus-cli/SKILL.md | GitNexus CLI 命令参考，覆盖 analyze、status、clean、wiki、list 五个子命令及其 flag，说明项目本地 runner 的回退选择与常见排错。 |
| gitnexus-debugging | 1 | .claude/skills/gitnexus/gitnexus-debugging/SKILL.md | GitNexus 调试技能文档，给出从症状到根因的工作流、checklist、症状对照表，以及 query/context/cypher/trace 工具的用法示例。 |
| gitnexus-exploring | 1 | .claude/skills/gitnexus/gitnexus-exploring/SKILL.md | GitNexus 代码探索技能文档，说明如何用 query/context 与 process/clusters 资源理解陌生代码库的架构与执行流。 |
| gitnexus-guide | 1 | .claude/skills/gitnexus/gitnexus-guide/SKILL.md | GitNexus 总览参考，集中列出全部 MCP 工具、轻量资源、图谱 schema，以及 list_repos 分页、explain 污点、pdg_query 依赖、trace 最短路径等高级用法。 |
| gitnexus-impact-analysis | 1 | .claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md | GitNexus 影响分析技能文档，定义 impact 按深度分级 (d=1 必坏/d=2 可能/d=3 需测) 的风险评估表与 detect_changes 提交前检查流程。 |
| gitnexus-refactoring | 1 | .claude/skills/gitnexus/gitnexus-refactoring/SKILL.md | GitNexus 重构技能文档，提供 rename、extract、split 三类重构的 checklist，结合 rename 多文件改名与 detect_changes 验证作用域，并列出风险缓解规则。 |

## 关键模块摘要

_None detected._

## 图谱路径热点

| 路径前缀 | 节点数 |
| --- | --- |
| plugins/project-intelligence/scripts/project_intel_lib | 325 |
| plugins/project-intelligence/tests/test_project_intel.py | 17 |
| plugins/project-intelligence/skills/project-design | 5 |
| plugins/project-intelligence/tests/design_fixtures.py | 4 |
| plugins/project-intelligence/tests/test_document_truth_validation.py | 4 |
| scripts/run-skill-evals.mjs | 4 |
| scripts/skill-eval-events.mjs | 4 |
| plugins/project-intelligence/tests/test_requirement_hardening.py | 3 |
| plugins/project-intelligence/tests/test_requirement_layout_v2.py | 3 |
| scripts/validate_bundle.py | 3 |
| plugins/project-intelligence/tests/test_project_design.py | 2 |
| plugins/project-intelligence/tests/test_project_test.py | 2 |
| plugins/project-intelligence/tests/test_requirement_workflow.py | 2 |
| plugins/project-intelligence/tests/test_testing_security.py | 2 |
| scripts/check-package.mjs | 2 |
| scripts/validate-skill-evals.mjs | 1 |
| .github/workflows/live-skill-evals.yml | 1 |
| .github/workflows/validate.yml | 1 |
| .project-intel/knowledge/backend.json | 1 |
| .project-intel/knowledge/files.json | 1 |

## 约定

- 需求涉及任一业务域时，先按项目实际目录、模块和图谱标签定位对应业务域，再查 GitNexus/Understand-Anything 影响面。
- 修改业务流入口时需要同时检查页面、路由、API 模块、store、公共组件和错误处理链路。
- 图谱摘要只作为项目理解和影响分析输入，不替代源码确认；最终实现仍以源码和 `.project-intel/knowledge` 为准。
