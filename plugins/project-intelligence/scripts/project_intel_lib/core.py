from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


GENERATED_AGENT_FILES = {"AGENTS.md", "CLAUDE.md"}


def file_signature(path: Path) -> str:
    """Return a cheap signature suitable for repository-local scan caching."""
    try:
        stat = path.stat()
    except OSError:
        return "missing"
    raw = f"{stat.st_size}:{stat.st_mtime_ns}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


class IncrementalScanCache:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        payload = payload if isinstance(payload, dict) else {}
        entries = payload.get("entries", {})
        self.entries: dict[str, dict[str, Any]] = entries if isinstance(entries, dict) else {}
        self.seen: set[str] = set()

    @classmethod
    def load(cls, path: Path) -> "IncrementalScanCache":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        return cls(payload)

    def get(self, rel_path: str, namespace: str, signature: str) -> Any | None:
        self.seen.add(rel_path)
        entry = self.entries.get(rel_path, {})
        if entry.get("signature") != signature:
            return None
        return copy.deepcopy(entry.get(namespace))

    def put(self, rel_path: str, namespace: str, signature: str, value: Any) -> None:
        self.seen.add(rel_path)
        entry = self.entries.setdefault(rel_path, {})
        if entry.get("signature") != signature:
            entry.clear()
            entry["signature"] = signature
        entry[namespace] = copy.deepcopy(value)

    def payload(self) -> dict[str, Any]:
        retained = {path: self.entries[path] for path in sorted(self.seen) if path in self.entries}
        return {"schemaVersion": 1, "entries": retained}


def sanitize_tooling(tooling: dict[str, Any]) -> dict[str, Any]:
    """Return the portable subset safe to persist in committed project facts."""
    optional = tooling.get("optional", {}) if isinstance(tooling, dict) else {}
    return {
        "schemaVersion": 1,
        "required": [
            {"name": item.get("name"), "status": item.get("status")}
            for item in tooling.get("required", [])
            if isinstance(item, dict)
        ],
        "optional": {
            "git": {"status": optional.get("git", {}).get("status")},
            "node": {"status": optional.get("node", {}).get("status")},
            "packageManagers": [
                {
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "selected": bool(item.get("selected")),
                }
                for item in optional.get("packageManagers", [])
                if isinstance(item, dict)
            ],
            "gitnexus": {
                "status": optional.get("gitnexus", {}).get("status"),
                "indexPath": optional.get("gitnexus", {}).get("indexPath"),
                "runnerPath": optional.get("gitnexus", {}).get("runnerPath"),
            },
            "understandAnything": {
                "status": optional.get("understandAnything", {}).get("status"),
                "graphPath": optional.get("understandAnything", {}).get("graphPath"),
            },
            "qualityTools": [
                {
                    "kind": item.get("kind"),
                    "status": item.get("status"),
                    "command": item.get("command"),
                }
                for item in optional.get("qualityTools", [])
                if isinstance(item, dict)
            ],
        },
        "recommendedActions": [
            {
                "tool": item.get("tool"),
                "reason": item.get("reason"),
                "command": item.get("command"),
                "canRun": bool(item.get("canRun")),
            }
            for item in tooling.get("recommendedActions", [])
            if isinstance(item, dict)
        ],
        "followUpActions": [
            {
                "tool": item.get("tool"),
                "command": item.get("command"),
                "refreshCommand": item.get("refreshCommand"),
                "fallbackRefreshCommand": item.get("fallbackRefreshCommand"),
                "canRun": bool(item.get("canRun")),
            }
            for item in tooling.get("followUpActions", [])
            if isinstance(item, dict)
        ],
    }
