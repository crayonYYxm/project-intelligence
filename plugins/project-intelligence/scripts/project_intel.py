#!/usr/bin/env python3
"""Project Intelligence CLI.

This v1 intentionally avoids cgraphx. It creates a repository-local
.project-intel directory with lightweight project facts, standards, knowledge,
reports, and optional references to GitNexus / Understand-Anything artifacts.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VERSION = "0.1.0"
EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    ".claude",
    ".cgraphx",
    ".project-intel",
    ".project-intel/cache",
    ".project-intel/tmp",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "target",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
}
TEXT_SUFFIXES = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".java",
    ".kt",
    ".py",
    ".go",
    ".rs",
    ".scss",
    ".sass",
    ".css",
    ".less",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".xml",
    ".properties",
}
FRONTEND_SUFFIXES = {".vue", ".tsx", ".jsx", ".ts", ".js"}
BACKEND_SUFFIXES = {".java", ".kt", ".py", ".go", ".ts", ".js"}


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def run(cmd: list[str], cwd: Path, timeout: int = 30) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def run_shell(command: str, cwd: Path, timeout: int = 120) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            shell=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as exc:
        return 124, "", str(exc)


def read_text(path: Path, max_bytes: int = 500_000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="ignore")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def project_root(arg: str | None) -> Path:
    root = Path(arg or os.getcwd()).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Project path is not a directory: {root}")
    return root


def project_dir(root: Path) -> Path:
    return root / ".project-intel"


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def is_excluded(root: Path, path: Path) -> bool:
    parts = path.relative_to(root).parts if path.is_absolute() else path.parts
    joined = "/".join(parts)
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    return any(joined.startswith(ex + "/") or joined == ex for ex in EXCLUDED_DIRS)


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if is_excluded(root, path):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def git_info(root: Path) -> dict[str, Any]:
    code, commit, _ = run(["git", "rev-parse", "HEAD"], root)
    code2, branch, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    code3, status, _ = run(["git", "status", "--porcelain"], root)
    return {
        "commit": commit if code == 0 else None,
        "branch": branch if code2 == 0 else None,
        "dirty": bool(status) if code3 == 0 else None,
    }


def detect_package(root: Path) -> dict[str, Any]:
    package = load_json(root / "package.json", {})
    deps = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(package.get(key, {}) or {})
    frameworks: list[str] = []
    for name, markers in {
        "Vue": ["vue", "@vitejs/plugin-vue", "nuxt"],
        "React": ["react", "next", "@vitejs/plugin-react"],
        "Vite": ["vite"],
        "NestJS": ["@nestjs/core", "@nestjs/common"],
        "Express": ["express"],
        "Koa": ["koa"],
        "Fastify": ["fastify"],
        "TypeScript": ["typescript"],
        "Element Plus": ["element-plus"],
        "Pinia": ["pinia"],
        "Vue Router": ["vue-router"],
        "Redux": ["redux", "@reduxjs/toolkit"],
    }.items():
        if any(marker in deps for marker in markers):
            frameworks.append(name)
    backend_files = {
        "Java/Spring": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "Python": ["pyproject.toml", "requirements.txt", "manage.py"],
        "Go": ["go.mod"],
        "Rust": ["Cargo.toml"],
    }
    for name, markers in backend_files.items():
        if any((root / marker).exists() for marker in markers):
            frameworks.append(name)
    return {
        "packageName": package.get("name"),
        "scripts": package.get("scripts", {}),
        "frameworks": sorted(set(frameworks)),
        "hasPackageJson": bool(package),
    }


def detect_quality_commands(root: Path, package: dict[str, Any]) -> list[dict[str, Any]]:
    scripts = package.get("scripts", {}) or {}
    commands: list[dict[str, Any]] = []
    aliases = {
        "lint": ["lint", "lint:eslint", "eslint"],
        "type-check": ["type-check", "typecheck", "check-types", "vue-tsc", "tsc"],
        "format-check": ["format:check", "prettier:check", "check:format"],
        "style-check": ["stylelint", "lint:style", "style:check"],
    }
    npm = "pnpm" if (root / "pnpm-lock.yaml").exists() else "yarn" if (root / "yarn.lock").exists() else "npm"
    for kind, names in aliases.items():
        for name in names:
            if name in scripts:
                commands.append({"kind": kind, "command": f"{npm} run {name}", "source": "package.json"})
                break
    if not any(cmd["kind"] == "lint" for cmd in commands):
        if any((root / name).exists() for name in ("eslint.config.js", "eslint.config.mjs", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json")):
            commands.append({"kind": "lint", "command": "npx eslint .", "source": "inferred"})
    if not any(cmd["kind"] == "type-check" for cmd in commands):
        if (root / "tsconfig.json").exists():
            if any("vue" in fw.lower() for fw in package.get("frameworks", [])):
                commands.append({"kind": "type-check", "command": "npx vue-tsc --noEmit", "source": "inferred"})
            else:
                commands.append({"kind": "type-check", "command": "npx tsc --noEmit", "source": "inferred"})
    if not any(cmd["kind"] == "style-check" for cmd in commands):
        if any((root / name).exists() for name in ("stylelint.config.js", "stylelint.config.cjs", ".stylelintrc", ".stylelintrc.js")):
            commands.append({"kind": "style-check", "command": "npx stylelint \"**/*.{css,scss,vue}\"", "source": "inferred"})
    if not any(cmd["kind"] == "format-check" for cmd in commands):
        if any((root / name).exists() for name in ("prettier.config.js", "prettier.config.cjs", ".prettierrc", ".prettierrc.js", ".prettierrc.json")):
            commands.append({"kind": "format-check", "command": "npx prettier --check .", "source": "inferred"})
    return commands


def extract_vue_props(text: str) -> list[str]:
    names: set[str] = set()
    inline_blocks = re.findall(r"defineProps\s*<\s*{([^}]*)}", text, re.S)
    for block in inline_blocks:
        names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:", block))
    for type_name in re.findall(r"defineProps\s*<\s*([A-Za-z_$][\w$]*)\s*>", text):
        pattern = rf"(?:interface\s+{re.escape(type_name)}|type\s+{re.escape(type_name)}\s*=)\s*{{([^}}]*)}}"
        for block in re.findall(pattern, text, re.S):
            names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:", block))
    runtime = re.findall(r"defineProps\s*\(\s*{([^}]*)}", text, re.S)
    for block in runtime:
        names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\s*:", block))
    return sorted(names)


def extract_emits(text: str) -> list[str]:
    names = set(re.findall(r"['\"]([A-Za-z0-9:_-]+)['\"]\s*:", text))
    array_blocks = re.findall(r"defineEmits\s*\(\s*\[([^\]]*)]", text, re.S)
    for block in array_blocks:
        names.update(re.findall(r"['\"]([^'\"]+)['\"]", block))
    return sorted(names)


def extract_react_props(text: str) -> list[str]:
    names: set[str] = set()
    for block in re.findall(r"(?:interface|type)\s+\w*Props\w*\s*(?:=\s*)?{([^}]*)}", text, re.S):
        names.update(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:", block))
    destructured = re.findall(r"function\s+[A-Z][A-Za-z0-9_]*\s*\(\s*{([^}]*)}", text, re.S)
    destructured += re.findall(r"=\s*\(\s*{([^}]*)}\s*\)\s*=>", text, re.S)
    for block in destructured:
        names.update(name.strip().split(":")[0].strip() for name in block.split(",") if name.strip())
    return sorted(name for name in names if re.match(r"^[A-Za-z_$][\w$]*$", name))


def scan_frontend(root: Path, files: list[Path]) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    hooks: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    api_modules: list[dict[str, Any]] = []
    styles: list[dict[str, Any]] = []
    patterns: Counter[str] = Counter()
    pattern_locations: dict[str, list[str]] = defaultdict(list)
    for path in files:
        suffix = path.suffix.lower()
        rp = rel(root, path)
        if suffix not in FRONTEND_SUFFIXES and suffix not in {".scss", ".css", ".less", ".sass"}:
            continue
        text = read_text(path)
        lower = rp.lower()
        if suffix in {".vue", ".tsx", ".jsx"} and ("/components/" in lower or suffix == ".vue"):
            name = path.stem if path.stem != "index" else path.parent.name
            components.append(
                {
                    "name": name,
                    "path": rp,
                    "kind": "vue" if suffix == ".vue" else "react",
                    "props": extract_vue_props(text) if suffix == ".vue" else extract_react_props(text),
                    "emits": extract_emits(text) if suffix == ".vue" else [],
                    "level": "candidate",
                }
            )
        if re.search(r"(^|/)use[A-Z][A-Za-z0-9_]*\.(ts|tsx|js|jsx)$", rp):
            hooks.append({"name": path.stem, "path": rp, "level": "candidate"})
        if "/router" in lower or "route" in path.stem.lower():
            route_hits = re.findall(r"path\s*:\s*['\"]([^'\"]+)['\"]", text)
            if route_hits:
                routes.append({"path": rp, "routes": sorted(set(route_hits))})
        if "/api/" in lower or re.search(r"\b(axios|fetch|request)\s*[.(]", text):
            api_modules.append({"path": rp, "signals": sorted(set(re.findall(r"\b(axios|fetch|request)\b", text)))})
        if suffix in {".scss", ".css", ".less", ".sass", ".vue"}:
            hardcoded = re.findall(r"#[0-9a-fA-F]{3,8}|\b\d+px\b", text)
            if hardcoded:
                styles.append({"path": rp, "hardcodedValuesSample": hardcoded[:20], "count": len(hardcoded)})
        pattern_defs = {
            "table": [r"<(el-table|ProTable)\b", r"\bcolumns\s*=", r"type:\s*['\"]selection"],
            "pagination": [r"<(el-pagination|Pagination)\b", r"page(Size|Num|Index)", r"usePagination"],
            "dialog-drawer": [r"<(el-dialog|el-drawer|Drawer)\b", r"v-model:visible", r"defineEmits"],
            "search-form": [r"<el-form\b", r"handle(Search|Reset)", r"search(Form|Params)"],
            "permission": [r"\b(permission|auth|v-permission|hasPermission)\b"],
            "export-download": [r"\b(export|download|导出)\b"],
        }
        for name, regexes in pattern_defs.items():
            score = sum(1 for regex in regexes if re.search(regex, text))
            if score >= 2:
                patterns[name] += 1
                pattern_locations[name].append(rp)
    redundancy = [
        {
            "type": "frontend-pattern",
            "name": name,
            "count": count,
            "locations": pattern_locations[name][:20],
            "level": "candidate",
            "recommendation": "Review whether repeated usage should reuse or become a component/Hook; do not block by default.",
        }
        for name, count in patterns.items()
        if count >= 3
    ]
    return {
        "components": components,
        "hooks": hooks,
        "routes": routes,
        "apiModules": api_modules,
        "styles": styles,
        "redundancyCandidates": redundancy,
    }


def scan_backend(root: Path, files: list[Path]) -> dict[str, Any]:
    apis: list[dict[str, Any]] = []
    services: list[dict[str, Any]] = []
    data_types: list[dict[str, Any]] = []
    repositories: list[dict[str, Any]] = []
    configs: list[dict[str, Any]] = []
    entrypoint_candidates: list[dict[str, Any]] = []
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in BACKEND_SUFFIXES and suffix not in {".yaml", ".yml", ".properties", ".xml"}:
            continue
        rp = rel(root, path)
        text = read_text(path)
        lower = rp.lower()
        route_signals = re.findall(
            r"@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|MessageListener|Scheduled)|\b(router|app)\.(get|post|put|delete|use)\s*\(",
            text,
        )
        decorators = re.findall(r"@(Controller|Get|Post|Put|Delete|Patch|Injectable|MessagePattern|Cron)\b", text)
        if route_signals or decorators:
            endpoints = re.findall(r"@(?:RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)\s*\(([^)]*)\)", text)
            endpoints += re.findall(r"\b(?:router|app)\.(?:get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]", text)
            apis.append({"path": rp, "signals": sorted(set(str(s) for s in route_signals + decorators))[:20], "endpoints": endpoints[:20]})
        if re.search(r"(Service|Manager|UseCase|Facade)\.(java|kt|ts|js|py)$", rp) or "@Service" in text or "@Injectable" in text:
            services.append({"name": path.stem, "path": rp})
        if re.search(r"(DTO|Dto|VO|Entity|Model|Schema)\.(java|kt|ts|js|py)$", rp) or re.search(r"@(Entity|Table|Column)\b", text):
            data_types.append({"name": path.stem, "path": rp})
        if re.search(r"(Repository|Mapper|Dao|DAO)\.(java|kt|ts|js|py)$", rp) or re.search(r"@(Repository|Mapper)\b", text):
            repositories.append({"name": path.stem, "path": rp})
        if suffix in {".yaml", ".yml", ".properties", ".xml"} or "/config" in lower:
            configs.append({"path": rp})
        if not (route_signals or decorators) and re.search(r"(handler|endpoint|facade|adapter|action)", lower):
            entrypoint_candidates.append({"path": rp, "reason": "path/name suggests non-standard entrypoint", "level": "candidate"})
    return {
        "apis": apis,
        "services": services,
        "dataTypes": data_types,
        "repositories": repositories,
        "configs": configs,
        "candidateEntrypoints": entrypoint_candidates,
    }


def detect_graph_sources(root: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    if (root / ".gitnexus").exists():
        sources.append({"name": "GitNexus", "path": ".gitnexus", "role": "symbol calls, impact, change risk", "status": "present"})
    else:
        sources.append({"name": "GitNexus", "path": ".gitnexus", "role": "symbol calls, impact, change risk", "status": "missing"})
    ua_graph = root / ".understand-anything" / "knowledge-graph.json"
    if ua_graph.exists():
        graph = load_json(ua_graph, {})
        sources.append(
            {
                "name": "Understand-Anything",
                "path": ".understand-anything/knowledge-graph.json",
                "role": "architecture, modules, domain flow, onboarding",
                "status": "present",
                "nodes": len(graph.get("nodes", []) or []),
                "edges": len(graph.get("edges", []) or []),
            }
        )
    else:
        sources.append({"name": "Understand-Anything", "path": ".understand-anything/knowledge-graph.json", "role": "architecture, modules, domain flow, onboarding", "status": "missing"})
    return sources


def file_index(root: Path, files: list[Path]) -> list[dict[str, Any]]:
    result = []
    for path in files:
        try:
            stat = path.stat()
        except OSError:
            continue
        result.append({"path": rel(root, path), "size": stat.st_size, "mtime": int(stat.st_mtime), "suffix": path.suffix.lower()})
    return result


def build_manifest(root: Path, files: list[Path], package: dict[str, Any], graph_sources: list[dict[str, Any]]) -> dict[str, Any]:
    suffix_counts = Counter(path.suffix.lower() or "<none>" for path in files)
    return {
        "schemaVersion": 1,
        "toolVersion": VERSION,
        "projectRoot": str(root),
        "generatedAt": now_iso(),
        "git": git_info(root),
        "frameworks": package.get("frameworks", []),
        "packageName": package.get("packageName"),
        "fileCount": len(files),
        "suffixCounts": dict(suffix_counts.most_common()),
        "graphSources": graph_sources,
        "notes": [
            "project-intelligence does not read or integrate .cgraphx data.",
            "GitNexus and Understand-Anything are preferred graph sources when available.",
        ],
    }


def default_config(root: Path, package: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "scan": {
            "include": ["src/**", "app/**", "packages/**", "apps/**", "server/**", "client/**"],
            "exclude": sorted(EXCLUDED_DIRS),
        },
        "quality": {"commands": detect_quality_commands(root, package)},
        "backend": {
            "entrypointRules": [
                {"type": "annotation", "pattern": "@RestController|@Controller|@RequestMapping|@GetMapping|@PostMapping|@MessageListener|@Scheduled"},
                {"type": "call", "pattern": "router\\.(get|post|put|delete|use)|app\\.(get|post|put|delete|use)"},
                {"type": "path", "pattern": "**/{controller,handler,endpoint,facade,adapter}/**/*"},
            ]
        },
        "rules": {"hard": [], "preferred": [], "inferred": [], "candidate": []},
    }


def standards_docs(data: dict[str, Any]) -> dict[str, str]:
    frontend = data["frontend"]
    backend = data["backend"]
    config = data["config"]
    quality = config.get("quality", {}).get("commands", [])
    docs = {}
    docs["quality.md"] = f"""# Quality Checks

