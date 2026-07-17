from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

TESTS = Path(__file__).resolve().parent
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from design_fixtures import bug_design, requirement_design, requirement_document
from project_intel_lib import design_documents, requirement_documents


class DesignSourceTruthTests(unittest.TestCase):
    def source_repo(self, root: Path) -> None:
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True)
        source.write_text("def answer():\n    return 1\n", encoding="utf-8")

    def validate_bug(self, root: Path, text: str) -> dict:
        return design_documents.validate(
            text,
            root,
            "docs/requirements/bug1234-返回值错误-设计文档.md",
            "bug",
            expected_id="bug1234",
            expected_name="返回值错误",
        )

    def test_existing_repo_path_and_symbol_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_repo(root)
            payload = self.validate_bug(root, bug_design("bug1234", "返回值错误"))
            self.assertTrue(payload["ok"], payload["errors"])
            self.assertEqual(payload["sourceEvidence"][0]["path"], "src/service.py")
            self.assertIn("answer", payload["sourceEvidence"][0]["symbols"])

    def test_nonexistent_repo_path_is_not_source_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_repo(root)
            text = bug_design("bug1234", "返回值错误").replace(
                "src/service.py", "src/not-exist.py"
            )
            payload = self.validate_bug(root, text)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("不存在" in item for item in payload["errors"]), payload)

    def test_source_evidence_symlink_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            root.mkdir()
            self.source_repo(root)
            outside = base / "outside.py"
            outside.write_text("def answer():\n    return 1\n", encoding="utf-8")
            link = root / "src" / "outside.py"
            link.symlink_to(outside)
            text = bug_design("bug1234", "返回值错误").replace("src/service.py", "src/outside.py")
            payload = self.validate_bug(root, text)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("越界" in item for item in payload["errors"]), payload)

    def test_claimed_symbol_must_exist_in_claimed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_repo(root)
            text = bug_design("bug1234", "返回值错误").replace("`answer`", "`missing_symbol`")
            payload = self.validate_bug(root, text)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("符号" in item and "missing_symbol" in item for item in payload["errors"]), payload)

    def test_unavailable_external_source_is_an_explicit_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_repo(root)
            text = bug_design("bug1234", "返回值错误").replace(
                "`src/service.py` 中的 `answer` 仍返回旧常量。",
                "`external/customer-service/src/Client.java` 中的 `queryCustomer` 返回旧值。"
                "该实现位于外部客户中心，源码未取得，无法核验。",
            )
            payload = self.validate_bug(root, text)
            self.assertFalse(payload["ok"])
            self.assertTrue(payload["blockingIssues"], payload)
            self.assertTrue(any("外部源码" in item for item in payload["blockingIssues"]), payload)

    def test_requirement_design_uses_the_same_source_truth_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.source_repo(root)
            passed = design_documents.validate(
                requirement_design("REQ-1001", "设计文档接入"),
                root,
                "docs/requirements/REQ-1001_设计文档接入_设计文档.md",
                "requirement",
                expected_id="REQ-1001",
                expected_name="设计文档接入",
            )
            self.assertTrue(passed["ok"], passed["errors"])

            text = requirement_design("REQ-1001", "设计文档接入").replace(
                "src/service.py", "src/not-exist.py"
            )
            failed = design_documents.validate(
                text,
                root,
                "docs/requirements/REQ-1001_设计文档接入_设计文档.md",
                "requirement",
                expected_id="REQ-1001",
                expected_name="设计文档接入",
            )
            self.assertFalse(failed["ok"])
            self.assertTrue(any("不存在" in item for item in failed["errors"]), failed)


class RequirementManifestTruthTests(unittest.TestCase):
    CRITERIA = [
        {"id": "AC-01", "description": "实现需求约定的目标行为。"},
        {"id": "AC-02", "description": "相关测试通过且无重要回归。"},
    ]

    def validate(self, text: str, **overrides: object) -> dict:
        arguments = {
            "kind": "requirement",
            "expected_id": "REQ-1001",
            "expected_name": "订单查询",
            "acceptance_ids": ["AC-01", "AC-02"],
            "acceptance_criteria": self.CRITERIA,
            "expected_external_api": False,
        }
        arguments.update(overrides)
        return requirement_documents.validate(text, **arguments)

    def document(self) -> str:
        return requirement_document("REQ-1001", "订单查询")

    def test_exact_manifest_identity_impact_and_acceptance_pass(self):
        payload = self.validate(self.document())
        self.assertTrue(payload["ok"], payload["errors"])
        self.assertEqual(payload["documentIdentity"]["requirementId"], "REQ-1001")
        self.assertFalse(payload["documentIdentity"]["externalApiImpact"])

    def test_document_information_fields_must_exactly_match_manifest(self):
        text = self.document().replace("- 需求名称：订单查询", "- 需求名称：错误名称")
        payload = self.validate(text)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("需求名称" in item and "manifest" in item for item in payload["errors"]), payload)

        text = self.document().replace("单据类型：Requirement", "单据类型：Bug")
        payload = self.validate(text)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("单据类型" in item and "manifest" in item for item in payload["errors"]), payload)

    def test_acceptance_description_must_match_manifest(self):
        text = self.document().replace(
            "AC-01：实现需求约定的目标行为。",
            "AC-01：删除所有订单数据。",
        )
        payload = self.validate(text)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("AC-01" in item and "描述" in item for item in payload["errors"]), payload)

    def test_external_api_impact_must_match_manifest(self):
        text = self.document().replace(
            "不影响对外接口；本测试需求仅调整内部服务行为。",
            "影响对外接口；需要调整服务契约。",
        )
        payload = self.validate(text)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("外部接口影响" in item and "manifest" in item for item in payload["errors"]), payload)

    def test_external_api_impact_rejects_conflicting_statements(self):
        text = self.document().replace(
            "不影响对外接口；本测试需求仅调整内部服务行为。",
            "不影响对外接口 A，但同时新增外部接口 B。",
        )
        payload = self.validate(text)
        self.assertFalse(payload["ok"])
        self.assertTrue(any("矛盾" in item and "消歧" in item for item in payload["errors"]), payload)
        self.assertIsNone(payload["documentIdentity"]["externalApiImpact"])

    def test_pending_items_are_structured_readiness_blockers(self):
        text = self.document().replace(
            "无；测试范围和目标行为已经确认。",
            "客户中心返回字段仍需确认。",
        )
        payload = self.validate(text)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["blockingIssues"], payload)
        self.assertTrue(any("待确认事项" in item for item in payload["blockingIssues"]), payload)


if __name__ == "__main__":
    unittest.main()
