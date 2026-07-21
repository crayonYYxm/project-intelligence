#!/usr/bin/env python3
"""Generate GraphFragment nodes/edges for batch 1 of project-intelligence."""
from __future__ import annotations
import json, math, os

RESULTS_PATH = "/Users/xumeng/Desktop/code/project-intelligence/.ua/tmp/ua-file-extract-results-1.json"
OUT_DIR = "/Users/xumeng/Desktop/code/project-intelligence/.ua/intermediate"

BASE = "plugins/project-intelligence/scripts/project_intel_lib"
APP = f"{BASE}/application.py"
INIT = f"{BASE}/__init__.py"
CLI = f"{BASE}/cli.py"
CORE = f"{BASE}/core.py"
SCANNER_INIT = f"{BASE}/scanner/__init__.py"
BACKEND = f"{BASE}/scanner/backend.py"
FRONTEND = f"{BASE}/scanner/frontend.py"

with open(RESULTS_PATH) as f:
    EXTRACT = json.load(f)
RESULTS = {r["path"]: r for r in EXTRACT["results"]}

# --- Application.py: curated summaries for important functions -----------------
APP_FUNC_SUMMARIES = {
    "run": "在指定工作目录执行命令并以超时控制捕获 stdout/stderr。",
    "run_shell": "通过 shell 解析执行命令字符串，复用 run 的超时与捕获逻辑。",
    "read_text": "安全读取文件前若干字节文本，自动跳过二进制与超大文件。",
    "write_text": "原子写入文本到文件，必要时创建父目录并截断已有内容。",
    "_assert_safe_managed_path": "断言 managed block 的相对路径落在 root 之内，阻止越界写入。",
    "_replace_single_managed_block": "在一段文本中按起止标记替换单个 managed block，缺失时可选追加。",
    "upsert_adapter_managed_block": "在 adapter 文件中按标记插入或替换 managed block，支持 dry-run。",
    "remove_adapter_managed_block": "从 adapter 文件中移除指定标记区间的 managed block，支持 dry-run。",
    "upsert_managed_block_with_markers": "以自定义起止标记在任意文件中插入或替换 managed block。",
    "remove_managed_block_with_markers": "按自定义起止标记从文件中移除 managed block。",
    "cleanup_legacy_local_skills": "清理 v0.1.7 及更早版本遗留到目标项目的 local skill 副本。",
    "load_json_strict": "严格读取并解析 JSON 文件，解析失败时报错带标签。",
    "project_root": "从 CLI 参数解析并校验项目根目录，默认使用当前工作目录。",
    "path_matches_pattern": "按 gitignore 风格 glob 匹配相对路径，支持目录与文件通配。",
    "is_excluded": "判断路径是否被项目配置或内置排除目录命中。",
    "iter_project_files": "遍历项目文件并按配置过滤，text_only 模式仅保留可读文本后缀。",
    "git_info": "通过 git 命令收集当前分支、HEAD 提交与 remote 等仓库元信息。",
    "detect_package": "探测项目包管理器、构建框架与 monorepo 结构，输出 package 摘要。",
    "detect_quality_commands": "结合项目类型推断 lint/format/test/类型检查等质量工具命令。",
    "understand_plugin_roots": "枚举 Understand-Anything 插件在各 agent 平台的安装根目录。",
    "current_agent_platform": "识别当前运行的 agent 平台（claude / codex / 其他）。",
    "claude_understand_installs": "枚举 Claude 侧 Understand-Anything 插件的已知安装位置与状态。",
    "claude_plugin_list_statuses": "调用 claude plugin list 并解析插件启用/安装状态。",
    "understand_installed_platforms": "汇总 Understand-Anything 在各 agent 平台的已安装情况。",
    "understand_install_options": "为各平台生成 Understand-Anything 的安装/启用命令候选项。",
    "detect_graph_actions": "检测项目可执行的图谱分析动作（analyze/refresh）及其命令来源。",
    "detect_quality_tool_status": "检查质量工具（eslint/prettier/tsc 等）在项目中的可用状态。",
    "detect_tooling": "综合探测 git/node/包管理器/质量工具/图谱工具，生成完整 tooling 摘要。",
    "print_tooling_summary": "以人类可读表格输出工具探测结果，标红缺失项。",
    "print_graph_tools_report": "输出图谱工具状态报告，支持 JSON 与文本两种格式。",
    "run_graph_command": "执行图谱分析命令并捕获 stdout/stderr/退出码，应用超时控制。",
    "command_uses_external_path": "判断图谱命令是否引用项目根目录之外的路径。",
    "graph_command_authorized": "按权限开关判定图谱命令是否被允许执行。",
    "choose_install_option": "在交互或自动模式下为图谱动作选择安装方案。",
    "run_install_option": "执行选定的 Understand-Anything 安装/启用命令。",
    "verify_understand_claude_install": "校验 Claude 侧 Understand-Anything 插件安装与启用状态。",
    "setup_graph_tools": "为缺失的图谱工具执行安装/启用，并校验安装结果。",
    "handle_tooling_setup": "按交互/自动模式编排图谱工具的批量安装流程。",
    "extract_backend_endpoints": "facade：委托 backend_scanner 提取后端路由/端点注解。",
    "scan_frontend": "facade：调用 frontend_scanner.scan_frontend 扫描前端组件与依赖。",
    "scan_backend": "facade：调用 backend_scanner.scan_backend 扫描后端结构信号。",
    "file_index": "为扫描到的文件构建相对路径与签名索引。",
    "build_manifest": "汇总 package、扫描结果、图谱来源与工具状态生成项目 manifest。",
    "default_config": "为项目生成默认配置，包含 exclude/include/质量命令等字段。",
    "validate_string_list": "校验配置字段是否为非空字符串列表，按需允许空列表。",
    "validate_relative_pattern": "校验配置中的 glob 模式是否合法且为相对路径。",
    "validate_project_config": "全面校验 .project-intel 配置 schema，报告字段级错误。",
    "merge_quality_commands": "将探测到的质量命令与用户已有配置合并，优先保留用户配置。",
    "prepare_project_config": "结合探测结果生成待写入的项目配置并做字段校验。",
    "read_project_config": "读取并解析 .project-intel 配置文件，缺失时返回默认值。",
    "infer_standards": "依据前端/后端扫描结果推断项目级开发规范规则集合。",
    "render_inferred_rules": "将推断出的规则渲染成 markdown 文本片段。",
    "render_components_standard": "渲染前端组件命名/组织/复用相关规范文档。",
    "render_api_standard": "渲染前端 API 调用/封装相关规范文档。",
    "render_router_standard": "渲染前端路由组织与命名规范文档。",
    "render_domain_flows_standard": "渲染基于图谱的领域流程规范文档。",
    "render_backend_api_standard": "渲染后端 API/控制器层规范文档。",
    "render_backend_services_standard": "渲染后端服务层规范文档。",
    "render_backend_models_standard": "渲染后端数据模型层规范文档。",
    "render_backend_repository_standard": "渲染后端仓储层规范文档。",
    "render_backend_config_standard": "渲染后端配置管理规范文档。",
    "render_backend_security_standard": "渲染后端安全（鉴权/越权）规范文档。",
    "render_backend_transaction_standard": "渲染后端事务边界规范文档。",
    "render_backend_remote_calls_standard": "渲染后端远程调用规范文档。",
    "render_backend_async_standard": "渲染后端异步/消息任务规范文档。",
    "render_backend_errors_standard": "渲染后端错误码与异常处理规范文档。",
    "render_backend_utilities_standard": "渲染后端工具/公共函数规范文档。",
    "standards_docs": "将所有规范渲染为按主题分组的 markdown 文档集合。",
    "table": "将表头与行列表渲染为对齐的纯文本表格。",
    "collect_project_state": "采集 package/tooling/扫描结果/配置汇总成项目状态快照。",
    "preview_init": "预览 project-intel init 将写入的文件清单与变更摘要。",
    "init_project": "执行项目初始化：写配置、生成 manifest、装配 adapter、可选安装图谱工具。",
    "ensure_project_intel_gitignore": "确保 .project-intel 目录被加入项目 .gitignore。",
    "ensure_gitignore": "维护项目 .gitignore，注入 project-intel 推荐的忽略条目。",
    "build_init_report": "生成 init 命令的人类可读报告，覆盖 manifest/前后端/工具状态。",
    "build_project_status": "生成 status 命令报告，展示项目事实、工具与图谱状态。",
    "build_redundancy_report": "基于前端扫描结果生成可复用组件冗余报告。",
    "build_tooling_report": "生成工具探测与安装结果的报告。",
    "load_project_snapshot": "加载 .project-intel 下的 manifest 与扫描快照。",
    "collect_reuse_candidates": "从快照中筛选最可能被复用的组件候选项。",
    "standard_paths": "枚举快照中出现的规范/文档路径。",
    "infer_affected_areas": "根据任务描述与快照推断受影响的代码区域。",
    "analyze_task_intake": "执行 intake 分析：分流 quick/standard/complex 并产出影响面与建议。",
    "build_intake_doc": "生成 intake 阶段的 markdown 文档，含分流结果与影响面。",
    "write_intake": "将 intake 文档写入 .project-intel 并返回路径。",
    "build_spec_doc": "生成需求 spec 文档，含验收标准与 source-backed 依据。",
    "write_spec": "将 spec 文档写入项目并返回路径。",
    "build_plan_doc": "基于 spec 生成可执行的实施计划文档。",
    "write_plan": "将实施计划写入项目并返回路径。",
    "build_task_impact_doc": "生成任务影响面文档，覆盖测试类型、报告动作与验收编号。",
    "lifecycle_payload": "组装 lifecycle 阶段共享的事件 payload。",
    "write_lifecycle": "将 lifecycle 事件写入项目并返回路径。",
    "build_debug_doc": "生成 Bug 调查上下文文档，含受影响面与可复用线索。",
    "write_debug_context": "将 debug 上下文写入项目并返回路径。",
    "contains_cjk": "判断字符串是否包含中日韩字符，用于规范摘要展示。",
    "normalize_requirement_summary": "规范化需求摘要文本，统一换行与空白。",
    "normalize_project_file": "将用户输入的项目文件路径规范化为相对路径。",
    "should_track_requirement_file": "判断相对路径是否应纳入需求级文件跟踪。",
    "changed_requirement_files": "结合 git diff 列出本需求跟踪范围内变更的文件。",
    "requirement_doc_path": "为指定文件推导对应的 per-file 需求文档路径。",
    "build_file_requirement_doc": "为单个文件生成 per-file 需求文档内容。",
    "resolve_requirement_files": "解析需求任务涉及的全部相对路径集合。",
    "write_file_requirement_docs": "批量写入 per-file 需求文档。",
    "update_file_requirement_docs": "按变更文件更新对应的 per-file 需求文档。",
    "build_maintenance_report": "生成 maintain 阶段报告，覆盖刷新/退出码/质量/需求文档。",
    "maintain_project": "执行 maintain 流程：刷新事实、运行质量、归档需求、更新文档。",
    "finish_changed_files": "规范化并去重 finish 阶段传入的变更文件列表。",
    "normalize_test_files": "规范化 finish/test 阶段传入的测试文件列表。",
    "configured_test_commands": "读取项目配置中的测试命令列表。",
    "run_project_test": "执行测试运行并产出 RED/GREEN/回归证据，支持手动审批与失败预期。",
    "git_diff_summary": "对 git diff 输出做摘要，列出变更文件与增删行数。",
    "build_finish_report": "生成 finish 阶段报告，覆盖变更、质量、测试证据与验收。",
    "finish_project": "执行 finish 流程：检查测试/质量证据、归档需求并输出报告。",
    "hook_script_body": "生成 git hook 脚本内容，调用 project-intel 校验命令。",
    "write_hook_templates": "将 hook 脚本模板写入 .project-intel/hooks 目录。",
    "git_hooks_path": "解析当前仓库的 git hooks 路径，可选放行外部路径。",
    "activate_git_hooks": "将 project-intel hook 模板链接到 git hooks 目录。",
    "agent_project_intelligence_priority_rules": "生成 agent 优先级规则文本，用于 adapter 注入。",
    "project_agent_rules": "生成项目级 agent 规则文本，覆盖工作流与质量约束。",
    "claude_project_agent_rules": "生成 Claude 平台特定的项目 agent 规则文本。",
    "codex_adapter_rules": "生成 Codex adapter 的注入规则文本。",
    "claude_adapter_rules": "生成 Claude adapter 的注入规则文本。",
    "nested_claude_adapter_rules": "生成嵌套 Claude adapter 的精简规则文本。",
    "_adapter_targets": "枚举 adapter 注入目标文件及其存在性状态。",
    "adapters_preview": "预览 adapter 注入将修改的文件与内容片段。",
    "adapters_status": "展示各 adapter 目标的当前注入状态。",
    "adapters_apply": "向目标文件注入 adapter 规则块，支持 dry-run。",
    "adapters_remove": "从目标文件移除 adapter 规则块，支持 dry-run。",
    "write_agent_entrypoints": "在项目根写入 agent 入口文件（AGENTS.md / CLAUDE.md）。",
    "install_claude": "为 Claude 平台安装 project-intel 入口与可选 hooks。",
    "hard_rule_text": "将单条 hard rule 渲染为可写入文件的文本片段。",
    "selected_hard_rule_files": "根据配置与 check 标志选出需要执行 hard rule 校验的文件。",
    "run_hard_rule_checks": "对选定文件执行 forbid/require 类 hard rule 校验并收集结果。",
    "markdown_command_output": "将命令执行结果格式化为 markdown 代码块输出。",
    "run_check": "执行 check 命令：运行 hard rules 与可选质量工具并汇总结果。",
    "build_quality_report": "汇总质量工具与 hard rule 校验结果生成质量报告。",
    "query_project": "基于项目快照对自然语言查询做关键词匹配并返回相关条目。",
    "report_graph_tools": "输出图谱工具状态报告，支持 JSON 格式。",
    "marketplace_bundle_root": "解析 agent 插件 marketplace 包的根路径。",
    "agent_install_commands": "为指定 agent 平台生成插件安装命令序列。",
    "install_agent_plugin": "为目标 agent 平台安装 project-intelligence 插件，支持 dry-run。",
    "doctor_report": "生成 doctor 诊断报告，检查项目初始化与工具健康度。",
    "build_parser": "构建 project-intel CLI 的 argparse 命令树，覆盖全部子命令与选项。",
    "comma_values": "将逗号分隔的字符串值解析为去重的字符串列表。",
    "parse_review_findings": "解析 review 子命令传入的 findings 字符串为结构化列表。",
    "parse_acceptance_values": "解析验收标准编号字符串为去重的整数列表。",
    "legacy_workflow_warning": "生成旧版工作流命令的弃用提示文本。",
    "require_legacy": "在旧版命令模式下发出提示并继续派发。",
    "dispatch_command": "命令派发核心：按 args.command 路由到对应子命令处理函数。",
    "main": "CLI 入口：解析参数、处理 --json/--version 并派发命令。",
    "detect_package_manager": "探测系统可用的包管理器并返回首选项。",
}

