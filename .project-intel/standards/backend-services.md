# 后端 Service 与业务编排规范

## Service 清单

| 名称 | 路径 | 方法样例 | 事务信号 | 远程调用 | 权限信号 |
| --- | --- | --- | --- | --- | --- |
| backend | plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py | unique_limited, flatten_regex_hits, annotation_values, mask_comments_and_strings, annotation_values_in_code, quoted_literal_at, python_ast_facts, detect_backend_framework, extract_backend_endpoints, extract_backend_methods | 5 | 10 | 7 |
| test_project_intel | plugins/project-intelligence/tests/test_project_intel.py | symlink_or_skip, test_iter_files_excludes_hidden_paths, test_init_runs_installed_graph_analysis, test_init_asks_before_installing_missing_graph_tool, test_init_continues_when_missing_graph_tool_is_declined, test_noninteractive_init_never_waits_for_missing_tool_input, test_interactive_flag_without_tty_degrades_without_input, test_init_runs_configured_understand_analysis, test_repo_runner_and_environment_commands_require_explicit_authorization, test_external_absolute_graph_command_requires_separate_authorization | 1 | 1 | 4 |

## 方法命名前缀热点

| 前缀 | 出现次数 |
| --- | --- |
| test | 29 |
| extract | 13 |
| annotation | 2 |
| scan | 2 |
| unique | 1 |
| flatten | 1 |
| mask | 1 |
| quoted | 1 |
| python | 1 |
| detect | 1 |
| dotted | 1 |
| symlink | 1 |

## 约定

- Controller/API 层不要绕过 Service 直接访问 Repository/Mapper。
- 新增业务流程优先找同域 Service、Manager、UseCase、Facade，复用已有编排方式。
- 涉及写操作、支付、订单、库存、状态机等流程时，先确认事务边界和幂等策略。
- Service 内远程调用要复用已有客户端/适配器，并保留错误映射、超时、重试和日志链路。
