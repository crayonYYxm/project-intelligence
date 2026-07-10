from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXCLUDED_PACKAGE_PARTS = {"node_modules", "dist", "build", ".git", ".project-intel", ".next", ".nuxt"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def workspace_package_files(root: Path, root_package: dict[str, Any]) -> list[Path]:
    workspaces = root_package.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])
    patterns = [item for item in workspaces if isinstance(item, str)] if isinstance(workspaces, list) else []
    candidates: set[Path] = set()
    for pattern in patterns:
        normalized = pattern.rstrip("/")
        for directory in root.glob(normalized):
            path = directory / "package.json" if directory.is_dir() else directory
            if path.name == "package.json" and path.is_file():
                candidates.add(path)
    if not patterns:
        for parent in ("apps", "packages", "services", "frontend", "backend"):
            base = root / parent
            if not base.is_dir():
                continue
            for path in base.glob("*/package.json"):
                candidates.add(path)
    return sorted(
        (path for path in candidates if not any(part in EXCLUDED_PACKAGE_PARTS for part in path.relative_to(root).parts)),
        key=lambda path: path.as_posix(),
    )


def package_frameworks(deps: dict[str, Any]) -> list[str]:
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
    return frameworks


def detect_package(root: Path) -> dict[str, Any]:
    root_payload = load_json(root / "package.json")
    package_files = ([root / "package.json"] if root_payload else []) + workspace_package_files(root, root_payload)
    packages: list[dict[str, Any]] = []
    frameworks: set[str] = set()
    for path in package_files:
        payload = root_payload if path == root / "package.json" else load_json(path)
        deps: dict[str, Any] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            deps.update(payload.get(key, {}) or {})
        detected = package_frameworks(deps)
        frameworks.update(detected)
        packages.append(
            {
                "path": path.parent.relative_to(root).as_posix() or ".",
                "name": payload.get("name"),
                "scripts": payload.get("scripts", {}) or {},
                "frameworks": detected,
            }
        )
    for name, markers in {
        "Java/Spring": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "Python": ["pyproject.toml", "requirements.txt", "manage.py"],
        "Go": ["go.mod"],
        "Rust": ["Cargo.toml"],
    }.items():
        if any((root / marker).exists() for marker in markers):
            frameworks.add(name)
    return {
        "packageName": root_payload.get("name"),
        "scripts": root_payload.get("scripts", {}) or {},
        "frameworks": sorted(frameworks),
        "hasPackageJson": bool(root_payload),
        "packages": packages,
        "workspace": len(packages) > 1,
    }


def package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def package_script_command(manager: str, directory: str, script: str) -> str:
    if directory in {"", "."}:
        return f"{manager} run {script}"
    if manager == "pnpm":
        return f"pnpm --dir {directory} run {script}"
    if manager == "yarn":
        return f"yarn --cwd {directory} run {script}"
    return f"npm --prefix {directory} run {script}"


def append_unique(commands: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if item.get("command") and not any(existing.get("command") == item.get("command") for existing in commands):
        commands.append(item)


def detect_quality_commands(root: Path, package: dict[str, Any]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    aliases = {
        "lint": ["lint", "lint:eslint", "eslint"],
        "type-check": ["type-check", "typecheck", "check-types", "vue-tsc", "tsc"],
        "format-check": ["format:check", "prettier:check", "check:format"],
        "style-check": ["stylelint", "lint:style", "style:check"],
        "test": ["test", "test:unit", "unit"],
    }
    manager = package_manager(root)
    packages = package.get("packages", []) or ([{"path": ".", "scripts": package.get("scripts", {})}] if package.get("hasPackageJson") else [])
    for workspace in packages:
        directory = workspace.get("path") or "."
        scripts = workspace.get("scripts", {}) or {}
        for kind, names in aliases.items():
            for name in names:
                if name in scripts:
                    append_unique(commands, {
                        "kind": kind,
                        "command": package_script_command(manager, directory, name),
                        "source": "package.json" if directory == "." else f"{directory}/package.json",
                    })
                    break

    root_kinds = {item.get("kind") for item in commands if item.get("source") == "package.json"}
    if "lint" not in root_kinds and any((root / name).exists() for name in ("eslint.config.js", "eslint.config.mjs", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json")):
        append_unique(commands, {"kind": "lint", "command": "npx eslint .", "source": "inferred"})
    if "type-check" not in root_kinds and (root / "tsconfig.json").exists():
        command = "npx vue-tsc --noEmit" if "Vue" in package.get("frameworks", []) else "npx tsc --noEmit"
        append_unique(commands, {"kind": "type-check", "command": command, "source": "inferred"})
    if "style-check" not in root_kinds and any((root / name).exists() for name in ("stylelint.config.js", "stylelint.config.cjs", ".stylelintrc", ".stylelintrc.js")):
        append_unique(commands, {"kind": "style-check", "command": 'npx stylelint "**/*.{css,scss,vue}"', "source": "inferred"})
    if "format-check" not in root_kinds and any((root / name).exists() for name in ("prettier.config.js", "prettier.config.cjs", ".prettierrc", ".prettierrc.js", ".prettierrc.json")):
        append_unique(commands, {"kind": "format-check", "command": "npx prettier --check .", "source": "inferred"})

    if (root / "pom.xml").exists():
        mvn = "./mvnw" if (root / "mvnw").exists() else "mvn"
        append_unique(commands, {"kind": "test", "command": f"{mvn} test", "source": "pom.xml"})
        append_unique(commands, {"kind": "verify", "command": f"{mvn} verify", "source": "pom.xml"})
    if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        gradle = "./gradlew" if (root / "gradlew").exists() else "gradle"
        append_unique(commands, {"kind": "test", "command": f"{gradle} test", "source": "gradle"})
        append_unique(commands, {"kind": "verify", "command": f"{gradle} check", "source": "gradle"})
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore") if (root / "pyproject.toml").exists() else ""
        requirements = (root / "requirements.txt").read_text(encoding="utf-8", errors="ignore") if (root / "requirements.txt").exists() else ""
        combined = (pyproject + "\n" + requirements).lower()
        if "pytest" in combined or (root / "tests").is_dir():
            append_unique(commands, {"kind": "test", "command": "python3 -m pytest", "source": "python-project"})
        if "ruff" in combined:
            append_unique(commands, {"kind": "lint", "command": "python3 -m ruff check .", "source": "python-project"})
        if "mypy" in combined:
            append_unique(commands, {"kind": "type-check", "command": "python3 -m mypy .", "source": "python-project"})
    if (root / "go.mod").exists():
        append_unique(commands, {"kind": "test", "command": "go test ./...", "source": "go.mod"})
        append_unique(commands, {"kind": "verify", "command": "go vet ./...", "source": "go.mod"})
    if (root / "Cargo.toml").exists():
        append_unique(commands, {"kind": "type-check", "command": "cargo check", "source": "Cargo.toml"})
        append_unique(commands, {"kind": "test", "command": "cargo test", "source": "Cargo.toml"})
        append_unique(commands, {"kind": "format-check", "command": "cargo fmt -- --check", "source": "Cargo.toml"})
    return commands