# Subset of important / exported functions in application.py that we explicitly
# tag (others get generic tags).
APP_FUNC_TAGS = {
    "main": ["entry-point", "cli", "dispatch"],
    "dispatch_command": ["dispatch", "cli", "command-router"],
    "build_parser": ["cli", "argparse", "command-tree"],
    "init_project": ["init", "lifecycle", "bootstrap"],
    "preview_init": ["init", "preview", "dry-run"],
    "build_project_status": ["status", "report", "lifecycle"],
    "collect_project_state": ["snapshot", "scan", "state"],
    "build_manifest": ["manifest", "scan", "report"],
    "detect_tooling": ["tooling", "detection", "scan"],
    "detect_quality_tool_status": ["tooling", "quality", "detection"],
    "detect_quality_commands": ["tooling", "quality", "detection"],
    "setup_graph_tools": ["tooling", "graph-tools", "installer"],
    "handle_tooling_setup": ["tooling", "graph-tools", "orchestration"],
    "run_graph_command": ["graph-tools", "runner", "subprocess"],
    "graph_command_authorized": ["graph-tools", "security", "authorization"],
    "verify_understand_claude_install": ["understand-anything", "claude", "verifier"],
    "understand_install_options": ["understand-anything", "installer", "options"],
    "analyze_task_intake": ["intake", "lifecycle", "triage"],
    "build_intake_doc": ["intake", "documentation", "lifecycle"],
    "write_intake": ["intake", "writer", "lifecycle"],
    "build_spec_doc": ["spec", "documentation", "lifecycle"],
    "write_spec": ["spec", "writer", "lifecycle"],
    "build_plan_doc": ["plan", "documentation", "lifecycle"],
    "write_plan": ["plan", "writer", "lifecycle"],
    "build_task_impact_doc": ["impact", "documentation", "lifecycle"],
    "lifecycle_payload": ["lifecycle", "payload", "event"],
    "write_lifecycle": ["lifecycle", "writer", "event"],
    "build_debug_doc": ["debug", "documentation", "lifecycle"],
    "write_debug_context": ["debug", "writer", "lifecycle"],
    "run_project_test": ["test", "runner", "evidence"],
    "build_finish_report": ["finish", "report", "lifecycle"],
    "finish_project": ["finish", "lifecycle", "gate"],
    "maintain_project": ["maintain", "lifecycle", "refresh"],
    "build_maintenance_report": ["maintain", "report", "lifecycle"],
    "run_check": ["check", "quality", "runner"],
    "build_quality_report": ["quality", "report", "validation"],
    "run_hard_rule_checks": ["hard-rules", "validation", "runner"],
    "validate_project_config": ["config", "validation", "schema"],
    "prepare_project_config": ["config", "writer", "bootstrap"],
    "default_config": ["config", "factory", "defaults"],
    "read_project_config": ["config", "reader"],
    "infer_standards": ["standards", "inference", "scan"],
    "standards_docs": ["standards", "documentation", "renderer"],
    "render_components_standard": ["standards", "frontend", "renderer"],
    "render_api_standard": ["standards", "frontend", "renderer"],
    "render_backend_api_standard": ["standards", "backend", "renderer"],
    "render_backend_services_standard": ["standards", "backend", "renderer"],
    "render_backend_models_standard": ["standards", "backend", "renderer"],
    "adapters_apply": ["adapter", "writer", "agent-rules"],
    "adapters_remove": ["adapter", "writer", "agent-rules"],
    "adapters_status": ["adapter", "status", "agent-rules"],
    "adapters_preview": ["adapter", "preview", "agent-rules"],
    "write_agent_entrypoints": ["adapter", "entrypoint", "agent-rules"],
    "install_claude": ["adapter", "claude", "installer"],
    "activate_git_hooks": ["hooks", "git", "installer"],
    "write_hook_templates": ["hooks", "writer", "git"],
    "doctor_report": ["doctor", "diagnostics", "report"],
    "install_agent_plugin": ["agent-plugin", "installer", "marketplace"],
    "query_project": ["query", "search", "knowledge"],
    "detect_package": ["package", "detection", "scan"],
    "iter_project_files": ["scan", "file-walker", "filter"],
    "read_text": ["io", "reader", "safe"],
    "write_text": ["io", "writer", "atomic"],
    "run": ["subprocess", "runner", "io"],
    "run_shell": ["subprocess", "runner", "shell"],
    "scan_frontend": ["scanner", "facade", "frontend"],
    "scan_backend": ["scanner", "facade", "backend"],
    "extract_backend_endpoints": ["scanner", "facade", "backend"],
}

