import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_intel.py"
SPEC = importlib.util.spec_from_file_location("project_intel", MODULE_PATH)
project_intel = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(project_intel)


class HandleToolingSetupTests(unittest.TestCase):
    def test_init_runs_installed_graph_analysis(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "installed",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "analyzeCommand": "gitnexus analyze",
                    "canAnalyze": True,
                }
            ]
        }

        with patch.object(project_intel, "print_tooling_summary"), patch.object(
            project_intel, "run_shell", return_value=(0, "ok", "")
        ) as run_shell, patch(
            "builtins.input", side_effect=AssertionError("input should not be called")
        ):
            result = project_intel.handle_tooling_setup(
                Path("."),
                tooling,
                interactive=False,
                setup_missing=False,
                with_graph=True,
            )

        self.assertEqual(result[0]["tool"], "GitNexus")
        self.assertEqual(result[0]["status"], "ok")
        run_shell.assert_called_once_with("gitnexus analyze", Path("."), timeout=300)

    def test_init_asks_before_installing_missing_graph_tool(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "missing",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "installCommand": "npx gitnexus analyze",
                    "canInstall": True,
                }
            ]
        }

        with patch.object(project_intel, "print_tooling_summary"), patch.object(
            project_intel, "run_shell", return_value=(0, "ok", "")
        ) as run_shell, patch("builtins.input", return_value="y"):
            result = project_intel.handle_tooling_setup(
                Path("."),
                tooling,
                interactive=False,
                setup_missing=False,
                with_graph=True,
            )

        self.assertEqual(result[0]["tool"], "GitNexus")
        self.assertEqual(result[0]["status"], "ok")
        run_shell.assert_called_once_with("npx gitnexus analyze", Path("."), timeout=300)

    def test_init_continues_when_missing_graph_tool_is_declined(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "missing",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "installCommand": "npx gitnexus analyze",
                    "canInstall": True,
                }
            ]
        }

        with patch.object(project_intel, "print_tooling_summary"), patch.object(
            project_intel, "run_shell"
        ) as run_shell, patch("builtins.input", return_value="n"):
            result = project_intel.handle_tooling_setup(
                Path("."),
                tooling,
                interactive=False,
                setup_missing=False,
                with_graph=True,
            )

        self.assertEqual(result[0]["tool"], "GitNexus")
        self.assertEqual(result[0]["status"], "skipped")
        run_shell.assert_not_called()

    def test_init_runs_configured_understand_analysis(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "Understand-Anything",
                    "state": "installed",
                    "reason": "架构概览、模块关系、领域流、入职图谱",
                    "analyzeCommand": "understand .",
                    "canAnalyze": True,
                }
            ]
        }

        with patch.object(project_intel, "print_tooling_summary"), patch.object(
            project_intel, "run_shell", return_value=(0, "ok", "")
        ) as run_shell:
            result = project_intel.handle_tooling_setup(
                Path("."),
                tooling,
                interactive=False,
                setup_missing=False,
                with_graph=True,
            )

        self.assertEqual(result[0]["tool"], "Understand-Anything")
        self.assertEqual(result[0]["status"], "ok")
        run_shell.assert_called_once_with("understand .", Path("."), timeout=300)


class GraphToolsReportTests(unittest.TestCase):
    def test_report_graph_tools_json_prints_graph_actions(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "installable",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "installCommand": "npx gitnexus analyze",
                }
            ]
        }

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            project_intel.print_graph_tools_report(tooling, as_json=True)

        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload[0]["tool"], "GitNexus")
        self.assertEqual(payload[0]["state"], "installable")

    def test_report_graph_tools_text_is_chinese(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "installable",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "installCommand": "npx gitnexus analyze",
                    "analyzeCommand": None,
                }
            ]
        }

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            project_intel.print_graph_tools_report(tooling, as_json=False)

        output = buffer.getvalue()
        self.assertIn("图谱工具检查结果", output)
        self.assertIn("GitNexus", output)
        self.assertIn("可安装", output)


