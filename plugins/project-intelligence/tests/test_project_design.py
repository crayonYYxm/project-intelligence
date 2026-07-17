import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

from design_fixtures import bug_design, requirement_design

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from project_intel_lib import design_documents


class ProjectDesignValidationTests(unittest.TestCase):
    @staticmethod
    def write_source(root: Path) -> None:
        source = root / "src" / "service.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("def answer():\n    return 1\n", encoding="utf-8")

    def test_requirement_template_passes_without_acceptance_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_source(root)
            relative = "docs/requirements/REQ-1001_设计文档接入_设计文档.md"
            payload = design_documents.validate(
                requirement_design("REQ-1001", "设计文档接入"),
                root,
                relative,
                "requirement",
                expected_id="REQ-1001",
                expected_name="设计文档接入",
            )
            self.assertTrue(payload["ok"], payload["errors"])
            self.assertEqual(payload["kind"], "requirement")

    def test_requirement_rejects_extra_acceptance_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = requirement_design("REQ-1001", "设计文档接入") + "\n# 验收标准\n\n- AC-01：不应写在文档中。\n"
            payload = design_documents.validate(
                text,
                root,
                "docs/requirements/REQ-1001_设计文档接入_设计文档.md",
                "requirement",
            )
            self.assertFalse(payload["ok"])
            self.assertTrue(any("验收标准" in item for item in payload["errors"]))

    def test_bug_template_and_identity_are_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_source(root)
            payload = design_documents.validate(
                bug_design("bug1234", "返回值错误"),
                root,
                "docs/requirements/bug1234-返回值错误-设计文档.md",
                "auto",
                expected_id="bug1234",
                expected_name="返回值错误",
            )
            self.assertTrue(payload["ok"], payload["errors"])
            mismatch = design_documents.validate(
                bug_design("bug1234", "返回值错误"),
                root,
                "docs/requirements/bug9999-返回值错误-设计文档.md",
                "bug",
                expected_id="bug1234",
                expected_name="返回值错误",
            )
            self.assertFalse(mismatch["ok"])
            self.assertTrue(any("需求号" in item or "Bug 编号" in item for item in mismatch["errors"]))

            standalone_mismatch = design_documents.validate(
                bug_design("bug1234", "返回值错误"),
                root,
                "docs/requirements/bug1234-另一个名称-设计文档.md",
                "bug",
            )
            self.assertFalse(standalone_mismatch["ok"])
            self.assertTrue(any("文件名与标题" in item for item in standalone_mismatch["errors"]))

    def test_requirement_filename_must_match_title_without_manifest_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = design_documents.validate(
                requirement_design("REQ-1001", "设计文档接入"),
                root,
                "docs/requirements/REQ-1001_错误名称_设计文档.md",
                "requirement",
            )
            self.assertFalse(payload["ok"])
            self.assertTrue(any("文件名与标题" in item for item in payload["errors"]))

    def test_empty_sections_sensitive_values_and_path_escape_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = requirement_design("REQ-1001", "设计文档接入").replace(
                "实现“设计文档接入”，保持现有接口兼容。",
                "Authorization: Bearer abcdefghijklmnop",
            ).replace("研发中心测试人员。", "")
            payload = design_documents.validate(
                text,
                root,
                "docs/requirements/REQ-1001_设计文档接入_设计文档.md",
                "requirement",
            )
            self.assertFalse(payload["ok"])
            self.assertTrue(any("为空" in item for item in payload["errors"]))
            self.assertTrue(any("敏感" in item or "Bearer" in item for item in payload["errors"]))

            repo = root / "repo"
            repo.mkdir()
            outside = root / "outside.md"
            outside.write_text(text, encoding="utf-8")
            with self.assertRaises(design_documents.UsageError):
                design_documents.resolve_document(str(outside), repo)

    def test_bundled_validator_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            self.write_source(root)
            relative = "docs/requirements/REQ-1001_设计文档接入_设计文档.md"
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_text(requirement_design("REQ-1001", "设计文档接入"), encoding="utf-8")
            wrapper = SCRIPTS.parent / "skills" / "project-design" / "scripts" / "validate_design_doc.py"

            passed = subprocess.run(
                [sys.executable, str(wrapper), "--file", relative, "--repo", str(root), "--kind", "auto", "--json"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertTrue(json.loads(passed.stdout)["ok"])

            path.write_text(path.read_text(encoding="utf-8") + "\n# 验收标准\n\n不应存在。\n", encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(wrapper), "--file", relative, "--repo", str(root), "--kind", "requirement", "--json"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(failed.returncode, 1, failed.stderr)
            self.assertFalse(json.loads(failed.stdout)["ok"])

            usage = subprocess.run(
                [sys.executable, str(wrapper), "--file", "missing.md", "--repo", str(root), "--json"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(usage.returncode, 2, usage.stderr)


if __name__ == "__main__":
    unittest.main()