def app_func_complexity(fn):
    lines = fn["endLine"] - fn["startLine"] + 1
    if lines >= 100:
        return "complex"
    if lines >= 30:
        return "moderate"
    return "simple"

def make_function_node(path, fn, summary, tags, complexity=None):
    lines = fn["endLine"] - fn["startLine"] + 1
    if complexity is None:
        complexity = "complex" if lines >= 100 else ("moderate" if lines >= 30 else "simple")
    return {
        "id": f"function:{path}:{fn['name']}",
        "type": "function",
        "name": fn["name"],
        "filePath": path,
        "lineRange": [fn["startLine"], fn["endLine"]],
        "summary": summary,
        "tags": tags,
        "complexity": complexity,
    }

def make_class_node(path, cls, summary, tags):
    return {
        "id": f"class:{path}:{cls['name']}",
        "type": "class",
        "name": cls["name"],
        "filePath": path,
        "lineRange": [cls["startLine"], cls["endLine"]],
        "summary": summary,
        "tags": tags,
        "complexity": "moderate" if (cls["endLine"] - cls["startLine"] + 1) >= 30 else "simple",
    }

nodes = []
edges = []

# ---------------- File nodes ----------------
file_nodes = [
    {
        "id": f"file:{INIT}",
        "type": "file",
        "name": "__init__.py",
        "filePath": INIT,
        "summary": "project_intel_lib 包入口，re-export core 模块的 IncrementalScanCache、file_signature、sanitize_tooling 三个公共符号。",
        "tags": ["entry-point", "barrel", "package-init"],
        "complexity": "simple",
        "languageNotes": "Python 包 barrel：通过 __all__ 显式约束 re-export 范围。",
    },
    {
        "id": f"file:{APP}",
        "type": "file",
        "name": "application.py",
        "filePath": APP,
        "summary": "project-intel CLI 的应用服务层与命令派发核心，承载 init/status/intake/spec/plan/test/finish/maintain/check 等全部子命令实现、项目扫描装配、工具探测、规范渲染与 adapter 注入。",
        "tags": ["entry-point", "cli", "application-core", "dispatch", "lifecycle"],
        "complexity": "complex",
        "languageNotes": "单文件 5696 行聚合了 CLI 解析、命令派发与生命周期服务；通过 module-level 别名把 scanner/graph 子模块的函数暴露为公共 facade。",
    },
    {
        "id": f"file:{CLI}",
        "type": "file",
        "name": "cli.py",
        "filePath": CLI,
        "summary": "CLI 共享工具层：提供 --json 全局选项提取、统一 JSON envelope 输出与错误文本脱敏。",
        "tags": ["utility", "cli", "serialization", "security"],
        "complexity": "simple",
        "languageNotes": "json_envelope 是 CLI 与 agent 调用方的统一返回契约；_sanitize_error_text 在输出前对 token/密钥做正则脱敏。",
    },
    {
        "id": f"file:{CORE}",
        "type": "file",
        "name": "core.py",
        "filePath": CORE,
        "summary": "扫描与工具状态的核心原语：file_signature 提供基于 size+mtime 的廉价缓存签名，IncrementalScanCache 提供增量扫描缓存，sanitize_tooling 抽取可持久化的工具状态子集。",
        "tags": ["utility", "cache", "data-model", "serialization"],
        "complexity": "moderate",
        "languageNotes": "IncrementalScanCache 用 schemaVersion + per-file signature 实现增量扫描复用；sanitize_tooling 限定可提交到仓库的工具状态字段。",
    },
    {
        "id": f"file:{SCANNER_INIT}",
        "type": "file",
        "name": "__init__.py",
        "filePath": SCANNER_INIT,
        "summary": "scanner 子包入口，re-export scan_backend/scan_frontend/extract_emits/extract_vue_props 四个对外扫描 API。",
        "tags": ["entry-point", "barrel", "scanner", "package-init"],
        "complexity": "simple",
    },
    {
        "id": f"file:{BACKEND}",
        "type": "file",
        "name": "backend.py",
        "filePath": BACKEND,
        "summary": "后端扫描器：用 Python AST 与正则从 Java/Kotlin/Python/Go/TS 源码中提取框架、端点、方法、字段、仓储、SQL、配置键与权限/事务/远程调用/消息/错误码等结构信号。",
        "tags": ["scanner", "backend", "ast", "static-analysis"],
        "complexity": "complex",
        "languageNotes": "python_ast_facts 用 ast 模块解析 Python 源码提取函数/类/import 事实；mask_comments_and_strings 先剥离注释与字符串再做正则匹配以降低误报。",
    },
    {
        "id": f"file:{FRONTEND}",
        "type": "file",
        "name": "frontend.py",
        "filePath": FRONTEND,
        "summary": "前端扫描器：从 Vue/React/TS/JS 源码中提取组件 props/emits/slots/expose、依赖、API 端点、service 前缀与路由模块信息，供 infer_standards 与 manifest 使用。",
        "tags": ["scanner", "frontend", "vue", "react", "static-analysis"],
        "complexity": "complex",
        "languageNotes": "extract_object_argument_blocks 用括号深度计数解析嵌套对象字面量，兼容 defineProps/defineEmits 等 Vue 编译宏。",
    },
]
nodes.extend(file_nodes)