Rule levels:

- `hard`: confirmed rule that can fail `project-intel check`
- `preferred`: stable project convention
- `inferred`: scanner inference that needs review
- `candidate`: non-blocking suggestion

## Detected Commands

{table(["Kind", "Command", "Source"], [[c.get("kind"), c.get("command"), c.get("source")] for c in quality])}

## Policy

- Prefer existing package scripts over inferred commands.
- Treat redundancy findings as `candidate` until a human upgrades the rule.
- Combine project quality checks with standards and graph context during review.
"""
    docs["frontend.md"] = f"""# Frontend Standards

## Extracted Facts

- Components found: {len(frontend.get("components", []))}
- Hooks found: {len(frontend.get("hooks", []))}
- Route files found: {len(frontend.get("routes", []))}
- API-related modules found: {len(frontend.get("apiModules", []))}
- Redundancy candidates: {len(frontend.get("redundancyCandidates", []))}

## Default Rules

- Reuse existing components and Hooks before adding new ones.
- Use project request/state/style abstractions when they exist.
- Run detected lint/type/style/format checks before final review.
- Treat duplicated table/search/dialog/export/permission patterns as candidates for component or Hook extraction.
"""
    docs["backend.md"] = f"""# Backend Standards

## Extracted Facts

- API/entry modules found: {len(backend.get("apis", []))}
- Services found: {len(backend.get("services", []))}
- DTO/VO/Entity/model files found: {len(backend.get("dataTypes", []))}
- Repository/Mapper files found: {len(backend.get("repositories", []))}
- Candidate non-standard entrypoints: {len(backend.get("candidateEntrypoints", []))}

