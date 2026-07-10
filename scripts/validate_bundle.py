#!/usr/bin/env python3
"""Repository-local validation for the npm bundle and dual plugin manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "project-intelligence"


def load(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return payload


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    codex = load(PLUGIN / ".codex-plugin" / "plugin.json")
    claude = load(PLUGIN / ".claude-plugin" / "plugin.json")
    codex_marketplace = load(ROOT / ".agents" / "plugins" / "marketplace.json")
    claude_marketplace = load(ROOT / ".claude-plugin" / "marketplace.json")
    require(codex.get("name") == "project-intelligence", "Invalid Codex plugin name")
    require(claude.get("name") == "project-intelligence", "Invalid Claude plugin name")
    require(isinstance(codex.get("skills"), str), "Codex manifest must declare skills")
    require(any(item.get("name") == "project-intelligence" for item in codex_marketplace.get("plugins", [])), "Codex marketplace entry missing")
    require(any(item.get("name") == "project-intelligence" for item in claude_marketplace.get("plugins", [])), "Claude marketplace entry missing")
    skill_paths = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    require(bool(skill_paths), "No skills found")
    for path in skill_paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        require(lines[:1] == ["---"], f"Missing frontmatter: {path}")
        try:
            end = lines.index("---", 1)
        except ValueError as exc:
            raise SystemExit(f"Unclosed frontmatter: {path}") from exc
        fields = {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in lines[1:end] if ":" in line}
        require(fields.get("name") == path.parent.name, f"Skill name mismatch: {path}")
        require(bool(fields.get("description")), f"Skill description missing: {path}")
    print(f"Bundle validation passed: {len(skill_paths)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