# ---------------- core.py function/class nodes ----------------
core_r = RESULTS[CORE]
# file_signature (exported, 8 lines)
nodes.append(make_function_node(
    CORE, core_r["functions"][0],
    "基于文件 size 与 mtime_ns 生成 sha256 截断签名，用于增量扫描缓存键。",
    ["utility", "cache", "signature"], "simple"))
# sanitize_tooling (exported, 63 lines)
nodes.append(make_function_node(
    CORE, core_r["functions"][1],
    "从完整 tooling 探测结果中抽取可安全持久化到仓库的字段子集，统一 schemaVersion。",
    ["serialization", "tooling", "sanitizer"], "moderate"))
# IncrementalScanCache class
nodes.append(make_class_node(
    CORE, core_r["classes"][0],
    "增量扫描缓存：按文件签名缓存多个 namespace 的扫描结果，支持 load/get/put 并在 payload() 时按 seen 集合保留有效条目。",
    ["cache", "data-model", "scanner"], ))

# ---------------- cli.py function nodes ----------------
cli_r = RESULTS[CLI]
# _sanitize_error_text (12 lines, not exported but security-sensitive and >=10 lines)
nodes.append(make_function_node(
    CLI, cli_r["functions"][0],
    "用一组正则对错误文本中的 token/cookie/密钥/AWS 凭证/URL userinfo 做脱敏，避免泄漏到 JSON 输出。",
    ["security", "sanitizer", "redaction"], "simple"))