## Default Rules

- Identify entrypoints through framework adapters, AST/call patterns, and project-specific rules.
- Do not rely only on `Controller` naming.
- Preserve service, data, repository, permission, transaction, and config boundaries.
- Confirm candidate entrypoints before upgrading them to hard standards.
"""
    docs["reuse.md"] = """# Reuse And Redundancy

## Policy

- Search `.project-intel/knowledge` before implementing components, Hooks, API clients, services, or utilities.
- Treat repeated UI, data transformation, validation, request building, and style blocks as `candidate` findings by default.
- Upgrade candidates to `preferred` or `hard` only after human confirmation.
"""
    return docs


def table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None detected._"
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell or "") for cell in row) + " |")
    return "\n".join(out)


def init_project(root: Path, refresh: bool = False) -> dict[str, Any]:
    files = iter_files(root)
    package = detect_package(root)
    graph_sources = detect_graph_sources(root)
    config_path = project_dir(root) / "config.json"
    config = load_json(config_path, None)
    if not config:
        config = default_config(root, package)
    else:
        config.setdefault("quality", {})["commands"] = detect_quality_commands(root, package)
    frontend = scan_frontend(root, files)
    backend = scan_backend(root, files)
    manifest = build_manifest(root, files, package, graph_sources)
    graph = {
        "schemaVersion": 1,
        "generatedAt": now_iso(),
        "sources": graph_sources,
        "summary": {
            "components": len(frontend.get("components", [])),
            "hooks": len(frontend.get("hooks", [])),
            "apis": len(backend.get("apis", [])),
            "services": len(backend.get("services", [])),
            "candidateEntrypoints": len(backend.get("candidateEntrypoints", [])),
        },
    }
    pdir = project_dir(root)
    for sub in ("standards", "knowledge", "graph", "reports", "cache", "tmp"):
        (pdir / sub).mkdir(parents=True, exist_ok=True)
    write_json(pdir / "manifest.json", manifest)
    write_json(pdir / "config.json", config)
    write_json(pdir / "knowledge" / "frontend.json", frontend)
    write_json(pdir / "knowledge" / "backend.json", backend)
    write_json(pdir / "knowledge" / "files.json", file_index(root, files))
    write_json(pdir / "graph" / "project-graph.json", graph)
    for name, text in standards_docs({"frontend": frontend, "backend": backend, "config": config}).items():
        write_text(pdir / "standards" / name, text)
    write_text(pdir / "reports" / ("refresh-report.md" if refresh else "init-report.md"), build_init_report(root, manifest, frontend, backend, config))
    write_text(pdir / "reports" / "redundancy-report.md", build_redundancy_report(frontend))
    ensure_gitignore(root)
    return {"manifest": manifest, "frontend": frontend, "backend": backend, "config": config}


def ensure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    additions = [".project-intel/cache/", ".project-intel/tmp/"]
    existing = read_text(path) if path.exists() else ""
    missing = [item for item in additions if item not in existing]
    if missing:
        with path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write("\n# Project Intelligence cache\n")
            for item in missing:
                handle.write(item + "\n")


def build_init_report(root: Path, manifest: dict[str, Any], frontend: dict[str, Any], backend: dict[str, Any], config: dict[str, Any]) -> str:
    source_rows = [[s.get("name"), s.get("status"), s.get("role"), s.get("path")] for s in manifest.get("graphSources", [])]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    return f"""# Project Intelligence Report

