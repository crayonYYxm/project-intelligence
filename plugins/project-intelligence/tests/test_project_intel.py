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
    def test_default_understand_install_command_windows_targets_official_repo_and_codex(self):
        with patch.object(project_intel.os, "name", "nt"), patch.object(
            project_intel, "command_exists", side_effect=lambda name: name == "powershell"
        ):
            command = project_intel.default_understand_install_command()

        self.assertIn("https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.ps1", command)
        self.assertIn("codex", command)

    def test_default_understand_install_command_posix_targets_official_repo_and_codex(self):
        with patch.object(project_intel.os, "name", "posix"), patch.object(
            project_intel, "command_exists", side_effect=lambda name: name in {"curl", "bash"}
        ):
            command = project_intel.default_understand_install_command()

        self.assertEqual(
            command,
            "curl -fsSL https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.sh | bash -s codex",
        )

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

    def test_detect_graph_actions_uses_zh_understand_agent_command(self):
        with patch.object(project_intel, "command_exists", return_value=False), patch.object(
            project_intel, "understand_plugin_roots", return_value=[Path("C:/Users/test/.understand-anything-plugin")]
        ), patch.object(project_intel, "understand_analyze_command", return_value=None), patch.object(
            project_intel, "default_understand_install_command", return_value="install understand"
        ):
            actions = project_intel.detect_graph_actions(Path("."))

        understand = next(action for action in actions if action["tool"] == "Understand-Anything")
        self.assertEqual(understand["agentCommand"], "/understand . --language zh")

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
                "installCommand": "install understand",
                "agentCommand": "/understand . --language zh",
                "canAnalyze": False,
                "canInstall": True,
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


class UnderstandSetupFlowTests(unittest.TestCase):
    def test_understand_install_returns_follow_up_instead_of_retrying_init(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "Understand-Anything",
                    "state": "installable",
                    "reason": "architecture",
                    "installCommand": "install understand",
                    "agentCommand": "/understand . --language zh",
                    "canInstall": True,
                }
            ]
        }

        with patch.object(project_intel, "run_shell", return_value=(0, "ok", "")) as run_shell, patch.object(
            project_intel, "understand_analyze_command", return_value=None
        ):
            result = project_intel.setup_graph_tools(Path("."), tooling, auto_approve=True)

        self.assertEqual(result[0]["status"], "ok")
        self.assertEqual(result[1]["status"], "needs-agent")
        self.assertEqual(result[1]["command"], "/understand . --language zh")
        self.assertIn("refresh", result[1]["detail"])
        run_shell.assert_called_once_with("install understand", Path("."), timeout=300)


if __name__ == "__main__":
    unittest.main()
