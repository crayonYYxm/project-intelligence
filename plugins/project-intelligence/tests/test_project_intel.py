import importlib.util
import io
import json
import subprocess
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


class FileDiscoveryTests(unittest.TestCase):
    def test_iter_files_excludes_hidden_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export const ok = true;\n", encoding="utf-8")
            (root / ".hidden" / "src").mkdir(parents=True)
            (root / ".hidden" / "src" / "ignored.ts").write_text("export const ignored = true;\n", encoding="utf-8")

            files = {path.relative_to(root).as_posix() for path in project_intel.iter_files(root)}

            self.assertIn("src/index.ts", files)
            self.assertNotIn(".hidden/src/ignored.ts", files)


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
        ) as run_shell, patch("builtins.input", return_value="y"), patch.object(
            project_intel.sys.stdin, "isatty", return_value=True
        ):
            result = project_intel.handle_tooling_setup(
                Path("."),
                tooling,
                interactive=True,
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
        ) as run_shell, patch("builtins.input", return_value="n"), patch.object(
            project_intel.sys.stdin, "isatty", return_value=True
        ):
            result = project_intel.handle_tooling_setup(
                Path("."),
                tooling,
                interactive=True,
                setup_missing=False,
                with_graph=True,
            )

        self.assertEqual(result[0]["tool"], "GitNexus")
        self.assertEqual(result[0]["status"], "skipped")
        run_shell.assert_not_called()

    def test_noninteractive_init_never_waits_for_missing_tool_input(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "installable",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "installCommand": "npx gitnexus analyze",
                    "canInstall": True,
                }
            ]
        }

        with patch.object(project_intel, "print_tooling_summary"), patch.object(
            project_intel, "run_shell"
        ) as run_shell, patch("builtins.input", side_effect=AssertionError("input should not be called")):
            result = project_intel.handle_tooling_setup(
                Path("."), tooling, interactive=False, setup_missing=False, with_graph=True
            )

        self.assertEqual(result, [])
        run_shell.assert_not_called()

    def test_interactive_flag_without_tty_degrades_without_input(self):
        tooling = {
            "graphActions": [
                {
                    "tool": "GitNexus",
                    "state": "installable",
                    "reason": "符号级调用、影响分析、PR/变更风险",
                    "installCommand": "npx gitnexus analyze",
                    "canInstall": True,
                }
            ]
        }
        output = io.StringIO()
        with patch.object(project_intel, "print_tooling_summary"), patch.object(
            project_intel.sys.stdin, "isatty", return_value=False
        ), patch("builtins.input", side_effect=AssertionError("input should not be called")), redirect_stdout(output):
            result = project_intel.handle_tooling_setup(
                Path("."), tooling, interactive=True, setup_missing=False, with_graph=True
            )

        self.assertEqual(result, [])
        self.assertIn("不是交互终端", output.getvalue())

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
            self.assertTrue(claude.startswith(project_intel.PROJECT_INTEL_BLOCK_START))
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, agents)
            self.assertIn("Project Intelligence is the workflow layer", agents)
            self.assertIn("Tools such as Grep, Read, Edit, Bash", agents)
            self.assertIn("pause before the first Edit/Write", agents)
            self.assertIn("state which Project Intelligence workflow is being followed", agents)
            self.assertIn("project-task` or `project-intelligence:project-task", agents)
            self.assertIn("project-review` or `project-intelligence:project-review", agents)
            self.assertIn("project-maintain` or `project-intelligence:project-maintain", agents)
            self.assertIn("GitNexus impact/explore/detect_changes", agents)
            self.assertIn("project-intel lifecycle", agents)
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, claude)
            self.assertIn("/project-task", claude)
            self.assertIn("/project-task", nested)
            self.assertIn(str(root / "AGENTS.md"), result["agentFiles"])
            self.assertIn(str(root / "CLAUDE.md"), result["agentFiles"])
            self.assertIn(str(root / ".claude" / "CLAUDE.md"), result["agentFiles"])
            # Skills come from the plugin, not copied into the project
            self.assertFalse((root / ".claude" / "skills").exists())

    def test_install_writes_root_agent_entrypoints_without_overwriting_existing_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Team Notes\n\nKeep this section.\n", encoding="utf-8")
            (root / ".claude").mkdir()
            (root / ".claude" / "CLAUDE.md").write_text("# Claude Team Notes\n\nKeep nested content.\n", encoding="utf-8")

            result = project_intel.install_claude(root)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            nested = (root / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertTrue(agents.startswith(project_intel.AGENT_PROJECT_INTEL_BLOCK_START))
            self.assertTrue(claude.startswith(project_intel.PROJECT_INTEL_BLOCK_START))
            self.assertIn("# Team Notes", agents)
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, agents)
            self.assertIn("This repository uses `.project-intel/`", agents)
            self.assertIn("If slash skills are not available", agents)
            self.assertIn("project-intelligence:*", agents)
            self.assertIn(project_intel.PROJECT_INTEL_BLOCK_START, claude)
            self.assertIn("/project-task", claude)
            self.assertIn("GitNexus or Understand-Anything graph context", nested)
            self.assertIn("Keep nested content.", nested)
            self.assertEqual(nested.count(project_intel.PROJECT_INTEL_BLOCK_START), 1)
            self.assertIn(str(root / "AGENTS.md"), result["agentFiles"])
            self.assertIn(str(root / "CLAUDE.md"), result["agentFiles"])
            # Skills come from the plugin, not copied into the project
            self.assertFalse((root / ".claude" / "skills").exists())

    def test_install_does_not_generate_skill_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            project_intel.install_claude(root)

            # Skills come from the plugin itself — no local copies needed
            self.assertFalse((root / ".claude" / "skills").exists())

    def test_install_migrates_pure_legacy_nested_adapter_to_managed_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / ".claude" / "CLAUDE.md"
            nested.parent.mkdir()
            nested.write_text(
                "# 项目智能\n\n" + project_intel.claude_project_agent_rules() + "\n",
                encoding="utf-8",
            )

            project_intel.install_claude(root)

            body = nested.read_text(encoding="utf-8")
            self.assertEqual(body.count(project_intel.PROJECT_INTEL_BLOCK_START), 1)
            self.assertNotIn("# 项目智能", body)

    def test_install_updates_managed_agent_block_without_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            project_intel.install_claude(root)
            project_intel.install_claude(root)

            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertEqual(agents.count(project_intel.AGENT_PROJECT_INTEL_BLOCK_START), 1)
            self.assertEqual(agents.count(project_intel.AGENT_PROJECT_INTEL_BLOCK_END), 1)
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
            (root / ".project-intel").mkdir()
            (root / ".project-intel" / "manifest.json").write_text("{}", encoding="utf-8")
            with patch.object(project_intel, "init_project", return_value=refresh_result), patch.object(
                project_intel, "run_check", return_value=0
            ):
                exit_code = project_intel.maintain_project(root, "首次维护任务", run_quality=False)
                self.assertEqual(exit_code, 0)
                latest = root / ".project-intel" / "maintenance" / "latest.md"
                self.assertTrue(latest.exists())
                self.assertIn("首次维护任务", latest.read_text(encoding="utf-8"))
                self.assertEqual(list((root / ".project-intel" / "maintenance").glob("*-maintenance.md")), [])

                project_intel.maintain_project(root, "第二次维护任务", run_quality=False)
                self.assertIn("第二次维护任务", latest.read_text(encoding="utf-8"))
                self.assertEqual(list((root / ".project-intel" / "maintenance").glob("*-maintenance.md")), [])

                project_intel.maintain_project(root, "归档维护任务", run_quality=False, archive=True)
                archives = list((root / ".project-intel" / "maintenance").glob("*-maintenance.md"))
                self.assertEqual(len(archives), 1)
                self.assertIn("归档维护任务", archives[0].read_text(encoding="utf-8"))

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
            (root / ".project-intel").mkdir()
            (root / ".project-intel" / "manifest.json").write_text("{}", encoding="utf-8")
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


