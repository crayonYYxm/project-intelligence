from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GENERIC_PATH_PARTS = {
    "src", "app", "apps", "lib", "libs", "packages", "modules", "module", "main",
    "java", "kotlin", "python", "javascript", "typescript", "resources", "components",
    "pages", "services", "controllers", "api", "routes", "router", "common", "shared",
}
MODULE_MARKERS = {"api", "components", "pages", "routes", "router", "services", "domain", "modules", "features"}


def load_json_checked(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {}, str(exc)
    except json.JSONDecodeError as exc:
        return {}, f"JSON 格式错误：{exc.lineno}:{exc.colno} {exc.msg}"
    if not isinstance(payload, dict):
        return {}, "根节点不是 JSON 对象"
    return payload, None


def gitnexus_summary(root: Path) -> dict[str, Any]:
    directory = root / ".gitnexus"
    if not directory.is_dir():
        return {"status": "missing", "path": ".gitnexus", "reason": "未找到索引目录"}
    meta_path = next((path for path in (directory / "meta.json", directory / "gitnexus.json") if path.is_file()), None)
    if meta_path is None:
        return {"status": "invalid", "path": ".gitnexus", "reason": "缺少 meta.json/gitnexus.json"}
    meta, error = load_json_checked(meta_path)
    if error:
        return {"status": "invalid", "path": meta_path.relative_to(root).as_posix(), "reason": error}
    stats = meta.get("stats", {}) if isinstance(meta.get("stats"), dict) else {}
    graph_capability = meta.get("capabilities", {}).get("graph", {}) if isinstance(meta.get("capabilities"), dict) else {}
    counts = {name: int(stats.get(name) or 0) for name in ("files", "nodes", "edges", "communities", "processes")}
    graph_ready = graph_capability.get("status") == "available" or (counts["nodes"] > 0 and counts["edges"] > 0)
    if not graph_ready:
        return {
            "status": "invalid",
            "path": meta_path.relative_to(root).as_posix(),
            "reason": "索引元数据存在，但没有可用图关系",
            "stats": counts,
        }
    return {
        "status": "present",
        "path": meta_path.relative_to(root).as_posix(),
        "schemaVersion": meta.get("schemaVersion"),
        "indexedCommit": meta.get("lastCommit"),
        "stats": counts,
        "capabilities": {
            "graph": graph_capability.get("status") or "available",
            "fts": meta.get("capabilities", {}).get("fts", {}).get("status") if isinstance(meta.get("capabilities"), dict) else None,
            "vectorSearch": meta.get("capabilities", {}).get("vectorSearch", {}).get("status") if isinstance(meta.get("capabilities"), dict) else None,
        },
    }


def understand_summary(root: Path) -> dict[str, Any]:
    path = root / ".understand-anything" / "knowledge-graph.json"
    if not path.is_file():
        return {"status": "missing", "path": ".understand-anything/knowledge-graph.json", "reason": "未找到知识图谱"}
    graph, error = load_json_checked(path)
    if error:
        return {"status": "invalid", "path": path.relative_to(root).as_posix(), "reason": error}
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list) or not nodes:
        return {
            "status": "invalid",
            "path": path.relative_to(root).as_posix(),
            "reason": "图谱必须包含非空 nodes 数组和 edges 数组",
        }
    return {
        "status": "present",
        "path": path.relative_to(root).as_posix(),
        "nodes": len(nodes),
        "edges": len(edges),
        "graph": graph,
    }


def detect_graph_sources(root: Path) -> list[dict[str, Any]]:
    gitnexus = gitnexus_summary(root)
    understand = understand_summary(root)
    return [
        {
            "name": "GitNexus",
            "path": gitnexus.get("path", ".gitnexus"),
            "role": "符号调用、影响、变更风险",
            **{key: value for key, value in gitnexus.items() if key not in {"path", "graph"}},
        },
        {
            "name": "Understand-Anything",
            "path": understand.get("path", ".understand-anything/knowledge-graph.json"),
            "role": "架构、模块、领域流、入职",
            **{key: value for key, value in understand.items() if key not in {"path", "graph"}},
        },
    ]


def meaningful_domain(path: str, tags: list[str] | None = None) -> str | None:
    candidates = [part for part in Path(path).parts[:-1] if part.lower() not in GENERIC_PATH_PARTS and not part.startswith(".")]
    if candidates:
        return candidates[-1]
    clean_tags = [str(tag).strip() for tag in (tags or []) if str(tag).strip() and str(tag).lower() not in GENERIC_PATH_PARTS]
    return clean_tags[0] if clean_tags else None


def path_prefix(path: str, depth: int = 4) -> str:
    parts = Path(path).parts
    return Path(*parts[:depth]).as_posix() if len(parts) > depth else Path(path).as_posix()


def understand_graph_summary(root: Path) -> dict[str, Any]:
    inspected = understand_summary(root)
    if inspected.get("status") != "present":
        return {"status": inspected.get("status"), "reason": inspected.get("reason"), "nodes": 0, "edges": 0, "domains": [], "keyModules": [], "topPathPrefixes": []}
    graph = inspected.pop("graph")
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    domain_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    key_modules: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        path = str(node.get("filePath") or node.get("id") or "")
        summary = str(node.get("summary") or "")
        tags = node.get("tags") if isinstance(node.get("tags"), list) else []
        if not path:
            continue
        domain = meaningful_domain(path, tags)
        if domain:
            domain_buckets[domain].append({"path": path, "summary": summary, "tags": tags[:8]})
        if any(part.lower() in MODULE_MARKERS for part in Path(path).parts):
            key_modules.append({"path": path, "name": node.get("name") or Path(path).name, "summary": summary, "tags": tags[:8]})
    domains = [
        {
            "name": name,
            "count": len(items),
            "paths": [item["path"] for item in items[:12]],
            "summaries": [item["summary"] for item in items if item.get("summary")][:5],
        }
        for name, items in sorted(domain_buckets.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    prefixes = Counter(path_prefix(str(node.get("filePath") or node.get("id") or "")) for node in nodes if isinstance(node, dict) and (node.get("filePath") or node.get("id"))).most_common(20)
    return {
        "status": "present",
        "nodes": len(nodes),
        "edges": len(edges),
        "domains": domains[:20],
        "keyModules": key_modules[:50],
        "topPathPrefixes": prefixes,
    }
