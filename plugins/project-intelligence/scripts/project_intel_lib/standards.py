from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


GENERIC_SEGMENTS = {
    "src", "app", "apps", "packages", "modules", "components", "pages", "services",
    "controllers", "api", "common", "shared", "utils", "lib", "main", "java", "resources",
}


def project_domain_candidates(frontend: dict[str, Any], backend: dict[str, Any], graph: dict[str, Any]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    locations: dict[str, list[str]] = {}
    paths: list[str] = []
    for key in ("components", "hooks", "routes", "apiModules", "stores"):
        paths.extend(str(item.get("path") or "") for item in frontend.get(key, []) if isinstance(item, dict))
    for key in ("apis", "services", "dataTypes", "repositories"):
        paths.extend(str(item.get("path") or "") for item in backend.get(key, []) if isinstance(item, dict))
    for path in paths:
        parts = [part for part in Path(path).parts[:-1] if part.lower() not in GENERIC_SEGMENTS and not part.startswith(".")]
        if not parts:
            continue
        name = parts[-1]
        counts[name] += 1
        locations.setdefault(name, []).append(path)
    for item in graph.get("understandSummary", {}).get("domains", []):
        if not isinstance(item, dict) or not item.get("name"):
            continue
        name = str(item["name"])
        counts[name] += int(item.get("count") or 0)
        locations.setdefault(name, []).extend(str(path) for path in item.get("paths", []))
    return [
        {"name": name, "count": count, "paths": list(dict.fromkeys(locations.get(name, [])))[:12], "source": "project-derived"}
        for name, count in counts.most_common(20)
        if count >= 2
    ]
