#!/usr/bin/env python3
"""Project Intelligence CLI.

This v1 intentionally avoids cgraphx. It creates a repository-local
.project-intel directory with lightweight project facts, standards, knowledge,
reports, and optional references to GitNexus / Understand-Anything artifacts.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
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


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def slugify(value: str) -> str:
    raw = value.strip()
    slug = re.sub(r"[^A-Za-z0-9]+", "-", raw.lower()).strip("-")
    if slug:
        return slug[:64].strip("-")
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8] if raw else "untitled"
    return f"task-{digest}"


def today_slug() -> str:
    return _dt.datetime.now().date().isoformat()


def truncate(value: str, limit: int = 6000) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "\n\n[truncated]"


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
    npm = package_manager(root)
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


def understand_plugin_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "")),
        home / ".understand-anything-plugin",
        home / ".codex" / "understand-anything" / "understand-anything-plugin",
        home / ".opencode" / "understand-anything" / "understand-anything-plugin",
        home / ".pi" / "understand-anything" / "understand-anything-plugin",
        home / "understand-anything" / "understand-anything-plugin",
    ]
    roots = []
    for candidate in candidates:
        if str(candidate) and (candidate / "package.json").exists() and (candidate / "pnpm-workspace.yaml").exists():
            roots.append(candidate)
    return roots


def detect_quality_tool_status(root: Path, commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    configured = []
    for item in commands:
        command = item.get("command", "")
        first = command.split()[0] if command else ""
        if item.get("source") == "package.json":
            configured.append(
                {
                    "kind": item.get("kind"),
                    "command": command,
                    "status": "configured",
                    "detail": "Uses project package script; dependency ownership stays with the project.",
                }
            )
        elif first == "npx":
            configured.append(
                {
                    "kind": item.get("kind"),
                    "command": command,
                    "status": "available" if command_exists("npx") else "missing",
                    "detail": "Requires npx because no project script was found.",
                }
            )
        else:
            configured.append(
                {
                    "kind": item.get("kind"),
                    "command": command,
                    "status": "available" if first and command_exists(first) else "missing",
                    "detail": "Inferred from project config.",
                }
            )
    return configured


def detect_tooling(root: Path, package: dict[str, Any]) -> dict[str, Any]:
    quality_commands = detect_quality_commands(root, package)
    selected_pm = package_manager(root)
    gitnexus_runner = root / ".gitnexus" / "run.cjs"
    gitnexus_index = root / ".gitnexus"
    ua_graph = root / ".understand-anything" / "knowledge-graph.json"
    ua_roots = understand_plugin_roots()
    package_managers = [
        {"name": name, "status": "present" if command_exists(name) else "missing", "selected": name == selected_pm}
        for name in ("pnpm", "npm", "yarn")
    ]
    gitnexus_available = gitnexus_runner.exists() or command_exists("gitnexus") or command_exists("npx")
    gitnexus_status = "present" if gitnexus_index.exists() else "available" if gitnexus_available else "missing"
    understand_status = "present" if ua_graph.exists() else "available" if ua_roots else "missing"
    recommended_actions = []
    if gitnexus_status != "present":
        recommended_actions.append(
            {
                "tool": "GitNexus",
                "reason": "symbol-level calls, impact analysis, PR/change risk",
                "command": "node .gitnexus/run.cjs analyze" if gitnexus_runner.exists() else "npx gitnexus analyze",
                "canRun": gitnexus_runner.exists() or command_exists("gitnexus") or command_exists("npx"),
            }
        )
    if understand_status != "present":
        recommended_actions.append(
            {
                "tool": "Understand-Anything",
                "reason": "architecture overview, module relationships, domain flow, onboarding graph",
                "command": "/understand .",
                "canRun": False,
            }
        )
    if package.get("hasPackageJson") and not command_exists(selected_pm):
        recommended_actions.append(
            {
                "tool": selected_pm,
                "reason": "run project package scripts such as lint/type-check/format-check",
                "command": f"Install {selected_pm}, then run {selected_pm} install",
                "canRun": False,
            }
        )
    return {
        "schemaVersion": 1,
        "generatedAt": now_iso(),
        "required": [
            {"name": "python3", "status": "present" if command_exists("python3") else "missing"},
            {"name": "project-write-access", "status": "present" if os.access(root, os.W_OK) else "missing"},
        ],
        "optional": {
            "git": {"status": "present" if command_exists("git") else "missing"},
            "node": {"status": "present" if command_exists("node") else "missing"},
            "packageManagers": package_managers,
            "gitnexus": {
                "status": gitnexus_status,
                "indexPath": ".gitnexus" if gitnexus_index.exists() else None,
                "runnerPath": ".gitnexus/run.cjs" if gitnexus_runner.exists() else None,
            },
            "understandAnything": {
                "status": understand_status,
                "graphPath": ".understand-anything/knowledge-graph.json" if ua_graph.exists() else None,
                "pluginRoots": [str(path) for path in ua_roots],
            },
            "qualityTools": detect_quality_tool_status(root, quality_commands),
        },
        "recommendedActions": recommended_actions,
    }


def tooling_has_missing_optional(tooling: dict[str, Any]) -> bool:
    return bool(tooling.get("recommendedActions"))


def print_tooling_summary(tooling: dict[str, Any]) -> None:
    actions = tooling.get("recommendedActions", [])
    if not actions:
        print("Project Intelligence tooling check: optional graph and quality tooling look ready.")
        return
    print("Project Intelligence detected optional tools that can improve results:")
    for idx, action in enumerate(actions, start=1):
        runnable = "can run now" if action.get("canRun") else "manual setup needed"
        print(f"{idx}. {action.get('tool')}: {runnable}")
        print(f"   use: {action.get('reason')}")
        print(f"   command: {action.get('command')}")


def setup_missing_tools(root: Path, tooling: dict[str, Any], with_graph: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in tooling.get("recommendedActions", []):
        tool = action.get("tool")
        if tool != "GitNexus":
            results.append({"tool": tool, "status": "skipped", "detail": action.get("command")})
            continue
        if not action.get("canRun"):
            results.append({"tool": tool, "status": "skipped", "detail": "No runnable GitNexus command was detected."})
            continue
        command = action.get("command") or "npx gitnexus analyze"
        code, out, err = run_shell(command, root, timeout=300)
        results.append(
            {
                "tool": tool,
                "status": "ok" if code == 0 else "failed",
                "command": command,
                "exitCode": code,
                "stdout": out[-4000:],
                "stderr": err[-4000:],
            }
        )
    return results


def handle_tooling_setup(root: Path, tooling: dict[str, Any], interactive: bool, setup_missing: bool, with_graph: bool) -> list[dict[str, Any]]:
    if setup_missing or with_graph:
        print_tooling_summary(tooling)
        return setup_missing_tools(root, tooling, with_graph=True)
    if interactive and sys.stdin.isatty() and tooling_has_missing_optional(tooling):
        print_tooling_summary(tooling)
        print("\nChoose an action:")
        print("[1] Install/initialize recommended graph tooling")
        print("[2] Initialize .project-intel only")
        print("[3] Print install commands only")
        print("[4] Cancel")
        choice = input("> ").strip()
        if choice == "1":
            return setup_missing_tools(root, tooling, with_graph=True)
        if choice == "3":
            return []
        if choice == "4":
            raise SystemExit(130)
    elif tooling_has_missing_optional(tooling):
        print_tooling_summary(tooling)
    return []


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


def build_manifest(root: Path, files: list[Path], package: dict[str, Any], graph_sources: list[dict[str, Any]], tooling: dict[str, Any]) -> dict[str, Any]:
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
        "tooling": {
            "node": tooling.get("optional", {}).get("node", {}).get("status"),
            "gitnexus": tooling.get("optional", {}).get("gitnexus", {}).get("status"),
            "understandAnything": tooling.get("optional", {}).get("understandAnything", {}).get("status"),
            "recommendedActions": len(tooling.get("recommendedActions", [])),
        },
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
        "tooling": detect_tooling(root, package),
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


def init_project(root: Path, refresh: bool = False, interactive: bool = False, setup_missing: bool = False, with_graph: bool = False, strict: bool = False) -> dict[str, Any]:
    package = detect_package(root)
    tooling = detect_tooling(root, package)
    setup_results = handle_tooling_setup(root, tooling, interactive=interactive, setup_missing=setup_missing, with_graph=with_graph)
    if setup_results:
        tooling = detect_tooling(root, package)
    files = iter_files(root)
    graph_sources = detect_graph_sources(root)
    config_path = project_dir(root) / "config.json"
    config = load_json(config_path, None)
    if not config:
        config = default_config(root, package)
    else:
        config.setdefault("quality", {})["commands"] = detect_quality_commands(root, package)
        config["tooling"] = tooling
    frontend = scan_frontend(root, files)
    backend = scan_backend(root, files)
    manifest = build_manifest(root, files, package, graph_sources, tooling)
    if strict and with_graph and not any(source.get("status") == "present" for source in graph_sources):
        raise SystemExit("Strict graph initialization requested, but no GitNexus or Understand-Anything graph is present.")
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
    for sub in ("standards", "knowledge", "graph", "reports", "specs", "plans", "maintenance", "hooks", "cache", "tmp"):
        (pdir / sub).mkdir(parents=True, exist_ok=True)
    write_json(pdir / "manifest.json", manifest)
    write_json(pdir / "config.json", config)
    write_json(pdir / "knowledge" / "frontend.json", frontend)
    write_json(pdir / "knowledge" / "backend.json", backend)
    write_json(pdir / "knowledge" / "files.json", file_index(root, files))
    write_json(pdir / "graph" / "project-graph.json", graph)
    for name, text in standards_docs({"frontend": frontend, "backend": backend, "config": config}).items():
        write_text(pdir / "standards" / name, text)
    write_text(pdir / "reports" / ("refresh-report.md" if refresh else "init-report.md"), build_init_report(root, manifest, frontend, backend, config, tooling))
    write_text(pdir / "reports" / "redundancy-report.md", build_redundancy_report(frontend))
    write_text(pdir / "reports" / "tooling-report.md", build_tooling_report(tooling, setup_results))
    ensure_gitignore(root)
    return {"manifest": manifest, "frontend": frontend, "backend": backend, "config": config, "tooling": tooling, "setupResults": setup_results}


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


def build_init_report(root: Path, manifest: dict[str, Any], frontend: dict[str, Any], backend: dict[str, Any], config: dict[str, Any], tooling: dict[str, Any]) -> str:
    source_rows = [[s.get("name"), s.get("status"), s.get("role"), s.get("path")] for s in manifest.get("graphSources", [])]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    action_rows = [[a.get("tool"), a.get("command"), "yes" if a.get("canRun") else "manual"] for a in tooling.get("recommendedActions", [])]
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

## Recommended Tooling Actions

{table(["Tool", "Command", "Runnable"], action_rows)}
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


def build_tooling_report(tooling: dict[str, Any], setup_results: list[dict[str, Any]]) -> str:
    required_rows = [[item.get("name"), item.get("status")] for item in tooling.get("required", [])]
    optional = tooling.get("optional", {})
    pm_rows = [[item.get("name"), item.get("status"), "yes" if item.get("selected") else ""] for item in optional.get("packageManagers", [])]
    quality_rows = [[item.get("kind"), item.get("status"), item.get("command")] for item in optional.get("qualityTools", [])]
    action_rows = [[item.get("tool"), item.get("command"), "yes" if item.get("canRun") else "manual"] for item in tooling.get("recommendedActions", [])]
    setup_rows = [[item.get("tool"), item.get("status"), item.get("command") or item.get("detail"), item.get("exitCode", "")] for item in setup_results]
    return f"""# Tooling Report