class GraphToolCommandTests(unittest.TestCase):
    def test_default_understand_install_command_prefers_current_agent(self):
        with patch.dict(project_intel.os.environ, {"PROJECT_INTEL_AGENT": "codex"}, clear=True), patch.object(
            project_intel, "command_exists", side_effect=lambda name: name in {"curl", "bash", "claude"}
        ):
            command = project_intel.default_understand_install_command()

        self.assertEqual(command, project_intel.UNDERSTAND_CODEX_INSTALL_COMMAND)

    def test_default_understand_install_command_can_be_overridden_by_env(self):
        with patch.dict(project_intel.os.environ, {"PROJECT_INTEL_UNDERSTAND_INSTALL_COMMAND": "custom install"}):
            command = project_intel.default_understand_install_command()

        self.assertEqual(command, "custom install")

    def test_detect_graph_actions_marks_gitnexus_as_download_and_run(self):
        with patch.object(project_intel, "command_exists", side_effect=lambda name: name == "npx"), patch.object(
            project_intel, "understand_plugin_roots", return_value=[]
        ), patch.object(project_intel, "understand_analyze_command", return_value=None), patch.object(
            project_intel, "default_understand_install_command", return_value=None
        ):
            actions = project_intel.detect_graph_actions(Path("."))

        gitnexus = next(action for action in actions if action["tool"] == "GitNexus")
        self.assertEqual(gitnexus["state"], "installable")
        self.assertEqual(gitnexus["installCommand"], "npx gitnexus analyze")
        self.assertEqual(gitnexus["stateLabel"], "可下载并运行分析")

    def test_detect_graph_actions_marks_understand_as_agent_installed(self):
        with patch.object(project_intel, "command_exists", return_value=False), patch.object(
            project_intel, "understand_plugin_roots", return_value=[Path("C:/Users/test/.understand-anything-plugin")]
        ), patch.object(project_intel, "claude_understand_installs", return_value=[]), patch.object(
            project_intel, "understand_installed_platforms", return_value=["codex"]
        ), patch.object(
            project_intel, "understand_analyze_command", return_value=None
        ), patch.object(project_intel, "understand_install_options", return_value=[]), patch.object(
            project_intel, "default_understand_install_command", return_value=None
        ):
            actions = project_intel.detect_graph_actions(Path("."))

        understand = next(action for action in actions if action["tool"] == "Understand-Anything")
        self.assertEqual(understand["state"], "agent-installed")
        self.assertEqual(understand["stateLabel"], "已安装到 agent；当前 shell 不能直接分析")
        self.assertEqual(understand["agentCommand"], "/understand . --language zh")

    def test_detect_graph_actions_marks_understand_as_installable(self):
        options = [
            {
                "platform": "claude",
                "label": "Claude Code 插件安装",
                "command": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                "commands": [project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND, project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND],
                "canRun": True,
            }
        ]
        with patch.object(project_intel, "command_exists", return_value=False), patch.object(
            project_intel, "understand_plugin_roots", return_value=[]
        ), patch.object(project_intel, "claude_understand_installs", return_value=[]), patch.object(
            project_intel, "understand_installed_platforms", return_value=[]
        ), patch.object(project_intel, "current_agent_platform", return_value="claude"), patch.object(
            project_intel, "understand_analyze_command", return_value=None
        ), patch.object(project_intel, "understand_install_options", return_value=options), patch.object(
            project_intel, "default_understand_install_command", return_value=project_intel.UNDERSTAND_MANUAL_INSTALL_HINT
        ):
            actions = project_intel.detect_graph_actions(Path("."))

        understand = next(action for action in actions if action["tool"] == "Understand-Anything")
        self.assertEqual(understand["state"], "installable")
        self.assertEqual(understand["stateLabel"], "未安装，可选择安装")
        self.assertEqual(understand["installOptions"], options)

    def test_detect_graph_actions_marks_understand_as_partially_installed(self):
        options = [
            {
                "platform": "claude",
                "label": "Claude Code 插件安装",
                "command": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                "commands": [project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND, project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND],
                "canRun": True,
            },
            {
                "platform": "codex",
                "label": "Codex skills 安装",
                "command": project_intel.UNDERSTAND_CODEX_INSTALL_COMMAND,
                "commands": [project_intel.UNDERSTAND_CODEX_INSTALL_COMMAND],
                "canRun": True,
            },
        ]
        with patch.object(project_intel, "command_exists", return_value=False), patch.object(
            project_intel, "understand_plugin_roots", return_value=[Path("/tmp/.understand-anything-plugin")]
        ), patch.object(project_intel, "claude_understand_installs", return_value=[]), patch.object(
            project_intel, "understand_installed_platforms", return_value=["codex"]
        ), patch.object(project_intel, "current_agent_platform", return_value="codex"), patch.object(
            project_intel, "understand_analyze_command", return_value=None
        ), patch.object(project_intel, "understand_install_options", return_value=options):
            actions = project_intel.detect_graph_actions(Path("."))

        understand = next(action for action in actions if action["tool"] == "Understand-Anything")
        self.assertEqual(understand["state"], "partially-installed")
        self.assertEqual([option["platform"] for option in understand["installOptions"]], ["claude"])

    def test_detect_tooling_treats_agent_installed_understand_as_follow_up(self):
        package = {"hasPackageJson": False}
        graph_actions = [
            {
                "tool": "GitNexus",
                "state": "installed",
                "reason": "impact",
                "analyzeCommand": "gitnexus analyze",
                "installCommand": "npx gitnexus analyze",
                "canAnalyze": True,
                "canInstall": True,
            },
            {
                "tool": "Understand-Anything",
                "state": "agent-installed",
                "reason": "architecture",
                "installCommand": None,
                "agentCommand": "/understand . --language zh",
                "canAnalyze": False,
                "canInstall": False,
            },
        ]

        with patch.object(project_intel, "detect_quality_commands", return_value=[]), patch.object(
            project_intel, "package_manager", return_value="npm"
        ), patch.object(project_intel, "command_exists", return_value=True), patch.object(
            project_intel, "detect_graph_actions", return_value=graph_actions
        ), patch.object(project_intel, "understand_plugin_roots", return_value=[Path("C:/Users/test/.understand-anything-plugin")]):
            tooling = project_intel.detect_tooling(Path("."), package)

        self.assertEqual(tooling["recommendedActions"], [])
        self.assertEqual(len(tooling["followUpActions"]), 1)
        self.assertEqual(tooling["followUpActions"][0]["tool"], "Understand-Anything")
        self.assertEqual(tooling["followUpActions"][0]["command"], "/understand . --language zh")
        self.assertEqual(tooling["followUpActions"][0]["refreshCommand"], "/project-refresh")
        self.assertEqual(tooling["followUpActions"][0]["fallbackRefreshCommand"], "project-intel refresh")
        self.assertIn("已安装到 Codex/Claude Code agent", tooling["followUpActions"][0]["detail"])

    def test_detect_tooling_treats_partially_installed_understand_as_install_and_follow_up(self):
        package = {"hasPackageJson": False}
        graph_actions = [
            {
                "tool": "GitNexus",
                "state": "installed",
                "reason": "impact",
                "analyzeCommand": "gitnexus analyze",
                "canAnalyze": True,
            },
            {
                "tool": "Understand-Anything",
                "state": "partially-installed",
                "reason": "architecture",
                "installCommand": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                "installOptions": [
                    {
                        "platform": "claude",
                        "label": "Claude Code 插件安装",
                        "command": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                        "commands": [
                            project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND,
                            project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND,
                        ],
                        "canRun": True,
                    }
                ],
                "agentCommand": "/understand . --language zh",
                "canAnalyze": False,
                "canInstall": True,
            },
        ]

        with patch.object(project_intel, "detect_quality_commands", return_value=[]), patch.object(
            project_intel, "package_manager", return_value="npm"
        ), patch.object(project_intel, "command_exists", return_value=True), patch.object(
            project_intel, "detect_graph_actions", return_value=graph_actions
        ), patch.object(project_intel, "understand_plugin_roots", return_value=[]):
            tooling = project_intel.detect_tooling(Path("."), package)

        self.assertEqual(tooling["recommendedActions"][0]["tool"], "Understand-Anything")
        self.assertEqual(tooling["followUpActions"][0]["tool"], "Understand-Anything")