Generated at: `{manifest.get("generatedAt")}`

Project root: `{root}`

## Graph Sources

{table(["Source", "Status", "Role", "Path"], source_rows)}

## Frontend Summary

- Components: {len(frontend.get("components", []))}
- Hooks: {len(frontend.get("hooks", []))}
- API modules: {len(frontend.get("apiModules", []))}
- Redundancy candidates: {len(frontend.get("redundancyCandidates", []))}

## Backend Summary

- APIs / entry modules: {len(backend.get("apis", []))}
- Services: {len(backend.get("services", []))}
- Data types: {len(backend.get("dataTypes", []))}
- Repositories / mappers: {len(backend.get("repositories", []))}
- Candidate entrypoints: {len(backend.get("candidateEntrypoints", []))}

## Quality Commands

{table(["Kind", "Command", "Source"], quality_rows)}
"""


def build_redundancy_report(frontend: dict[str, Any]) -> str:
    rows = [
        [item.get("name"), item.get("count"), ", ".join(item.get("locations", [])[:8]), item.get("level")]
        for item in frontend.get("redundancyCandidates", [])
    ]
    return f"""# Redundancy Candidates

These findings are `candidate` level by default and do not block development.

{table(["Pattern", "Count", "Locations", "Level"], rows)}
"""


def install_claude(root: Path) -> None:
    claude = root / ".claude"
    skills = claude / "skills"
    standards = claude / "standards"
    skills.mkdir(parents=True, exist_ok=True)
    standards.mkdir(parents=True, exist_ok=True)
    write_text(
        claude / "CLAUDE.md",
        """# Project Intelligence

