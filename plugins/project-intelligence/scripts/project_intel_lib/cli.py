from __future__ import annotations

import argparse
from typing import Any


def extract_global_json(argv: list[str]) -> tuple[list[str], bool]:
    return [item for item in argv if item != "--json"], "--json" in argv


def json_envelope(command: str, exit_code: int, result: Any = None, output: str = "") -> dict[str, Any]:
    ok = exit_code == 0
    error = None
    if not ok:
        if isinstance(result, dict) and "error" in result:
            message = str(result.get("error") or "command failed")
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