# json_envelope (19 lines, exported)
nodes.append(make_function_node(
    CLI, cli_r["functions"][2],
    "构建 CLI 统一返回 envelope：包含 ok/status/exitCode/error/result/output，失败时调用 _sanitize_error_text 脱敏。",
    ["serialization", "cli", "envelope"], "simple"))

# ---------------- scanner/backend.py function nodes ----------------
be_r = RESULTS[BACKEND]
BE_SUMMARIES = {
    "unique_limited": "对任意项列表去重并截断到上限，dict/list 用 JSON 序列化作为去重键。",
    "flatten_regex_hits": "把正则 match 元组结果展平为去重后的字符串列表。",
    "annotation_values": "从文本中提取指定注解名后的字符串/列表参数值。",
    "mask_comments_and_strings": "用状态机剥离源码中的注释与字符串字面量，便于后续正则匹配降低误报。",
    "annotation_values_in_code": "在已 mask 的代码文本上提取注解参数值，避免命中字符串/注释。",
    "quoted_literal_at": "从给定的引号位置解析出完整的字符串字面量内容。",
    "python_ast_facts": "用 ast 模块解析 Python 源码，提取函数/类/导入/赋值等事实供后续信号提取使用。",
    "detect_backend_framework": "结合路径、文本与 AST 事实判断后端框架（Spring/Django/FastAPI/Gin 等）。",
    "extract_backend_endpoints": "从后端源码中提取 HTTP 路由/端点注解与方法级路径。",
    "extract_backend_methods": "提取后端 service/controller 的公开方法名列表。",
    "extract_backend_fields": "从模型/DTO 中提取字段定义列表。",
    "extract_repository_methods": "识别仓储类并提取其数据访问方法。",
    "extract_sql_ops": "在源码中扫描 SQL 关键操作（select/insert/update/delete）。",
    "extract_config_keys": "从配置文件/代码中提取配置键名。",
    "extract_signals": "按模式列表从文本中提取去重后的信号字符串。",
    "extract_permission_signals": "提取鉴权/权限相关信号（@PreAuthorize、permission 等）。",
    "extract_transaction_signals": "提取事务边界信号（@Transactional 等）。",
    "extract_remote_call_signals": "提取远程调用信号（HTTP/RPC/Feign 客户端等）。",
    "extract_message_job_signals": "提取消息队列/定时任务信号。",
    "extract_error_code_signals": "提取错误码定义与抛出信号。",
    "extract_exported_functions": "提取模块对外导出的函数名。",
    "scan_backend_file": "对单个后端文件执行全套信号提取，产出结构化扫描结果。",
    "scan_backend": "遍历后端文件集合，结合增量缓存执行批量扫描并汇总结果。",
}
BE_TAGS = {
    "unique_limited": ["utility", "dedup"],
    "flatten_regex_hits": ["utility", "regex"],
    "annotation_values": ["extraction", "annotation"],
    "mask_comments_and_strings": ["parsing", "sanitizer", "static-analysis"],
    "annotation_values_in_code": ["extraction", "annotation"],
    "quoted_literal_at": ["parsing", "literal"],
    "python_ast_facts": ["ast", "python", "static-analysis"],
    "detect_backend_framework": ["detection", "framework", "backend"],
    "extract_backend_endpoints": ["extraction", "endpoint", "backend"],
    "extract_backend_methods": ["extraction", "method", "backend"],
    "extract_backend_fields": ["extraction", "field", "backend"],
    "extract_repository_methods": ["extraction", "repository", "backend"],
    "extract_sql_ops": ["extraction", "sql", "backend"],
    "extract_config_keys": ["extraction", "config", "backend"],
    "extract_signals": ["extraction", "signals"],
    "extract_permission_signals": ["extraction", "security", "backend"],
    "extract_transaction_signals": ["extraction", "transaction", "backend"],
    "extract_remote_call_signals": ["extraction", "remote-call", "backend"],
    "extract_message_job_signals": ["extraction", "message-queue", "backend"],
    "extract_error_code_signals": ["extraction", "error-code", "backend"],
    "extract_exported_functions": ["extraction", "exports"],
    "scan_backend_file": ["scanner", "backend", "orchestration"],
    "scan_backend": ["scanner", "backend", "orchestration"],
}
for fn in be_r["functions"]:
    lines = fn["endLine"] - fn["startLine"] + 1
    exported = any(e["name"] == fn["name"] for e in be_r.get("exports", []))
    # significance filter: 10+ lines OR exported AND >=6 lines (these are all meaningful scanner APIs)
    if lines >= 10 or (exported and lines >= 6):
        nodes.append(make_function_node(
            BACKEND, fn,
            BE_SUMMARIES.get(fn["name"], f"后端扫描辅助函数 {fn['name']}。"),
            BE_TAGS.get(fn["name"], ["scanner", "backend", "utility"]),
        ))