class UnderstandSetupFlowTests(unittest.TestCase):
    def test_understand_agent_installed_state_skips_install_and_returns_detail(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "Understand-Anything",
                    "state": "agent-installed",
                    "reason": "architecture",
                    "installCommand": None,
                    "agentCommand": "/understand . --language zh",
                    "canInstall": False,
                }
            ]
        }

        with patch.object(project_intel, "run_shell", return_value=(0, "ok", "")) as run_shell:
            result = project_intel.setup_graph_tools(Path("."), tooling, auto_approve=True)

        self.assertEqual(result[0]["status"], "skipped")
        self.assertIn("已安装到 agent", result[0]["detail"])
        self.assertIn("/understand . --language zh", result[0]["detail"])
        run_shell.assert_not_called()

    def test_understand_installable_state_runs_selected_install_commands(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "Understand-Anything",
                    "state": "installable",
                    "reason": "architecture",
                    "installCommand": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                    "installOptions": [
                        {
                            "platform": "claude",
                            "label": "Claude Code 插件安装",
                            "command": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                            "commands": [
                                project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND,
                                project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND,
                            ],
                            "canRun": True,
                        }
                    ],
                    "agentCommand": "/understand . --language zh",
                    "canInstall": True,
                }
            ]
        }

        with patch.object(project_intel, "current_agent_platform", return_value="claude"), patch.object(
            project_intel, "understand_analyze_command", return_value=None
        ), patch.object(project_intel, "verify_understand_claude_install", return_value={"tool": "Understand-Anything", "status": "ok"}), patch.object(
            project_intel, "run_shell", return_value=(0, "ok", "")
        ) as run_shell:
            result = project_intel.setup_graph_tools(Path("."), tooling, auto_approve=True)

        self.assertEqual(result[0]["status"], "ok")
        self.assertEqual(result[0]["command"], project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND)
        self.assertEqual(result[1]["command"], project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND)
        self.assertEqual(result[2]["status"], "ok")
        self.assertEqual(result[3]["status"], "needs-agent")
        self.assertEqual(run_shell.call_count, 2)

    def test_understand_partially_installed_state_can_install_missing_platform(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "Understand-Anything",
                    "state": "partially-installed",
                    "reason": "architecture",
                    "installCommand": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                    "installOptions": [
                        {
                            "platform": "claude",
                            "label": "Claude Code 插件安装",
                            "command": project_intel.UNDERSTAND_MANUAL_INSTALL_HINT,
                            "commands": [
                                project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND,
                                project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND,
                            ],
                            "canRun": True,
                        }
                    ],
                    "agentCommand": "/understand . --language zh",
                    "canInstall": True,
                }
            ]
        }

        with patch.object(project_intel, "current_agent_platform", return_value="codex"), patch.object(
            project_intel, "understand_analyze_command", return_value=None
        ), patch.object(project_intel, "verify_understand_claude_install", return_value={"tool": "Understand-Anything", "status": "ok"}), patch.object(
            project_intel, "run_shell", return_value=(0, "ok", "")
        ) as run_shell:
            result = project_intel.setup_graph_tools(Path("."), tooling, auto_approve=True)

        self.assertEqual(result[0]["command"], project_intel.UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND)
        self.assertEqual(result[1]["command"], project_intel.UNDERSTAND_CLAUDE_INSTALL_COMMAND)
        self.assertEqual(result[2]["status"], "ok")
        self.assertEqual(result[3]["status"], "needs-agent")
        self.assertEqual(run_shell.call_count, 2)

    def test_failed_claude_local_install_does_not_mark_platform_ready(self):
        installs = [
            {
                "id": "understand-anything@local",
                "enabled": True,
                "listStatus": "✘ failed to load",
            }
        ]

        platforms = project_intel.understand_installed_platforms(
            [Path("/Users/test/.claude/plugins/cache/local/understand-anything")],
            installs,
        )

        self.assertNotIn("claude", platforms)


