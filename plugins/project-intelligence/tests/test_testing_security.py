import importlib.util
import re
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "project_intel_lib" / "testing.py"
SPEC = importlib.util.spec_from_file_location("project_intel_testing_security", MODULE_PATH)
testing = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(testing)


class TestingSecurityTests(unittest.TestCase):
    def test_authorization_redacts_the_complete_value_for_common_schemes(self):
        raw = "\n".join(
            [
                "Authorization: Basic dXNlcjpwYXNz",
                'Authorization: Digest username="alice", realm="private", nonce="abcdef"',
                "Authorization: ApiKey key-with-secret-tail",
                "Authorization: Bearer bearer-secret",
                "curl -H 'Authorization: Basic shell-secret' https://example.test/health",
            ]
        )

        safe = testing.sanitize_text(raw)

        for secret in (
            "dXNlcjpwYXNz",
            "alice",
            "private",
            "abcdef",
            "key-with-secret-tail",
            "bearer-secret",
            "shell-secret",
        ):
            self.assertNotIn(secret, safe)
        self.assertIn("https://example.test/health", safe)
        self.assertEqual(safe.count("Authorization: [REDACTED]"), 5)
        self.assertEqual(testing.sanitize_text(safe), safe)

    def test_url_userinfo_is_redacted_without_hiding_the_destination(self):
        raw = (
            "https://alice:super-secret@example.test/orders "
            "ssh://deploy-token@git.example.test/repo "
            "postgresql://db-user:db-password@db.example.test:5432/app"
        )

        safe = testing.sanitize_text(raw)

        for secret in ("alice", "super-secret", "deploy-token", "db-user", "db-password"):
            self.assertNotIn(secret, safe)
        for destination in (
            "example.test/orders",
            "git.example.test/repo",
            "db.example.test:5432/app",
        ):
            self.assertIn(destination, safe)

    def test_phone_identity_number_and_party_id_are_redacted(self):
        raw = "\n".join(
            [
                "联系电话：13800138000",
                "备用电话：+86 139-0013-8000",
                "身份证：320311199001011234",
                "旧身份证：130503670401001",
                'partyId=P-2026-0001&action=query',
                '{"party_id": "customer-8899"}',
                "--party-id cli-party-42",
            ]
        )

        safe = testing.sanitize_text(raw)

        for secret in (
            "13800138000",
            "139-0013-8000",
            "320311199001011234",
            "130503670401001",
            "P-2026-0001",
            "customer-8899",
            "cli-party-42",
        ):
            self.assertNotIn(secret, safe)
        self.assertIn("action=query", safe)

    def test_redaction_preserves_non_sensitive_identifiers_and_urls(self):
        raw = (
            "token_count=4 authorization_required=true partyIdentity=aggregate "
            "orderId=12345678901 version=20260717001 "
            "https://example.test/users/alice?q=a@example.test"
        )

        self.assertEqual(testing.sanitize_text(raw), raw)

    def test_markdown_renderer_escapes_untrusted_fields_and_uses_safe_fences(self):
        output = "before\n```\n# forged section\n````\nafter Authorization: Basic output-secret"
        payload = {
            "task": "任务 [恶意链接](javascript:alert(1))\n# 伪造标题",
            "updatedAt": "2026-07-17` injected",
            "entries": [
                {
                    "phase": "verify | forged",
                    "status": "passed\n| forged | row |",
                    "commands": [
                        {
                            "command": "printf 'x|y'\n# forged command Authorization: ApiKey command-secret",
                            "exitCode": 0,
                            "stdout": output,
                            "stderr": "",
                        }
                    ],
                    "files": ["src/a|b.py", "tests/`injected`.py"],
                }
            ],
        }

        markdown = testing.render_test_evidence(payload)

        for secret in ("output-secret", "command-secret"):
            self.assertNotIn(secret, markdown)
        self.assertNotIn("[恶意链接](javascript:alert(1))", markdown)
        self.assertNotIn("\n# 伪造标题", markdown)
        self.assertNotIn("\n# forged command", markdown)
        self.assertNotIn("src/a|b.py", markdown)
        self.assertIn("src/a&#124;b.py", markdown)
        fences = re.findall(r"(?m)^(`{3,})(?:text)?$", markdown)
        self.assertGreaterEqual(len(fences), 2)
        self.assertEqual(fences[0], fences[-1])
        self.assertGreater(len(fences[0]), 4)


if __name__ == "__main__":
    unittest.main()