Before project tasks, reviews, component/API questions, or quality checks, inspect `.project-intel/manifest.json` and the relevant files under `.project-intel/standards` and `.project-intel/knowledge`.

Use GitNexus for symbol-level calls/impact when available and Understand-Anything for architecture/domain context when available. Do not read or rely on `.cgraphx`.
""",
    )
    skill_template = """---
name: {name}
description: {description}
---

# {title}

Use `.project-intel` as the project fact source. Start with `.project-intel/manifest.json`, then read only the relevant standards, knowledge JSON, reports, and graph summary.

Do not use `.cgraphx`. Prefer GitNexus for symbol-level impact and Understand-Anything for architecture/domain context when available.
"""
    entries = [
        ("project-task", "Use when implementing a project request and needing reuse, standards, components, APIs, services, or graph context.", "Project Task"),
        ("project-review", "Use when reviewing code changes against project standards, graph impact, quality checks, redundancy, and tests.", "Project Review"),
        ("project-knowledge", "Use when answering questions about project structure, components, APIs, services, modules, standards, or business flows.", "Project Knowledge"),
        ("project-refresh", "Use when updating or initializing project standards, knowledge, graph summaries, and reports.", "Project Refresh"),
        ("project-standards", "Use when querying, explaining, confirming, upgrading, or downgrading project standards and rule levels.", "Project Standards"),
        ("project-quality", "Use when running or interpreting frontend/backend lint, type, format, style, redundancy, and standards checks.", "Project Quality"),
    ]
    for name, desc, title in entries:
        write_text(skills / f"{name}.md", skill_template.format(name=name, description=desc, title=title))
    write_text(standards / "project-intelligence.md", "Project standards are generated under `.project-intel/standards/`.\n")


def run_check(root: Path, run_quality: bool) -> int:
    pdir = project_dir(root)
    manifest = load_json(pdir / "manifest.json", {})
    config = load_json(pdir / "config.json", {})
    frontend = load_json(pdir / "knowledge" / "frontend.json", {})
    backend = load_json(pdir / "knowledge" / "backend.json", {})
    if not manifest:
        init_project(root, refresh=False)
        manifest = load_json(pdir / "manifest.json", {})
        config = load_json(pdir / "config.json", {})
        frontend = load_json(pdir / "knowledge" / "frontend.json", {})
        backend = load_json(pdir / "knowledge" / "backend.json", {})
    quality_results: list[dict[str, Any]] = []
    exit_code = 0
    if run_quality:
        for item in config.get("quality", {}).get("commands", []):
            cmd = item.get("command", "")
            code, out, err = run_shell(cmd, root, timeout=120)
            quality_results.append({"kind": item.get("kind"), "command": cmd, "exitCode": code, "stdout": out[-4000:], "stderr": err[-4000:]})
            if code != 0:
                exit_code = 1
    write_text(pdir / "reports" / "frontend-quality.md", build_quality_report(quality_results, frontend, backend))
    print(f"Project Intelligence check complete: {pdir / 'reports' / 'frontend-quality.md'}")
    return exit_code


def build_quality_report(results: list[dict[str, Any]], frontend: dict[str, Any], backend: dict[str, Any]) -> str:
    rows = [[r.get("kind"), r.get("command"), r.get("exitCode")] for r in results]
    redundancy = frontend.get("redundancyCandidates", [])
    return f"""# Quality Report