# ---------------- scanner/frontend.py function nodes ----------------
fe_r = RESULTS[FRONTEND]
FE_SUMMARIES = {
    "extract_object_argument_blocks": "按括号深度解析指定函数调用处的对象字面量参数块文本。",
    "split_top_level_items": "将对象字面量文本按顶层逗号切分为多个键值项。",
    "top_level_object_keys": "提取对象字面量文本中的顶层键名列表。",
    "extract_vue_props": "从 Vue defineProps 调用中提取组件 props 声明。",
    "extract_emits": "从 Vue defineEmits 调用中提取组件事件声明。",
    "extract_slots": "从 Vue defineSlots 调用中提取插槽声明。",
    "extract_expose": "从 Vue defineExpose 调用中提取对外暴露的成员。",
    "extract_dependencies": "从 import 语句中提取外部依赖模块名。",
    "component_scope": "依据文件路径推断组件的作用域命名空间。",
    "extract_service_prefixes": "从前端代码中提取 service 调用前缀，用于推断 API 客户端组织方式。",
    "extract_api_endpoints": "从前端代码中提取被调用的 API 端点字符串。",
    "extract_exported_functions": "提取模块对外导出的函数名。",
    "extract_react_props": "从 React 组件的 Props 类型/接口中提取字段。",
    "route_module_info": "从路由模块中提取路由声明与元信息。",
    "scan_frontend_file": "对单个前端文件执行组件/依赖/API/路由信号提取，产出结构化结果。",
    "scan_frontend": "遍历前端文件集合，结合增量缓存执行批量扫描并汇总结果。",
}
FE_TAGS = {
    "extract_object_argument_blocks": ["parsing", "object-literal"],
    "split_top_level_items": ["parsing", "object-literal"],
    "top_level_object_keys": ["parsing", "object-literal"],
    "extract_vue_props": ["extraction", "vue", "props"],
    "extract_emits": ["extraction", "vue", "emits"],
    "extract_slots": ["extraction", "vue", "slots"],
    "extract_expose": ["extraction", "vue", "expose"],
    "extract_dependencies": ["extraction", "dependency", "import"],
    "component_scope": ["extraction", "component", "naming"],
    "extract_service_prefixes": ["extraction", "service", "frontend"],
    "extract_api_endpoints": ["extraction", "endpoint", "frontend"],
    "extract_exported_functions": ["extraction", "exports"],
    "extract_react_props": ["extraction", "react", "props"],
    "route_module_info": ["extraction", "router", "frontend"],
    "scan_frontend_file": ["scanner", "frontend", "orchestration"],
    "scan_frontend": ["scanner", "frontend", "orchestration"],
}
for fn in fe_r["functions"]:
    lines = fn["endLine"] - fn["startLine"] + 1
    exported = any(e["name"] == fn["name"] for e in fe_r.get("exports", []))
    if lines >= 10 or (exported and lines >= 6):
        nodes.append(make_function_node(
            FRONTEND, fn,
            FE_SUMMARIES.get(fn["name"], f"前端扫描辅助函数 {fn['name']}。"),
            FE_TAGS.get(fn["name"], ["scanner", "frontend", "utility"]),
        ))

