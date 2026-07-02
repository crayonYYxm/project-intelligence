import importlib.util
import io
import json
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


if __name__ == "__main__":
    unittest.main()
