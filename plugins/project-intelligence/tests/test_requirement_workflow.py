import importlib.util
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from design_fixtures import requirement_design, requirement_document


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

    def write_requirement_design(self, root: Path, requirement_id: str = "REQ-1001", name: str = "增强需求级交付流程") -> str:
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        existing = source.read_text(encoding="utf-8") if source.is_file() else ""
        if not re.search(r"(?m)^def\s+answer\s*\(", existing):
            source.write_text(existing + "\n\ndef answer():\n    return 41\n", encoding="utf-8")
        path = requirements.requirement_dir(root, requirement_id) / "design.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(requirement_design(requirement_id, name), encoding="utf-8")
        return path.relative_to(root).as_posix()

    def write_requirement_document(self, root: Path, requirement_id: str = "REQ-1001", name: str = "增强需求级交付流程") -> str:
        path = requirements.requirement_dir(root, requirement_id) / "requirement.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        manifest = requirements.load_requirement(root, requirement_id)
        body = requirement_document(requirement_id, name, kind=manifest.get("ticketKind", "requirement"))
        criteria = "\n".join(
            f"- {item['id']}：{item['description']}"
            for item in manifest.get("acceptanceCriteria", [])
        ) or "- 尚未登记验收标准。"
        body = re.sub(
            r"(?s)(## 验收标准\n\n).*?(\n\n## 外部接口影响)",
            rf"\g<1>{criteria}\g<2>",
            body,
            count=1,
        )
        external_text = (
            "影响对外接口；必须使用服务测试验证请求和响应契约。"
            if manifest.get("externalApiImpact", {}).get("value")
            else "不影响对外接口；本测试需求仅调整内部服务行为。"
        )
        body = re.sub(
            r"(?s)(## 外部接口影响\n\n).*?(\n\n## 待确认事项)",
            rf"\g<1>{external_text}\g<2>",
            body,
            count=1,
        )
        path.write_text(body, encoding="utf-8")
        return path.relative_to(root).as_posix()

    def create_documented_requirement(self, root: Path, *, external_api: bool = False) -> dict:
        manifest = requirements.create_requirement(
            root,
            "REQ-1001",
            "增强需求级交付流程",
            track="complex",
            external_api=external_api,
            external_api_source="user",
            ticket_kind="requirement",
        )
        self.assertEqual(manifest["state"], "draft")
        requirements.set_acceptance_criteria(root, "REQ-1001", [
            {"id": "AC-01", "description": "实现需求约定的目标行为。"},
            {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
        ])
        requirements.set_test_contract(
            root,
            "REQ-1001",
            kind="both" if external_api else "unit",
            report_action="generate",
            acceptance_ids=["AC-01", "AC-02"],
        )
        requirement_path = self.write_requirement_document(root)
        requirements.register_artifact(root, "REQ-1001", "requirement", requirement_path)
        design_path = self.write_requirement_design(root)
        requirements.register_artifact(root, "REQ-1001", "design", design_path)
        manifest = requirements.load_requirement(root, "REQ-1001")
        self.assertEqual(manifest["state"], "designed")
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
            with self.assertRaisesRegex(requirements.RequirementError, "designed"):
                requirements.ready_requirement(root, "REQ-1001", "不能自动解决稍后处理")
            requirements.set_acceptance_criteria(root, "REQ-1001", [
                {"id": "AC-01", "description": "需求档案可以进入实现。"},
            ])
            requirement_path = self.write_requirement_document(root, name="需求档案")
            requirements.register_artifact(root, "REQ-1001", "requirement", requirement_path)
            design_path = self.write_requirement_design(root, name="需求档案")
            with self.assertRaisesRegex(requirements.RequirementError, "已选择 later"):
                requirements.register_artifact(root, "REQ-1001", "design", design_path)
            requirements.amend_requirement(
                root,
                "REQ-1001",
                design_action="register",
                design_path=design_path,
                reason="用户决定补齐设计文档",
            )
            requirements.register_artifact(root, "REQ-1001", "design", design_path)
            requirements.set_test_contract(
                root, "REQ-1001", kind="unit", report_action="generate", acceptance_ids=["AC-01"]
            )
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
            self.assertEqual(manifest["state"], "designed")
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
            second = requirements.generate_artifact(root, "REQ-1001", "requirement")
            self.assertGreater(second["revision"], first["revision"])
            self.assertEqual(second["state"], "draft")
            path = root / ".project-intel" / "requirements" / "REQ-1001" / "manifest.json"
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["revision"], second["revision"])

    def test_generated_design_scaffold_cannot_be_reregistered_to_bypass_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "需求档案", ticket_kind="requirement")
            requirements.set_acceptance_criteria(root, "REQ-1001", [
                {"id": "AC-01", "description": "实现需求约定的目标行为。"},
                {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
            ])
            requirement_path = self.write_requirement_document(root, name="需求档案")
            requirements.register_artifact(root, "REQ-1001", "requirement", requirement_path)
            manifest = requirements.generate_artifact(root, "REQ-1001", "requirement-design")
            artifact = manifest["artifacts"][-1]
            self.assertEqual(artifact["status"], "draft")
            with self.assertRaisesRegex(requirements.RequirementError, "真实的仓库相对路径"):
                requirements.register_artifact(root, "REQ-1001", "requirement-design", artifact["path"])

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
            requirements.set_test_contract(
                root, "REQ-1001", kind="manual", report_action="generate", acceptance_ids=["AC-01", "AC-02"]
            )
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
            report.write_text("# Unit test\n\nResult: passed\n1 test passed\n", encoding="utf-8")
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

    def test_failed_registered_test_report_cannot_be_declared_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            report = root / ".project-intel" / "reports" / "unit-report.md"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("# Unit Test Report\n\nResult: FAILED\n3 tests failed.\n", encoding="utf-8")

            with self.assertRaisesRegex(requirements.RequirementError, "实际结果"):
                requirements.register_artifact(
                    root,
                    "REQ-1001",
                    "unit-test",
                    report.relative_to(root).as_posix(),
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    files=["src/service.py"],
                )

    def test_failed_structured_test_reports_cannot_be_declared_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_documented_requirement(root)
            requirements.ready_requirement(root, "REQ-1001", "已确认")
            requirements.begin_requirement(root, "REQ-1001")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            reports = root / "reports"
            reports.mkdir()
            fixtures = {
                "unit-results.json": '{"tests": 3, "failures": 1, "status": "failed"}\n',
                "unit-results.xml": '<testsuite tests="3" failures="1"><testcase><failure /></testcase></testsuite>\n',
            }

            for filename, content in fixtures.items():
                with self.subTest(filename=filename):
                    report = reports / filename
                    report.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(requirements.RequirementError, "实际结果"):
                        requirements.register_artifact(
                            root,
                            "REQ-1001",
                            "unit-test",
                            report.relative_to(root).as_posix(),
                            result="passed",
                            acceptance_ids=["AC-01", "AC-02"],
                            files=["src/service.py"],
                        )

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

    def test_registered_closure_requires_complete_structure(self):
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
            closure = requirements.requirement_dir(root, "REQ-1001") / "closure-summary.md"
            closure.write_text("x\n", encoding="utf-8")

            with self.assertRaisesRegex(requirements.RequirementError, "收口总结"):
                requirements.register_artifact(
                    root,
                    "REQ-1001",
                    "closure",
                    closure.relative_to(root).as_posix(),
                )

    def test_design_artifact_outside_project_intel_does_not_require_test_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            requirements.create_requirement(
                root,
                "REQ-DOCS",
                "真实设计目录流程",
                track="standard",
                external_api=False,
                ticket_kind="requirement",
            )
            requirements.set_acceptance_criteria(
                root,
                "REQ-DOCS",
                [{"id": "AC-01", "description": "实现目标行为。"}],
            )
            requirements.set_test_contract(
                root, "REQ-DOCS", kind="unit", report_action="generate", acceptance_ids=["AC-01"]
            )
            requirement_path = self.write_requirement_document(root, "REQ-DOCS", "真实设计目录流程")
            requirements.register_artifact(root, "REQ-DOCS", "requirement", requirement_path)
            design = root / "docs" / "requirements" / "REQ-DOCS_真实设计目录流程_设计文档.md"
            design.parent.mkdir(parents=True)
            design.write_text(requirement_design("REQ-DOCS", "真实设计目录流程"), encoding="utf-8")
            requirements.register_artifact(
                root,
                "REQ-DOCS",
                "requirement-design",
                design.relative_to(root).as_posix(),
            )
            requirements.ready_requirement(root, "REQ-DOCS", "已确认")
            requirements.begin_requirement(root, "REQ-DOCS")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            requirements.generate_artifact(root, "REQ-DOCS", "test")
            requirements.append_test_report_execution(
                root, "REQ-DOCS", test_kind="unit", result="passed",
                acceptance_ids=["AC-01"], command="python -m unittest", details="1 passed",
            )
            manifest = requirements.record_test_result(
                root,
                "REQ-DOCS",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01"],
                files=["src/service.py"],
            )
            self.assertEqual(manifest["state"], "verified")
            snapshot = requirements.capture_requirement_scope(root, manifest)
            self.assertEqual(snapshot["evidenceFiles"], ["src/service.py"])
            self.assertEqual(snapshot["artifactFiles"], [design.relative_to(root).as_posix()])
            requirements.record_review(
                root,
                "REQ-DOCS",
                result="passed",
                summary="通过",
                findings=[],
                files=snapshot["files"],
            )
            requirements.generate_artifact(root, "REQ-DOCS", "closure")
            finished = requirements.finish_requirement(root, "REQ-DOCS", files=snapshot["files"])
            self.assertEqual(finished["state"], "finished")

    def test_registered_closure_after_review_does_not_expire_code_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            requirements.create_requirement(
                root,
                "REQ-CLOSURE",
                "登记外部收口总结",
                track="standard",
                external_api=False,
                ticket_kind="requirement",
            )
            requirements.set_acceptance_criteria(
                root, "REQ-CLOSURE", [{"id": "AC-01", "description": "实现目标行为。"}]
            )
            requirements.set_test_contract(
                root, "REQ-CLOSURE", kind="unit", report_action="generate", acceptance_ids=["AC-01"]
            )
            requirement_path = self.write_requirement_document(root, "REQ-CLOSURE", "登记外部收口总结")
            requirements.register_artifact(root, "REQ-CLOSURE", "requirement", requirement_path)
            design = root / "docs" / "requirements" / "REQ-CLOSURE_登记外部收口总结_设计文档.md"
            design.parent.mkdir(parents=True)
            design.write_text(requirement_design("REQ-CLOSURE", "登记外部收口总结"), encoding="utf-8")
            requirements.register_artifact(
                root, "REQ-CLOSURE", "requirement-design", design.relative_to(root).as_posix()
            )
            requirements.ready_requirement(root, "REQ-CLOSURE", "已确认")
            requirements.begin_requirement(root, "REQ-CLOSURE")
            source.write_text("def answer():\n    return 42\n", encoding="utf-8")
            requirements.generate_artifact(root, "REQ-CLOSURE", "test")
            requirements.append_test_report_execution(
                root, "REQ-CLOSURE", test_kind="unit", result="passed",
                acceptance_ids=["AC-01"], command="python -m unittest", details="1 passed",
            )
            requirements.record_test_result(
                root, "REQ-CLOSURE", test_kind="unit", result="passed",
                acceptance_ids=["AC-01"], files=["src/service.py"],
            )
            review_scope = requirements.capture_requirement_scope(
                root, requirements.load_requirement(root, "REQ-CLOSURE")
            )
            requirements.record_review(
                root, "REQ-CLOSURE", result="passed", summary="通过", findings=[],
                files=review_scope["files"],
            )
            generated = requirements.generate_artifact(root, "REQ-CLOSURE", "closure")
            generated_closure = root / generated["artifacts"][-1]["path"]
            external_closure = root / "docs" / "requirements" / "REQ-CLOSURE_收口总结.md"
            external_closure.write_text(generated_closure.read_text(encoding="utf-8"), encoding="utf-8")
            requirements.register_artifact(
                root, "REQ-CLOSURE", "closure", external_closure.relative_to(root).as_posix()
            )
            finish_scope = requirements.capture_requirement_scope(
                root, requirements.load_requirement(root, "REQ-CLOSURE")
            )

            self.assertIn(external_closure.relative_to(root).as_posix(), finish_scope["artifactFiles"])
            self.assertEqual(finish_scope["evidenceFiles"], ["src/service.py"])
            finished = requirements.finish_requirement(
                root, "REQ-CLOSURE", files=finish_scope["files"]
            )
            self.assertEqual(finished["state"], "finished")

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
                    "--ticket-kind", "requirement",
                    "--requirement-action", "generate",
                    "--design-action", "generate",
                    "--track", "complex",
                ]),
                0,
            )
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "acceptance", "set",
                "--requirement-id", "REQ-CLI-1",
                "--criterion", "AC-01:实现需求约定的目标行为",
                "--criterion", "AC-02:相关测试通过且无重要回归",
            ]), 0)
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "test-contract", "set",
                "--requirement-id", "REQ-CLI-1", "--kind", "unit",
                "--report-action", "generate", "--acceptance", "AC-01,AC-02",
            ]), 0)
            requirement_path = self.write_requirement_document(root, "REQ-CLI-1", "需求级命令行闭环")
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "add",
                "--requirement-id", "REQ-CLI-1", "--type", "requirement", "--path", requirement_path,
            ]), 0)
            design_path = self.write_requirement_design(root, "REQ-CLI-1", "需求级命令行闭环")
            self.assertEqual(project_intel.main([
                "--project", str(root), "requirement", "add",
                "--requirement-id", "REQ-CLI-1", "--type", "design", "--path", design_path,
            ]), 0)
            selections = requirements.status_payload(root, "REQ-CLI-1")["workflowSelections"]
            self.assertEqual(selections["requirement"]["status"], "completed")
            self.assertEqual(selections["design"]["status"], "completed")
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
                "--command", f'"{sys.executable}" -c "print(\'1 passed\')"',
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
            closed = requirements.load_requirement(root, "REQ-CLI-1")
            self.assertEqual(closed["state"], "closed")
            self.assertEqual(closed["finishResult"]["status"], "passed")
            self.assertEqual(closed["maintenanceResult"]["status"], "passed")
            self.assertTrue((root / ".project-intel" / "project-status.md").is_file())
            self.assertFalse((root / ".project-intel" / "reports").exists())
            self.assertFalse((root / ".project-intel" / "maintenance").exists())
            self.assertFalse((root / ".project-intel" / "requirements" / "files").exists())
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
            self.assertEqual(payload["result"]["ticketKind"], "requirement")
            self.assertTrue(payload["result"]["designValidation"]["ok"])

    def test_design_and_acceptance_are_independent_ready_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "增强需求级交付流程", ticket_kind="requirement")
            requirement_path = self.write_requirement_document(root)
            with self.assertRaisesRegex(requirements.RequirementError, "验收标准"):
                requirements.register_artifact(root, "REQ-1001", "requirement", requirement_path)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "增强需求级交付流程", ticket_kind="requirement")
            manifest = requirements.set_acceptance_criteria(root, "REQ-1001", [
                {"id": "AC-01", "description": "实现目标行为。"},
            ])
            self.assertEqual(manifest["state"], "draft")
            with self.assertRaisesRegex(requirements.RequirementError, "designed"):
                requirements.ready_requirement(root, "REQ-1001", "验收标准已确认")

    def test_numeric_ticket_id_is_canonicalized_by_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            bug = requirements.create_requirement(root, "1234", "返回值错误", ticket_kind="bug")
            requirement = requirements.create_requirement(root, "73822", "新增核验能力", ticket_kind="requirement")
            self.assertEqual(bug["requirementId"], "bug1234")
            self.assertEqual(requirement["requirementId"], "req73822")

    def test_material_amend_invalidates_registered_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_documented_requirement(root)
            manifest = requirements.amend_requirement(
                root,
                "REQ-1001",
                external_api=True,
                ticket_kind="bug",
                reason="单据类型和接口影响重新确认",
            )
            self.assertEqual(manifest["state"], "draft")
            self.assertEqual(manifest["ticketKind"], "bug")
            self.assertEqual(manifest["artifacts"][-1]["status"], "stale")
            with self.assertRaisesRegex(requirements.RequirementError, "designed"):
                requirements.ready_requirement(root, "REQ-1001", "尝试使用旧设计")

    def test_legacy_v1_design_remains_readable_until_reregistered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            self.create_documented_requirement(root)
            path = requirements.manifest_path(root, "REQ-1001")
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["schemaVersion"] = 1
            payload["state"] = "documented"
            payload.pop("ticketKind", None)
            payload["artifacts"][-1].pop("validation", None)
            payload["artifacts"][-1].pop("documentKind", None)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            status = requirements.status_payload(root, "REQ-1001")
            self.assertEqual(status["ticketKind"], "requirement")
            self.assertTrue(status["designValidation"]["ok"])
            self.assertTrue(status["designValidation"]["legacy"])

            requirements.ready_requirement(root, "REQ-1001", "旧生命周期继续执行")
            reopened = requirements.reopen_requirement(root, "REQ-1001", "重新确认设计")
            self.assertEqual(reopened["state"], "draft")
            self.assertEqual(reopened["artifacts"][-1]["status"], "stale")
            self.assertFalse(requirements.status_payload(root, "REQ-1001")["designValidation"]["ok"])

    def test_amend_requires_legacy_design_to_be_reregistered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            self.create_documented_requirement(root)
            path = requirements.manifest_path(root, "REQ-1001")
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["schemaVersion"] = 1
            payload["state"] = "documented"
            payload["artifacts"] = [item for item in payload["artifacts"] if item.get("type") != "requirement"]
            payload["artifacts"][-1].pop("validation", None)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            amended = requirements.amend_requirement(root, "REQ-1001", track="standard", reason="调整任务轨道")
            self.assertEqual(amended["state"], "draft")
            self.assertEqual(amended["artifacts"][-1]["status"], "stale")

    def test_acceptance_set_rejects_invalid_or_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.initialized_project(root)
            requirements.create_requirement(root, "REQ-1001", "需求档案")
            with self.assertRaisesRegex(requirements.RequirementError, "AC-01"):
                requirements.set_acceptance_criteria(root, "REQ-1001", [{"id": "AC-1", "description": "错误编号"}])
            with self.assertRaisesRegex(requirements.RequirementError, "重复"):
                requirements.set_acceptance_criteria(root, "REQ-1001", [
                    {"id": "AC-01", "description": "第一项"},
                    {"id": "AC-01", "description": "重复项"},
                ])

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
            self.assertIn("designed", payload["result"]["error"])

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

    def test_intake_document_actions_persist_across_status_and_validate_paths(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            self.git_project(root)
            project_intel.init_project(root, with_graph=False)
            tickets = root / "tickets"
            tickets.mkdir()
            requirement_source = tickets / "REQ-ACTION-requirement.md"
            design_source = tickets / "REQ-ACTION-design.md"
            requirement_source.write_text("# existing requirement\n", encoding="utf-8")
            design_source.write_text("# existing design\n", encoding="utf-8")

            self.assertEqual(project_intel.main([
                "--project", str(root), "intake",
                "--requirement-id", "REQ-ACTION",
                "--requirement-name", "持久化文档动作",
                "--ticket-kind", "requirement",
                "--external-api", "no",
                "--requirement-action", "register",
                "--requirement-path", requirement_source.relative_to(root).as_posix(),
                "--design-action", "register",
                "--design-path", design_source.relative_to(root).as_posix(),
            ]), 0)
            status = requirements.status_payload(root, "REQ-ACTION")
            self.assertEqual(status["workflowSelections"]["requirement"]["action"], "register")
            self.assertEqual(status["workflowSelections"]["requirement"]["path"], "tickets/REQ-ACTION-requirement.md")
            self.assertEqual(status["workflowSelections"]["design"]["path"], "tickets/REQ-ACTION-design.md")

            alternate = tickets / "alternate-requirement.md"
            alternate.write_text("# alternate requirement\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "已选择登记路径"):
                requirements.register_artifact(
                    root,
                    "REQ-ACTION",
                    "requirement",
                    alternate.relative_to(root).as_posix(),
                )

            amended = requirements.amend_requirement(
                root,
                "REQ-ACTION",
                design_action="later",
                reason="设计文档暂缓处理",
            )
            self.assertEqual(amended["workflowSelections"]["design"]["action"], "later")
            deferred = requirements.record_later(root, "REQ-ACTION", "design")
            self.assertEqual(deferred["workflowSelections"]["design"]["status"], "deferred")

            outside = Path(outside_tmp) / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "越出|项目目录"):
                requirements.create_requirement(
                    root,
                    "REQ-OUTSIDE",
                    "拒绝仓库外动作路径",
                    external_api=False,
                    requirement_action="register",
                    requirement_path=str(outside),
                )
            invalid_suffix = tickets / "not-a-document.json"
            invalid_suffix.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "Markdown"):
                requirements.create_requirement(
                    root,
                    "REQ-BAD-SUFFIX",
                    "拒绝非 Markdown 文档动作",
                    external_api=False,
                    requirement_action="register",
                    requirement_path=invalid_suffix.relative_to(root).as_posix(),
                )

    def test_selected_later_action_cannot_generate_without_amend(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            requirements.create_requirement(
                root,
                "REQ-LATER-ACTION",
                "稍后处理需求文档",
                external_api=False,
                requirement_action="later",
                design_action="generate",
            )
            with self.assertRaisesRegex(requirements.RequirementError, "已选择 later"):
                requirements.generate_artifact(root, "REQ-LATER-ACTION", "requirement")
            requirements.record_later(root, "REQ-LATER-ACTION", "requirement")
            with self.assertRaisesRegex(requirements.RequirementError, "已选择 later"):
                requirements.generate_artifact(root, "REQ-LATER-ACTION", "requirement")

    def test_defer_requires_the_persisted_later_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            requirements.create_requirement(
                root,
                "REQ-GENERATE-ACTION",
                "生成需求文档",
                external_api=False,
                requirement_action="generate",
            )
            with self.assertRaisesRegex(requirements.RequirementError, "已选择 generate"):
                requirements.record_later(root, "REQ-GENERATE-ACTION", "requirement")


if __name__ == "__main__":
    unittest.main()
