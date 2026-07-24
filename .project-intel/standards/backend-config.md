# 后端配置规范

## 配置文件/配置类

| 路径 | 类型 | 配置键样例 |
| --- | --- | --- |
| .github/workflows/live-skill-evals.yml | yml | name, on, workflow_dispatch, schedule, jobs, claude, runs-on, steps, with, node-version, env, ANTHROPIC_API_KEY, run, codex, OPENAI_API_KEY |
| .github/workflows/validate.yml | yml | name, on, push, pull_request, jobs, node-core, runs-on, strategy, matrix, os, node-version, steps, with, run |
| plugins/project-intelligence/skills/project-design/agents/openai.yaml | yaml | interface, display_name, short_description, default_prompt |

## 配置前缀热点

| 前缀 | 出现次数 |
| --- | --- |
| name | 2 |
| on | 2 |
| jobs | 2 |
| runs-on | 2 |
| steps | 2 |
| with | 2 |
| node-version | 2 |
| run | 2 |
| workflow_dispatch | 1 |
| schedule | 1 |
| claude | 1 |
| env | 1 |
| ANTHROPIC_API_KEY | 1 |
| codex | 1 |
| OPENAI_API_KEY | 1 |
| push | 1 |
| pull_request | 1 |
| node-core | 1 |
| strategy | 1 |
| matrix | 1 |
| os | 1 |
| interface | 1 |
| display_name | 1 |
| short_description | 1 |
| default_prompt | 1 |

## 约定

- 新增配置项优先放到同域已有配置文件或配置类，并保持前缀命名一致。
- 配置变更需要同步默认值、环境变量、测试环境配置、部署文档和回滚策略。
- 涉及开关、限流、超时、重试、灰度的配置，需要在 review 中说明默认行为。
- 不要把密钥、token、密码或私有地址沉淀到项目规范；这里只保留配置键和路径。
