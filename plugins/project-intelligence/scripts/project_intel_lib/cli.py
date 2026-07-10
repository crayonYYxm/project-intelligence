from __future__ import annotations

import argparse
from typing import Any


def extract_global_json(argv: list[str]) -> tuple[list[str], bool]:
    return [item for item in argv if item != "--json"], "--json" in argv


def json_envelope(command: str, exit_code: int, result: Any = None, output: str = "") -> dict[str, Any]:
    return {
        "command": command,
        "status": "ok" if exit_code == 0 else "failed",
        "exitCode": exit_code,
        "result": result,
        "output": output.strip(),
    }


def add_global_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
