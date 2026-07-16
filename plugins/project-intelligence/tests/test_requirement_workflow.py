import importlib.util
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from project_intel_lib import requirements


MODULE_PATH = SCRIPTS / "project_intel.py"
SPEC = importlib.util.spec_from_file_location("project_intel_requirement_facade", MODULE_PATH)
project_intel = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(project_intel)


class RequirementWorkflowTests(unittest.TestCase):
    def initialized_project(self, root: Path) -> None:
        (root / ".project-intel").mkdir(parents=True)
        (root / ".project-intel" / "manifest.json").write_text("{}\n", encoding="utf-8")

    def git_project(self, root: Path) -> Path:
        self.initialized_project(root)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True)
        source.write_text("def answer():\n    return 41\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/service.py"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
        return source

    def create_documented_requirement(self, root: Path, *, external_api: bool = False) -> dict:
        manifest = requirements.create_requirement(
            root,
            "REQ-1001",
            "增强需求级交付流程",
            track="complex",
            external_api=external_api,
            external_api_source="user",
        )
        self.assertEqual(manifest["state"], "draft")
        requirements.generate_artifact(root, "REQ-1001", "requirement-design")
        manifest = requirements.load_requirement(root, "REQ-1001")
        self.assertEqual(manifest["state"], "documented")
        self.assertEqual([item["id"] for item in manifest["acceptanceCriteria"]], ["AC-01", "AC-02"])
        return manifest

    def test_full_requirement_state_machine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "需求范围和验收标准已经确认")
            requirements.begin_requirement(root, "REQ-1001")

            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            manifest = requirements.record_test_result(
                root,
                "REQ-1001",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
                snapshot=snapshot,
                command="python -m unittest",
            )
            self.assertEqual(manifest["state"], "verified")

            manifest = requirements.record_review(
                root,
                "REQ-1001",
                result="passed",
                summary="未发现阻塞交付的问题",
                findings=[],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            self.assertEqual(manifest["state"], "reviewed")
            requirements.generate_artifact(root, "REQ-1001", "closure")
            manifest = requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])
            self.assertEqual(manifest["state"], "finished")
            manifest = requirements.close_requirement(root, "REQ-1001", check_succeeded=True)
            self.assertEqual(manifest["state"], "closed")

    def test_external_api_requires_service_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root, external_api=True)
            requirements.ready_requirement(root, "REQ-1001", "对外接口影响已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)

            manifest = requirements.record_test_result(
                root,
                "REQ-1001",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            self.assertEqual(manifest["state"], "implementing")
            manifest = requirements.record_test_result(
                root,
                "REQ-1001",
                test_kind="service",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            self.assertEqual(manifest["state"], "verified")

    def test_later_action_blocks_readiness_until_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "需求档案")
            requirements.record_later(root, "REQ-1001", "requirement-design")
            with self.assertRaises(requirements.RequirementError):
                requirements.ready_requirement(root, "REQ-1001", "")
            with self.assertRaisesRegex(requirements.RequirementError, "documented"):
                requirements.ready_requirement(root, "REQ-1001", "不能自动解决稍后处理")
            requirements.generate_artifact(root, "REQ-1001", "requirement-design")
            manifest = requirements.ready_requirement(root, "REQ-1001", "已补齐并确认需求设计文档")
            self.assertEqual(manifest["state"], "ready")
            self.assertTrue(all(item.get("resolvedAt") for item in manifest["readiness"]["blockers"]))

    def test_artifact_path_must_be_nonempty_and_inside_repository(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "需求档案")
            empty = root / "empty.md"
            empty.write_text("", encoding="utf-8")
            external = Path(outside) / "external.md"
            external.write_text("external", encoding="utf-8")
            for value in ("https://example.com/doc", "../external.md", str(external), "empty.md"):
                with self.subTest(value=value), self.assertRaises(requirements.RequirementError):
                    requirements.register_artifact(root, "REQ-1001", "requirement-design", value)

    def test_reopen_invalidates_downstream_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            requirements.record_review(
                root, "REQ-1001", result="passed", summary="通过", findings=[],
                files=["src/service.py"], snapshot=snapshot,
            )
            manifest = requirements.reopen_requirement(root, "REQ-1001", "验收范围发生变化")
            self.assertEqual(manifest["state"], "documented")
            self.assertFalse(manifest["testEvidence"][-1]["valid"])
            self.assertFalse(manifest["reviewRounds"][-1]["valid"])

    def test_code_change_after_review_makes_finish_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            requirements.record_review(
                root, "REQ-1001", result="passed", summary="通过", findings=[],
                files=["src/service.py"], snapshot=snapshot,
            )
            requirements.generate_artifact(root, "REQ-1001", "closure")
            source.write_text("def answer():\n    return 43\n", encoding="utf-8")
            with self.assertRaises(requirements.RequirementError):
                requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])

    def test_clean_commit_change_after_review_makes_finish_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            requirements.record_review(
                root, "REQ-1001", result="passed", summary="通过", findings=[],
                files=["src/service.py"], snapshot=snapshot,
            )
            requirements.generate_artifact(root, "REQ-1001", "closure")
            subprocess.run(["git", "add", "src/service.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "change after evidence"], cwd=root, check=True)
            with self.assertRaisesRegex(requirements.RequirementError, "测试证据"):
                requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])

    def test_git_unavailable_fails_closed_for_requirement_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            (root / "src").mkdir()
            (root / "src" / "service.py").write_text("value = 1\n", encoding="utf-8")
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            with self.assertRaisesRegex(requirements.RequirementError, "Git"):
                requirements.record_test_result(
                    root,
                    "REQ-1001",
                    test_kind="unit",
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    files=["src/service.py"],
                )

    def test_finish_rejects_missing_test_report_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            requirements.record_review(
                root, "REQ-1001", result="passed", summary="通过", findings=[],
                files=["src/service.py"], snapshot=snapshot,
            )
            requirements.generate_artifact(root, "REQ-1001", "closure")
            with self.assertRaisesRegex(requirements.RequirementError, "测试报告"):
                requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])

    def test_manifest_revisions_increase_and_json_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            first = requirements.create_requirement(root, "REQ-1001", "需求档案")
            second = requirements.generate_artifact(root, "REQ-1001", "requirement-design")
            self.assertGreater(second["revision"], first["revision"])
            path = root / ".project-intel" / "requirements" / "by-id" / "REQ-1001" / "manifest.json"
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["revision"], second["revision"])

    def test_local_id_format_and_parallel_updates_do_not_lose_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            generated = requirements.generate_requirement_id()
            self.assertRegex(generated, r"^LOCAL-\d{8}-\d{6}$")
            requirements.create_requirement(root, "REQ-LOCK-1", "并发证据登记")
            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(lambda _: requirements.record_later(root, "REQ-LOCK-1", "requirement-design"), range(8)))
            manifest = requirements.load_requirement(root, "REQ-LOCK-1")
            self.assertEqual(len(manifest["readiness"]["blockers"]), 8)
            self.assertEqual(manifest["revision"], 9)

    def test_review_with_unresolved_important_finding_does_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            manifest = requirements.record_review(
                root,
                "REQ-1001",
                result="passed",
                summary="仍有重要问题",
                findings=[{"severity": "important", "text": "缺少兼容处理", "resolved": False}],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            self.assertEqual(manifest["state"], "verified")
            self.assertEqual(manifest["reviewRounds"][-1]["result"], "failed")

    def test_new_passed_review_does_not_auto_resolve_prior_blocking_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            requirements.record_review(
                root, "REQ-1001", result="failed", summary="发现重要问题",
                findings=[{"severity": "important", "text": "缺少兼容处理", "resolved": False}],
                files=["src/service.py"], snapshot=snapshot,
            )
            manifest = requirements.record_review(
                root, "REQ-1001", result="passed", summary="新一轮未发现新增问题",
                findings=[], files=["src/service.py"], snapshot=snapshot,
            )
            self.assertEqual(manifest["state"], "reviewed")
            unresolved = [
                finding for review in manifest["reviewRounds"] for finding in review.get("findings", [])
                if finding["severity"] == "important" and not finding.get("resolved")
            ]
            self.assertTrue(unresolved)
            requirements.generate_artifact(root, "REQ-1001", "closure")
            with self.assertRaisesRegex(requirements.RequirementError, "评审问题"):
                requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])

    def test_scope_selection_cannot_omit_untracked_or_modified_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            extra = root / "src" / "extra.py"
            extra.write_text("value = 1\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            with self.assertRaises(requirements.RequirementError) as raised:
                requirements.validate_scope_selection(root, ["src/service.py"], snapshot)
            self.assertIn("src/extra.py", str(raised.exception))

    def test_manual_exception_requires_allowed_category_and_evidence_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            base = {
                "approved": True,
                "reason": "必须在真机上观察交互反馈",
                "steps": "打开页面并触发按钮状态变化",
                "input": "空值和正常值",
                "observation": "错误提示和成功状态均符合预期",
                "evidencePath": "evidence/device.log",
            }
            with self.assertRaises(requirements.RequirementError):
                requirements.record_test_result(
                    root, "REQ-1001", test_kind="manual", result="passed",
                    acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
                    manual={**base, "category": "business"},
                )
            evidence = root / "evidence" / "device.log"
            evidence.parent.mkdir()
            evidence.write_text("device verification passed\n", encoding="utf-8")
            manifest = requirements.record_test_result(
                root, "REQ-1001", test_kind="manual", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
                manual={**base, "category": "device"},
            )
            self.assertEqual(manifest["state"], "verified")

    def test_registered_test_report_requires_explicit_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            report = root / "reports" / "unit.md"
            report.parent.mkdir()
            report.write_text("# Unit test\n\nPassed.\n", encoding="utf-8")
            with self.assertRaises(requirements.RequirementError):
                requirements.register_artifact(
                    root, "REQ-1001", "unit-test", "reports/unit.md",
                    result="passed", acceptance_ids=["AC-01", "AC-02"],
                )
            manifest = requirements.register_artifact(
                root, "REQ-1001", "unit-test", "reports/unit.md",
                result="passed", acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"],
            )
            self.assertEqual(manifest["state"], "verified")
            self.assertEqual(manifest["testEvidence"][-1]["files"], ["src/service.py"])

    def test_business_source_file_cannot_be_registered_as_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "源码文件"):
                requirements.register_artifact(
                    root, "REQ-1001", "unit-test", "src/service.py",
                    result="passed", acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"],
                )

    def test_changed_business_json_cannot_be_registered_as_test_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            config = root / "src" / "config.json"
            config.write_text('{"mode":"old"}\n', encoding="utf-8")
            subprocess.run(["git", "add", "src/config.json"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "add config"], cwd=root, check=True)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            config.write_text('{"mode":"new"}\n', encoding="utf-8")

            with self.assertRaisesRegex(requirements.RequirementError, "测试报告路径"):
                requirements.register_artifact(
                    root,
                    "REQ-1001",
                    "unit-test",
                    "src/config.json",
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    files=["src/config.json"],
                )

            fake_report = root / "reports" / "config.json"
            fake_report.parent.mkdir()
            fake_report.write_text('{"mode":"production"}\n', encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "测试报告"):
                requirements.register_artifact(
                    root,
                    "REQ-1001",
                    "unit-test",
                    "reports/config.json",
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    project_wide=True,
                )

    def test_close_rejects_source_changes_after_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            requirements.record_review(
                root, "REQ-1001", result="passed", summary="通过", findings=[],
                files=["src/service.py"], snapshot=snapshot,
            )
            requirements.generate_artifact(root, "REQ-1001", "closure")
            requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])
            (root / "src" / "late.py").write_text("late = True\n", encoding="utf-8")

            with self.assertRaisesRegex(requirements.RequirementError, "finish 后"):
                requirements.close_requirement(root, "REQ-1001", check_succeeded=True)
            with patch.object(project_intel, "init_project") as refresh:
                self.assertEqual(project_intel.maintain_project(
                    root,
                    None,
                    False,
                    files=["src/service.py"],
                    requirement_id="REQ-1001",
                ), 1)
            refresh.assert_not_called()

    def test_review_text_is_redacted_and_findings_can_be_resolved_by_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            snapshot = requirements.capture_scope_snapshot(root)
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            requirements.record_test_result(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], files=["src/service.py"], snapshot=snapshot,
            )
            manifest = requirements.record_review(
                root,
                "REQ-1001",
                result="failed",
                summary="Authorization: Bearer review-secret",
                findings=[{"severity": "important", "text": "password=hunter2", "resolved": False}],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            finding_id = manifest["reviewRounds"][-1]["findings"][0]["id"]
            body = requirements.manifest_path(root, "REQ-1001").read_text(encoding="utf-8")
            self.assertNotIn("review-secret", body)
            self.assertNotIn("hunter2", body)

            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "resolve-finding",
                "--requirement-id", "REQ-1001",
                "--finding-id", finding_id,
                "--resolved-by", "reviewer-token=private-value",
                "--resolution", "已补充兼容处理，api_key=private-key",
            ]), 0)
            manifest = requirements.load_requirement(root, "REQ-1001")
            finding = manifest["reviewRounds"][-1]["findings"][0]
            self.assertTrue(finding["resolved"])
            self.assertEqual(finding["resolvedBy"], "reviewer-token=[REDACTED]")
            self.assertNotIn("private-key", json.dumps(finding, ensure_ascii=False))
            manifest = requirements.record_review(
                root, "REQ-1001", result="passed", summary="修复已复核", findings=[],
                files=["src/service.py"], snapshot=snapshot,
            )
            self.assertEqual(manifest["state"], "reviewed")
            requirements.generate_artifact(root, "REQ-1001", "closure")
            self.assertEqual(
                requirements.finish_requirement(root, "REQ-1001", files=["src/service.py"])["state"],
                "finished",
            )

    def test_generated_test_report_remains_a_living_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="failed",
                acceptance_ids=["AC-01"], command="python -m unittest", details="expected failure",
            )
            requirements.generate_artifact(root, "REQ-1001", "test")
            requirements.append_test_report_execution(
                root, "REQ-1001", test_kind="unit", result="passed",
                acceptance_ids=["AC-01", "AC-02"], command="python -m unittest", details="2 passed",
            )
            body = (requirements.requirement_dir(root, "REQ-1001") / "test-report.md").read_text(encoding="utf-8")
            self.assertIn("expected failure", body)
            self.assertIn("2 passed", body)

    def test_cli_full_requirement_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            project_intel.init_project(root, with_graph=False)
            self.assertEqual(
                project_intel.main([
                    "--project", str(root), "intake",
                    "--requirement-id", "REQ-CLI-1",
                    "--requirement-name", "需求级命令行闭环",
                    "--external-api", "no",
                    "--track", "complex",
                ]),
                0,
            )
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "generate",
                "--requirement-id", "REQ-CLI-1", "--type", "requirement-design",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "ready",
                "--requirement-id", "REQ-CLI-1", "--resolution", "需求和验收标准已经确认",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "begin", "--requirement-id", "REQ-CLI-1",
            ]), 0)

            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            self.assertEqual(project_intel.main([
                "--project", str(root), "test",
                "--requirement-id", "REQ-CLI-1",
                "--test-kind", "unit",
                "--report-action", "generate",
                "--phase", "green",
                "--command", f'"{sys.executable}" -c "assert 42 == 42"',
                "--files", "src/service.py",
                "--acceptance", "AC-01,AC-02",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "review",
                "--requirement-id", "REQ-CLI-1",
                "--result", "passed",
                "--summary", "未发现严重或重要问题",
                "--files", "src/service.py",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "generate",
                "--requirement-id", "REQ-CLI-1", "--type", "closure",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "finish",
                "--requirement-id", "REQ-CLI-1", "--files", "src/service.py",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "maintain",
                "--requirement-id", "REQ-CLI-1", "--files", "src/service.py",
            ]), 0)
            self.assertEqual(requirements.load_requirement(root, "REQ-CLI-1")["state"], "closed")
            with self.assertRaises(SystemExit):
                project_intel.main([
                    "--project", str(root), "requirement", "generate",
                    "--requirement-id", "REQ-CLI-1", "--type", "closure",
                ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = project_intel.main([
                    "--json", "--project", str(root), "requirement", "status", "--requirement-id", "REQ-CLI-1",
                ])
            self.assertEqual(code, 0)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["result"]["state"], "closed")

    def test_json_gate_failure_returns_machine_readable_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-JSON-1", "JSON 门禁")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = project_intel.main([
                    "--json", "--project", str(root), "requirement", "ready",
                    "--requirement-id", "REQ-JSON-1", "--resolution", "尝试跳过文档",
                ])
            self.assertEqual(code, 2)
            payload = json.loads(output.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"]["code"], "USAGE_ERROR")
            self.assertEqual(payload["status"], "failed")
            self.assertIn("documented", payload["result"]["error"])

    def test_duplicate_intake_conflict_requires_amend(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "需求档案", external_api=False)
            with self.assertRaisesRegex(requirements.RequirementError, "amend"):
                requirements.create_requirement(root, "REQ-1001", "需求档案", external_api=True)
            manifest = requirements.amend_requirement(
                root,
                "REQ-1001",
                external_api=True,
                reason="接口影响确认结果修正",
            )
            self.assertTrue(manifest["externalApiImpact"]["value"])


if __name__ == "__main__":
    unittest.main()