class SafetyAndConfigTests(unittest.TestCase):
    def test_requirement_paths_reject_parent_traversal_and_external_symlink(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "external").symlink_to(Path(outside), target_is_directory=True)

            self.assertIsNone(project_intel.normalize_project_file(root, "src/../../../../../escaped.ts"))
            self.assertIsNone(project_intel.normalize_project_file(root, "src/external/secret.ts"))
            with self.assertRaises(SystemExit) as raised:
                project_intel.update_file_requirement_docs(root, "拒绝越界需求路径", ["src/../../../../../escaped.ts"])
            self.assertEqual(raised.exception.code, 2)

    def test_invalid_config_is_preserved_and_blocks_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / ".project-intel" / "config.json"
            config.parent.mkdir(parents=True)
            broken = '{"rules": BROKEN_USER_RULE}'
            config.write_text(broken, encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                project_intel.init_project(root, with_graph=False)

            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(config.read_text(encoding="utf-8"), broken)
            self.assertFalse((root / ".project-intel" / "manifest.json").exists())

    def test_atomic_write_replaces_content_and_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "value.md"
            project_intel.write_text(path, "first")
            project_intel.write_text(path, "second")

            self.assertEqual(path.read_text(encoding="utf-8"), "second\n")
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_scan_config_controls_include_exclude_and_hidden_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("src/keep.ts", "src/generated/skip.ts", "docs/skip.ts", ".hidden/skip.ts"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("export const value = true;\n", encoding="utf-8")
            config = {
                "scan": {
                    "include": ["src/**"],
                    "exclude": ["src/generated/**"],
                    "excludeHidden": True,
                }
            }

            files = {project_intel.rel(root, path) for path in project_intel.iter_files(root, config)}

            self.assertEqual(files, {"src/keep.ts"})

    def test_custom_backend_entrypoint_rule_is_applied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "internal-action.ts"
            source.parent.mkdir(parents=True)
            source.write_text("registerInternalAction('sync-order', handler)\n", encoding="utf-8")
            config = {
                "backend": {
                    "entrypointRules": [
                        {"type": "regex", "pattern": r"registerInternalAction\s*\("}
                    ]
                }
            }

            backend = project_intel.scan_backend(root, [source], config)

            self.assertEqual(len(backend["apis"]), 1)
            self.assertIn("config:regex:1", backend["apis"][0]["signals"])

    def test_invalid_hard_rule_regex_is_rejected(self):
        config = {
            "scan": {"include": ["**/*"], "exclude": [".git"], "excludeHidden": True},
            "backend": {"entrypointRules": []},
            "rules": {
                "hard": [{"rule": "无效规则", "check": {"type": "forbid-regex", "pattern": "["}}],
                "preferred": [],
                "inferred": [],
                "candidate": [],
            },
            "quality": {"commands": []},
        }

        with self.assertRaises(SystemExit) as raised:
            project_intel.validate_project_config(config)

        self.assertEqual(raised.exception.code, 2)

    def test_refresh_preserves_manual_quality_commands(self):
        existing = [
            {"kind": "custom", "command": "make verify", "source": "manual"},
            {"kind": "lint", "command": "npm run old-lint", "source": "package.json"},
        ]
        detected = [{"kind": "lint", "command": "npm run lint", "source": "package.json"}]

        merged = project_intel.merge_quality_commands(existing, detected)

        self.assertEqual([item["command"] for item in merged], ["make verify", "npm run lint"])


class HardRuleAndQualityTests(unittest.TestCase):
    def write_initialized_project(self, root, hard_rules, quality_commands=None):
        pdir = root / ".project-intel"
        (pdir / "knowledge").mkdir(parents=True)
        (pdir / "reports").mkdir()
        (pdir / "manifest.json").write_text('{"schemaVersion": 1}', encoding="utf-8")
        config = {
            "schemaVersion": 1,
            "scan": {"include": ["**/*"], "exclude": [".git", ".project-intel"], "excludeHidden": True},
            "backend": {"entrypointRules": []},
            "rules": {"hard": hard_rules, "preferred": [], "inferred": [], "candidate": []},
            "quality": {"commands": quality_commands or []},
        }
        (pdir / "config.json").write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        (pdir / "knowledge" / "frontend.json").write_text("{}", encoding="utf-8")
        (pdir / "knowledge" / "backend.json").write_text("{}", encoding="utf-8")

    def test_hard_rules_fail_pass_and_mark_manual_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "main.ts"
            source.parent.mkdir()
            source.write_text("const forbiddenCall = true;\n", encoding="utf-8")
            rules = [
                "所有公共接口必须人工确认兼容性",
                {
                    "id": "no-forbidden-call",
                    "rule": "禁止 forbiddenCall",
                    "check": {"type": "forbid-regex", "pattern": "forbiddenCall", "include": ["src/**"]},
                },
                {
                    "id": "require-const",
                    "rule": "源码必须包含 const",
                    "check": {"type": "require-regex", "pattern": r"\bconst\b", "include": ["src/**"]},
                },
            ]
            self.write_initialized_project(root, rules)

            exit_code = project_intel.run_check(root, run_quality=False)
            report = (root / ".project-intel" / "reports" / "frontend-quality.md").read_text(encoding="utf-8")

            self.assertEqual(exit_code, 1)
            self.assertIn("manual-review", report)
            self.assertIn("no-forbidden-call", report)
            self.assertIn("src/main.ts:1", report)
            self.assertIn("require-const", report)

    def test_manual_hard_rule_does_not_fail_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_initialized_project(root, ["人工检查事务边界"])

            self.assertEqual(project_intel.run_check(root, run_quality=False), 0)

    def test_hard_path_checks_support_required_and_forbidden_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "required.txt").write_text("ok\n", encoding="utf-8")
            rules = [
                {"id": "required", "rule": "必须有 required.txt", "check": {"type": "require-file", "path": "required.txt"}},
                {"id": "forbidden", "rule": "禁止提交 secret 文件", "check": {"type": "forbid-path", "path": "**/secret.*"}},
            ]
            self.write_initialized_project(root, rules)

            self.assertEqual(project_intel.run_check(root, run_quality=False), 0)
            (root / "src").mkdir()
            (root / "src" / "secret.txt").write_text("secret\n", encoding="utf-8")
            self.assertEqual(project_intel.run_check(root, run_quality=False), 1)

    def test_quality_report_contains_command_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_initialized_project(root, [], [{"kind": "lint", "command": "fake-lint"}])

            with patch.object(project_intel, "run_shell", return_value=(1, "lint stdout detail", "lint stderr detail")):
                exit_code = project_intel.run_check(root, run_quality=True)

            report = (root / ".project-intel" / "reports" / "frontend-quality.md").read_text(encoding="utf-8")
            self.assertEqual(exit_code, 1)
            self.assertIn("lint stdout detail", report)
            self.assertIn("lint stderr detail", report)

    def test_check_requires_initialization(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as raised:
                project_intel.run_check(Path(tmp), run_quality=False)
            self.assertEqual(raised.exception.code, 2)


class HookTests(unittest.TestCase):
    def test_hook_activation_is_idempotent_and_does_not_run_maintain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)

            first = project_intel.activate_git_hooks(root)
            second = project_intel.activate_git_hooks(root)
            body = (root / ".git" / "hooks" / "post-commit").read_text(encoding="utf-8")

            self.assertEqual({item["status"] for item in first}, {"installed"})
            self.assertEqual({item["status"] for item in second}, {"installed"})
            self.assertIn(" refresh ", body)
            self.assertIn(" check ", body)
            self.assertNotIn(" maintain ", body)

    def test_existing_custom_hook_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            target = root / ".git" / "hooks" / "post-commit"
            target.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")

            results = project_intel.activate_git_hooks(root)

            post_commit = next(item for item in results if item["hook"] == "post-commit")
            self.assertEqual(post_commit["status"], "conflict")
            self.assertIn("echo custom", target.read_text(encoding="utf-8"))
            self.assertTrue((root / ".project-intel" / "hooks" / "post-commit.pending.sh").exists())

    def test_git_hook_path_uses_git_rev_parse_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hooks = root / "worktree-common" / "hooks"
            hooks.mkdir(parents=True)
            with patch.object(project_intel, "run", return_value=(0, str(hooks), "")):
                self.assertEqual(project_intel.git_hooks_path(root), hooks.resolve())


class SkillCommandPathTests(unittest.TestCase):
    def test_skill_files_use_global_project_intel_command(self):
        skills_dir = MODULE_PATH.parents[1] / "skills"
        skill_files = sorted(skills_dir.glob("*/SKILL.md"))
        self.assertTrue(skill_files, "未找到任何 SKILL.md")
        for skill_md in skill_files:
            text = skill_md.read_text(encoding="utf-8")
            self.assertNotIn("/Users/", text, f"{skill_md} 包含硬编码的用户路径")
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)
            self.assertNotIn("project_intel.py", text)
            self.assertIn("project-intel", text, f"{skill_md} 未提供 CLI 调用")

    def test_generated_task_impact_doc_uses_global_cli(self):
        snapshot = {
            "manifest": {"graphSources": []},
            "frontend": {"components": [], "hooks": []},
            "backend": {"services": []},
        }
        doc = project_intel.build_task_impact_doc(Path("/tmp/example"), "示例任务", snapshot)
        self.assertNotIn("/Users/xumeng/plugins", doc)
        self.assertIn("project-intel maintain", doc)

    def test_generated_hook_script_uses_runtime_script_path(self):
        body = project_intel.hook_script_body("post-commit")
        self.assertNotIn("/Users/xumeng/plugins", body)
        self.assertIn(str(MODULE_PATH.resolve()), body)