# ---------------- application.py function/class nodes ----------------
app_r = RESULTS[APP]
# JsonArgumentParser class (4 lines, 1 method) -- meets "exported class" bar via class + export
app_exports = {e["name"] for e in app_r.get("exports", [])}
# class is exported
nodes.append(make_class_node(
    APP, app_r["classes"][0],
    "argparse.ArgumentParser 子类，覆写 error() 以在 --json 模式下输出结构化错误而非退出到 stderr。",
    ["cli", "argparse", "error-handling"], ))
# Its complexity is simple (4 lines) but it is exported; override
nodes[-1]["complexity"] = "simple"

app_significant = 0
for fn in app_r["functions"]:
    lines = fn["endLine"] - fn["startLine"] + 1
    exported = fn["name"] in app_exports
    # significance: 10+ lines OR exported AND lines >= 6
    if lines >= 10 or (exported and lines >= 6):
        nodes.append(make_function_node(
            APP, fn,
            APP_FUNC_SUMMARIES.get(fn["name"], f"application 服务函数 {fn['name']}。"),
            APP_FUNC_TAGS.get(fn["name"], ["application-core", "cli", "service"]),
            app_func_complexity(fn),
        ))
        app_significant += 1

# ---------------- Edges ----------------
# contains edges: file -> every function/class node created for that file
node_paths = {}
for n in nodes:
    if n["type"] in ("function", "class"):
        node_paths.setdefault(n["filePath"], []).append(n)

for fpath, sub_nodes in node_paths.items():
    for n in sub_nodes:
        edges.append({
            "source": f"file:{fpath}",
            "target": n["id"],
            "type": "contains",
            "direction": "forward",
            "weight": 1.0,
        })

# exports edges: file -> exported function/class
def add_export_edges(file_result, fpath):
    for e in file_result.get("exports", []) or []:
        name = e["name"]
        target = None
        for n in nodes:
            if n["type"] in ("function", "class") and n["filePath"] == fpath and n["name"] == name:
                target = n["id"]
                break
        if target:
            edges.append({
                "source": f"file:{fpath}",
                "target": target,
                "type": "exports",
                "direction": "forward",
                "weight": 0.8,
            })

add_export_edges(core_r, CORE)
add_export_edges(cli_r, CLI)
add_export_edges(be_r, BACKEND)
add_export_edges(fe_r, FRONTEND)
add_export_edges(app_r, APP)

# imports edges (1:1 from batchImportData)
IMPORTS = {
    INIT: [CORE],
    APP: [INIT, CLI, SCANNER_INIT],
    CLI: [],
    CORE: [],
    SCANNER_INIT: [],
    BACKEND: [],
    FRONTEND: [],
}
for src, targets in IMPORTS.items():
    for tgt in targets:
        edges.append({
            "source": f"file:{src}",
            "target": f"file:{tgt}",
            "type": "imports",
            "direction": "forward",
            "weight": 0.7,
        })

# depends_on edges: scanner modules depend on core (file_signature, IncrementalScanCache)
# backend.py imports ..core (already captured in batchImportData? No — batchImportData shows [] for backend/frontend
# because the project scanner only resolved top-level package imports, not relative within-package imports.
# However the source clearly does `from ..core import IncrementalScanCache, file_signature`.
# Emit depends_on edges to core.py for the scanner files.
for scanner_path in (BACKEND, FRONTEND):
    edges.append({
        "source": f"file:{scanner_path}",
        "target": f"file:{CORE}",
        "type": "depends_on",
        "direction": "forward",
        "weight": 0.6,
    })

# calls edges (cross-file, high confidence):
# application.py -> cli.py: json_envelope (used in main). extract_global_json is a
# 2-line helper below the significance threshold, so no node exists for it — skip
# that calls edge to avoid an unresolved target.
edges.append({"source": f"function:{APP}:main", "target": f"function:{CLI}:json_envelope", "type": "calls", "direction": "forward", "weight": 0.8})

# application.py -> scanner: scan_frontend / scan_backend (facade in application.py delegates)
edges.append({"source": f"function:{APP}:scan_frontend", "target": f"function:{FRONTEND}:scan_frontend", "type": "calls", "direction": "forward", "weight": 0.8})
edges.append({"source": f"function:{APP}:scan_backend", "target": f"function:{BACKEND}:scan_backend", "type": "calls", "direction": "forward", "weight": 0.8})
# extract_backend_endpoints in application.py is a 2-line facade below the node
# threshold, so skip the calls edge from it to backend_scanner.extract_backend_endpoints.

# application.py -> core: file_signature / IncrementalScanCache used via _ACTIVE_SCAN_CACHE
edges.append({"source": f"file:{APP}", "target": f"class:{CORE}:IncrementalScanCache", "type": "depends_on", "direction": "forward", "weight": 0.6})

# scanner scan_backend/scan_frontend -> core file_signature & IncrementalScanCache
edges.append({"source": f"function:{BACKEND}:scan_backend", "target": f"class:{CORE}:IncrementalScanCache", "type": "depends_on", "direction": "forward", "weight": 0.6})
edges.append({"source": f"function:{BACKEND}:scan_backend", "target": f"function:{CORE}:file_signature", "type": "calls", "direction": "forward", "weight": 0.8})
edges.append({"source": f"function:{FRONTEND}:scan_frontend", "target": f"class:{CORE}:IncrementalScanCache", "type": "depends_on", "direction": "forward", "weight": 0.6})
edges.append({"source": f"function:{FRONTEND}:scan_frontend", "target": f"function:{CORE}:file_signature", "type": "calls", "direction": "forward", "weight": 0.8})

