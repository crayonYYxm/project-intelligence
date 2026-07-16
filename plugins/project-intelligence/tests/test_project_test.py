import importlib.util
import json
import os
import subprocess
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

    def initialized_requirement_project(self, root: Path) -> Path:
        source = self.initialized_project(root)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
        subprocess.run(["git", "add", "src/service.py", ".project-intel"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
        self.assertEqual(project_intel.main([
            "--project", str(root), "intake",
            "--requirement-id", "REQ-TEST-1",
            "--requirement-name", "需求级测试门禁",
            "--external-api", "no",
            "--track", "complex",
        ]), 0)
        self.assertEqual(project_intel.main([
            "--project", str(root), "requirement", "generate",
            "--requirement-id", "REQ-TEST-1", "--type", "requirement-design",
        ]), 0)
        self.assertEqual(project_intel.main([
            "--project", str(root), "requirement", "ready",
            "--requirement-id", "REQ-TEST-1", "--resolution", "需求和验收标准确认",
        ]), 0)
        self.assertEqual(project_intel.main([
            "--project", str(root), "requirement", "begin",
            "--requirement-id", "REQ-TEST-1",
        ]), 0)
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
                    expect_failure="expected assertion failure",
                )

            self.assertEqual(code, 0)
            self.assertEqual(result["entry"]["status"], "passed")
            self.assertEqual(result["entry"]["phase"], "red")
            self.assertIn("expected assertion failure", (root / ".project-intel/reports/test-evidence.md").read_text(encoding="utf-8"))

    def test_requirement_red_observation_does_not_verify_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.initialized_requirement_project(root)
            source.write_text("def answer():\n    return 43\n", encoding="utf-8")
            with patch.object(project_intel, "run_shell", return_value=(1, "expected assertion failure", "")):
                code, result = project_intel.run_project_test(
                    root,
                    None,
                    "red",
                    commands=["python3 -m pytest tests/test_retry.py"],
                    files=["src/service.py"],
                    expect_failure="expected assertion failure",
                    requirement_id="REQ-TEST-1",
                    test_kind="unit",
                    report_action="generate",
                    acceptance_ids=["AC-01", "AC-02"],
                )

            self.assertEqual(code, 0)
            manifest = result["requirement"]
            self.assertEqual(manifest["state"], "implementing")
            self.assertEqual(manifest["testEvidence"][-1]["result"], "failed")

    def test_requirement_manual_phase_cannot_be_registered_as_service_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.initialized_requirement_project(root)
            source.write_text("def answer():\n    return 43\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                project_intel.run_project_test(
                    root,
                    None,
                    "manual",
                    files=["src/service.py"],
                    manual_evidence="打开页面，输入边界值，观察到错误提示和日志均符合预期。",
                    requirement_id="REQ-TEST-1",
                    test_kind="service",
                    report_action="generate",
                    acceptance_ids=["AC-01", "AC-02"],
                )
            self.assertEqual(raised.exception.code, 2)

    def test_red_phase_rejects_command_errors_and_unexpected_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            for exit_code in (0, 2, 3, 4, 5, 124, 127):
                with self.subTest(exit_code=exit_code), patch.object(project_intel, "run_shell", return_value=(exit_code, "", "error")):
                    code, result = project_intel.run_project_test(
                        root,
                        "修复缓存回归问题",
                        "red",
                        commands=["bad-test-command"],
                        files=["src/service.py"],
                        expect_failure="error",
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

    def test_finish_rejects_explicit_scope_that_omits_actual_git_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.initialized_project(root)
            second = root / "src" / "other.py"
            second.write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
            subprocess.run(["git", "add", "src"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
            first.write_text("def answer():\n    return 43\n", encoding="utf-8")
            second.write_text("value = 2\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                project_intel.finish_project(root, "验证完整变更范围", files=["src/service.py"])
            self.assertEqual(raised.exception.code, 2)

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
                    expect_failure="expected assertion failure",
                )

            status = project_intel.testing_module.evaluate_test_evidence(
                root,
                "修复缓存回归问题",
                ["src/service.py"],
            )
            self.assertFalse(status["redObserved"])

    def test_empty_file_scope_requires_explicit_project_wide(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            with self.assertRaises(SystemExit) as raised:
                project_intel.run_project_test(
                    root,
                    "运行项目级回归测试",
                    "verify",
                    commands=["python3 -m unittest"],
                    files=[],
                )
            self.assertEqual(raised.exception.code, 2)

            with patch.object(project_intel, "run_shell", return_value=(0, "92 passed", "")):
                code, result = project_intel.run_project_test(
                    root,
                    "运行项目级回归测试",
                    "verify",
                    commands=["python3 -m unittest"],
                    files=[],
                    project_wide=True,
                )
            self.assertEqual(code, 0)
            self.assertTrue(result["entry"]["projectWide"])

    def test_legacy_cli_requires_explicit_legacy_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            with self.assertRaises(SystemExit) as raised:
                project_intel.main([
                    "--project", str(root), "test",
                    "--task", "运行兼容测试",
                    "--phase", "manual",
                    "--manual-evidence", "读取页面并确认兼容模式证据写入正常。",
                    "--files", "src/service.py",
                ])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(project_intel.main([
                "--project", str(root), "test",
                "--legacy",
                "--task", "运行兼容测试",
                "--phase", "manual",
                "--manual-evidence", "读取页面并确认兼容模式证据写入正常。",
                "--files", "src/service.py",
            ]), 0)

    def test_persisted_test_evidence_redacts_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            command = "curl -H 'Authorization: Bearer super-secret' --token abc123 https://example.test"
            with patch.object(
                project_intel,
                "run_shell",
                return_value=(0, "access_token=server-token password=hunter2", "Cookie: session=private"),
            ):
                code, _ = project_intel.run_project_test(
                    root,
                    "验证敏感信息脱敏",
                    "verify",
                    commands=[command],
                    files=["src/service.py"],
                )
            self.assertEqual(code, 0)
            body = (root / ".project-intel/reports/test-evidence.json").read_text(encoding="utf-8")
            for secret in ("super-secret", "abc123", "server-token", "hunter2", "session=private"):
                self.assertNotIn(secret, body)
            self.assertIn("[REDACTED]", body)

    def test_redaction_covers_json_quotes_cookie_and_environment_assignments(self):
        raw = (
            'Authorization: Bearer "quoted auth"\n'
            'Cookie: session=abc; refresh=def\n'
            '{"access_token": "json-secret", "password": "space secret"}\n'
            'OPENAI_API_KEY="environment secret" --token "cli secret"\n'
            'AWS_SECRET_ACCESS_KEY=aws-secret-value\n'
            'postgresql://db_user:db_password@localhost:5432/app'
        )
        safe = project_intel.testing_module.sanitize_text(raw)
        for secret in (
            "quoted auth",
            "session=abc",
            "json-secret",
            "space secret",
            "environment secret",
            "cli secret",
            "aws-secret-value",
            "db_user",
            "db_password",
        ):
            self.assertNotIn(secret, safe)
        self.assertGreaterEqual(safe.count("[REDACTED]"), 9)


if __name__ == "__main__":
    unittest.main()