class CliAndReleaseContractTests(unittest.TestCase):
    def test_refresh_only_runs_graph_when_explicitly_requested(self):
        result = {"manifest": {"fileCount": 0}, "agentFiles": [], "legacyCleanup": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".project-intel").mkdir()
            (root / ".project-intel" / "manifest.json").write_text("{}", encoding="utf-8")
            with patch.object(project_intel, "init_project", return_value=result) as init_project:
                self.assertEqual(project_intel.main(["--project", str(root), "refresh"]), 0)
                init_project.assert_called_once_with(root.resolve(), refresh=True, with_graph=False)
            with patch.object(project_intel, "init_project", return_value=result) as init_project:
                self.assertEqual(project_intel.main(["--project", str(root), "refresh", "--with-graph"]), 0)
                init_project.assert_called_once_with(root.resolve(), refresh=True, with_graph=True)

    def test_cli_smoke_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "index.ts"
            source.parent.mkdir()
            source.write_text("export const answer = 42;\n", encoding="utf-8")
            base = [project_intel.sys.executable, str(MODULE_PATH), "--project", str(root)]

            for args in (
                ["init", "--no-graph"],
                ["check"],
                ["refresh"],
                ["maintain", "--task", "完成稳定性维护", "--files", "src/index.ts"],
            ):
                completed = subprocess.run(base + args, text=True, capture_output=True)
                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_versions_prompts_and_publisher_are_consistent(self):
        repo_root = MODULE_PATH.parents[3]
        plugin_root = MODULE_PATH.parents[1]
        claude = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        npm = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))

        self.assertEqual(project_intel.VERSION, "0.1.13")
        self.assertEqual(claude["version"], project_intel.VERSION)
        self.assertEqual(codex["version"].split("+")[0], project_intel.VERSION)
        self.assertEqual(npm["version"], project_intel.VERSION)
        self.assertEqual(npm["bin"]["project-intel"], "bin/project-intel.mjs")
        self.assertLessEqual(len(codex["interface"]["defaultPrompt"]), 3)
        self.assertEqual(codex["author"]["name"], "crayonYYxm")
        self.assertEqual(codex["interface"]["developerName"], "crayonYYxm")

    def test_skills_only_persist_specs_and_plans_on_explicit_request(self):
        skills = MODULE_PATH.parents[1] / "skills"
        brainstorm = (skills / "project-brainstorm" / "SKILL.md").read_text(encoding="utf-8")
        plan = (skills / "project-plan" / "SKILL.md").read_text(encoding="utf-8")
        refresh = (skills / "project-refresh" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("only when the user explicitly asks", brainstorm)
        self.assertIn("Do not create spec or plan files merely because the skill triggered", plan)
        self.assertNotIn(".claude/skills/project-*", refresh)

    def test_release_sources_do_not_contain_removed_integration_name(self):
        repo_root = MODULE_PATH.parents[3]
        plugin_root = MODULE_PATH.parents[1]
        banned = "cgraph" + "x"
        files = [repo_root / "README.md"] + list(plugin_root.rglob("*"))
        for path in files:
            if not path.is_file() or "__pycache__" in path.parts or path.name == "plugin-intro-teal.html":
                continue
            self.assertNotIn(banned, path.read_text(encoding="utf-8", errors="ignore").lower(), str(path))


class InferStandardsTests(unittest.TestCase):
    def _frontend(self, **overrides):
        base = {
            "components": [
                {"name": "UserTable", "path": "src/components/UserTable.vue", "kind": "vue"},
                {"name": "OrderList", "path": "src/components/OrderList.vue", "kind": "vue"},
                {"name": "SearchBar", "path": "src/components/SearchBar.vue", "kind": "vue"},
                {"name": "DetailDialog", "path": "src/components/DetailDialog.vue", "kind": "vue"},
                {"name": "OrderForm", "path": "src/pages/order/components/OrderForm.vue", "kind": "vue", "scope": "page-local"},
                {"name": "OrderCoupon", "path": "src/pages/order/components/OrderCoupon.vue", "kind": "vue", "scope": "page-local"},
                {"name": "OrderAmount", "path": "src/pages/order/components/OrderAmount.vue", "kind": "vue", "scope": "page-local"},
            ],
            "hooks": [
                {"name": "usePagination", "path": "src/hooks/usePagination.ts"},
                {"name": "useSearch", "path": "src/hooks/useSearch.ts"},
                {"name": "useExport", "path": "src/hooks/useExport.ts"},
            ],
            "apiModules": [
                {"path": "src/api/user.ts", "signals": ["request"], "wrappers": ["$post"], "servicePrefixes": [{"name": "miniName", "value": "/so-mini-service/openapi"}]},
                {"path": "src/api/order.ts", "signals": ["request"], "wrappers": ["$post"], "servicePrefixes": [{"name": "serviceName", "value": "/order-service/service"}]},
                {"path": "src/api/goods.ts", "signals": ["request"], "wrappers": ["$post"], "servicePrefixes": [{"name": "adaptName", "value": "/order-service/adapt"}]},
            ],
            "routes": [
                {"path": "src/router/modules/subpackages/order/order.js", "baseUrls": ["pages/subPages/order/"], "routes": ["orderConfirm/orderConfirm", "payResult/payResult"], "routeCount": 2, "customNavigationCount": 2, "pluginProviders": []},
                {"path": "src/router/modules/subpackages/information/index.js", "baseUrls": ["pages/subPages/information/"], "routes": ["login/login", "pickNumber/pickNumber"], "routeCount": 2, "customNavigationCount": 1, "pluginProviders": ["wx2fe3215291922d97"]},
            ],
            "stores": [{"path": "src/stores/module/order.ts", "definesStore": True}],
            "styles": [
                {"path": "src/components/UserTable.vue", "hardcodedValuesSample": ["#fff", "12px"], "count": 30},
                {"path": "src/pages/home.vue", "hardcodedValuesSample": ["#333"], "count": 25},
            ],
            "redundancyCandidates": [
                {
                    "type": "frontend-pattern",
                    "name": "table",
                    "count": 5,
                    "locations": ["src/pages/a.vue", "src/pages/b.vue"],
                    "level": "candidate",
                },
            ],
        }
        base.update(overrides)
        return base

    def _backend(self, **overrides):
        base = {
            "apis": [
                {"path": "server/controller/UserController.java", "framework": "Spring", "signals": ["RestController"], "endpoints": ["/user"]},
                {"path": "server/controller/OrderController.java", "framework": "Spring", "signals": ["RestController"], "endpoints": ["/order"]},
            ],
            "services": [
                {"name": "UserService", "path": "server/service/UserService.java"},
                {"name": "OrderService", "path": "server/service/OrderService.java"},
            ],
            "dataTypes": [
                {"name": "UserDTO", "path": "server/dto/UserDTO.java"},
                {"name": "OrderDTO", "path": "server/dto/OrderDTO.java"},
            ],
            "repositories": [
                {"name": "UserRepository", "path": "server/repository/UserRepository.java"},
            ],
            "configs": [
                {"path": "server/src/main/resources/application.yml", "kind": "yml", "keys": ["spring", "server", "order.timeout"]}
            ],
            "permissionChecks": [
                {"path": "server/controller/OrderController.java", "signals": ["@PreAuthorize(\"hasRole('ORDER')\")"], "level": "candidate"}
            ],
            "transactions": [
                {"path": "server/service/OrderService.java", "signals": ["@Transactional"], "level": "candidate"}
            ],
            "remoteCalls": [
                {"path": "server/service/OrderService.java", "signals": ["RestTemplate"], "level": "candidate"}
            ],
            "messagesJobs": [
                {"path": "server/job/OrderJob.java", "signals": ["@Scheduled(cron = \"0 * * * * ?\")"], "level": "candidate"}
            ],
            "errorCodes": [
                {"path": "server/service/OrderService.java", "signals": ["ORDER_FAILED", "BusinessException"], "level": "candidate"}
            ],
            "utilities": [
                {"name": "OrderUtils", "path": "server/common/OrderUtils.java", "exports": ["normalizeOrder"]}
            ],
            "candidateEntrypoints": [],
        }
        base.update(overrides)
        return base

    def test_infers_naming_directory_style_request_pattern_and_backend_rules(self):
        rules = project_intel.infer_standards(self._frontend(), self._backend())
        self.assertTrue(rules, "应至少推断出一条规范")
        for rule in rules:
            self.assertEqual(rule["level"], "inferred")
            self.assertTrue(project_intel.contains_cjk(rule["rule"]), f"规则文案应为中文：{rule}")
            self.assertIn("category", rule)
            self.assertIn("evidence", rule)
        categories = {rule["category"] for rule in rules}
        self.assertIn("naming", categories)
        self.assertIn("structure", categories)
        self.assertIn("style", categories)
        self.assertIn("request", categories)
        self.assertIn("api-prefix", categories)
        self.assertIn("router", categories)
        self.assertIn("component-reuse", categories)
        self.assertIn("ui-pattern", categories)
        self.assertIn("backend-layering", categories)
        self.assertIn("backend-api", categories)
        self.assertIn("config", categories)
        self.assertIn("permission", categories)
        self.assertIn("transaction", categories)
        self.assertIn("remote-call", categories)
        self.assertIn("message-job", categories)
        self.assertIn("error-code", categories)
        self.assertIn("utility", categories)

    def test_extract_emits_does_not_read_prop_defaults_as_events(self):
        text = """
        const props = defineProps({
          type: { type: String, default: 'primary' },
          visible: { type: Boolean, default: false }
        })
        const emit = defineEmits(['update:visible', 'onConfirm'])
        """
        self.assertEqual(project_intel.extract_emits(text), ["onConfirm", "update:visible"])

    def test_extract_vue_props_only_reads_top_level_runtime_props(self):
        text = """
        const props = defineProps({
          type: { type: String, default: 'primary', required: true },
          visible: { type: Boolean, default: false },
          "order-info": {
            type: Object,
            default: () => ({ id: '', name: '' })
          }
        })
        """
        self.assertEqual(project_intel.extract_vue_props(text), ["order-info", "type", "visible"])

    def test_scan_frontend_extracts_mini_app_api_route_store_and_component_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "components" / "common").mkdir(parents=True)
            (root / "src" / "components" / "common" / "dx-dialog.vue").write_text(
                "<script setup>const emit = defineEmits(['update:visible'])</script>\n",
                encoding="utf-8",
            )
            (root / "src" / "api" / "order").mkdir(parents=True)
            (root / "src" / "api" / "order" / "index.ts").write_text(
                "const miniName = '/so-mini-service/openapi'\n"
                "export const saveOrder = (params) => $post(`${miniName}/somini_api_saveOrder`, [params])\n",
                encoding="utf-8",
            )
            (root / "src" / "router" / "modules" / "subpackages" / "order").mkdir(parents=True)
            (root / "src" / "router" / "modules" / "subpackages" / "order" / "order.js").write_text(
                "module.exports={baseUrl:'pages/subPages/order/',children:[{path:'orderConfirm/orderConfirm',style:{navigationStyle:'custom'}}]}\n",
                encoding="utf-8",
            )
            (root / "src" / "stores" / "module").mkdir(parents=True)
            (root / "src" / "stores" / "module" / "order.ts").write_text("export const useOrder = defineStore('order', {})\n", encoding="utf-8")

            files = list(root.rglob("*"))
            frontend = project_intel.scan_frontend(root, [path for path in files if path.is_file()])

        self.assertEqual(frontend["components"][0]["scope"], "public")
        self.assertEqual(frontend["components"][0]["emits"], ["update:visible"])
        self.assertEqual(frontend["apiModules"][0]["wrappers"], ["$post"])
        self.assertIn("${miniName}/somini_api_saveOrder", frontend["apiModules"][0]["endpoints"])
        self.assertEqual(frontend["apiModules"][0]["servicePrefixes"][0]["value"], "/so-mini-service/openapi")
        self.assertEqual(frontend["routes"][0]["baseUrls"], ["pages/subPages/order/"])
        self.assertEqual(frontend["routes"][0]["customNavigationCount"], 1)
        self.assertTrue(frontend["stores"][0]["definesStore"])

    def test_standards_docs_include_detailed_frontend_files(self):
        frontend = self._frontend(
            components=[
                {"name": "DxDialog", "path": "src/components/common/dx-dialog.vue", "kind": "vue", "scope": "public", "props": ["visible", "content"], "emits": ["update:visible"]},
                {"name": "OrderForm", "path": "src/pages/subPages/order/orderConfirm/components/orderForm.vue", "kind": "vue", "scope": "page-local", "props": ["orderInfo"], "emits": ["change"]},
            ],
        )
        graph = {
            "understandSummary": {
                "domains": [{"name": "订单/支付", "count": 2, "paths": ["src/pages/subPages/order/orderConfirm/orderConfirm.vue"], "summaries": ["订单确认页面负责提交和支付前确认。"]}],
                "keyModules": [{"path": "src/api/order/index.ts", "name": "order api", "summary": "订单接口", "tags": ["order"]}],
                "topPathPrefixes": [["src/pages/subPages/order", 10]],
            }
        }
        docs = project_intel.standards_docs(
            {
                "frontend": frontend,
                "backend": self._backend(),
                "config": {"quality": {"commands": []}, "rules": {"inferred": []}},
                "graph": graph,
            }
        )
        self.assertIn("components.md", docs)
        self.assertIn("api.md", docs)
        self.assertIn("router.md", docs)
        self.assertIn("domain-flows.md", docs)
        self.assertIn("DxDialog", docs["components.md"])
        self.assertIn("/so-mini-service/openapi", docs["api.md"])
        self.assertIn("pages/subPages/order/", docs["router.md"])
        self.assertIn("订单/支付", docs["domain-flows.md"])

    def test_standards_docs_include_detailed_backend_files(self):
        docs = project_intel.standards_docs(
            {
                "frontend": self._frontend(),
                "backend": self._backend(),
                "config": {"quality": {"commands": []}, "rules": {"inferred": []}},
                "graph": {},
            }
        )
        expected = {
            "backend-api.md",
            "backend-services.md",
            "backend-models.md",
            "backend-repository.md",
            "backend-config.md",
            "backend-security.md",
            "backend-transactions.md",
            "backend-remote-calls.md",
            "backend-async.md",
            "backend-errors.md",
            "backend-utilities.md",
        }
        self.assertTrue(expected.issubset(docs.keys()))
        self.assertIn("API 与入口", docs["backend-api.md"])
        self.assertIn("OrderService", docs["backend-services.md"])
        self.assertIn("UserDTO", docs["backend-models.md"])
        self.assertIn("UserRepository", docs["backend-repository.md"])
        self.assertIn("order.timeout", docs["backend-config.md"])
        self.assertIn("PreAuthorize", docs["backend-security.md"])
        self.assertIn("Transactional", docs["backend-transactions.md"])
        self.assertIn("RestTemplate", docs["backend-remote-calls.md"])
        self.assertIn("Scheduled", docs["backend-async.md"])
        self.assertIn("ORDER_FAILED", docs["backend-errors.md"])
        self.assertIn("OrderUtils", docs["backend-utilities.md"])
        self.assertIn("backend-api.md", docs["backend.md"])

    def test_infer_standards_skips_low_sample_signals(self):
        frontend = self._frontend(
            components=[{"name": "One", "path": "src/components/One.vue", "kind": "vue"}],
            hooks=[],
            routes=[],
            apiModules=[],
            stores=[],
            styles=[],
            redundancyCandidates=[],
        )
        backend = self._backend(
            apis=[],
            services=[],
            dataTypes=[],
            repositories=[],
            configs=[],
            permissionChecks=[],
            transactions=[],
            remoteCalls=[],
            messagesJobs=[],
            errorCodes=[],
            utilities=[],
        )
        rules = project_intel.infer_standards(frontend, backend)
        self.assertEqual(rules, [], "样本不足时不应产出推断规范")

    def test_scan_backend_extracts_detailed_spring_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            controller = root / "server" / "src" / "main" / "java" / "com" / "demo" / "controller" / "OrderController.java"
            controller.parent.mkdir(parents=True)
            controller.write_text(
                """
                @RestController
                @RequestMapping("/api/orders")
                public class OrderController {
                  @PreAuthorize("hasRole('ORDER')")
                  @PostMapping("/create")
                  public OrderDTO create(@RequestBody OrderDTO req) { return null; }
                }
                """,
                encoding="utf-8",
            )
            service = root / "server" / "src" / "main" / "java" / "com" / "demo" / "service" / "OrderService.java"
            service.parent.mkdir(parents=True)
            service.write_text(
                """
                @Service
                public class OrderService {
                  private RestTemplate restTemplate;
                  @Transactional
                  public OrderDTO createOrder(OrderDTO req) {
                    throw new BusinessException(ErrorCode.ORDER_FAILED);
                  }
                }
                """,
                encoding="utf-8",
            )
            dto = root / "server" / "src" / "main" / "java" / "com" / "demo" / "dto" / "OrderDTO.java"
            dto.parent.mkdir(parents=True)
            dto.write_text(
                """
                public class OrderDTO {
                  private String orderId;
                  private Integer amount;
                }
                """,
                encoding="utf-8",
            )
            mapper = root / "server" / "src" / "main" / "resources" / "mapper" / "OrderMapper.xml"
            mapper.parent.mkdir(parents=True)
            mapper.write_text("<mapper><select id=\"selectOrder\">SELECT * FROM ord_order</select></mapper>", encoding="utf-8")
            config = root / "server" / "src" / "main" / "resources" / "application.yml"
            config.write_text("server:\n  port: 8080\norder:\n  timeout: 30\n", encoding="utf-8")
            job = root / "server" / "src" / "main" / "java" / "com" / "demo" / "job" / "OrderJob.java"
            job.parent.mkdir(parents=True)
            job.write_text("@Scheduled(cron = \"0 * * * * ?\") public void syncOrders() {}\n", encoding="utf-8")
            util = root / "server" / "src" / "main" / "java" / "com" / "demo" / "common" / "OrderUtils.java"
            util.parent.mkdir(parents=True)
            util.write_text("public class OrderUtils { public static String normalizeOrder(String id) { return id; } }\n", encoding="utf-8")

            files = [path for path in root.rglob("*") if path.is_file()]
            backend = project_intel.scan_backend(root, files)

        self.assertEqual(backend["apis"][0]["framework"], "Spring")
        self.assertIn("/api/orders", backend["apis"][0]["endpoints"])
        self.assertTrue(backend["permissionChecks"])
        self.assertTrue(backend["transactions"])
        self.assertTrue(backend["remoteCalls"])
        self.assertTrue(backend["messagesJobs"])
        self.assertTrue(backend["errorCodes"])
        self.assertEqual(backend["dataTypes"][0]["fields"], ["orderId", "amount"])
        self.assertEqual(backend["repositories"][0]["methods"], ["selectOrder"])
        self.assertIn("server", backend["configs"][0]["keys"])
        self.assertEqual(backend["utilities"][0]["name"], "OrderUtils")

    def test_init_writes_inferred_rules_into_config_and_standards_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comp_dir = root / "src" / "components"
            comp_dir.mkdir(parents=True)
            for name in ("UserTable", "OrderList", "SearchBar", "DetailDialog"):
                (comp_dir / f"{name}.vue").write_text(
                    "<template><div /></template>\n", encoding="utf-8"
                )
            hooks_dir = root / "src" / "hooks"
            hooks_dir.mkdir(parents=True)
            for name in ("usePagination", "useSearch", "useExport"):
                (hooks_dir / f"{name}.ts").write_text("export default () => {}\n", encoding="utf-8")

            with patch.object(project_intel, "detect_tooling", return_value={"optional": {}, "recommendedActions": []}), patch.object(
                project_intel, "handle_tooling_setup", return_value=[]
            ):
                project_intel.init_project(root, refresh=False, with_graph=False)

            config = json.loads((root / ".project-intel" / "config.json").read_text(encoding="utf-8"))
            inferred = config["rules"]["inferred"]
            self.assertTrue(inferred, "config.rules.inferred 应包含推断规范")
            frontend_md = (root / ".project-intel" / "standards" / "frontend.md").read_text(encoding="utf-8")
            self.assertIn("## 推断规范", frontend_md)

    def test_refresh_preserves_user_rules_and_replaces_inferred(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir(parents=True)
            pdir = root / ".project-intel"
            pdir.mkdir(parents=True)
            (pdir / "config.json").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "rules": {
                            "hard": [{"rule": "禁止直接操作 DOM"}],
                            "preferred": [],
                            "inferred": [{"rule": "过时的旧推断", "level": "inferred"}],
                            "candidate": [],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.object(project_intel, "detect_tooling", return_value={"optional": {}, "recommendedActions": []}), patch.object(
                project_intel, "handle_tooling_setup", return_value=[]
            ):
                project_intel.init_project(root, refresh=True, with_graph=False)

            config = json.loads((pdir / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["rules"]["hard"], [{"rule": "禁止直接操作 DOM"}])
            self.assertNotIn(
                {"rule": "过时的旧推断", "level": "inferred"},
                config["rules"]["inferred"],
                "旧的 inferred 规则应被重算结果替换",
            )


class StabilityAndPackagingTests(unittest.TestCase):
    def test_init_keeps_team_facts_portable_and_tooling_local(self):
        tooling = {
            "required": [{"name": "python3", "status": "present"}],
            "optional": {
                "git": {"status": "present"},
                "node": {"status": "present"},
                "packageManagers": [],
                "gitnexus": {"status": "missing"},
                "understandAnything": {
                    "status": "agent-installed",
                    "pluginRoots": ["/Users/example/.claude/plugins/cache/secret"],
                },
                "qualityTools": [],
            },
            "graphActions": [],
            "recommendedActions": [],
            "followUpActions": [],
            "generatedAt": "2026-07-11T00:00:00Z",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export const ok = true;\n", encoding="utf-8")
            with patch.object(project_intel, "detect_tooling", return_value=tooling), patch.object(
                project_intel, "handle_tooling_setup", return_value=[]
            ):
                project_intel.init_project(root, with_graph=False)
            config_text = (root / ".project-intel" / "config.json").read_text(encoding="utf-8")
            manifest_text = (root / ".project-intel" / "manifest.json").read_text(encoding="utf-8")
            local_text = (root / ".project-intel" / "local" / "tooling.json").read_text(encoding="utf-8")
            self.assertNotIn("pluginRoots", config_text)
            self.assertNotIn(str(root), manifest_text)
            self.assertIn('"projectRoot": "."', manifest_text)
            self.assertIn("pluginRoots", local_text)
            self.assertIn(".project-intel/local/", (root / ".gitignore").read_text(encoding="utf-8"))

    def test_empty_or_invalid_graph_does_not_satisfy_strict_init(self):
        tooling = {"optional": {}, "recommendedActions": [], "graphActions": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitnexus").mkdir()
            with patch.object(project_intel, "detect_tooling", return_value=tooling), patch.object(
                project_intel, "handle_tooling_setup", return_value=[]
            ):
                with self.assertRaises(SystemExit) as raised:
                    project_intel.init_project(root, with_graph=True, strict=True)
            self.assertEqual(raised.exception.code, 2)
            source = project_intel.detect_graph_sources(root)[0]
            self.assertEqual(source["status"], "invalid")

    def test_changed_requirement_files_include_untracked_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "test"], cwd=root, check=True)
            (root / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
            source = root / "src" / "new.ts"
            source.parent.mkdir()
            source.write_text("export const created = true;\n", encoding="utf-8")
            self.assertEqual(project_intel.changed_requirement_files(root), ["src/new.ts"])

    def test_query_includes_graph_and_prints_match_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = root / ".project-intel"
            (pdir / "graph").mkdir(parents=True)
            (pdir / "manifest.json").write_text("{}", encoding="utf-8")
            (pdir / "graph" / "project-graph.json").write_text(
                json.dumps({"marker": "inventory-relationship"}), encoding="utf-8"
            )
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(project_intel.query_project(root, "relationship"), 0)
            self.assertIn("project-graph.json", output.getvalue())
            self.assertIn("inventory-relationship", output.getvalue())

    def test_generated_agent_entrypoints_are_excluded_from_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("generated\n", encoding="utf-8")
            (root / "CLAUDE.md").write_text("generated\n", encoding="utf-8")
            source = root / "src" / "index.ts"
            source.parent.mkdir()
            source.write_text("export const ok = true;\n", encoding="utf-8")
            files = {project_intel.rel(root, path) for path in project_intel.iter_files(root)}
            self.assertEqual(files, {"src/index.ts"})

    def test_dry_run_and_json_cli_do_not_write_project_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export const ok = true;\n", encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(project_intel.main(["--project", str(root), "init", "--no-graph", "--dry-run", "--json"]), 0)
            payload = json.loads(output.getvalue())
            self.assertTrue(payload["result"]["dryRun"])
            self.assertFalse((root / ".project-intel").exists())

    def test_workspace_and_multilanguage_quality_commands_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8")
            child = root / "packages" / "web"
            child.mkdir(parents=True)
            (child / "package.json").write_text(json.dumps({"name": "web", "scripts": {"lint": "eslint .", "test": "vitest"}}), encoding="utf-8")
            (root / "pom.xml").write_text("<project />", encoding="utf-8")
            (root / "pyproject.toml").write_text("[tool.ruff]\n[tool.pytest.ini_options]\n", encoding="utf-8")
            (root / "go.mod").write_text("module demo\n", encoding="utf-8")
            (root / "Cargo.toml").write_text("[package]\nname='demo'\n", encoding="utf-8")
            package = project_intel.detect_package(root)
            commands = project_intel.detect_quality_commands(root, package)
            rendered = "\n".join(item["command"] for item in commands)
            self.assertIn("packages/web", rendered)
            self.assertIn("mvn test", rendered)
            self.assertIn("python3 -m ruff check .", rendered)
            self.assertIn("go test ./...", rendered)
            self.assertIn("cargo check", rendered)

    def test_agent_install_dry_run_is_explicit_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(project_intel, "command_exists", return_value=True), patch.object(
                project_intel, "marketplace_bundle_root", return_value=Path("/bundle")
            ), patch.object(project_intel, "run") as run:
                code, result = project_intel.install_agent_plugin(root, "all", dry_run=True)
            self.assertEqual(code, 0)
            self.assertTrue(all(item["status"] == "planned" for item in result["results"]))
            run.assert_not_called()

    def test_refresh_reuses_file_signature_cache_for_unchanged_source(self):
        tooling = {"optional": {}, "recommendedActions": [], "graphActions": []}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "index.ts"
            source.parent.mkdir()
            source.write_text("export const answer = 42;\n", encoding="utf-8")
            with patch.object(project_intel, "detect_tooling", return_value=tooling), patch.object(
                project_intel, "handle_tooling_setup", return_value=[]
            ):
                project_intel.init_project(root, with_graph=False)
            with patch.object(project_intel.frontend_scanner, "scan_frontend_file") as frontend_file, patch.object(
                project_intel.backend_scanner, "scan_backend_file"
            ) as backend_file, patch.object(project_intel, "detect_tooling", return_value=tooling), patch.object(
                project_intel, "handle_tooling_setup", return_value=[]
            ):
                project_intel.init_project(root, refresh=True, with_graph=False)
            frontend_file.assert_not_called()
            backend_file.assert_not_called()


class LegacyLocalSkillCleanupTests(unittest.TestCase):
    def test_cleanup_removes_legacy_skill_copies_and_claude_md_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / ".claude" / "skills" / "project-task"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("---\nname: project-task\n---\n", encoding="utf-8")
            custom = root / ".claude" / "skills" / "my-own"
            custom.mkdir(parents=True)
            (custom / "SKILL.md").write_text("---\nname: my-own\n---\n", encoding="utf-8")
            claude_md = root / "CLAUDE.md"
            claude_md.write_text(
                "<!-- local-project-skills:start -->\n旧规则\n<!-- local-project-skills:end -->\n\n# 用户内容\n保留我\n",
                encoding="utf-8",
            )

            removed = project_intel.cleanup_legacy_local_skills(root)

            self.assertFalse(legacy.exists())
            self.assertTrue(custom.exists())
            text = claude_md.read_text(encoding="utf-8")
            self.assertNotIn("local-project-skills", text)
            self.assertNotIn("旧规则", text)
            self.assertIn("保留我", text)
            self.assertTrue(removed)

    def test_cleanup_is_noop_for_clean_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            removed = project_intel.cleanup_legacy_local_skills(root)
            self.assertEqual(removed, [])

    def test_install_claude_runs_legacy_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / ".claude" / "skills" / "project-debug"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("---\nname: project-debug\n---\n", encoding="utf-8")

            result = project_intel.install_claude(root)

            self.assertFalse(legacy.exists())
            self.assertTrue(result.get("legacyCleanup"))


if __name__ == "__main__":
    unittest.main()
