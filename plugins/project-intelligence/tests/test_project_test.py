import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_intel.py"
SPEC = importlib.util.spec_from_file_location("project_intel_test_facade", MODULE_PATH)
project_intel = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(project_intel)


class ProjectTestEvidenceTests(unittest.TestCase):
    def initialized_project(self, root: Path, commands=None) -> Path:
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True)
        source.write_text("def answer():\n    return 42\n", encoding="utf-8")
        project_intel.init_project(root, with_graph=False)
        config_path = root / ".project-intel" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["quality"]["commands"] = commands or []
        config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return source

    def test_red_phase_requires_an_expected_test_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            with patch.object(project_intel, "run_shell", return_value=(1, "expected assertion failure", "")):
                code, result = project_intel.run_project_test(
                    root,
                    "新增重试退避策略",
                    "red",
                    commands=["python3 -m unittest tests.test_retry"],
                    files=["src/service.py", "tests/test_retry.py"],
                )

            self.assertEqual(code, 0)
            self.assertEqual(result["entry"]["status"], "passed")
            self.assertEqual(result["entry"]["phase"], "red")
            self.assertIn("expected assertion failure", (root / ".project-intel/reports/test-evidence.md").read_text(encoding="utf-8"))

    def test_red_phase_rejects_command_errors_and_unexpected_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            for exit_code in (0, 124, 127):
                with self.subTest(exit_code=exit_code), patch.object(project_intel, "run_shell", return_value=(exit_code, "", "error")):
                    code, result = project_intel.run_project_test(
                        root,
                        "修复缓存回归问题",
                        "red",
                        commands=["bad-test-command"],
                        files=["src/service.py"],
                    )
                    self.assertEqual(code, 1)
                    self.assertEqual(result["entry"]["status"], "failed")

    def test_green_evidence_is_task_scoped_file_scoped_and_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.initialized_project(root)
            with patch.object(project_intel, "run_shell", return_value=(0, "1 passed", "")):
                code, _ = project_intel.run_project_test(
                    root,
                    "新增重试退避策略",
                    "green",
                    commands=["python3 -m pytest tests/test_retry.py"],
                    files=["src/service.py"],
                )

            self.assertEqual(code, 0)
            status = project_intel.testing_module.evaluate_test_evidence(root, "新增重试退避策略", ["src/service.py"])
            self.assertTrue(status["ready"])
            self.assertEqual(status["passingPhase"], "green")

            future = source.stat().st_mtime + 5
            os.utime(source, (future, future))
            stale = project_intel.testing_module.evaluate_test_evidence(root, "新增重试退避策略", ["src/service.py"])
            self.assertFalse(stale["ready"])

    def test_finish_rejects_changed_source_without_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            with patch.object(project_intel, "run_check", return_value=0), patch.object(
                project_intel,
                "git_diff_summary",
                return_value={"available": True, "status": [" M src/service.py"], "changedFiles": ["src/service.py"], "stat": "src/service.py | 1 +"},
            ):
                code = project_intel.finish_project(root, "新增重试退避策略", files=["src/service.py"])

            self.assertEqual(code, 1)
            report = (root / ".project-intel/reports/finish-report.md").read_text(encoding="utf-8")
            self.assertIn("测试证据门禁：未通过", report)

    def test_finish_accepts_fresh_green_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            with patch.object(project_intel, "run_shell", return_value=(0, "1 passed", "")):
                project_intel.run_project_test(
                    root,
                    "新增重试退避策略",
                    "green",
                    commands=["python3 -m pytest tests/test_retry.py"],
                    files=["src/service.py"],
                )
            with patch.object(project_intel, "run_check", return_value=0), patch.object(
                project_intel,
                "git_diff_summary",
                return_value={"available": True, "status": [" M src/service.py"], "changedFiles": ["src/service.py"], "stat": "src/service.py | 1 +"},
            ):
                code = project_intel.finish_project(root, "新增重试退避策略", files=["src/service.py"])

            self.assertEqual(code, 0)
            self.assertIn("测试证据门禁：通过", (root / ".project-intel/reports/finish-report.md").read_text(encoding="utf-8"))

    def test_finish_accepts_explicit_reproducible_manual_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            with patch.object(project_intel, "run_check", return_value=0), patch.object(
                project_intel,
                "git_diff_summary",
                return_value={"available": True, "status": [" M src/service.py"], "changedFiles": ["src/service.py"], "stat": "src/service.py | 1 +"},
            ):
                code = project_intel.finish_project(
                    root,
                    "调整设备端交互行为",
                    files=["src/service.py"],
                    manual_evidence="在测试设备打开页面，输入空值后观察到错误提示且日志无异常。",
                )

            self.assertEqual(code, 0)
            payload = project_intel.testing_module.load_test_evidence(root)
            self.assertEqual(payload["entries"][-1]["phase"], "manual")

    def test_finish_run_quality_records_detected_test_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root, [{"kind": "test", "command": "python3 -m pytest", "source": "manual"}])

            def fake_check(_root, run_quality, result_sink=None):
                self.assertTrue(run_quality)
                result_sink.append({"kind": "test", "command": "python3 -m pytest", "exitCode": 0, "stdout": "2 passed", "stderr": ""})
                return 0

            with patch.object(project_intel, "run_check", side_effect=fake_check), patch.object(
                project_intel,
                "git_diff_summary",
                return_value={"available": True, "status": [" M src/service.py"], "changedFiles": ["src/service.py"], "stat": "src/service.py | 1 +"},
            ):
                code = project_intel.finish_project(root, "新增测试执行门禁", run_quality=True, files=["src/service.py"])

            self.assertEqual(code, 0)
            payload = project_intel.testing_module.load_test_evidence(root)
            self.assertEqual(payload["entries"][-1]["phase"], "verify")

    def test_manual_phase_requires_reproducible_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            for evidence in ("", "已手动验证", "manual verification passed"):
                with self.subTest(evidence=evidence), self.assertRaises(SystemExit) as raised:
                    project_intel.run_project_test(
                        root,
                        "调整视觉状态",
                        "manual",
                        files=["src/service.py"],
                        manual_evidence=evidence,
                    )
                self.assertEqual(raised.exception.code, 2)

    def test_red_observation_is_file_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            other = root / "src" / "other.py"
            other.write_text("value = 1\n", encoding="utf-8")
            with patch.object(project_intel, "run_shell", return_value=(1, "expected assertion failure", "")):
                project_intel.run_project_test(
                    root,
                    "修复缓存回归问题",
                    "red",
                    commands=["python3 -m pytest tests/test_cache.py"],
                    files=["src/other.py"],
                )

            status = project_intel.testing_module.evaluate_test_evidence(
                root,
                "修复缓存回归问题",
                ["src/service.py"],
            )
            self.assertFalse(status["redObserved"])


if __name__ == "__main__":
    unittest.main()