Generated at: `{tooling.get("generatedAt")}`

## Required

{table(["Tool", "Status"], required_rows)}

## Optional Runtime

- Git: `{optional.get("git", {}).get("status")}`
- Node: `{optional.get("node", {}).get("status")}`
- GitNexus: `{optional.get("gitnexus", {}).get("status")}`
- Understand-Anything: `{optional.get("understandAnything", {}).get("status")}`

## Package Managers

{table(["Name", "Status", "Selected"], pm_rows)}

## Quality Commands

{table(["Kind", "Status", "Command"], quality_rows)}

## Recommended Actions

{table(["Tool", "Command", "Runnable"], action_rows)}

## Setup Results

{table(["Tool", "Status", "Command/Detail", "Exit"], setup_rows)}

`init` does not silently install tools. It only runs setup when `--setup-missing`, `--with-graph`, or an interactive menu choice authorizes it.
"""


def ensure_initialized(root: Path) -> None:
    if not (project_dir(root) / "manifest.json").exists():
        init_project(root, refresh=False)


def load_project_snapshot(root: Path) -> dict[str, Any]:
    ensure_initialized(root)
    pdir = project_dir(root)
    return {
        "manifest": load_json(pdir / "manifest.json", {}),
        "config": load_json(pdir / "config.json", {}),
        "frontend": load_json(pdir / "knowledge" / "frontend.json", {}),
        "backend": load_json(pdir / "knowledge" / "backend.json", {}),
        "graph": load_json(pdir / "graph" / "project-graph.json", {}),
    }


def spec_filename(title: str, suffix: str) -> str:
    return f"{today_slug()}-{slugify(title)}-{suffix}.md"


def build_spec_doc(root: Path, title: str, requirement: str, snapshot: dict[str, Any]) -> str:
    manifest = snapshot["manifest"]
    config = snapshot["config"]
    frontend = snapshot["frontend"]
    backend = snapshot["backend"]
    graph_rows = [[s.get("name"), s.get("status"), s.get("role")] for s in manifest.get("graphSources", [])]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    return f"""# {title} Spec

