from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from pathlib import Path

import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from design_fixtures import bug_design, requirement_design, requirement_document
from project_intel_lib import requirements


class RequirementHardeningTests(unittest.TestCase):
    def git_project(self, root: Path, *, preexisting_dirty: bool = False) -> Path:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True)
        source.write_text("def answer():\n    return 1\n", encoding="utf-8")
        report_source = root / "src" / "report.json"
        report_source.write_text('{"tests": 1, "failures": 0, "status": "passed"}\n', encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
        if preexisting_dirty:
            unrelated = root / "src" / "unrelated.py"
            unrelated.write_text("value = 'belongs to another task'\n", encoding="utf-8")
        return source

    def create_designed(self, root: Path, *, external_api: bool = False, identifier: str = "REQ-HARD") -> None:
        name = "需求门禁加固"
        requirements.create_requirement(
            root,
            identifier,
            name,
            external_api=external_api,
            ticket_kind="requirement",
            track="complex",
        )
        criteria = [
            {"id": "AC-01", "description": "实现需求约定的目标行为。"},
            {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
        ]
        requirements.set_acceptance_criteria(root, identifier, criteria)
        directory = requirements.requirement_dir(root, identifier)
        directory.mkdir(parents=True, exist_ok=True)
        requirement_body = requirement_document(identifier, name)
        if external_api:
            requirement_body = requirement_body.replace(
                "不影响对外接口；本测试需求仅调整内部服务行为。",
                "影响对外接口；必须使用服务测试验证请求和响应契约。",
            )
        requirement_path = directory / "requirement.md"
        requirement_path.write_text(requirement_body, encoding="utf-8")
        requirements.register_artifact(root, identifier, "requirement", requirement_path.relative_to(root).as_posix())
        design_path = directory / "design.md"
        design_path.write_text(requirement_design(identifier, name), encoding="utf-8")
        requirements.register_artifact(root, identifier, "design", design_path.relative_to(root).as_posix())

    def begin(self, root: Path, *, external_api: bool = False, identifier: str = "REQ-HARD") -> Path:
        source = root / "src" / "service.py"
        self.create_designed(root, external_api=external_api, identifier=identifier)
        requirements.ready_requirement(root, identifier, "范围与验收标准已经确认")
        requirements.begin_requirement(root, identifier)
        source.write_text("def answer():\n    return 2\n", encoding="utf-8")
        return source

    def add_generated_test(
        self,
        root: Path,
        *,
        identifier: str = "REQ-HARD",
        test_kind: str = "unit",
        files: tuple[str, ...] = ("src/service.py",),
    ) -> dict:
        requirements.generate_artifact(root, identifier, "test")
        requirements.append_test_report_execution(
            root,
            identifier,
            test_kind=test_kind,
            result="passed",
            acceptance_ids=["AC-01", "AC-02"],
            command="python -m unittest",
            details="2 passed",
        )
        return requirements.record_test_result(
            root,
            identifier,
            test_kind=test_kind,
            result="passed",
            acceptance_ids=["AC-01", "AC-02"],
            files=list(files),
            command="python -m unittest",
        )

    def finish(self, root: Path, *, identifier: str = "REQ-HARD") -> dict:
        snapshot = requirements.capture_requirement_scope(root, requirements.load_requirement(root, identifier))
        requirements.record_review(
            root,
            identifier,
            result="passed",
            summary="当前代码快照未发现阻塞问题",
            findings=[],
            files=["src/service.py"],
            snapshot=snapshot,
        )
        requirements.generate_artifact(root, identifier, "closure")
        return requirements.finish_requirement(root, identifier, files=["src/service.py"])

    def test_requirement_directory_symlink_cannot_write_outside_repository(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            (root / ".project-intel" / "requirements").mkdir(parents=True)
            outside = Path(outside_tmp)
            os.symlink(outside, root / ".project-intel" / "requirements" / "REQ-LINK")
            with self.assertRaisesRegex(requirements.RequirementError, "符号链接|项目目录"):
                requirements.create_requirement(root, "REQ-LINK", "符号链接越界")
            self.assertFalse((outside / "manifest.json").exists())

    def test_zero_test_reports_are_rejected_for_text_json_and_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            reports.mkdir()
            samples = {
                "zero.md": "# Unit test report\n\nResult: passed\n0 tests passed\n",
                "zero.json": '{"tests": 0, "failures": 0, "status": "passed"}\n',
                "zero.xml": '<testsuite tests="0" failures="0" status="passed"/>\n',
            }
            for name, body in samples.items():
                path = reports / name
                path.write_text(body, encoding="utf-8")
                with self.subTest(name=name), self.assertRaisesRegex(requirements.RequirementError, "0|执行|测试用例"):
                    requirements._validate_test_report_file(path, path.relative_to(root).as_posix(), expected_result="passed")

    def test_manual_report_cannot_be_registered_as_service_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root, external_api=True)
            report = root / "reports" / "manual-result.md"
            report.parent.mkdir()
            report.write_text("# Manual test report\n\nResult: passed\n1 test passed\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "manual|人工|类型"):
                requirements.register_artifact(
                    root,
                    "REQ-HARD",
                    "service-test",
                    report.relative_to(root).as_posix(),
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    files=["src/service.py"],
                )

    def test_explicit_both_contract_requires_unit_and_service_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_designed(root, external_api=True)
            requirements.set_test_contract(
                root,
                "REQ-HARD",
                kind="both",
                report_action="generate",
                acceptance_ids=["AC-01", "AC-02"],
            )
            requirements.ready_requirement(root, "REQ-HARD", "测试契约已确认")
            requirements.begin_requirement(root, "REQ-HARD")
            (root / "src" / "service.py").write_text("def answer():\n    return 2\n", encoding="utf-8")
            requirements.generate_artifact(root, "REQ-HARD", "test")
            requirements.append_test_report_execution(
                root,
                "REQ-HARD",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                command="python -m unittest",
                details="2 passed",
            )
            manifest = requirements.record_test_result(
                root,
                "REQ-HARD",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
                command="python -m unittest",
            )
            self.assertEqual(manifest["state"], "implementing")
            requirements.append_test_report_execution(
                root,
                "REQ-HARD",
                test_kind="service",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                command="python -m unittest tests.test_service",
                details="2 passed",
            )
            manifest = requirements.record_test_result(
                root,
                "REQ-HARD",
                test_kind="service",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
                command="python -m unittest tests.test_service",
            )
            self.assertEqual(manifest["state"], "verified")

    def test_existing_dirty_files_are_not_claimed_by_new_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root, preexisting_dirty=True)
            self.begin(root)
            snapshot = requirements.capture_requirement_scope(root, requirements.load_requirement(root, "REQ-HARD"))
            self.assertEqual(snapshot["evidenceFiles"], ["src/service.py"])
            requirements.validate_scope_selection(root, ["src/service.py"], snapshot)

    def test_committed_requirement_changes_remain_in_scope_after_worktree_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root, preexisting_dirty=True)
            self.begin(root)
            subprocess.run(
                ["git", "add", "src/service.py", "src/unrelated.py"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "commit", "-qm", "implement requirement"], cwd=root, check=True)

            snapshot = requirements.capture_requirement_scope(
                root, requirements.load_requirement(root, "REQ-HARD")
            )

            self.assertEqual(snapshot["evidenceFiles"], ["src/service.py"])
            self.assertEqual(snapshot["files"], ["src/service.py"])
            self.add_generated_test(root)
            finished = self.finish(root)
            self.assertEqual(
                [item["path"] for item in finished["changedFiles"]],
                ["src/service.py"],
            )

    def test_rejected_registration_does_not_overwrite_canonical_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_designed(root)
            requirements.ready_requirement(root, "REQ-HARD", "已确认")
            canonical = requirements.requirement_dir(root, "REQ-HARD") / "design.md"
            original = canonical.read_bytes()
            replacement = root / "docs" / "requirements" / "replacement.md"
            replacement.parent.mkdir(parents=True)
            replacement.write_text(requirement_design("REQ-HARD", "需求门禁加固") + "\n替换内容\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "reopen|下游"):
                requirements.register_artifact(root, "REQ-HARD", "design", replacement.relative_to(root).as_posix())
            self.assertEqual(canonical.read_bytes(), original)

    def test_document_copy_rolls_back_when_manifest_write_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            requirements.create_requirement(
                root, "REQ-HARD", "需求门禁加固", external_api=False, ticket_kind="requirement"
            )
            requirements.set_acceptance_criteria(root, "REQ-HARD", [
                {"id": "AC-01", "description": "实现需求约定的目标行为。"},
                {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
            ])
            external = root / "docs" / "requirements" / "REQ-HARD_需求门禁加固_需求文档.md"
            external.parent.mkdir(parents=True)
            external.write_text(requirement_document("REQ-HARD", "需求门禁加固"), encoding="utf-8")
            canonical = requirements.requirement_dir(root, "REQ-HARD") / "requirement.md"
            before = requirements.load_requirement(root, "REQ-HARD")
            with mock.patch.object(requirements, "_write_manifest", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(OSError, "disk full"):
                    requirements.register_artifact(
                        root, "REQ-HARD", "requirement", external.relative_to(root).as_posix()
                    )
            self.assertFalse(canonical.exists())
            after = requirements.load_requirement(root, "REQ-HARD")
            self.assertEqual(after["revision"], before["revision"])
            self.assertEqual(after["state"], "draft")

    def test_generate_does_not_replace_existing_requirement_without_explicit_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            requirements.create_requirement(
                root, "REQ-HARD", "需求门禁加固", external_api=False, ticket_kind="requirement"
            )
            requirements.set_acceptance_criteria(root, "REQ-HARD", [
                {"id": "AC-01", "description": "实现需求约定的目标行为。"},
                {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
            ])
            canonical = requirements.requirement_dir(root, "REQ-HARD") / "requirement.md"
            canonical.write_text(requirement_document("REQ-HARD", "需求门禁加固"), encoding="utf-8")
            requirements.register_artifact(root, "REQ-HARD", "requirement", canonical.relative_to(root).as_posix())
            original = canonical.read_bytes()
            with self.assertRaisesRegex(requirements.RequirementError, "已存在|replace|覆盖"):
                requirements.generate_artifact(root, "REQ-HARD", "requirement")
            self.assertEqual(canonical.read_bytes(), original)

    def test_plan_scaffold_must_be_completed_before_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_designed(root)
            manifest = requirements.generate_artifact(root, "REQ-HARD", "plan")
            plan = requirements.requirement_dir(root, "REQ-HARD") / "plan.md"
            self.assertEqual(manifest["artifacts"][-1]["status"], "draft")
            with self.assertRaisesRegex(requirements.RequirementError, "占位|计划验证"):
                requirements.register_artifact(root, "REQ-HARD", "plan", plan.relative_to(root).as_posix())
            plan.write_text(
                """# REQ-HARD 需求门禁加固 实施计划

## 实施范围

只修改需求门禁实现及其回归测试，不扩大业务范围。

## 输入基线

- `requirement.md`
- `design.md`

## 文件级变更

| 仓库相对路径 | 符号 | 修改目的 | 对应 AC |
| --- | --- | --- | --- |
| `src/service.py` | `answer` | 修复目标行为 | AC-01、AC-02 |

## 实施步骤

1. 调整 `answer` 的实现并保留兼容行为。
2. 增加目标单元测试和受影响回归测试。
3. 执行评审、收口和维护门禁。

## 测试与验收映射

| 验收标准 | 说明 | 测试类型 | 命令或步骤 |
| --- | --- | --- | --- |
| AC-01 | 实现需求约定的目标行为。 | unit | `python -m unittest` |
| AC-02 | 相关测试通过且无重要回归。 | unit | `python -m unittest` |

## 风险与回滚

- 风险：返回值变化可能影响调用方。
- 观测：检查单元测试和调用方回归结果。
- 回滚：恢复 `answer` 的上一版实现并重新执行测试。
""",
                encoding="utf-8",
            )
            manifest = requirements.register_artifact(
                root, "REQ-HARD", "plan", plan.relative_to(root).as_posix()
            )
            self.assertEqual(manifest["artifacts"][-1]["status"], "registered")
            plan.write_text(plan.read_text(encoding="utf-8") + "\n[待补充篡改]\n", encoding="utf-8")
            status = requirements.status_payload(root, "REQ-HARD")
            self.assertFalse(status["planValidation"]["ok"])
            with self.assertRaisesRegex(requirements.RequirementError, "plan.md|实施计划"):
                requirements.ready_requirement(root, "REQ-HARD", "计划已确认")

    def test_repeated_test_generate_preserves_executed_artifact_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root)
            requirements.generate_artifact(root, "REQ-HARD", "test")
            requirements.append_test_report_execution(
                root,
                "REQ-HARD",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                command="python -m unittest",
                details="2 passed",
                phase="green",
                executed_count=2,
            )
            before = requirements.load_requirement(root, "REQ-HARD")
            self.assertEqual(before["artifacts"][-1]["status"], "executed")
            requirements.generate_artifact(root, "REQ-HARD", "test")
            after = requirements.load_requirement(root, "REQ-HARD")
            self.assertEqual(after["artifacts"][-1]["status"], "executed")

    def test_external_api_requires_current_service_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.begin(root, external_api=True)
            self.add_generated_test(root, test_kind="service")
            source.write_text("def answer():\n    return 3\n", encoding="utf-8")
            manifest = self.add_generated_test(root, test_kind="unit")
            self.assertEqual(manifest["state"], "implementing")
            with self.assertRaisesRegex(requirements.RequirementError, "verified|测试"):
                requirements.record_review(
                    root,
                    "REQ-HARD",
                    result="passed",
                    summary="不应允许旧服务测试证据",
                    findings=[],
                    files=["src/service.py"],
                )

    def test_latest_failed_service_test_cannot_be_masked_by_later_unit_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root, external_api=True)
            self.add_generated_test(root, test_kind="service")
            requirements.append_test_report_execution(
                root,
                "REQ-HARD",
                test_kind="service",
                result="failed",
                acceptance_ids=["AC-01", "AC-02"],
                command="python -m unittest service",
                details="1 failed",
            )
            requirements.record_test_result(
                root,
                "REQ-HARD",
                test_kind="service",
                result="failed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
            )
            requirements.append_test_report_execution(
                root,
                "REQ-HARD",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                command="python -m unittest unit",
                details="2 passed",
            )
            manifest = requirements.record_test_result(
                root,
                "REQ-HARD",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
            )

            self.assertEqual(manifest["state"], "implementing")
            self.assertFalse(requirements._test_gate_satisfied(
                manifest,
                manifest["testEvidence"][-1]["evidenceDiffHash"],
            ))

    def test_missing_report_cannot_contribute_acceptance_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root)
            reports = root / "reports"
            reports.mkdir()
            for index, acceptance_id in enumerate(("AC-01", "AC-02"), 1):
                report = reports / f"unit-{index}.md"
                report.write_text(
                    f"# Unit test report {index}\n\nResult: passed\n1 test passed\n",
                    encoding="utf-8",
                )
                requirements.register_artifact(
                    root,
                    "REQ-HARD",
                    "unit-test",
                    report.relative_to(root).as_posix(),
                    result="passed",
                    acceptance_ids=[acceptance_id],
                    files=["src/service.py"],
                )
            manifest = requirements.load_requirement(root, "REQ-HARD")
            first_archive = root / manifest["testEvidence"][0]["reportSourcePath"]
            first_archive.unlink()
            snapshot = requirements.capture_requirement_scope(root, manifest)
            requirements.record_review(
                root,
                "REQ-HARD",
                result="passed",
                summary="当前代码快照未发现阻塞问题",
                findings=[],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            requirements.generate_artifact(root, "REQ-HARD", "closure")

            with self.assertRaisesRegex(requirements.RequirementError, "验收标准|测试报告|完整性"):
                requirements.finish_requirement(root, "REQ-HARD", files=["src/service.py"])

    def test_tampered_archived_report_invalidates_status_and_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root)
            report = root / "reports" / "unit.md"
            report.parent.mkdir()
            report.write_text("# Unit test report\n\nResult: passed\n2 tests passed\n", encoding="utf-8")
            manifest = requirements.register_artifact(
                root,
                "REQ-HARD",
                "unit-test",
                report.relative_to(root).as_posix(),
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                files=["src/service.py"],
            )
            readable_report = requirements.requirement_dir(root, "REQ-HARD") / "test-report.md"
            readable_text = readable_report.read_text(encoding="utf-8")
            self.assertRegex(readable_text, r"Git 提交：`[0-9a-f]{40}`")
            self.assertRegex(readable_text, r"代码快照：`[0-9a-f]{64}`")
            archive = root / manifest["testEvidence"][-1]["reportSourcePath"]
            archive.write_text("# Unit test report\n\nResult: passed\n1 test passed\n", encoding="utf-8")

            self.assertFalse(requirements.status_payload(root, "REQ-HARD")["testGateSatisfied"])
            snapshot = requirements.capture_requirement_scope(root, manifest)
            requirements.record_review(
                root,
                "REQ-HARD",
                result="passed",
                summary="当前代码快照未发现阻塞问题",
                findings=[],
                files=["src/service.py"],
                snapshot=snapshot,
            )
            requirements.generate_artifact(root, "REQ-HARD", "closure")
            with self.assertRaisesRegex(requirements.RequirementError, "测试报告|完整性"):
                requirements.finish_requirement(root, "REQ-HARD", files=["src/service.py"])

    def test_test_result_rejects_caller_snapshot_after_source_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.begin(root)
            requirements.generate_artifact(root, "REQ-HARD", "test")
            requirements.append_test_report_execution(
                root,
                "REQ-HARD",
                test_kind="unit",
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                command="python -m unittest",
                details="2 passed",
                phase="green",
                executed_count=2,
            )
            tested_snapshot = requirements.capture_requirement_scope(
                root, requirements.load_requirement(root, "REQ-HARD")
            )
            source.write_text("def answer():\n    return 3\n", encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "旧快照|发生变化"):
                requirements.record_test_result(
                    root,
                    "REQ-HARD",
                    test_kind="unit",
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    files=["src/service.py"],
                    snapshot=tested_snapshot,
                    report_path=".project-intel/requirements/REQ-HARD/test-report.md",
                )

    def test_bug_ready_requires_persisted_diagnosis_before_current_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            requirements.create_requirement(
                root, "1234", "返回值错误", external_api=False, ticket_kind="bug", track="standard"
            )
            requirements.set_acceptance_criteria(root, "bug1234", [
                {"id": "AC-01", "description": "实现需求约定的目标行为。"},
                {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
            ])
            directory = requirements.requirement_dir(root, "bug1234")
            requirement_path = directory / "requirement.md"
            requirement_path.write_text(
                requirement_document("bug1234", "返回值错误", kind="bug"), encoding="utf-8"
            )
            requirements.register_artifact(
                root, "bug1234", "requirement", requirement_path.relative_to(root).as_posix()
            )
            external_design = root / "docs" / "requirements" / "bug1234-返回值错误-设计文档.md"
            external_design.parent.mkdir(parents=True)
            external_design.write_text(bug_design("bug1234", "返回值错误"), encoding="utf-8")
            requirements.register_artifact(
                root, "bug1234", "design", external_design.relative_to(root).as_posix()
            )
            with self.assertRaisesRegex(requirements.RequirementError, "根因|diagnosis"):
                requirements.ready_requirement(root, "bug1234", "尝试跳过根因")
            diagnosed = requirements.record_diagnosis(
                root,
                "bug1234",
                root_cause="answer 函数仍返回旧常量，导致调用方得到错误结果。",
                evidence=["src/service.py#answer"],
            )
            self.assertEqual(diagnosed["state"], "specified")
            self.assertEqual(diagnosed["artifacts"][-1]["status"], "stale")
            requirements.register_artifact(
                root, "bug1234", "design", external_design.relative_to(root).as_posix()
            )
            ready = requirements.ready_requirement(root, "bug1234", "根因和修复设计已确认")
            self.assertEqual(ready["state"], "ready")

    def test_business_report_file_is_not_excluded_from_requirement_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root)
            report = root / "src" / "report.json"
            report.write_text('{"tests": 2, "failures": 0, "status": "passed"}\n', encoding="utf-8")
            requirements.register_artifact(
                root,
                "REQ-HARD",
                "unit-test",
                report.relative_to(root).as_posix(),
                result="passed",
                acceptance_ids=["AC-01", "AC-02"],
                project_wide=True,
            )
            snapshot = requirements.capture_requirement_scope(root, requirements.load_requirement(root, "REQ-HARD"))
            self.assertIn("src/report.json", snapshot["evidenceFiles"])

    def test_maintain_revalidates_required_documents_before_closing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root)
            self.add_generated_test(root)
            self.finish(root)
            closure = requirements.requirement_dir(root, "REQ-HARD") / "closure-summary.md"
            closure_text = closure.read_text(encoding="utf-8")
            self.assertIn("### 业务源码与测试变更", closure_text)
            self.assertIn("### 需求交付文档", closure_text)
            self.assertIn("`src/service.py`", closure_text)
            closure.unlink()
            with self.assertRaisesRegex(requirements.RequirementError, "收口|closure|产物"):
                requirements.close_requirement(root, "REQ-HARD", check_succeeded=True)

    def test_maintain_revalidates_test_report_before_closing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.begin(root)
            self.add_generated_test(root)
            self.finish(root)
            report = requirements.requirement_dir(root, "REQ-HARD") / "test-report.md"
            report.unlink()

            with self.assertRaisesRegex(requirements.RequirementError, "测试|报告|完整性"):
                requirements.close_requirement(root, "REQ-HARD", check_succeeded=True)

    def test_concurrent_registered_reports_all_reach_readable_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            reports = root / "reports"
            reports.mkdir()
            paths = []
            for index in range(8):
                report = reports / f"concurrent-{index}.md"
                report.write_text(
                    f"# Unit test report {index}\n\nResult: passed\n1 test passed\n",
                    encoding="utf-8",
                )
                paths.append(report.relative_to(root).as_posix())
            subprocess.run(["git", "add", "reports"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "add test reports"], cwd=root, check=True)
            self.begin(root)

            def register(path: str) -> None:
                requirements.register_artifact(
                    root,
                    "REQ-HARD",
                    "unit-test",
                    path,
                    result="passed",
                    acceptance_ids=["AC-01", "AC-02"],
                    project_wide=True,
                )

            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(register, paths))

            summary = (requirements.requirement_dir(root, "REQ-HARD") / "test-report.md").read_text(
                encoding="utf-8"
            )
            for path in paths:
                self.assertIn(f"`{path}`", summary)
            manifest = requirements.load_requirement(root, "REQ-HARD")
            self.assertEqual(len(manifest["testEvidence"]), len(paths))

    def test_requirement_query_ignores_symlinked_manifest_directory(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            self.git_project(root)
            requirement_root = root / ".project-intel" / "requirements"
            requirement_root.mkdir(parents=True)
            outside = Path(outside_tmp)
            (outside / "manifest.json").write_text(
                '{"schemaVersion": 2, "requirementId": "EVIL", "requirementName": "outside", '
                '"state": "closed", "changedFiles": []}\n',
                encoding="utf-8",
            )
            os.symlink(outside, requirement_root / "EVIL")

            self.assertEqual(requirements.query_requirements(root, state="closed"), [])


if __name__ == "__main__":
    unittest.main()
