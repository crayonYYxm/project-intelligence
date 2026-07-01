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


if __name__ == "__main__":
    unittest.main()
