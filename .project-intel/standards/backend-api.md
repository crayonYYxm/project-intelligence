# 后端 API 与入口规范

## 框架入口分布

| 框架/入口风格 | 文件数 |
| --- | --- |
| Spring | 3 |

## API/入口清单

| 路径 | 框架 | 入口信号 | 路径样例 | 方法样例 |
| --- | --- | --- | --- | --- |
| plugins/project-intelligence/scripts/project_intel_lib/application.py | Spring | Controller, GetMapping, MessageListener, PostMapping, RequestMapping, RestController |  | now_iso, script_path, run, run_shell, command_exists, user_home, package_manager, slugify |
| plugins/project-intelligence/scripts/project_intel_lib/scanner/backend.py | Spring | Injectable |  | unique_limited, flatten_regex_hits, annotation_values, mask_comments_and_strings, annotation_values_in_code, quoted_literal_at, python_ast_facts, detect_backend_framework |
| plugins/project-intelligence/tests/test_project_intel.py | Spring | GetMapping, PostMapping, RequestMapping, RestController, Scheduled, app | /api/orders; /create; /fake\\\; /fake\\; /comment; /real | symlink_or_skip, test_iter_files_excludes_hidden_paths, test_init_runs_installed_graph_analysis, test_init_asks_before_installing_missing_graph_tool, test_init_continues_when_missing_graph_tool_is_declined, test_noninteractive_init_never_waits_for_missing_tool_input, test_interactive_flag_without_tty_degrades_without_input, test_init_runs_configured_understand_analysis |

## 路径热点

| 路径前缀 | 出现次数 |
| --- | --- |
| api/orders | 1 |
| create | 1 |
| fake\\\ | 1 |
| fake\\ | 1 |
| comment | 1 |
| real | 1 |
| health | 1 |
| fixture | 1 |
| fake | 1 |

## 非标准入口候选

_None detected._

## 约定

- 新增 API 入口应跟随同模块已有框架风格，例如 Spring 注解、Nest 装饰器或 router 注册。
- 不要只靠文件名判断入口；handler、facade、adapter、action 等候选入口需要在初始化后人工确认。
- 入口层只做参数接收、权限/校验编排和响应转换，业务编排应下沉到 Service/UseCase。
- 改入口路径时同步检查调用方、路由/网关配置、鉴权配置、测试和接口文档。