## Commands

{table(["Kind", "Command", "Exit"], rows) if rows else "_Quality commands were detected but not run, or no commands were configured._"}

## Redundancy

- Frontend redundancy candidates: {len(redundancy)}
- Backend candidate entrypoints: {len(backend.get("candidateEntrypoints", []))}

Redundancy findings are `candidate` by default and do not fail checks unless promoted by team policy.
"""


def query_project(root: Path, text: str) -> int:
    pdir = project_dir(root)
    if not (pdir / "manifest.json").exists():
        print("No .project-intel found. Run project-intel init first.")
        return 1
    needle = text.lower()
    matches: list[tuple[str, str]] = []
    for path in list((pdir / "standards").glob("*.md")) + list((pdir / "reports").glob("*.md")):
        body = read_text(path)
        if needle in body.lower():
            matches.append((rel(root, path), body[:1200]))
    for path in (pdir / "knowledge").glob("*.json"):
        body = read_text(path)
        if needle in body.lower():
            matches.append((rel(root, path), body[:1200]))
    if not matches:
        print("No direct project-intel matches. Try broader terms or refresh the knowledge base.")
        return 0
    for name, snippet in matches[:10]:
        print(f"\n## {name}\n")
        print(snippet)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="project-intel", description="Project Intelligence CLI")
    parser.add_argument("--project", help="Project root. Defaults to current directory.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Initialize .project-intel")
    sub.add_parser("refresh", help="Refresh .project-intel from current workspace")
    sub.add_parser("install", help="Install Claude-compatible project entrypoints")
    check = sub.add_parser("check", help="Run project intelligence checks")
    check.add_argument("--run-quality", action="store_true", help="Actually run detected lint/type/style/format commands")
    query = sub.add_parser("query", help="Search project intelligence artifacts")
    query.add_argument("text")
    sub.add_parser("version", help="Print version")
    args = parser.parse_args(argv)
    root = project_root(args.project)
    if args.command == "version":
        print(VERSION)
        return 0
    if args.command == "init":
        result = init_project(root, refresh=False)
        print(f"Initialized .project-intel with {result['manifest']['fileCount']} indexed text files.")
        return 0
    if args.command == "refresh":
        result = init_project(root, refresh=True)
        print(f"Refreshed .project-intel with {result['manifest']['fileCount']} indexed text files.")
        return 0
    if args.command == "install":
        install_claude(root)
        print(f"Installed Claude adapters under {root / '.claude'}")
        return 0
    if args.command == "check":
        return run_check(root, args.run_quality)
    if args.command == "query":
        return query_project(root, args.text)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