# __init__.py exports re-export core symbols -> depends_on already covered by imports edge.
# cli.py json_envelope calls _sanitize_error_text (intra-file, skip — contains already covers relationship)

# Collect_project_state in application calls scan_frontend + scan_backend
edges.append({"source": f"function:{APP}:collect_project_state", "target": f"function:{APP}:scan_frontend", "type": "calls", "direction": "forward", "weight": 0.8})
edges.append({"source": f"function:{APP}:collect_project_state", "target": f"function:{APP}:scan_backend", "type": "calls", "direction": "forward", "weight": 0.8})

# Remove self-referencing edges (safety)
edges = [e for e in edges if e["source"] != e["target"]]

# ---------------- Partition ----------------
# application.py is a dominant file (~140 sub-nodes). The protocol's file-based
# chunking would stack all of its nodes into one part. To respect the per-part
# budget (60 nodes / 120 edges), we split application.py's sub-nodes sequentially
# (by start line) across parts, and distribute the remaining small files one
# per part alongside.
node_count = len(nodes)
edge_count = len(edges)
parts = max(1, math.ceil(max(node_count / 60, edge_count / 120)))

# Separate application.py sub-nodes (sorted by start line) from everything else.
app_sub = [n for n in nodes if n.get("filePath") == APP and n["type"] in ("function", "class")]
app_sub.sort(key=lambda n: n["lineRange"][0])
app_file_node = next(n for n in nodes if n["id"] == f"file:{APP}")

other_files = sorted([INIT, CLI, CORE, SCANNER_INIT, BACKEND, FRONTEND])
other_nodes = [n for n in nodes if n.get("filePath") in other_files]

# Distribute app_sub across all `parts`; each part also gets the app file node
# (so app file-level edges resolve) plus a share of the small files.
# Small files: assign one per part (parts >= len(other_files) here since parts=4, other_files=6)
# Actually distribute small files round-robin across parts.
part_nodes = {i: [] for i in range(1, parts + 1)}

# Every part gets the application.py file node (it owns contains/exports edges to
# sub-nodes spread across parts; the file node itself can legitimately appear in
# multiple parts as the edge source — but to avoid duplicate node IDs we place
# the file node in part 1 only and let other parts reference it by id in edges).
part_nodes[1].append(app_file_node)

# Split app_sub into `parts` chunks by line order
chunk_size = math.ceil(len(app_sub) / parts) if app_sub else 0
for i, n in enumerate(app_sub):
    p = min(i // chunk_size + 1, parts) if chunk_size else 1
    part_nodes[p].append(n)

# Distribute other_nodes: group by filePath, assign each file's nodes to a part.
# Spread files across parts to balance.
for idx, fp in enumerate(other_files):
    p = (idx % parts) + 1
    for n in other_nodes:
        if n.get("filePath") == fp:
            part_nodes[p].append(n)

# Build node id -> part map (a node appears in exactly one part)
node_id_to_part = {}
for i, ns in part_nodes.items():
    for n in ns:
        node_id_to_part[n["id"]] = i

# Assign edges to parts by source node's part.
# Source may be a file: node that lives in a different part (e.g. app file node
# is in part 1 but contains-edges target sub-nodes in other parts). Per protocol:
# "All edges whose source is in this part's nodes" — so a contains edge from
# file:application.py (in part 1) to a function in part 2 belongs to part 1.
# That is fine; targets may be anywhere.
part_edges = {i: [] for i in range(1, parts + 1)}
for e in edges:
    src = e["source"]
    src_part = node_id_to_part.get(src)
    if src_part is None and src.startswith("file:"):
        # file node not placed in any part (shouldn't happen — all file nodes placed)
        fp = src[len("file:"):]
        # find which part holds this file node
        for i, ns in part_nodes.items():
            if any(n["id"] == src for n in ns):
                src_part = i
                break
    if src_part is None:
        src_part = 1
    part_edges[src_part].append(e)

# Write parts
os.makedirs(OUT_DIR, exist_ok=True)
written = []
for k in range(1, parts+1):
    payload = {"nodes": part_nodes[k], "edges": part_edges[k]}
    path = os.path.join(OUT_DIR, f"batch-1-part-{k}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    written.append((path, len(part_nodes[k]), len(part_edges[k])))

print(f"TOTAL nodes={node_count} edges={edge_count} parts={parts}")
max_nodes = max(len(ns) for ns in part_nodes.values())
max_edges = max(len(es) for es in part_edges.values())
print(f"max nodes per part={max_nodes} (budget 60), max edges per part={max_edges} (budget 120)")
budget_ok = max_nodes <= 60 and max_edges <= 120
print(f"budget_ok={budget_ok}")
for p, nn, ee in written:
    print(f"  {p}: nodes={nn} edges={ee}")

# Self-validation summary
print("\n--- Validation ---")
print(f"Imports edges expected: {sum(len(v) for v in IMPORTS.values())} = {sum(len(v) for v in IMPORTS.values())}")
imports_in_output = sum(1 for e in edges if e["type"] == "imports")
print(f"Imports edges emitted: {imports_in_output}")
print(f"Contains edges: {sum(1 for e in edges if e['type']=='contains')}")
print(f"Exports edges: {sum(1 for e in edges if e['type']=='exports')}")
print(f"calls edges: {sum(1 for e in edges if e['type']=='calls')}")
print(f"depends_on edges: {sum(1 for e in edges if e['type']=='depends_on')}")
