from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from design_fixtures import requirement_design
from project_intel_lib import application, requirements


def requirement_text(identifier: str, name: str, acceptance: tuple[str, ...] = ("AC-01",)) -> str:
    criteria = "\n".join(f"- {item}：满足已确认的目标行为。" for item in acceptance)
    return f"""# {identifier} {name} 需求文档

## 文档信息

- 需求号：`{identifier}`
- 需求名称：{name}
- 单据类型：Requirement

## 背景与现状

当前流程缺少按需求隔离的交付档案，历史报告会被后续需求覆盖。

## 目标

每个需求拥有独立且可验证的需求、设计、测试和收口文档。

## 业务场景

Agent 登记需求后，在同一个需求目录完成设计、开发、验证和收口。

## 范围

调整需求档案目录、文档门禁和生命周期写入位置。

## 非目标

不修改业务仓库源码，不自动发布或安装插件。

## 业务规则与异常边界

所有文件必须位于仓库内；缺少任一必选文档时对应门禁失败。

## 验收标准

{criteria}

## 外部接口影响

不影响对外接口，依据是本次仅修改本地插件文件组织。

## 待确认事项

无，目录和四类必选文档已经确认。
"""


class RequirementLayoutV2Tests(unittest.TestCase):
    def git_project(self, root: Path) -> Path:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True)
        source.write_text("def answer():\n    return 1\n", encoding="utf-8")
        project_intel = root / ".project-intel"
        project_intel.mkdir()
        (project_intel / "manifest.json").write_text('{"schemaVersion": 4}\n', encoding="utf-8")
        (project_intel / "config.json").write_text(
            '{"schemaVersion": 4, "quality": {"commands": [], "timeoutSeconds": 30}}\n',
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=root, check=True)
        return source

    def create_specified_requirement(self, root: Path, identifier: str = "REQ-4000") -> dict:
        requirements.create_requirement(
            root, identifier, "需求档案收敛", track="complex", external_api=False, ticket_kind="requirement"
        )
        requirements.set_acceptance_criteria(
            root, identifier, [{"id": "AC-01", "description": "满足已确认的目标行为。"}]
        )
        path = requirements.requirement_dir(root, identifier) / "requirement.md"
        path.write_text(requirement_text(identifier, "需求档案收敛"), encoding="utf-8")
        return requirements.register_artifact(root, identifier, "requirement", path.relative_to(root).as_posix())

    def create_designed_requirement(self, root: Path, identifier: str = "REQ-4000") -> dict:
        self.create_specified_requirement(root, identifier)
        path = requirements.requirement_dir(root, identifier) / "design.md"
        path.write_text(requirement_design(identifier, "需求档案收敛"), encoding="utf-8")
        return requirements.register_artifact(root, identifier, "design", path.relative_to(root).as_posix())

    def test_requirement_directory_is_direct_and_contains_four_canonical_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            manifest = self.create_designed_requirement(root)
            directory = root / ".project-intel" / "requirements" / "REQ-4000"
            self.assertEqual(requirements.requirement_dir(root, "REQ-4000"), directory)
            self.assertEqual(manifest["schemaVersion"], 2)
            self.assertEqual(manifest["state"], "designed")
            self.assertTrue((directory / "manifest.json").is_file())
            self.assertTrue((directory / "requirement.md").is_file())
            self.assertTrue((directory / "design.md").is_file())
            self.assertFalse((root / ".project-intel" / "requirements" / "by-id").exists())

    def test_init_writes_one_project_status_and_does_not_create_legacy_output_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "service.py").write_text("def answer():\n    return 1\n", encoding="utf-8")
            (root / ".project-intel").mkdir()
            (root / ".project-intel" / ".gitignore").write_text("custom-local/\n", encoding="utf-8")
            application.init_project(root, with_graph=False)
            self.assertTrue((root / ".project-intel" / "project-status.md").is_file())
            self.assertTrue((root / ".project-intel" / ".gitignore").is_file())
            self.assertIn("custom-local/", (root / ".project-intel" / ".gitignore").read_text(encoding="utf-8"))
            for name in ("reports", "specs", "plans", "maintenance"):
                self.assertFalse((root / ".project-intel" / name).exists(), name)
            self.assertFalse((root / ".project-intel" / "requirements" / "files").exists())

    def test_registered_external_documents_are_copied_to_canonical_requirement_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            requirements.create_requirement(
                root, "REQ-4000", "需求档案收敛", track="complex", external_api=False, ticket_kind="requirement"
            )
            requirements.set_acceptance_criteria(
                root, "REQ-4000", [{"id": "AC-01", "description": "满足已确认的目标行为。"}]
            )
            external_dir = root / "docs" / "requirements"
            external_dir.mkdir(parents=True)
            external_requirement = external_dir / "source-requirement.md"
            external_requirement.write_text(requirement_text("REQ-4000", "需求档案收敛"), encoding="utf-8")
            registered = requirements.register_artifact(
                root, "REQ-4000", "requirement", external_requirement.relative_to(root).as_posix()
            )
            self.assertEqual(registered["artifacts"][-1]["path"], ".project-intel/requirements/REQ-4000/requirement.md")
            external_design = external_dir / "REQ-4000_需求档案收敛_设计文档.md"
            external_design.write_text(requirement_design("REQ-4000", "需求档案收敛"), encoding="utf-8")
            registered = requirements.register_artifact(
                root, "REQ-4000", "design", external_design.relative_to(root).as_posix()
            )
            self.assertEqual(registered["artifacts"][-1]["path"], ".project-intel/requirements/REQ-4000/design.md")

    def test_plan_is_optional_and_is_generated_inside_requirement_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_designed_requirement(root)
            self.assertFalse((requirements.requirement_dir(root, "REQ-4000") / "plan.md").exists())
            manifest = requirements.generate_artifact(root, "REQ-4000", "plan")
            self.assertEqual(manifest["state"], "designed")
            self.assertTrue((requirements.requirement_dir(root, "REQ-4000") / "plan.md").is_file())
            self.assertFalse((root / ".project-intel" / "plans").exists())

    def test_ready_requires_both_requirement_and_design_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_specified_requirement(root)
            with self.assertRaisesRegex(requirements.RequirementError, "设计"):
                requirements.ready_requirement(root, "REQ-4000", "尝试跳过设计")

    def test_ready_revalidates_requirement_document_against_manifest_acceptance_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            self.create_designed_requirement(root)
            manifest_path = requirements.manifest_path(root, "REQ-4000")
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["acceptanceCriteria"].append(
                {"id": "AC-02", "description": "新增边界验收。", "status": "pending"}
            )
            manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            with self.assertRaisesRegex(requirements.RequirementError, "需求文档"):
                requirements.ready_requirement(root, "REQ-4000", "尝试使用与需求文档不一致的 AC")

    def test_requirement_test_evidence_is_not_written_to_shared_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_designed_requirement(root)
            requirements.ready_requirement(root, "REQ-4000", "范围已确认")
            requirements.begin_requirement(root, "REQ-4000")
            source.write_text("def answer():\n    return 2\n", encoding="utf-8")
            code, _ = application.run_project_test(
                root,
                None,
                "green",
                commands=[f'"{sys.executable}" -c "assert 2 == 2"'],
                files=["src/service.py"],
                requirement_id="REQ-4000",
                test_kind="unit",
                report_action="generate",
                acceptance_ids=["AC-01"],
            )
            self.assertEqual(code, 0)
            report = requirements.requirement_dir(root, "REQ-4000") / "test-report.md"
            self.assertTrue(report.is_file())
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("- 覆盖范围：`src/service.py`", report_text)
            self.assertRegex(report_text, r"- Git 提交：`[0-9a-f]{40}`")
            self.assertRegex(report_text, r"- 代码快照：`[0-9a-f]{64}`")
            self.assertFalse((root / ".project-intel" / "reports" / "test-evidence.md").exists())
            self.assertFalse((root / ".project-intel" / "reports" / "test-evidence.json").exists())

    def test_registered_markdown_test_report_is_copied_to_canonical_requirement_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_designed_requirement(root)
            requirements.ready_requirement(root, "REQ-4000", "范围已确认")
            requirements.begin_requirement(root, "REQ-4000")
            source.write_text("def answer():\n    return 2\n", encoding="utf-8")
            external = root / "reports" / "unit-result.md"
            external.parent.mkdir()
            external.write_text("# Unit test report\n\n- Result: passed\n- 1 test passed\n", encoding="utf-8")

            manifest = requirements.register_artifact(
                root,
                "REQ-4000",
                "unit-test",
                external.relative_to(root).as_posix(),
                result="passed",
                acceptance_ids=["AC-01"],
                files=["src/service.py"],
            )

            canonical = requirements.requirement_dir(root, "REQ-4000") / "test-report.md"
            self.assertTrue(canonical.is_file())
            artifact = next(item for item in reversed(manifest["artifacts"]) if item["type"] == "unit-test")
            self.assertEqual(artifact["path"], ".project-intel/requirements/REQ-4000/test-report.md")
            self.assertEqual(artifact["sourcePath"], "reports/unit-result.md")
            self.assertEqual(manifest["testEvidence"][-1]["reportPath"], artifact["path"])

    def test_registered_structured_test_report_gets_canonical_markdown_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_designed_requirement(root)
            requirements.ready_requirement(root, "REQ-4000", "范围已确认")
            requirements.begin_requirement(root, "REQ-4000")
            source.write_text("def answer():\n    return 2\n", encoding="utf-8")
            external = root / "test-results" / "unit-results.json"
            external.parent.mkdir()
            external.write_text('{"tests": 1, "failures": 0, "status": "passed"}\n', encoding="utf-8")

            manifest = requirements.register_artifact(
                root,
                "REQ-4000",
                "unit-test",
                external.relative_to(root).as_posix(),
                result="passed",
                acceptance_ids=["AC-01"],
                files=["src/service.py"],
            )

            canonical = requirements.requirement_dir(root, "REQ-4000") / "test-report.md"
            content = canonical.read_text(encoding="utf-8")
            self.assertIn("结果：passed", content)
            self.assertIn("test-results/unit-results.json", content)
            artifact = next(item for item in reversed(manifest["artifacts"]) if item["type"] == "unit-test")
            self.assertEqual(artifact["path"], ".project-intel/requirements/REQ-4000/test-report.md")
            self.assertEqual(artifact["sourcePath"], "test-results/unit-results.json")

    def test_project_test_register_action_archives_report_without_expanding_business_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_designed_requirement(root)
            requirements.ready_requirement(root, "REQ-4000", "范围已确认")
            requirements.begin_requirement(root, "REQ-4000")
            source.write_text("def answer():\n    return 2\n", encoding="utf-8")
            external = root / "reports" / "unit-result.md"
            external.parent.mkdir()
            external.write_text("# Unit test report\n\n- Result: passed\n- 1 test passed\n", encoding="utf-8")

            code, result = application.run_project_test(
                root,
                None,
                "green",
                commands=[f'"{sys.executable}" -c "assert 2 == 2"'],
                files=["src/service.py"],
                requirement_id="REQ-4000",
                test_kind="unit",
                report_action="register",
                report_path="reports/unit-result.md",
                acceptance_ids=["AC-01"],
            )

            self.assertEqual(code, 0)
            manifest = result["requirement"]
            artifact = next(item for item in reversed(manifest["artifacts"]) if item["type"] == "unit-test")
            self.assertEqual(artifact["path"], ".project-intel/requirements/REQ-4000/test-report.md")
            self.assertEqual(artifact["sourcePath"], "reports/unit-result.md")
            reviewed = requirements.record_review(
                root,
                "REQ-4000",
                result="passed",
                summary="业务变更和测试覆盖均已检查。",
                findings=[],
                files=["src/service.py"],
            )
            self.assertEqual(reviewed["state"], "reviewed")

    def test_file_history_is_derived_from_requirement_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.git_project(root)
            self.create_designed_requirement(root)
            requirements.ready_requirement(root, "REQ-4000", "范围已确认")
            requirements.begin_requirement(root, "REQ-4000")
            source.write_text("def answer():\n    return 2\n", encoding="utf-8")
            snapshot = requirements.capture_requirement_scope(root, requirements.load_requirement(root, "REQ-4000"))
            requirements.record_changed_files(root, "REQ-4000", snapshot)
            matches = requirements.query_requirements(root, file_path="src/service.py")
            self.assertEqual([item["requirementId"] for item in matches], ["REQ-4000"])
            self.assertFalse((root / ".project-intel" / "requirements" / "files").exists())

    def test_layout_migration_dry_run_is_non_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            legacy = root / ".project-intel" / "requirements" / "by-id" / "REQ-OLD"
            legacy.mkdir(parents=True)
            payload = {"schemaVersion": 1, "requirementId": "REQ-OLD", "requirementName": "旧需求", "state": "draft"}
            (legacy / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
            result = requirements.migrate_layout(root, dry_run=True)
            self.assertTrue(result["ok"])
            self.assertTrue(legacy.exists())
            self.assertFalse((root / ".project-intel" / "requirements" / "REQ-OLD").exists())

    def test_unmigrated_v1_writes_stay_in_legacy_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            legacy = root / ".project-intel" / "requirements" / "by-id" / "REQ-OLD"
            legacy.mkdir(parents=True)
            payload = {
                "schemaVersion": 1,
                "revision": 1,
                "requirementId": "REQ-OLD",
                "requirementName": "旧需求",
                "state": "draft",
                "artifacts": [],
            }
            (legacy / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
            requirements.generate_artifact(root, "REQ-OLD", "requirement")
            self.assertTrue((legacy / "requirement.md").is_file())
            self.assertFalse((root / ".project-intel" / "requirements" / "REQ-OLD").exists())

    def test_layout_migration_apply_moves_manifest_and_rewrites_internal_artifact_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            legacy = root / ".project-intel" / "requirements" / "by-id" / "REQ-OLD"
            legacy.mkdir(parents=True)
            design = legacy / "design.md"
            design.write_text("# legacy design\n", encoding="utf-8")
            payload = {
                "schemaVersion": 1,
                "revision": 1,
                "requirementId": "REQ-OLD",
                "requirementName": "旧需求",
                "state": "draft",
                "artifacts": [{
                    "type": "requirement-design",
                    "path": ".project-intel/requirements/by-id/REQ-OLD/design.md",
                }],
                "testEvidence": [{
                    "reportPath": ".project-intel/requirements/by-id/REQ-OLD/test-report.md",
                    "manual": {
                        "evidencePath": ".project-intel/requirements/by-id/REQ-OLD/evidence/manual.log",
                    },
                }],
            }
            (legacy / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
            result = requirements.migrate_layout(root, dry_run=False)
            self.assertTrue(result["ok"])
            migrated = root / ".project-intel" / "requirements" / "REQ-OLD" / "manifest.json"
            self.assertTrue(migrated.is_file())
            stored = json.loads(migrated.read_text(encoding="utf-8"))
            self.assertEqual(stored["revision"], 2)
            self.assertEqual(
                stored["artifacts"][0]["path"],
                ".project-intel/requirements/REQ-OLD/design.md",
            )
            self.assertEqual(
                stored["testEvidence"][0]["reportPath"],
                ".project-intel/requirements/REQ-OLD/test-report.md",
            )
            self.assertEqual(
                stored["testEvidence"][0]["manual"]["evidencePath"],
                ".project-intel/requirements/REQ-OLD/evidence/manual.log",
            )
            self.assertEqual(stored["history"][-1]["action"], "migrate-layout-v2")

    def test_layout_migration_preflights_every_manifest_before_moving_any_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            legacy_root = root / ".project-intel" / "requirements" / "by-id"
            valid = legacy_root / "REQ-GOOD"
            valid.mkdir(parents=True)
            (valid / "manifest.json").write_text(json.dumps({
                "schemaVersion": 1,
                "revision": 1,
                "requirementId": "REQ-GOOD",
                "requirementName": "可迁移需求",
                "state": "draft",
            }), encoding="utf-8")
            invalid = legacy_root / "REQ-BAD"
            invalid.mkdir(parents=True)
            (invalid / "manifest.json").write_text("{bad json", encoding="utf-8")

            result = requirements.migrate_layout(root, dry_run=False)

            self.assertFalse(result["ok"])
            self.assertTrue(valid.is_dir())
            self.assertTrue(invalid.is_dir())
            self.assertFalse((root / ".project-intel" / "requirements" / "REQ-GOOD").exists())
            self.assertTrue(any("manifest" in item for item in result["conflicts"]))

    def test_layout_migration_rolls_back_all_directories_when_later_manifest_write_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.git_project(root)
            legacy_root = root / ".project-intel" / "requirements" / "by-id"
            originals = {}
            for identifier in ("REQ-A", "REQ-B"):
                directory = legacy_root / identifier
                directory.mkdir(parents=True)
                body = json.dumps({
                    "schemaVersion": 1,
                    "revision": 1,
                    "requirementId": identifier,
                    "requirementName": f"{identifier} 旧需求",
                    "state": "draft",
                }).encode("utf-8")
                (directory / "manifest.json").write_bytes(body)
                originals[identifier] = body
            real_write = requirements._write_manifest

            def fail_second(path, payload):
                if path.parent.name == "REQ-B":
                    raise OSError("simulated disk failure")
                return real_write(path, payload)

            with mock.patch.object(requirements, "_write_manifest", side_effect=fail_second):
                with self.assertRaisesRegex(requirements.RequirementError, "迁移失败|已回滚"):
                    requirements.migrate_layout(root, dry_run=False)

            for identifier, original in originals.items():
                legacy_manifest = legacy_root / identifier / "manifest.json"
                self.assertEqual(legacy_manifest.read_bytes(), original)
                self.assertFalse((root / ".project-intel" / "requirements" / identifier).exists())


if __name__ == "__main__":
    unittest.main()
