from __future__ import annotations

import argparse
import re
from typing import Any


def _sanitize_error_text(value: str) -> str:
    text = str(value or "")
    patterns = [
        (re.compile(r"(?i)(authorization\s*[:=]\s*)(bearer\s+)?[^\s,;]+"), r"\1[REDACTED]"),
        (re.compile(r"(?i)(cookie\s*[:=]\s*)[^\n]+"), r"\1[REDACTED]"),
        (re.compile(r"(?i)(token|access_token|refresh_token|password|secret|api_key)(\s*[:=]\s*)[^\s,;]+"), r"\1\2[REDACTED]"),
        (re.compile(r"(?i)(aws_access_key_id|aws_secret_access_key)(\s*[:=]\s*)[^\s,;]+"), r"\1\2[REDACTED]"),
        (re.compile(r"://([^:/\s]+):([^@\s]+)@"), r"://[REDACTED]:[REDACTED]@"),
    ]
    for pattern, replacement in patterns:
        text = pattern.sub(replacement, text)
    return text


def extract_global_json(argv: list[str]) -> tuple[list[str], bool]:
    return [item for item in argv if item != "--json"], "--json" in argv


def json_envelope(command: str, exit_code: int, result: Any = None, output: str = "") -> dict[str, Any]:
    ok = exit_code == 0
    error = None
    if not ok:
        if isinstance(result, dict) and "error" in result:
            message = _sanitize_error_text(str(result.get("error") or "command failed"))
            result = {**result, "error": message}
        else:
            message = "command failed"
        error = {"code": "COMMAND_FAILED" if exit_code != 2 else "USAGE_ERROR", "message": message}
    return {
        "ok": ok,
        "command": command,
        "status": "ok" if ok else "failed",
        "exitCode": exit_code,
        "error": error,
        "result": result,
        "output": output.strip(),
    }


def add_global_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