Generated at: `{now_iso()}`

## Requirement

{truncate(requirement, 3000)}

## Project Context

- Project root: `{root}`
- Frameworks: {", ".join(manifest.get("frameworks", []) or ["unknown"])}
- Components: {len(frontend.get("components", []))}
- Hooks: {len(frontend.get("hooks", []))}
- API modules: {len(frontend.get("apiModules", []))}
- Backend APIs: {len(backend.get("apis", []))}
- Services: {len(backend.get("services", []))}

## Graph Sources

{table(["Source", "Status", "Role"], graph_rows)}

## Relevant Standards

- Reuse existing components, Hooks, request utilities, services, and domain patterns before adding new abstractions.
- Treat redundancy findings as `candidate` unless promoted to `hard`.
- Do not read or rely on `.cgraphx`.

## Quality Gates

{table(["Kind", "Command", "Source"], quality_rows)}

## Acceptance Criteria

- The implementation satisfies the stated requirement.
- Related project standards and reusable capabilities have been checked.
- Project quality checks are run or explicitly skipped with a reason.
- `.project-intel` is refreshed after the task so new facts and candidates are captured.
"""


def write_spec(root: Path, title: str, requirement: str) -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "specs" / spec_filename(title, "spec")
    write_text(path, build_spec_doc(root, title, requirement, snapshot))
    print(f"Wrote spec: {path}")
    return path


def resolve_input_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def build_plan_doc(root: Path, title: str, spec_path: Path, spec_text: str, snapshot: dict[str, Any]) -> str:
    config = snapshot["config"]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    return f"""# {title} Implementation Plan

