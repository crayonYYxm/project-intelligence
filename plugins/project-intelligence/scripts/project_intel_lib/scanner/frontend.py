from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from ..core import IncrementalScanCache, file_signature


FRONTEND_SUFFIXES = {".vue", ".tsx", ".jsx", ".ts", ".js"}
STYLE_SUFFIXES = {".scss", ".css", ".less", ".sass"}


def extract_object_argument_blocks(text: str, function_name: str) -> list[str]:
    blocks: list[str] = []
    pattern = re.compile(rf"\b{re.escape(function_name)}\s*\(\s*{{")
    for match in pattern.finditer(text):
        start = match.end() - 1
        depth = 0
        quote = ""
        escaped = False
        for idx in range(start, len(text)):
            char = text[idx]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = ""
                continue
            if char in {"'", '"', "`"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start + 1 : idx])
                    break
    return blocks


def split_top_level_items(block: str) -> list[str]:
    items: list[str] = []
    start = depth = 0
    quote = ""
    escaped = False
    for idx, char in enumerate(block):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            item = block[start:idx].strip()
            if item:
                items.append(item)
            start = idx + 1
    tail = block[start:].strip()
    if tail:
        items.append(tail)
    return items


def top_level_object_keys(block: str) -> list[str]:
    names: list[str] = []
    for item in split_top_level_items(block):
        match = re.match(r"(?:['\"]([^'\"]+)['\"]|([A-Za-z_$][\w$]*))\??\s*:", item)
        if match:
            names.append(match.group(1) or match.group(2))
    return names


def extract_vue_props(text: str) -> list[str]:
    names: set[str] = set()
    for block in re.findall(r"defineProps\s*<\s*{([^}]*)}", text, re.S):
        names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:", block))
    for type_name in re.findall(r"defineProps\s*<\s*([A-Za-z_$][\w$]*)\s*>", text):
        pattern = rf"(?:interface\s+{re.escape(type_name)}|type\s+{re.escape(type_name)}\s*=)\s*{{([^}}]*)}}"
        for block in re.findall(pattern, text, re.S):
            names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:", block))
    for block in extract_object_argument_blocks(text, "defineProps"):
        names.update(top_level_object_keys(block))
    return sorted(names)


def extract_emits(text: str) -> list[str]:
    names: set[str] = set()
    for block in re.findall(r"defineEmits\s*\(\s*\[([^\]]*)]", text, re.S):
        names.update(re.findall(r"['\"]([^'\"]+)['\"]", block))
    for block in re.findall(r"defineEmits\s*\(\s*{([^}]*)}", text, re.S):
        for hit in re.findall(r"(?:^|[,{\s])(?:['\"]([^'\"]+)['\"]|([A-Za-z_$][\w$]*))\s*:", block):
            names.update(part for part in hit if part)
    for block in re.findall(r"defineEmits\s*<([^>]*)>", text, re.S):
        names.update(re.findall(r"['\"]([A-Za-z0-9:_-]+)['\"]", block))
    return sorted(name for name in names if re.match(r"^[A-Za-z][A-Za-z0-9:_-]*$", name))