class AgentEntrypointInstallTests(unittest.TestCase):
    def test_init_writes_root_agent_entrypoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export const answer = 42;\n", encoding="utf-8")

            result = project_intel.init_project(root, with_graph=False)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            nested = (root / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertTrue(agents.startswith(project_intel.AGENT_PROJECT_INTEL_BLOCK_START))
            self.assertTrue(claude.startswith(project_intel.CLAUDE_LOCAL_SKILLS_BLOCK_START))
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, agents)
            self.assertIn("Project Intelligence is the workflow layer", agents)
            self.assertIn("Tools such as Grep, Read, Edit, Bash", agents)
            self.assertIn("pause before the first Edit/Write", agents)
            self.assertIn("state which Project Intelligence workflow is being followed", agents)
            self.assertIn("project-task` or `project-intelligence:project-task", agents)
            self.assertIn("project-review` or `project-intelligence:project-review", agents)
            self.assertIn("project-maintain` or `project-intelligence:project-maintain", agents)
            self.assertIn("GitNexus impact/explore/detect_changes", agents)
            self.assertIn("do not use `cgraphx explore`", agents)
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, claude)
            self.assertIn("/project-task", claude)
            self.assertIn("local `.claude/skills/project-*` skills take precedence", claude)
            self.assertIn("Project Skills First for Claude Code", nested)
            self.assertIn("/project-task", nested)
            self.assertIn(str(root / "AGENTS.md"), result["agentFiles"])
            self.assertIn(str(root / "CLAUDE.md"), result["agentFiles"])
            self.assertIn(str(root / ".claude" / "CLAUDE.md"), result["agentFiles"])
            self.assertTrue((root / ".claude" / "skills" / "project-init" / "SKILL.md").exists())
            self.assertTrue((root / ".claude" / "skills" / "project-task" / "SKILL.md").exists())
            self.assertIn(str(root / ".claude" / "skills" / "project-init" / "SKILL.md"), result["skillFiles"])

    def test_install_writes_root_agent_entrypoints_without_overwriting_existing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Team Notes\n\nKeep this section.\n", encoding="utf-8")

            result = project_intel.install_claude(root)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            nested = (root / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertTrue(agents.startswith(project_intel.AGENT_PROJECT_INTEL_BLOCK_START))
            self.assertTrue(claude.startswith(project_intel.CLAUDE_LOCAL_SKILLS_BLOCK_START))
            self.assertIn("# Team Notes", agents)
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, agents)
            self.assertIn("This repository uses `.project-intel/`", agents)
            self.assertIn("If slash skills are not available", agents)
            self.assertIn("project-intelligence:*", agents)
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, claude)
            self.assertIn("/project-task", claude)
            self.assertIn("Do not read or rely on `.cgraphx`", nested)
            self.assertIn(str(root / "AGENTS.md"), result["agentFiles"])
            self.assertIn(str(root / "CLAUDE.md"), result["agentFiles"])
            self.assertTrue((root / ".claude" / "skills" / "project-init" / "SKILL.md").exists())
            self.assertTrue((root / ".claude" / "skills" / "project-task" / "SKILL.md").exists())
            self.assertIn(str(root / ".claude" / "skills" / "project-init" / "SKILL.md"), result["skillFiles"])
            self.assertIn(str(root / ".claude" / "skills" / "project-task" / "SKILL.md"), result["skillFiles"])

    def test_install_writes_claude_skill_directories_and_removes_generated_legacy_flat_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / ".claude" / "skills" / "project-task.md"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text("以 `.project-intel` 作为项目事实来源。\n", encoding="utf-8")

            project_intel.install_claude(root)

            self.assertTrue((root / ".claude" / "skills" / "project-task" / "SKILL.md").exists())
            self.assertFalse(legacy.exists())

    def test_install_updates_managed_agent_block_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            project_intel.install_claude(root)
            project_intel.install_claude(root)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertEqual(agents.count(project_intel.AGENT_PROJECT_INTEL_BLOCK_START), 1)
            self.assertEqual(agents.count(project_intel.AGENT_PROJECT_INTEL_BLOCK_END), 1)
            self.assertEqual(claude.count(project_intel.CLAUDE_LOCAL_SKILLS_BLOCK_START), 1)
            self.assertEqual(claude.count(project_intel.CLAUDE_LOCAL_SKILLS_BLOCK_END), 1)
            self.assertEqual(agents.count(project_intel.PROJECT_INTEL_BLOCK_START), 1)
            self.assertEqual(agents.count(project_intel.PROJECT_INTEL_BLOCK_END), 1)
            self.assertEqual(claude.count(project_intel.PROJECT_INTEL_BLOCK_START), 1)
            self.assertEqual(claude.count(project_intel.PROJECT_INTEL_BLOCK_END), 1)