Generated at: `{now_iso()}`

Source spec: `{spec_path}`

## Summary

{truncate(spec_text, 2500)}

## Tasks

- [ ] Refresh project context with `project-intel refresh` if the working tree changed since this plan was written.
- [ ] Identify impacted modules, components, Hooks, APIs, services, routes, and standards from `.project-intel`.
- [ ] Check for reusable components, Hooks, services, request utilities, and repeated candidate patterns before writing new code.
- [ ] Add or update focused tests according to the project test setup.
- [ ] Implement the requested behavior while preserving hard standards and existing boundaries.
- [ ] Run `project-intel check` and any relevant project test/type/lint commands.
- [ ] Run `project-intel maintain --task "{title}"` after implementation to refresh knowledge and maintenance reports.

## Quality Commands

{table(["Kind", "Command", "Source"], quality_rows)}
"""


def write_plan(root: Path, title: str, from_spec: str) -> Path:
    spec_path = resolve_input_path(root, from_spec)
    if not spec_path.exists():
        raise SystemExit(f"Spec file does not exist: {spec_path}")
    snapshot = load_project_snapshot(root)
    spec_text = read_text(spec_path)
    path = project_dir(root) / "plans" / spec_filename(title, "plan")
    write_text(path, build_plan_doc(root, title, spec_path, spec_text, snapshot))
    print(f"Wrote plan: {path}")
    return path


def build_task_impact_doc(root: Path, task: str, snapshot: dict[str, Any]) -> str:
    manifest = snapshot["manifest"]
    frontend = snapshot["frontend"]
    backend = snapshot["backend"]
    graph_rows = [[s.get("name"), s.get("status"), s.get("role")] for s in manifest.get("graphSources", [])]
    reuse_rows = []
    for component in frontend.get("components", [])[:20]:
        reuse_rows.append(["component", component.get("name"), component.get("path")])
    for hook in frontend.get("hooks", [])[:20]:
        reuse_rows.append(["hook", hook.get("name"), hook.get("path")])
    for service in backend.get("services", [])[:20]:
        reuse_rows.append(["service", service.get("name"), service.get("path")])
    return f"""# Task Impact