def extract_slots(text: str) -> list[str]:
    expanded: set[str] = {slot or "default" for slot in re.findall(r"<slot(?:\s+name=['\"]([^'\"]+)['\"])?", text)}
    for block in re.findall(r"defineSlots\s*<\s*{([^}]*)}", text, re.S):
        expanded.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*[:(]", block))
    return sorted(expanded)


def extract_expose(text: str) -> list[str]:
    names: set[str] = set()
    for block in extract_object_argument_blocks(text, "defineExpose"):
        for item in split_top_level_items(block):
            match = re.match(r"([A-Za-z_$][\w$]*)", item)
            if match:
                names.add(match.group(1))
    return sorted(names)


def extract_dependencies(text: str) -> list[str]:
    values = re.findall(r"(?:import\s+[^;]*?\s+from\s+|import\s*\(|require\s*\()\s*['\"]([^'\"]+)['\"]", text)
    return sorted(dict.fromkeys(values))[:50]


def component_scope(path: str) -> str:
    if path.startswith(("src/components/", "components/")):
        return "public"
    if "/components/" in path:
        return "page-local"
    if path.startswith(("src/pages/", "pages/", "app/")):
        return "page"
    return "module"


def extract_service_prefixes(text: str) -> list[dict[str, str]]:
    prefixes = []
    for name, value in re.findall(r"\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*['\"]([^'\"]*/[^'\"]*)['\"]", text):
        if any(token in value for token in ("service", "openapi", "api", "adapt")):
            prefixes.append({"name": name, "value": value.rstrip("/") or value})
    return prefixes[:20]


def extract_api_endpoints(text: str) -> list[str]:
    endpoints: list[str] = []
    pattern = r"(?<![\w$])(?:\$post|\$get|\$put|\$delete|request|fetch|axios)\s*\(\s*(`([^`]+)`|['\"]([^'\"]+)['\"])"
    for match in re.finditer(pattern, text):
        raw = match.group(2) or match.group(3) or ""
        if raw:
            endpoints.append(raw)
    endpoints.extend(re.findall(r"['\"](/[^'\"]*(?:service|openapi|api|adapt)[^'\"]*)['\"]", text))
    return sorted(dict.fromkeys(endpoints))[:40]


def extract_exported_functions(text: str) -> list[str]:
    names = re.findall(r"\bexport\s+const\s+([A-Za-z_$][\w$]*)\s*=", text)
    names += re.findall(r"\bexport\s+function\s+([A-Za-z_$][\w$]*)\s*\(", text)
    return sorted(dict.fromkeys(names))[:80]


def extract_react_props(text: str) -> list[str]:
    names: set[str] = set()
    for block in re.findall(r"(?:interface|type)\s+\w*Props\w*\s*(?:=\s*)?{([^}]*)}", text, re.S):
        names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:", block))
    blocks = re.findall(r"function\s+[A-Z][A-Za-z0-9_]*\s*\(\s*{([^}]*)}", text, re.S)
    blocks += re.findall(r"=\s*\(\s*{([^}]*)}\s*\)\s*=>", text, re.S)
    for block in blocks:
        names.update(name.strip().split(":")[0].strip() for name in block.split(",") if name.strip())
    return sorted(name for name in names if re.match(r"^[A-Za-z_$][\w$]*$", name))


def route_module_info(text: str) -> dict[str, Any]:
    routes = sorted(set(re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", text)))
    return {
        "baseUrls": sorted(set(re.findall(r"baseUrl\s*:\s*['\"]([^'\"]+)['\"]", text))),
        "routes": routes,
        "routeCount": len(routes),
        "customNavigationCount": len(re.findall(r"navigationStyle\s*:\s*['\"]custom['\"]", text)),
        "pluginProviders": sorted(set(re.findall(r"provider\s*:\s*['\"]([^'\"]+)['\"]", text))),
        "titlesSample": re.findall(r"navigationBarTitleText\s*:\s*['\"]([^'\"]+)['\"]", text)[:20],
    }


PATTERN_DEFS = {
    "table": [r"<(el-table|ProTable)\b", r"\bcolumns\s*=", r"type:\s*['\"]selection"],
    "pagination": [r"<(el-pagination|Pagination)\b", r"page(Size|Num|Index)", r"usePagination"],
    "dialog-drawer": [r"<(el-dialog|el-drawer|Drawer|nut-popup|dx-dialog)\b", r"v-model:visible", r"defineEmits|showModal"],
    "search-form": [r"<el-form\b", r"handle(Search|Reset)", r"search(Form|Params)"],
    "permission": [r"\b(permission|auth|v-permission|hasPermission)\b"],
    "export-download": [r"\b(export|download|导出)\b"],
}


def scan_frontend_file(path: Path, rel_path: str, text: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    lower = rel_path.lower()
    facts: dict[str, Any] = {key: [] for key in ("components", "hooks", "routes", "apiModules", "stores", "styles")}
    if suffix in {".vue", ".tsx", ".jsx"} and ("/components/" in lower or suffix == ".vue"):
        name = path.stem if path.stem != "index" else path.parent.name
        facts["components"].append(
            {
                "name": name,
                "path": rel_path,
                "kind": "vue" if suffix == ".vue" else "react",
                "scope": component_scope(rel_path),
                "props": extract_vue_props(text) if suffix == ".vue" else extract_react_props(text),
                "emits": extract_emits(text) if suffix == ".vue" else [],
                "slots": extract_slots(text) if suffix == ".vue" else [],
                "expose": extract_expose(text) if suffix == ".vue" else [],
                "dependencies": extract_dependencies(text),
                "level": "candidate",
            }
        )
    if re.search(r"(^|/)use[A-Z][A-Za-z0-9_]*\.(ts|tsx|js|jsx)$", rel_path):
        facts["hooks"].append({"name": path.stem, "path": rel_path, "exports": extract_exported_functions(text), "dependencies": extract_dependencies(text), "level": "candidate"})
    if "/router" in lower or "route" in path.stem.lower():
        route_info = route_module_info(text)
        if route_info["routes"]:
            facts["routes"].append({"path": rel_path, **route_info})
    if "/api/" in lower or re.search(r"\b(axios|fetch|request)\s*[.(]", text):
        facts["apiModules"].append(
            {
                "path": rel_path,
                "signals": sorted(set(re.findall(r"\b(axios|fetch|request)\b", text))),
                "wrappers": sorted(set(re.findall(r"(?<![\w$])(\$post|\$get|\$put|\$delete|axios|fetch|request)\s*\(", text))),
                "endpoints": extract_api_endpoints(text),
                "servicePrefixes": extract_service_prefixes(text),
                "exports": extract_exported_functions(text),
            }
        )
    if "/stores/" in lower and suffix in {".ts", ".js"}:
        facts["stores"].append({"path": rel_path, "definesStore": bool(re.search(r"\bdefineStore\s*\(", text)), "exports": extract_exported_functions(text)})
    if suffix in STYLE_SUFFIXES | {".vue"}:
        hardcoded = re.findall(r"#[0-9a-fA-F]{3,8}|\b\d+px\b", text)
        if hardcoded:
            facts["styles"].append({"path": rel_path, "hardcodedValuesSample": hardcoded[:20], "count": len(hardcoded)})
    facts["patterns"] = [name for name, regexes in PATTERN_DEFS.items() if sum(1 for regex in regexes if re.search(regex, text)) >= 2]
    return facts


def scan_frontend(
    root: Path,
    files: list[Path],
    *,
    read_text: Callable[[Path], str],
    rel: Callable[[Path, Path], str],
    cache: IncrementalScanCache | None = None,
) -> dict[str, Any]:
    cache = cache or IncrementalScanCache()
    groups = {key: [] for key in ("components", "hooks", "routes", "apiModules", "stores", "styles")}
    patterns: Counter[str] = Counter()
    locations: dict[str, list[str]] = defaultdict(list)
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in FRONTEND_SUFFIXES | STYLE_SUFFIXES:
            continue
        rel_path = rel(root, path)
        signature = file_signature(path)
        facts = cache.get(rel_path, "frontend", signature)
        if facts is None:
            facts = scan_frontend_file(path, rel_path, read_text(path))
            cache.put(rel_path, "frontend", signature, facts)
        for key in groups:
            groups[key].extend(facts.get(key, []))
        for name in facts.get("patterns", []):
            patterns[name] += 1
            locations[name].append(rel_path)
    groups["redundancyCandidates"] = [
        {
            "type": "frontend-pattern",
            "name": name,
            "count": count,
            "locations": locations[name][:20],
            "level": "candidate",
            "recommendation": "审查重复使用是否应复用或抽取为组件/Hook；默认不阻塞。",
        }
        for name, count in patterns.items()
        if count >= 3
    ]
    groups["scanMode"] = "regex-fallback"
    return groups