class LifecycleArtifactTests(unittest.TestCase):
    def test_lifecycle_and_debug_print_by_default_and_write_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export const answer = 42;\n", encoding="utf-8")
            project_intel.init_project(root, with_graph=False)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                lifecycle_path = project_intel.write_lifecycle(root, "demo task")
                debug_path = project_intel.write_debug_context(root, "demo bug")

            self.assertIsNone(lifecycle_path)
            self.assertIsNone(debug_path)
            self.assertIn("# 任务影响", buffer.getvalue())
            self.assertIn("# 调试上下文", buffer.getvalue())
            self.assertFalse((root / ".project-intel" / "reports" / "task-impact.md").exists())
            self.assertFalse((root / ".project-intel" / "reports" / "debug-context.md").exists())

            lifecycle_path = project_intel.write_lifecycle(root, "demo task", write_report=True)
            debug_path = project_intel.write_debug_context(root, "demo bug", write_report=True)

            self.assertEqual(lifecycle_path, root / ".project-intel" / "reports" / "task-impact.md")
            self.assertEqual(debug_path, root / ".project-intel" / "reports" / "debug-context.md")
            self.assertTrue(lifecycle_path.exists())
            self.assertTrue(debug_path.exists())

    def test_maintain_defaults_to_latest_and_archives_only_when_requested(self):
        refresh_result = {
            "manifest": {"fileCount": 1},
            "frontend": {"components": [], "hooks": [], "redundancyCandidates": []},
            "backend": {"apis": [], "services": [], "candidateEntrypoints": []},
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(project_intel, "init_project", return_value=refresh_result), patch.object(
                project_intel, "run_check", return_value=0
            ):
                exit_code = project_intel.maintain_project(root, "first task", run_quality=False)
                self.assertEqual(exit_code, 0)
                latest = root / ".project-intel" / "maintenance" / "latest.md"
                self.assertTrue(latest.exists())
                self.assertIn("first task", latest.read_text(encoding="utf-8"))
                self.assertEqual(list((root / ".project-intel" / "maintenance").glob("*-maintenance.md")), [])

                project_intel.maintain_project(root, "second task", run_quality=False)
                self.assertIn("second task", latest.read_text(encoding="utf-8"))
                self.assertEqual(list((root / ".project-intel" / "maintenance").glob("*-maintenance.md")), [])

                project_intel.maintain_project(root, "archive task", run_quality=False, archive=True)
                archives = list((root / ".project-intel" / "maintenance").glob("*-maintenance.md"))
                self.assertEqual(len(archives), 1)
                self.assertIn("archive task", archives[0].read_text(encoding="utf-8"))

    def test_file_requirements_use_one_markdown_per_source_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "utils" / "common.ts"
            source.parent.mkdir(parents=True)
            source.write_text("export const answer = 42;\n", encoding="utf-8")

            written = project_intel.update_file_requirement_docs(root, "支持校园预充值金额可选", [str(source)])

            expected = root / ".project-intel" / "requirements" / "files" / "src" / "utils" / "common.ts.md"
            self.assertEqual(written, [expected])
            body = expected.read_text(encoding="utf-8")
            self.assertIn("源文件：`src/utils/common.ts`", body)
            self.assertIn("支持校园预充值金额可选", body)

            project_intel.update_file_requirement_docs(root, "保持单值传入不可点开选择", ["src/utils/common.ts"])
            docs = list((root / ".project-intel" / "requirements" / "files").rglob("*.md"))
            self.assertEqual(docs, [expected])
            body = expected.read_text(encoding="utf-8")
            self.assertIn("支持校园预充值金额可选", body)
            self.assertIn("保持单值传入不可点开选择", body)

    def test_maintain_updates_file_requirements_for_explicit_files(self):
        refresh_result = {
            "manifest": {"fileCount": 1},
            "frontend": {"components": [], "hooks": [], "redundancyCandidates": []},
            "backend": {"apis": [], "services": [], "candidateEntrypoints": []},
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "page.vue"
            source.parent.mkdir(parents=True)
            source.write_text("<template />\n", encoding="utf-8")

            with patch.object(project_intel, "init_project", return_value=refresh_result), patch.object(
                project_intel, "run_check", return_value=0
            ):
                project_intel.maintain_project(root, "支持校园预充值金额可选", run_quality=False, files=["src/page.vue"])

            expected = root / ".project-intel" / "requirements" / "files" / "src" / "page.vue.md"
            self.assertTrue(expected.exists())
            self.assertIn("支持校园预充值金额可选", expected.read_text(encoding="utf-8"))
            latest = root / ".project-intel" / "maintenance" / "latest.md"
            self.assertIn("src/page.vue", latest.read_text(encoding="utf-8"))

    def test_file_requirements_require_chinese_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "page.vue"
            source.parent.mkdir(parents=True)
            source.write_text("<template />\n", encoding="utf-8")

            with self.assertRaises(SystemExit):
                project_intel.update_file_requirement_docs(root, "support selectable prepay amounts", ["src/page.vue"])


if __name__ == "__main__":
    unittest.main()