Generated at: `{now_iso()}`

## Task

{truncate(task, 3000)}

## Graph Context

{table(["Source", "Status", "Role"], graph_rows)}

## Reuse Candidates

{table(["Kind", "Name", "Path"], reuse_rows)}

## Standards To Check

- `.project-intel/standards/frontend.md`
- `.project-intel/standards/backend.md`
- `.project-intel/standards/reuse.md`
- `.project-intel/standards/quality.md`

## Completion Hook

After implementation, run:

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "{task[:120].replace('"', "'")}"
```
"""


def write_lifecycle(root: Path, task: str) -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "reports" / "task-impact.md"
    write_text(path, build_task_impact_doc(root, task, snapshot))
    print(f"Wrote task impact report: {path}")
    return path


def build_debug_doc(root: Path, bug: str, snapshot: dict[str, Any]) -> str:
    manifest = snapshot["manifest"]
    config = snapshot["config"]
    frontend = snapshot["frontend"]
    backend = snapshot["backend"]
    graph_rows = [[s.get("name"), s.get("status"), s.get("role")] for s in manifest.get("graphSources", [])]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    candidate_rows = []
    for api in backend.get("apis", [])[:12]:
        candidate_rows.append(["backend-api", "", api.get("path")])
    for service in backend.get("services", [])[:12]:
        candidate_rows.append(["service", service.get("name"), service.get("path")])
    for component in frontend.get("components", [])[:12]:
        candidate_rows.append(["component", component.get("name"), component.get("path")])
    for hook in frontend.get("hooks", [])[:12]:
        candidate_rows.append(["hook", hook.get("name"), hook.get("path")])
    return f"""# Debug Context

Generated at: `{now_iso()}`

## Bug

{truncate(bug, 3000)}

## Systematic Debugging Gate

Do not propose or implement fixes before root cause investigation is complete.

1. Read the full error, stack trace, logs, and failing assertion.
2. Reproduce the bug with exact steps or a failing test.
3. Check recent changes with `git diff`, `git status`, and relevant commits.
4. Trace data/control flow from the symptom back to the original bad input, state, config, or dependency.
5. Compare with a working example in this project.
6. State one hypothesis and test the smallest possible change.
7. Only after root cause is confirmed, add a regression test and fix the source cause.

## Graph Sources

{table(["Source", "Status", "Role"], graph_rows)}

## Candidate Areas To Inspect

{table(["Kind", "Name", "Path"], candidate_rows)}

## Quality And Verification Commands

{table(["Kind", "Command", "Source"], quality_rows)}

## Project Files To Read First

- `.project-intel/manifest.json`
- `.project-intel/standards/*.md`
- `.project-intel/knowledge/frontend.json`
- `.project-intel/knowledge/backend.json`
- `.project-intel/graph/project-graph.json`
- `.project-intel/reports/tooling-report.md`

Use GitNexus for call chains, impact, and changed-code risk when available. Use Understand-Anything for architecture/domain context when available. Do not read or rely on `.cgraphx`.
"""


def write_debug_context(root: Path, bug: str) -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "reports" / "debug-context.md"
    write_text(path, build_debug_doc(root, bug, snapshot))
    print(f"Wrote debug context report: {path}")
    return path


def build_maintenance_report(root: Path, task: str, refresh_result: dict[str, Any], check_exit: int, run_quality: bool) -> str:
    manifest = refresh_result.get("manifest", {})
    frontend = refresh_result.get("frontend", {})
    backend = refresh_result.get("backend", {})
    return f"""# Maintenance Report

Generated at: `{now_iso()}`

## Task

{truncate(task, 3000)}

## Refresh Summary

- Indexed files: {manifest.get("fileCount")}
- Components: {len(frontend.get("components", []))}
- Hooks: {len(frontend.get("hooks", []))}
- Backend APIs: {len(backend.get("apis", []))}
- Services: {len(backend.get("services", []))}
- Candidate frontend redundancy: {len(frontend.get("redundancyCandidates", []))}
- Candidate backend entrypoints: {len(backend.get("candidateEntrypoints", []))}

## Quality

- `project-intel check` exit code: {check_exit}
- Real lint/type/style/format commands run: {"yes" if run_quality else "no"}

Review `.project-intel/reports/frontend-quality.md` for details.
"""


def maintain_project(root: Path, task: str, run_quality: bool) -> int:
    refresh_result = init_project(root, refresh=True)
    check_exit = run_check(root, run_quality=run_quality)
    path = project_dir(root) / "maintenance" / spec_filename(task, "maintenance")
    write_text(path, build_maintenance_report(root, task, refresh_result, check_exit, run_quality))
    print(f"Wrote maintenance report: {path}")
    return check_exit


def hook_script_body(hook_name: str) -> str:
    return f"""#!/bin/sh
# Project Intelligence hook: {hook_name}

if [ "${{PROJECT_INTEL_SKIP_HOOKS:-0}}" = "1" ]; then
  exit 0
fi

SCRIPT="/Users/xumeng/plugins/project-intelligence/scripts/project_intel.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$SCRIPT" ]; then
  PROJECT_INTEL_SKIP_HOOKS=1 python3 "$SCRIPT" maintain --task "git hook: {hook_name}" >/dev/null 2>&1 || true
fi
"""


def write_hook_templates(root: Path) -> list[Path]:
    hooks_dir = project_dir(root) / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for hook_name in ("post-merge", "post-commit", "pre-push"):
        path = hooks_dir / f"{hook_name}.sh"
        write_text(path, hook_script_body(hook_name))
        try:
            path.chmod(0o755)
        except OSError:
            pass
        written.append(path)
    write_text(
        hooks_dir / "README.md",
        """# Project Intelligence Hooks

These hook templates are opt-in. They are not active until `project-intel install --hooks --activate-git-hooks` installs wrappers into `.git/hooks`.

Set `PROJECT_INTEL_SKIP_HOOKS=1` to skip hook execution.
""",
    )
    return written


def activate_git_hooks(root: Path) -> list[dict[str, Any]]:
    git_hooks = root / ".git" / "hooks"
    results = []
    if not git_hooks.exists() or not git_hooks.is_dir():
        return [{"hook": "*", "status": "skipped", "detail": "No .git/hooks directory found."}]
    git_hooks.mkdir(parents=True, exist_ok=True)
    for hook_name in ("post-merge", "post-commit", "pre-push"):
        target = git_hooks / hook_name
        body = hook_script_body(hook_name)
        if target.exists():
            existing = read_text(target)
            if "Project Intelligence hook" not in existing:
                pending = project_dir(root) / "hooks" / f"{hook_name}.pending.sh"
                write_text(pending, body)
                try:
                    pending.chmod(0o755)
                except OSError:
                    pass
                results.append({"hook": hook_name, "status": "conflict", "detail": f"Existing hook preserved; pending wrapper written to {pending}"})
                continue
        write_text(target, body)
        try:
            target.chmod(0o755)
        except OSError:
            pass
        results.append({"hook": hook_name, "status": "installed", "detail": str(target)})
    return results


def install_claude(root: Path, hooks: bool = False, activate_hooks: bool = False) -> dict[str, Any]:
    claude = root / ".claude"
    skills = claude / "skills"
    standards = claude / "standards"
    skills.mkdir(parents=True, exist_ok=True)
    standards.mkdir(parents=True, exist_ok=True)
    write_text(
        claude / "CLAUDE.md",
        """# Project Intelligence

Before project tasks, reviews, component/API questions, quality checks, brainstorming, specs, plans, or post-task maintenance, inspect `.project-intel/manifest.json` and the relevant files under `.project-intel/standards` and `.project-intel/knowledge`.

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
        ("project-task", "Use when implementing, modifying, fixing, refactoring, or adding a feature in a project and needing reuse, standards, components, APIs, services, or graph context.", "Project Task"),
        ("project-brainstorm", "Use when shaping a project requirement, brainstorming approaches, clarifying scope, or choosing between implementation directions before writing code.", "Project Brainstorm"),
        ("project-spec", "Use when writing or updating a project requirement spec, design note, acceptance criteria, or task impact summary.", "Project Spec"),
        ("project-plan", "Use when turning an approved project spec or requirement into an implementation plan with project standards and verification steps.", "Project Plan"),
        ("project-debug", "Use when investigating bugs, errors, test failures, regressions, unexpected behavior, or debugging questions with project context.", "Project Debug"),
        ("project-maintain", "Use when a project task is finished or when standards, knowledge, reports, hooks, or lifecycle artifacts should be refreshed.", "Project Maintain"),
        ("project-review", "Use when reviewing code changes against project standards, graph impact, quality checks, redundancy, and tests.", "Project Review"),
        ("project-knowledge", "Use when answering questions about project structure, components, APIs, services, modules, standards, or business flows.", "Project Knowledge"),
        ("project-refresh", "Use when updating or initializing project standards, knowledge, graph summaries, and reports.", "Project Refresh"),
        ("project-standards", "Use when querying, explaining, confirming, upgrading, or downgrading project standards and rule levels.", "Project Standards"),
        ("project-quality", "Use when running or interpreting frontend/backend lint, type, format, style, redundancy, and standards checks.", "Project Quality"),
    ]
    for name, desc, title in entries:
        write_text(skills / f"{name}.md", skill_template.format(name=name, description=desc, title=title))
    write_text(standards / "project-intelligence.md", "Project standards are generated under `.project-intel/standards/`.\n")
    hook_templates = write_hook_templates(root) if hooks or activate_hooks else []
    hook_results = activate_git_hooks(root) if activate_hooks else []
    return {"claude": str(claude), "hookTemplates": [str(path) for path in hook_templates], "hookResults": hook_results}


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
    init = sub.add_parser("init", help="Initialize .project-intel")
    init.add_argument("--interactive", action="store_true", help="Show an interactive setup menu when optional tooling is missing")
    init.add_argument("--setup-missing", action="store_true", help="Run safe setup for missing optional tooling where a runnable command is available")
    init.add_argument("--with-graph", action="store_true", help="Try to initialize graph tooling such as GitNexus when available")
    init.add_argument("--strict", action="store_true", help="Fail if --with-graph does not produce any graph source")
    sub.add_parser("refresh", help="Refresh .project-intel from current workspace")
    install = sub.add_parser("install", help="Install Claude-compatible project entrypoints")
    install.add_argument("--hooks", action="store_true", help="Generate opt-in Git hook templates under .project-intel/hooks")
    install.add_argument("--activate-git-hooks", action="store_true", help="Install Project Intelligence wrappers into .git/hooks without overwriting custom hooks")
    check = sub.add_parser("check", help="Run project intelligence checks")
    check.add_argument("--run-quality", action="store_true", help="Actually run detected lint/type/style/format commands")
    spec = sub.add_parser("spec", help="Write a project spec under .project-intel/specs")
    spec.add_argument("--title", required=True)
    spec.add_argument("--from", dest="requirement", required=True)
    plan = sub.add_parser("plan", help="Write an implementation plan under .project-intel/plans")
    plan.add_argument("--title", required=True)
    plan.add_argument("--from-spec", required=True)
    lifecycle = sub.add_parser("lifecycle", help="Write a task impact report")
    lifecycle.add_argument("--task", required=True)
    debug = sub.add_parser("debug", help="Write a systematic debugging context report")
    debug.add_argument("--bug", required=True)
    maintain = sub.add_parser("maintain", help="Refresh project intelligence after a task")
    maintain.add_argument("--task", required=True)
    maintain.add_argument("--run-quality", action="store_true", help="Actually run detected lint/type/style/format commands")
    query = sub.add_parser("query", help="Search project intelligence artifacts")
    query.add_argument("text")
    sub.add_parser("version", help="Print version")
    args = parser.parse_args(argv)
    root = project_root(args.project)
    if args.command == "version":
        print(VERSION)
        return 0
    if args.command == "init":
        result = init_project(root, refresh=False, interactive=args.interactive, setup_missing=args.setup_missing, with_graph=args.with_graph, strict=args.strict)
        print(f"Initialized .project-intel with {result['manifest']['fileCount']} indexed text files.")
        return 0
    if args.command == "refresh":
        result = init_project(root, refresh=True)
        print(f"Refreshed .project-intel with {result['manifest']['fileCount']} indexed text files.")
        return 0
    if args.command == "install":
        result = install_claude(root, hooks=args.hooks, activate_hooks=args.activate_git_hooks)
        print(f"Installed Claude adapters under {result['claude']}")
        if result.get("hookTemplates"):
            print(f"Generated hook templates: {len(result['hookTemplates'])}")
        for item in result.get("hookResults", []):
            print(f"{item.get('hook')}: {item.get('status')} - {item.get('detail')}")
        return 0
    if args.command == "check":
        return run_check(root, args.run_quality)
    if args.command == "spec":
        write_spec(root, args.title, args.requirement)
        return 0
    if args.command == "plan":
        write_plan(root, args.title, args.from_spec)
        return 0
    if args.command == "lifecycle":
        write_lifecycle(root, args.task)
        return 0
    if args.command == "debug":
        write_debug_context(root, args.bug)
        return 0
    if args.command == "maintain":
        return maintain_project(root, args.task, args.run_quality)
    if args.command == "query":
        return query_project(root, args.text)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
