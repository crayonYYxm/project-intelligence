#!/usr/bin/env python3
"""Project Intelligence application services and CLI command dispatch.

This CLI creates a repository-local .project-intel directory with lightweight
project facts, standards, knowledge, reports, and optional references to
GitNexus / Understand-Anything artifacts.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Optional

if sys.version_info < (3, 9):
    print("project-intel requires Python 3.9 or later.", file=sys.stderr)
    raise SystemExit(2)

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from project_intel_lib import core as core_module
from project_intel_lib import graph as graph_module
from project_intel_lib import lifecycle as lifecycle_module
from project_intel_lib import quality as quality_module
from project_intel_lib import requirements as requirements_module
from project_intel_lib import standards as standards_module
from project_intel_lib import testing as testing_module
from project_intel_lib.cli import extract_global_json, json_envelope
from project_intel_lib.scanner import backend as backend_scanner
from project_intel_lib.scanner import frontend as frontend_scanner


VERSION = "0.6.1"
TRACK_CHOICES = ("auto", "quick", "standard", "complex")
UNDERSTAND_AGENT_COMMAND = "/understand . --language zh"
UNDERSTAND_REPO = "Egonex-AI/Understand-Anything"
UNDERSTAND_CODEX_INSTALL_COMMAND = "curl -fsSL https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.sh | bash -s codex"
UNDERSTAND_WINDOWS_INSTALL_COMMAND = (
    "powershell -NoProfile -ExecutionPolicy Bypass -Command "
    '"$installer = Join-Path ([IO.Path]::GetTempPath()) \'understand-anything-install.ps1\'; '
    "iwr -useb https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.ps1 -OutFile $installer; "
    "try { & $installer codex } finally { Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue }\""
)
UNDERSTAND_CLAUDE_PLUGIN_ID = "understand-anything@understand-anything"
UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND = f"claude plugin marketplace add {UNDERSTAND_REPO}"
UNDERSTAND_CLAUDE_INSTALL_COMMAND = f"claude plugin install {UNDERSTAND_CLAUDE_PLUGIN_ID}"
UNDERSTAND_CLAUDE_ENABLE_COMMAND = f"claude plugin enable {UNDERSTAND_CLAUDE_PLUGIN_ID}"
UNDERSTAND_CLAUDE_RELOAD_COMMAND = "/reload-plugins"
PROJECT_REFRESH_AGENT_COMMAND = "/project-refresh"
PROJECT_REFRESH_CLI_COMMAND = "project-intel refresh"
UNDERSTAND_MANUAL_INSTALL_HINT = (
    f"{UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND} && {UNDERSTAND_CLAUDE_INSTALL_COMMAND} && {UNDERSTAND_CLAUDE_ENABLE_COMMAND}"
)
PROJECT_INTEL_BLOCK_START = "<!-- project-intelligence:start -->"
PROJECT_INTEL_BLOCK_END = "<!-- project-intelligence:end -->"
AGENT_PROJECT_INTEL_BLOCK_START = "<!-- agent-project-intelligence:start -->"
AGENT_PROJECT_INTEL_BLOCK_END = "<!-- agent-project-intelligence:end -->"
PROJECT_INTEL_HOOK_MARKER = "# Project Intelligence hook"
ADAPTER_MAX_BYTES = 2 * 1024 * 1024
LEGACY_SCAN_INCLUDE = ["src/**", "app/**", "packages/**", "apps/**", "server/**", "client/**"]
HARD_CHECK_TYPES = {"forbid-regex", "require-regex", "require-file", "forbid-path"}
# v0.1.7 及更早版本会把 skill 副本写入目标项目，以下常量仅用于清理这些残留。
LEGACY_LOCAL_SKILLS_BLOCK_START = "<!-- local-project-skills:start -->"
LEGACY_LOCAL_SKILLS_BLOCK_END = "<!-- local-project-skills:end -->"
LEGACY_LOCAL_SKILL_NAMES = (
    "project-brainstorm",
    "project-debug",
    "project-design",
    "project-finish",
    "project-init",
    "project-intake",
    "project-knowledge",
    "project-maintain",
    "project-orchestrate",
    "project-plan",
    "project-quality",
    "project-refresh",
    "project-review",
    "project-spec",
    "project-standards",
    "project-task",
    "project-test",
)
# A historical installation is safe to remove only if its SKILL.md still has an
# exact known content hash.  Keep this intentionally empty until a released
# legacy bundle is archived here; name/keyword matching is unsafe.
LEGACY_LOCAL_SKILL_HASHES: dict[str, set[str]] = {}
EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    ".claude",
    ".project-intel",
    ".project-intel/cache",
    ".project-intel/local",
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

_TEXT_CACHE: dict[tuple[str, int, int], str] = {}
_ACTIVE_SCAN_CACHE: core_module.IncrementalScanCache | None = None


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def script_path() -> Path:
    """返回当前脚本安装位置，供生成的文档与 hook 引用。"""
    return Path(__file__).resolve()


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


def user_home() -> Path | None:
    try:
        return Path.home()
    except RuntimeError:
        return None


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
        stat = path.stat()
    except OSError:
        return ""
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    cached = _TEXT_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > max_bytes:
        data = data[:max_bytes]
    try:
        value = data.decode("utf-8")
    except UnicodeDecodeError:
        value = data.decode("utf-8", errors="ignore")
    _TEXT_CACHE[key] = value
    return value


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = text.rstrip() + "\n"
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _assert_safe_managed_path(root: Path, relative: str | Path, *, label: str) -> Path:
    """Return a repository-internal managed path after rejecting symlink hops."""
    root_absolute = Path(os.path.abspath(root))
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise RuntimeError(f"{label}路径越出项目目录：{relative}")
    cursor = root_absolute
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RuntimeError(f"{label}路径不能包含符号链接：{cursor}")
    return cursor


def _adapter_relative_path(root: Path, path: Path) -> str:
    try:
        return Path(os.path.abspath(path)).relative_to(Path(os.path.abspath(root))).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"适配器路径越出项目目录：{path}") from exc


def _assert_safe_adapter_path(root: Path, path: Path) -> None:
    relative = _adapter_relative_path(root, path)
    if relative not in {"AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md"}:
        raise RuntimeError(f"不支持的适配器路径：{relative}")
    _assert_safe_managed_path(root, relative, label="适配器")
    if path.exists() and path.stat().st_size > ADAPTER_MAX_BYTES:
        raise RuntimeError(f"适配器文件超过 2MiB，停止自动写入：{relative}")


def _read_adapter_text(root: Path, path: Path) -> str:
    _assert_safe_adapter_path(root, path)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"适配器文件不是有效 UTF-8：{_adapter_relative_path(root, path)}") from exc


def _write_adapter_text(root: Path, path: Path, text: str) -> None:
    _assert_safe_adapter_path(root, path)
    write_text(path, text)


def _replace_single_managed_block(
    current: str,
    managed: str,
    start: str,
    end: str,
    *,
    prepend: bool = False,
) -> tuple[str, str]:
    start_count = current.count(start)
    end_count = current.count(end)
    if start_count != end_count:
        raise RuntimeError("适配器管理标记不完整，请人工处理后重试。")
    if start_count > 1:
        raise RuntimeError("适配器存在重复 Project Intelligence 管理块，请人工处理后重试。")
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    if start_count == 1:
        return pattern.sub(managed, current).rstrip(), "updated"
    if current.strip() and prepend:
        return managed + "\n\n" + current.rstrip(), "created"
    if current.strip():
        return current.rstrip() + "\n\n" + managed, "created"
    return managed, "created"


def upsert_adapter_managed_block(
    root: Path,
    path: Path,
    block: str,
    start: str,
    end: str,
    *,
    prepend: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    current = _read_adapter_text(root, path)
    managed = f"{start}\n{block.strip()}\n{end}"
    next_text, action = _replace_single_managed_block(current, managed, start, end, prepend=prepend)
    changed = next_text.rstrip() != current.rstrip()
    if changed and not dry_run:
        _write_adapter_text(root, path, next_text)
    return {
        "path": _adapter_relative_path(root, path),
        "action": action if changed else "unchanged",
        "changed": changed,
        "sha256": hashlib.sha256(managed.encode("utf-8")).hexdigest(),
    }


def remove_adapter_managed_block(
    root: Path,
    path: Path,
    start: str,
    end: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    current = _read_adapter_text(root, path)
    start_count = current.count(start)
    end_count = current.count(end)
    if start_count != end_count:
        raise RuntimeError("适配器管理标记不完整，请人工处理后重试。")
    if start_count > 1:
        raise RuntimeError("适配器存在重复 Project Intelligence 管理块，请人工处理后重试。")
    if start_count == 0:
        return {"path": _adapter_relative_path(root, path), "action": "absent", "changed": False}
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}\n*", re.DOTALL)
    next_text = pattern.sub("", current).strip()
    if not dry_run:
        _write_adapter_text(root, path, next_text)
    return {"path": _adapter_relative_path(root, path), "action": "removed", "changed": True}


def upsert_managed_block_with_markers(path: Path, block: str, start: str, end: str, prepend: bool = False) -> None:
    current = read_text(path)
    managed = f"{start}\n{block.strip()}\n{end}"
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(end)}",
        re.DOTALL,
    )
    if pattern.search(current):
        next_text = pattern.sub(managed, current).rstrip()
    elif current.strip() and prepend:
        next_text = managed + "\n\n" + current.rstrip()
    elif current.strip():
        next_text = current.rstrip() + "\n\n" + managed
    else:
        next_text = managed
    write_text(path, next_text)


def upsert_managed_block(path: Path, block: str) -> None:
    upsert_managed_block_with_markers(path, block, PROJECT_INTEL_BLOCK_START, PROJECT_INTEL_BLOCK_END)


def remove_managed_block_with_markers(path: Path, start: str, end: str) -> bool:
    current = read_text(path)
    if start not in current:
        return False
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(end)}\n*",
        re.DOTALL,
    )
    next_text = pattern.sub("", current).strip()
    write_text(path, next_text)
    return True


def cleanup_legacy_local_skills(root: Path) -> list[str]:
    """移除旧版本 init 写入项目的本地 skill 副本与 CLAUDE.md 规则块。

    v0.1.7 及更早版本会把插件 skill 复制到目标项目的 .claude/skills/ 下，并在
    CLAUDE.md 写入 local-project-skills 块，导致与插件命名空间 skill 冲突。
    """
    removed: list[str] = []
    skills_dir = root / ".claude" / "skills"
    _assert_safe_managed_path(root, ".claude", label="旧 Skill 清理")
    _assert_safe_managed_path(root, ".claude/skills", label="旧 Skill 清理")
    for name in LEGACY_LOCAL_SKILL_NAMES:
        skill_dir = skills_dir / name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        if skill_dir.is_symlink() or skill_md.is_symlink():
            continue
        digest = hashlib.sha256(skill_md.read_bytes()).hexdigest()
        if digest not in LEGACY_LOCAL_SKILL_HASHES.get(name, set()):
            continue
        backup_root = _assert_safe_managed_path(root, ".project-intel/backups/legacy-skills", label="旧 Skill 备份")
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / f"{name}-{digest[:12]}"
        if not backup.exists():
            shutil.copytree(skill_dir, backup, symlinks=True)
        shutil.rmtree(skill_dir)
        removed.append(str(skill_dir))
    if skills_dir.is_dir() and not any(skills_dir.iterdir()):
        skills_dir.rmdir()
    for doc in (root / "CLAUDE.md", root / "AGENTS.md", root / ".claude" / "CLAUDE.md"):
        if remove_managed_block_with_markers(doc, LEGACY_LOCAL_SKILLS_BLOCK_START, LEGACY_LOCAL_SKILLS_BLOCK_END):
            removed.append(f"{doc} 中的 local-project-skills 块")
    return removed


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def fail_usage(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def load_json_strict(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail_usage(f"无法读取{label}：{path}（{exc}）")
    except json.JSONDecodeError as exc:
        fail_usage(f"{label}格式错误，原文件未修改：{path}:{exc.lineno}:{exc.colno} {exc.msg}")
    if not isinstance(payload, dict):
        fail_usage(f"{label}必须是 JSON 对象，原文件未修改：{path}")
    return payload


def project_root(arg: str | None) -> Path:
    root = Path(arg or os.getcwd()).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        fail_usage(f"项目路径不是目录：{root}")
    return root


def project_dir(root: Path) -> Path:
    return _assert_safe_managed_path(root, ".project-intel", label=".project-intel")


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def path_matches_pattern(rel_path: str, pattern: str) -> bool:
    normalized = pattern.strip().replace("\\", "/").removeprefix("./").rstrip("/")
    rel_path = rel_path.replace("\\", "/").removeprefix("./").rstrip("/")
    if not normalized:
        return False
    brace = re.search(r"\{([^{}]+)}", normalized)
    if brace:
        return any(
            path_matches_pattern(rel_path, normalized[: brace.start()] + option.strip() + normalized[brace.end() :])
            for option in brace.group(1).split(",")
            if option.strip()
        )
    if normalized in {"**", "**/*", "*"}:
        return True
    if not any(char in normalized for char in "*?["):
        return rel_path == normalized or rel_path.startswith(normalized + "/") or normalized in Path(rel_path).parts
    regex = ""
    idx = 0
    while idx < len(normalized):
        char = normalized[idx]
        if char == "*" and idx + 1 < len(normalized) and normalized[idx + 1] == "*":
            idx += 2
            if idx < len(normalized) and normalized[idx] == "/":
                regex += "(?:.*/)?"
                idx += 1
            else:
                regex += ".*"
            continue
        if char == "*":
            regex += "[^/]*"
        elif char == "?":
            regex += "[^/]"
        else:
            regex += re.escape(char)
        idx += 1
    return bool(re.fullmatch(regex, rel_path))


def path_matches_any(rel_path: str, patterns: list[str]) -> bool:
    return any(path_matches_pattern(rel_path, pattern) for pattern in patterns)


def scan_settings(config: Optional[dict[str, Any]] = None) -> tuple[list[str], list[str], bool]:
    scan = (config or {}).get("scan", {}) if isinstance(config, dict) else {}
    includes = scan.get("include") if isinstance(scan, dict) else None
    excludes = scan.get("exclude") if isinstance(scan, dict) else None
    exclude_hidden = scan.get("excludeHidden", True) if isinstance(scan, dict) else True
    return list(includes or ["**/*"]), list(excludes or sorted(EXCLUDED_DIRS)), bool(exclude_hidden)


def is_excluded(root: Path, path: Path, config: Optional[dict[str, Any]] = None) -> bool:
    try:
        parts = path.relative_to(root).parts if path.is_absolute() else path.parts
    except ValueError:
        return True
    joined = "/".join(parts)
    if joined in core_module.GENERATED_AGENT_FILES:
        return True
    _, excludes, exclude_hidden = scan_settings(config)
    if exclude_hidden and any(part.startswith(".") and part not in {".", ".."} for part in parts):
        return True
    return path_matches_any(joined, excludes)


def iter_project_files(root: Path, config: Optional[dict[str, Any]] = None, text_only: bool = True) -> list[Path]:
    includes, _, _ = scan_settings(config)
    root_resolved = root.resolve()
    files: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [
            name
            for name in dirnames
            if not is_excluded(root, current_path / name, config)
        ]
        for name in filenames:
            path = current_path / name
            try:
                path.resolve().relative_to(root_resolved)
            except (OSError, ValueError):
                continue
            if is_excluded(root, path, config):
                continue
            rel_path = rel(root, path)
            if not path_matches_any(rel_path, includes):
                continue
            if text_only and path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            files.append(path)
    return sorted(files, key=lambda path: rel(root, path))


def iter_files(root: Path, config: Optional[dict[str, Any]] = None) -> list[Path]:
    return iter_project_files(root, config=config, text_only=True)


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


# Keep the public functions stable while the implementation lives in a reusable module.
package_manager = quality_module.package_manager
detect_package = quality_module.detect_package
detect_quality_commands = quality_module.detect_quality_commands


def understand_plugin_roots() -> list[Path]:
    home = user_home()
    candidates = []
    if home is not None:
        candidates.extend([
            home / ".understand-anything-plugin",
            home / ".understand-anything" / "repo" / "understand-anything-plugin",
            home / ".codex" / "understand-anything" / "understand-anything-plugin",
            home / ".opencode" / "understand-anything" / "understand-anything-plugin",
            home / ".pi" / "understand-anything" / "understand-anything-plugin",
            home / "understand-anything" / "understand-anything-plugin",
        ])
    configured_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if configured_root:
        candidates.insert(0, Path(configured_root))
    claude_cache = home / ".claude" / "plugins" / "cache" if home is not None else None
    if claude_cache is not None and claude_cache.exists():
        candidates.extend(claude_cache.glob("*/understand-anything"))
        candidates.extend(claude_cache.glob("*/understand-anything/*"))
    roots = []
    for candidate in candidates:
        package_path = candidate / "package.json"
        if not package_path.exists() or not (candidate / "pnpm-workspace.yaml").exists():
            continue
        package = load_json(package_path, {})
        package_name = str(package.get("name") or "").lower()
        if "understand" in package_name or "understand-anything" in candidate.as_posix().lower():
            roots.append(candidate.resolve())
    return roots


def current_agent_platform() -> str:
    configured = os.environ.get("PROJECT_INTEL_AGENT", "").strip().lower()
    if configured in {"codex", "claude"}:
        return configured
    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_CI") or os.environ.get("CODEX_HOME"):
        return "codex"
    if (
        os.environ.get("CLAUDE_PLUGIN_ROOT")
        or os.environ.get("CLAUDECODE")
        or os.environ.get("CLAUDE_CODE")
        or os.environ.get("CLAUDE_CODE_ENTRYPOINT")
    ):
        return "claude"
    return "unknown"


def claude_understand_installs() -> list[dict[str, Any]]:
    home = user_home()
    if home is None:
        return []
    installed = load_json(home / ".claude" / "plugins" / "installed_plugins.json", {})
    plugins = installed.get("plugins", {}) if isinstance(installed, dict) else {}
    enabled_plugins = load_json(home / ".claude" / "settings.json", {}).get("enabledPlugins", {})
    plugin_statuses = claude_plugin_list_statuses()
    results = []
    for plugin_id, entries in plugins.items():
        if not str(plugin_id).startswith("understand-anything@"):
            continue
        for entry in entries or []:
            if isinstance(entry, dict):
                item = {
                    "id": plugin_id,
                    "enabled": bool(enabled_plugins.get(plugin_id)),
                    "listStatus": plugin_statuses.get(plugin_id),
                    **entry,
                }
                results.append(item)
    return results


def claude_plugin_list_statuses() -> dict[str, str]:
    if not command_exists("claude"):
        return {}
    home = user_home()
    if home is None:
        return {}
    code, out, _ = run(["claude", "plugin", "list"], home, timeout=20)
    if code != 0:
        return {}
    statuses: dict[str, str] = {}
    current: str | None = None
    for line in out.splitlines():
        plugin_match = re.search(r"❯\s+([A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+)", line)
        if plugin_match:
            current = plugin_match.group(1)
            continue
        status_match = re.search(r"Status:\s*(.+)", line)
        if current and status_match:
            statuses[current] = status_match.group(1).strip()
            current = None
    return statuses


def claude_understand_install_is_ready(install: dict[str, Any]) -> bool:
    status = str(install.get("listStatus") or "").lower()
    if "failed" in status:
        return False
    if "enabled" in status:
        return True
    if "disabled" in status:
        return False
    return bool(install.get("enabled"))


def claude_understand_install_is_repairable(install: dict[str, Any]) -> bool:
    status = str(install.get("listStatus") or "").lower()
    plugin_id = str(install.get("id") or "")
    if "failed" in status:
        return False
    if plugin_id.endswith("@local"):
        return False
    return bool(plugin_id)


def understand_installed_platforms(roots: list[Path], claude_installs: list[dict[str, Any]]) -> list[str]:
    platforms = set()
    home = user_home()
    for root in roots:
        text = root.as_posix().lower()
        if (
            (home is not None and root == home / ".understand-anything-plugin")
            or "/.understand-anything/repo/understand-anything-plugin" in text
            or "/.codex/understand-anything/" in text
            or "/.agents/skills/" in text
        ):
            platforms.add("codex")
    if any(claude_understand_install_is_ready(install) for install in claude_installs):
        platforms.add("claude")
    return sorted(platforms)


def understand_install_options(claude_installs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    configured = os.environ.get("PROJECT_INTEL_UNDERSTAND_INSTALL_COMMAND", "").strip()
    if configured:
        return [
            {
                "platform": "custom",
                "label": "自定义安装命令",
                "command": configured,
                "commands": [configured],
                "canRun": True,
                "commandSource": "environment",
            }
        ]

    options: list[dict[str, Any]] = []
    if command_exists("claude"):
        claude_installs = claude_installs or claude_understand_installs()
        repairable_install = next((install for install in claude_installs if claude_understand_install_is_repairable(install)), None)
        if repairable_install and not claude_understand_install_is_ready(repairable_install):
            plugin_id = repairable_install.get("id")
            options.append(
                {
                    "platform": "claude",
                    "label": "Claude Code 插件启用",
                    "command": f"claude plugin enable {plugin_id}",
                    "commands": [f"claude plugin enable {plugin_id}"],
                    "canRun": True,
                    "postInstall": UNDERSTAND_CLAUDE_RELOAD_COMMAND,
                }
            )
        options.append(
            {
                "platform": "claude",
                "label": "Claude Code 插件安装/修复",
                "command": UNDERSTAND_MANUAL_INSTALL_HINT,
                "commands": [
                    UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND,
                    UNDERSTAND_CLAUDE_INSTALL_COMMAND,
                    UNDERSTAND_CLAUDE_ENABLE_COMMAND,
                ],
                "canRun": True,
                "postInstall": UNDERSTAND_CLAUDE_RELOAD_COMMAND,
            }
        )
    if os.name == "nt":
        if command_exists("powershell") or command_exists("pwsh"):
            powershell_command = UNDERSTAND_WINDOWS_INSTALL_COMMAND
            if not command_exists("powershell"):
                powershell_command = powershell_command.replace("powershell ", "pwsh ", 1)
            options.append(
                {
                    "platform": "codex",
                    "label": "Codex skills 安装",
                    "command": powershell_command,
                    "commands": [powershell_command],
                    "canRun": True,
                }
            )
    elif command_exists("curl") and command_exists("bash"):
        options.append(
            {
                "platform": "codex",
                "label": "Codex skills 安装",
                "command": UNDERSTAND_CODEX_INSTALL_COMMAND,
                "commands": [UNDERSTAND_CODEX_INSTALL_COMMAND],
                "canRun": True,
            }
        )
    return options


def filter_understand_install_options(options: list[dict[str, Any]], installed_platforms: list[str]) -> list[dict[str, Any]]:
    installed = set(installed_platforms)
    return [option for option in options if option.get("platform") not in installed or option.get("platform") == "custom"]


def default_understand_install_command(options: list[dict[str, Any]] | None = None) -> str | None:
    platform = current_agent_platform()
    options = options if options is not None else understand_install_options()
    for option in options:
        if option.get("platform") == platform:
            return option.get("command")
    return options[0].get("command") if options else None


def understand_analyze_command() -> str | None:
    configured = os.environ.get("PROJECT_INTEL_UNDERSTAND_COMMAND", "").strip()
    if configured:
        return configured
    if command_exists("understand"):
        return "understand ."
    return None


def detect_graph_actions(root: Path) -> list[dict[str, Any]]:
    gitnexus_runner = root / ".gitnexus" / "run.cjs"
    gitnexus_command = None
    if gitnexus_runner.exists():
        gitnexus_command = "node .gitnexus/run.cjs analyze"
        gitnexus_command_source = "repo-runner"
    elif command_exists("gitnexus"):
        gitnexus_command = "gitnexus analyze"
        gitnexus_command_source = "path"
    else:
        gitnexus_command_source = None
    gitnexus_install_command = "npx gitnexus analyze" if command_exists("npx") else None

    actions = [
        {
            "tool": "GitNexus",
            "reason": "符号级调用、影响分析、PR/变更风险",
            "state": "installed" if gitnexus_command else "installable" if gitnexus_install_command else "missing",
            "stateLabel": "已安装，可直接分析" if gitnexus_command else "可下载并运行分析" if gitnexus_install_command else "不可用",
            "analyzeCommand": gitnexus_command,
            "analyzeCommandSource": gitnexus_command_source,
            "installCommand": gitnexus_install_command,
            "canAnalyze": bool(gitnexus_command),
            "canInstall": bool(gitnexus_install_command),
        }
    ]

    ua_roots = understand_plugin_roots()
    ua_claude_installs = claude_understand_installs()
    ua_command = understand_analyze_command()
    ua_command_source = "environment" if os.environ.get("PROJECT_INTEL_UNDERSTAND_COMMAND", "").strip() else "path"
    ua_installed_platforms = understand_installed_platforms(ua_roots, ua_claude_installs)
    ua_install_options = filter_understand_install_options(understand_install_options(ua_claude_installs), ua_installed_platforms)
    ua_install_command = default_understand_install_command(ua_install_options)
    current_platform = current_agent_platform()
    ua_installed_for_current = (
        current_platform in ua_installed_platforms if current_platform in {"codex", "claude"} else bool(ua_installed_platforms)
    )
    ua_state = (
        "installed"
        if ua_command
        else "partially-installed"
        if ua_installed_for_current and ua_install_options
        else "agent-installed"
        if ua_installed_for_current
        else "installable"
        if ua_install_options
        else "missing"
    )
    ua_state_label = {
        "installed": "已安装，可直接分析",
        "partially-installed": "当前 agent 已安装；其他平台可选安装",
        "agent-installed": "已安装到 agent；当前 shell 不能直接分析",
        "installable": "未安装，可选择安装",
        "missing": "未安装且未找到可执行安装命令",
    }.get(ua_state, ua_state)
    actions.append(
        {
            "tool": "Understand-Anything",
            "reason": "架构概览、模块关系、领域流、入职图谱",
            "state": ua_state,
            "stateLabel": ua_state_label,
            "analyzeCommand": ua_command,
            "analyzeCommandSource": ua_command_source if ua_command else None,
            "installCommand": ua_install_command,
            "installOptions": ua_install_options,
            "agentCommand": UNDERSTAND_AGENT_COMMAND,
            "claudeInstallCommand": UNDERSTAND_MANUAL_INSTALL_HINT,
            "canAnalyze": bool(ua_command),
            "canInstall": bool(ua_install_command),
            "pluginRoots": [str(path) for path in ua_roots],
            "claudeInstalls": ua_claude_installs,
            "installedPlatforms": ua_installed_platforms,
            "currentPlatform": current_platform,
        }
    )
    return actions


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
                    "detail": "使用项目的 package script；依赖归属保持在项目中。",
                }
            )
        elif first == "npx":
            configured.append(
                {
                    "kind": item.get("kind"),
                    "command": command,
                    "status": "available" if command_exists("npx") else "missing",
                    "detail": "需要 npx，因为未找到项目 script。",
                }
            )
        else:
            configured.append(
                {
                    "kind": item.get("kind"),
                    "command": command,
                    "status": "available" if first and command_exists(first) else "missing",
                    "detail": "从项目配置推断。",
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
    graph_actions = detect_graph_actions(root)
    graph_action_by_tool = {action.get("tool"): action for action in graph_actions}
    package_managers = [
        {"name": name, "status": "present" if command_exists(name) else "missing", "selected": name == selected_pm}
        for name in ("pnpm", "npm", "yarn")
    ]
    gitnexus_action = graph_action_by_tool.get("GitNexus", {})
    understand_action = graph_action_by_tool.get("Understand-Anything", {})
    gitnexus_status = "present" if gitnexus_index.exists() else gitnexus_action.get("state", "missing")
    understand_status = "present" if ua_graph.exists() else understand_action.get("state", "missing")
    recommended_actions = []
    follow_up_actions = []
    if gitnexus_action.get("state") != "installed":
        recommended_actions.append(
            {
                "tool": "GitNexus",
                "reason": gitnexus_action.get("reason"),
                "command": gitnexus_action.get("installCommand") or gitnexus_action.get("analyzeCommand"),
                "canRun": gitnexus_action.get("canInstall") or gitnexus_action.get("canAnalyze"),
            }
        )
    if understand_action.get("state") in {"agent-installed", "partially-installed"}:
        follow_up_actions.append(
            {
                "tool": "Understand-Anything",
                "reason": understand_action.get("reason"),
                "command": understand_action.get("agentCommand"),
                "refreshCommand": PROJECT_REFRESH_AGENT_COMMAND,
                "fallbackRefreshCommand": PROJECT_REFRESH_CLI_COMMAND,
                "detail": (
                    f"Understand-Anything 已安装到 Codex/Claude Code agent，但当前 shell 没有 `understand` 命令。"
                    f"如果是在 Claude Code 刚完成安装/启用，请先运行 {UNDERSTAND_CLAUDE_RELOAD_COMMAND} 重新加载插件，"
                    f"再在当前 agent 会话中运行 {UNDERSTAND_AGENT_COMMAND} 或触发 Understand-Anything skill，"
                    f"生成图谱后立即执行 {PROJECT_REFRESH_AGENT_COMMAND}；如果不能触发 slash command，执行 {PROJECT_REFRESH_CLI_COMMAND}。"
                ),
                "canRun": False,
            }
        )
    if understand_action.get("state") in {"installable", "partially-installed"}:
        recommended_actions.append(
            {
                "tool": "Understand-Anything",
                "reason": understand_action.get("reason"),
                "command": understand_action.get("installCommand") or understand_action.get("agentCommand"),
                "installOptions": understand_action.get("installOptions", []),
                "canRun": understand_action.get("canInstall") or understand_action.get("canAnalyze"),
            }
        )
    if package.get("hasPackageJson") and not command_exists(selected_pm):
        recommended_actions.append(
            {
                "tool": selected_pm,
                "reason": "运行项目 package scripts，如 lint/type-check/format-check",
                "command": f"安装 {selected_pm}，然后运行 {selected_pm} install",
                "canRun": False,
            }
        )
    return {
        "schemaVersion": 1,
        "generatedAt": now_iso(),
        "required": [
            {"name": "python>=3.9", "status": "present"},
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
                "claudeInstalls": understand_action.get("claudeInstalls", []),
            },
            "qualityTools": detect_quality_tool_status(root, quality_commands),
        },
        "graphActions": graph_actions,
        "recommendedActions": recommended_actions,
        "followUpActions": follow_up_actions,
    }


def tooling_has_missing_optional(tooling: dict[str, Any]) -> bool:
    return bool(tooling.get("recommendedActions"))


def print_tooling_summary(tooling: dict[str, Any]) -> None:
    actions = tooling.get("recommendedActions", [])
    follow_ups = tooling.get("followUpActions", [])
    if not actions:
        if follow_ups:
            print("项目智能工具检查：初始化已完成，但以下图谱需要在 agent 中继续执行：")
            for idx, action in enumerate(follow_ups, start=1):
                print(f"{idx}. {action.get('tool')}：{action.get('detail')}")
            return
        print("项目智能工具检查：可选的图谱和质量工具已就绪。")
        return
    print("项目智能检测到可提升效果的可选工具：")
    for idx, action in enumerate(actions, start=1):
        runnable = "可准备并执行" if action.get("canRun") else "需手动设置"
        print(f"{idx}. {action.get('tool')}：{runnable}")
        print(f"   用途：{action.get('reason')}")
        print(f"   命令：{action.get('command')}")
    if follow_ups:
        print("后续 Agent 步骤：")
        for idx, action in enumerate(follow_ups, start=1):
            print(f"{idx}. {action.get('tool')}：{action.get('detail')}")
    if len(actions) + len(follow_ups) > 1:
        print("提示：可以选择全部，也可以组合执行，例如 GitNexus + Understand-Anything。")


def print_graph_tools_report(tooling: dict[str, Any], as_json: bool = False) -> None:
    actions = tooling.get("graphActions", [])
    if as_json:
        print(json.dumps(actions, ensure_ascii=False, indent=2))
        return
    print("图谱工具检查结果：")
    if not actions:
        print("未检测到可选图谱工具。")
        return
    state_map = {
        "installed": "已安装，可直接分析",
        "installable": "可安装",
        "partially-installed": "当前 agent 已安装；其他平台可选安装",
        "agent-installed": "已安装插件，需在 agent 中运行",
        "missing": "不可用",
    }
    for idx, action in enumerate(actions, start=1):
        command = action.get("analyzeCommand") or action.get("installCommand") or action.get("agentCommand") or "-"
        state_label = action.get("stateLabel") or state_map.get(action.get("state"), action.get("state"))
        print(f"{idx}. {action.get('tool')}：{state_label}")
        print(f"   用途：{action.get('reason')}")
        print(f"   命令：{command}")


def graph_timeout_seconds() -> int:
    raw = os.environ.get("PROJECT_INTEL_GRAPH_TIMEOUT_SECONDS", "900").strip()
    try:
        return min(7200, max(30, int(raw)))
    except ValueError:
        return 900


def run_graph_command(root: Path, action: dict[str, Any], command: str) -> dict[str, Any]:
    timeout = graph_timeout_seconds()
    tool = str(action.get("tool") or "图谱工具")
    stop = threading.Event()

    def report_progress() -> None:
        elapsed = 0
        while not stop.wait(15):
            elapsed += 15
            print(f"{tool} 仍在运行，已等待 {elapsed} 秒（超时上限 {timeout} 秒）...", flush=True)

    print(f"{tool} 开始执行，超时上限 {timeout} 秒。", flush=True)
    progress = threading.Thread(target=report_progress, name="project-intel-graph-progress", daemon=True)
    progress.start()
    try:
        code, out, err = run_shell(command, root, timeout=timeout)
    finally:
        stop.set()
        progress.join(timeout=1)
    return {
        "tool": action.get("tool"),
        "status": "ok" if code == 0 else "failed",
        "command": testing_module.sanitize_text(command),
        "exitCode": code,
        "stdout": testing_module.sanitize_text(out[-4000:]),
        "stderr": testing_module.sanitize_text(err[-4000:]),
        "detail": f"执行超过 {timeout} 秒后已终止。可通过 PROJECT_INTEL_GRAPH_TIMEOUT_SECONDS 调整。" if code == 124 else "",
    }


def command_uses_external_path(root: Path, command: str) -> bool:
    try:
        # Preserve backslashes before checking both POSIX and Windows paths.
        # POSIX parsing would otherwise consume the separators in `C:\\Tools\\...`.
        values = shlex.split(command, posix=False)
    except ValueError:
        values = command.split()
    root_resolved = root.resolve()
    for value in values:
        cleaned = value.strip("\"'")
        option, separator, option_value = cleaned.partition("=")
        if separator and (option.startswith("-") or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", option)):
            cleaned = option_value.strip("\"'")
        try:
            candidate = Path(cleaned).expanduser()
        except RuntimeError:
            return True
        native_absolute = candidate.is_absolute()
        any_platform_absolute = PureWindowsPath(cleaned).is_absolute() or PurePosixPath(cleaned).is_absolute()
        if not any_platform_absolute:
            continue
        if not native_absolute:
            return True
        try:
            candidate.resolve(strict=False).relative_to(root_resolved)
        except ValueError:
            return True
    return False


def command_has_shell_expansion(command: str) -> bool:
    return bool(re.search(r"(?<!\\)(?:\$(?:\{|\(|[A-Za-z_])|%[^%\r\n]+%|`|[<>]\()", command))


def graph_command_authorized(
    root: Path,
    command: str,
    source: str,
    *,
    allow_repo_runner: bool,
    allow_env_command: bool,
    allow_external_path: bool,
) -> tuple[bool, str]:
    if source == "repo-runner" and not allow_repo_runner:
        return False, "仓库内 runner 需要显式使用 --allow-repo-runner。"
    if source == "environment" and not allow_env_command:
        return False, "环境变量提供的命令需要显式使用 --allow-env-command。"
    if source != "builtin" and command_has_shell_expansion(command) and not allow_external_path:
        return False, "命令包含运行时 shell 展开，需要显式使用 --allow-external-path。"
    if command_uses_external_path(root, command) and not allow_external_path:
        return False, "命令引用项目外绝对路径，需要显式使用 --allow-external-path。"
    return True, ""


def install_options_for_action(action: dict[str, Any]) -> list[dict[str, Any]]:
    options = action.get("installOptions") or []
    if options:
        return options
    command = action.get("installCommand")
    if command:
        return [{"platform": "default", "label": "默认安装命令", "command": command, "commands": [command], "canRun": True}]
    return []


def choose_install_option(action: dict[str, Any], auto_approve: bool) -> dict[str, Any] | None:
    options = install_options_for_action(action)
    if not options:
        return None
    platform = current_agent_platform()
    if auto_approve:
        for option in options:
            if option.get("platform") == platform:
                return option
        return options[0]

    state_label = action.get("stateLabel") or "需要准备后才能运行分析"
    print(f"\n检测到 {action.get('tool')}：{state_label}。")
    print(f"用途：{action.get('reason')}")
    if len(options) == 1:
        print(f"准备/初始化命令：{options[0].get('command')}")
        print("[y] 继续执行并分析")
        print("[n] 跳过，继续初始化 .project-intel")
    else:
        print("请选择安装目标：")
        for idx, option in enumerate(options, start=1):
            marker = "（推荐）" if option.get("platform") == platform else ""
            print(f"{idx}. {option.get('label') or option.get('platform')} {marker}")
            print(f"   命令：{option.get('command')}")
        print(f"{len(options) + 1}. 跳过，继续初始化 .project-intel")
    try:
        choice = input("> ").strip().lower()
    except EOFError:
        print("未读取到交互输入，跳过该图谱工具。")
        return None
    if len(options) == 1:
        return options[0] if choice in ("y", "yes", "是") else None
    if choice in ("", "y", "yes", "是"):
        for option in options:
            if option.get("platform") == platform:
                return option
        return options[0]
    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(options):
            return options[index - 1]
    return None


def run_install_option(root: Path, action: dict[str, Any], option: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    commands = option.get("commands") or [option.get("command")]
    for command in commands:
        if not command:
            continue
        result = run_graph_command(root, action, command)
        result["platform"] = option.get("platform")
        results.append(result)
        if result.get("status") != "ok":
            break
    return results


def verify_understand_claude_install() -> dict[str, Any]:
    installs = claude_understand_installs()
    ready = [install for install in installs if claude_understand_install_is_ready(install)]
    if ready:
        plugin_id = ready[0].get("id")
        return {
            "tool": "Understand-Anything",
            "status": "ok",
            "command": "claude plugin list",
            "detail": (
                f"Claude Code 已启用 {plugin_id}。"
                f"在当前 Claude Code 会话运行 {UNDERSTAND_CLAUDE_RELOAD_COMMAND} 后，"
                f"再运行 {UNDERSTAND_AGENT_COMMAND} 生成图谱；完成后立即运行 {PROJECT_REFRESH_AGENT_COMMAND}。"
            ),
            "pluginId": plugin_id,
        }
    broken = [install for install in installs if str(install.get("listStatus") or "").lower().find("failed") >= 0]
    if broken:
        detail = "; ".join(
            f"{install.get('id')} 状态为 {install.get('listStatus') or 'failed'}" for install in broken
        )
        return {
            "tool": "Understand-Anything",
            "status": "failed",
            "command": "claude plugin list",
            "detail": (
                f"Claude Code 检测到损坏的 Understand-Anything 安装：{detail}。"
                f"请移除损坏安装后重新执行安装，或检查 marketplace clone 网络。"
            ),
        }
    return {
        "tool": "Understand-Anything",
        "status": "failed",
        "command": "claude plugin list",
        "detail": (
            f"Claude Code 未检测到已启用的 Understand-Anything。"
            f"请确认 {UNDERSTAND_CLAUDE_MARKETPLACE_COMMAND} 和 {UNDERSTAND_CLAUDE_INSTALL_COMMAND} 是否成功。"
        ),
    }


def setup_graph_tools(
    root: Path,
    tooling: dict[str, Any],
    auto_approve: bool = False,
    *,
    allow_repo_runner: bool = False,
    allow_env_command: bool = False,
    allow_external_path: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in tooling.get("graphActions", []):
        tool = action.get("tool")
        analyze_command = action.get("analyzeCommand")
        state = action.get("state")

        if analyze_command:
            allowed, detail = graph_command_authorized(
                root,
                analyze_command,
                str(action.get("analyzeCommandSource") or "path"),
                allow_repo_runner=allow_repo_runner,
                allow_env_command=allow_env_command,
                allow_external_path=allow_external_path,
            )
            if not allowed:
                print(f"{tool}：{detail}")
                results.append({"tool": tool, "status": "skipped", "command": testing_module.sanitize_text(analyze_command), "detail": detail})
                continue
            print(f"{tool} 已安装，开始运行分析：{testing_module.sanitize_text(analyze_command)}")
            results.append(run_graph_command(root, action, analyze_command))
            continue

        install_options = install_options_for_action(action)

        if tool == "Understand-Anything" and state == "agent-installed" and not install_options:
            detail = (
                f"Understand-Anything 已安装到 agent；当前 shell 不能直接分析。"
                f"如果是在 Claude Code，请先运行 {UNDERSTAND_CLAUDE_RELOAD_COMMAND}，"
                f"再在 Codex/Claude Code 会话中运行 {action.get('agentCommand')}，"
                f"或触发 Understand-Anything skill；图谱完成后立即执行 {PROJECT_REFRESH_AGENT_COMMAND}，"
                f"不能触发 slash command 时执行 {PROJECT_REFRESH_CLI_COMMAND}。"
            )
            print(detail)
            results.append({"tool": tool, "status": "skipped", "detail": detail})
            continue

        install_option = choose_install_option(action, auto_approve=auto_approve)
        if not install_options:
            detail = "未检测到可安装或可运行的命令。"
            print(f"{tool}：{detail}")
            results.append({"tool": tool, "status": "skipped", "detail": detail})
            continue
        if not install_option:
            results.append({"tool": tool, "status": "skipped", "detail": "用户选择跳过。"})
            continue

        install_command = str(install_option.get("command") or "")
        allowed, detail = graph_command_authorized(
            root,
            install_command,
            str(install_option.get("commandSource") or action.get("installCommandSource") or "builtin"),
            allow_repo_runner=allow_repo_runner,
            allow_env_command=allow_env_command,
            allow_external_path=allow_external_path,
        )
        if not allowed:
            print(f"{tool}：{detail}")
            results.append({"tool": tool, "status": "skipped", "command": testing_module.sanitize_text(install_command), "detail": detail})
            continue

        print(f"开始准备并执行 {tool}：{testing_module.sanitize_text(str(install_option.get('command') or ''))}")
        install_results = run_install_option(root, action, install_option)
        results.extend(install_results)
        install_ok = bool(install_results) and all(result.get("status") == "ok" for result in install_results)
        if tool == "Understand-Anything" and install_ok:
            if install_option.get("platform") == "claude":
                verification = verify_understand_claude_install()
                results.append(verification)
                if verification.get("status") != "ok":
                    print(verification.get("detail"))
                    continue
            refreshed_command = understand_analyze_command()
            if refreshed_command:
                results.append(run_graph_command(root, action, refreshed_command))
            else:
                if install_option.get("platform") == "claude":
                    detail = (
                        f"Understand-Anything 已安装/启用到 Claude Code，但当前 shell 不能执行 slash command；"
                        f"请在 Claude Code 当前会话运行 {UNDERSTAND_CLAUDE_RELOAD_COMMAND}，"
                        f"再运行 {action.get('agentCommand')}，完成后立即执行 {PROJECT_REFRESH_AGENT_COMMAND}。"
                    )
                else:
                    detail = (
                        f"Understand-Anything 已安装到 agent，但当前 shell 不能直接识别它；"
                        f"请触发 Understand-Anything skill 或运行 {action.get('agentCommand')}，"
                        f"完成后立即执行 {PROJECT_REFRESH_AGENT_COMMAND}；不能触发 slash command 时执行 {PROJECT_REFRESH_CLI_COMMAND}。"
                    )
                print(detail)
                results.append(
                    {
                        "tool": tool,
                        "status": "needs-agent",
                        "command": action.get("agentCommand"),
                        "refreshCommand": PROJECT_REFRESH_AGENT_COMMAND,
                        "fallbackRefreshCommand": PROJECT_REFRESH_CLI_COMMAND,
                        "detail": detail,
                    }
                )
    return results


def tooling_with_graph_actions(tooling: dict[str, Any], actions: list[dict[str, Any]]) -> dict[str, Any]:
    subset = dict(tooling)
    subset["graphActions"] = actions
    return subset


def handle_tooling_setup(
    root: Path,
    tooling: dict[str, Any],
    interactive: bool,
    setup_missing: bool,
    with_graph: bool,
    *,
    allow_repo_runner: bool = False,
    allow_env_command: bool = False,
    allow_external_path: bool = False,
) -> list[dict[str, Any]]:
    if not with_graph:
        return []
    if tooling_has_missing_optional(tooling):
        print_tooling_summary(tooling)
    actions = tooling.get("graphActions", [])
    installed = [action for action in actions if action.get("analyzeCommand")]
    pending = [action for action in actions if not action.get("analyzeCommand")]
    permissions = {
        "allow_repo_runner": allow_repo_runner,
        "allow_env_command": allow_env_command,
        "allow_external_path": allow_external_path,
    }
    results = setup_graph_tools(root, tooling_with_graph_actions(tooling, installed), auto_approve=True, **permissions) if installed else []
    if setup_missing and pending:
        results.extend(setup_graph_tools(root, tooling_with_graph_actions(tooling, pending), auto_approve=True, **permissions))
    elif interactive and pending:
        if sys.stdin.isatty():
            results.extend(setup_graph_tools(root, tooling_with_graph_actions(tooling, pending), auto_approve=False, **permissions))
        else:
            print("当前不是交互终端，已跳过缺失图谱工具安装；可先运行 graph-tools --json 再确认安装。")
    return results


# Public compatibility facade for the extracted scanner and graph modules.
extract_object_argument_blocks = frontend_scanner.extract_object_argument_blocks
split_top_level_items = frontend_scanner.split_top_level_items
top_level_object_keys = frontend_scanner.top_level_object_keys
extract_vue_props = frontend_scanner.extract_vue_props
extract_emits = frontend_scanner.extract_emits
component_scope = frontend_scanner.component_scope
extract_service_prefixes = frontend_scanner.extract_service_prefixes
extract_api_endpoints = frontend_scanner.extract_api_endpoints
extract_exported_functions = frontend_scanner.extract_exported_functions
route_module_info = frontend_scanner.route_module_info
extract_react_props = frontend_scanner.extract_react_props
unique_limited = backend_scanner.unique_limited
flatten_regex_hits = backend_scanner.flatten_regex_hits
annotation_values = backend_scanner.annotation_values
detect_backend_framework = backend_scanner.detect_backend_framework
extract_backend_methods = backend_scanner.extract_backend_methods
extract_backend_fields = backend_scanner.extract_backend_fields
extract_repository_methods = backend_scanner.extract_repository_methods
extract_sql_ops = backend_scanner.extract_sql_ops
extract_config_keys = backend_scanner.extract_config_keys
extract_permission_signals = backend_scanner.extract_permission_signals
extract_transaction_signals = backend_scanner.extract_transaction_signals
extract_remote_call_signals = backend_scanner.extract_remote_call_signals
extract_message_job_signals = backend_scanner.extract_message_job_signals
extract_error_code_signals = backend_scanner.extract_error_code_signals
detect_graph_sources = graph_module.detect_graph_sources
understand_graph_summary = graph_module.understand_graph_summary
path_prefix = graph_module.path_prefix


def extract_backend_endpoints(text: str, suffix: str = ".java") -> list[str]:
    return backend_scanner.extract_backend_endpoints(text, suffix)


def scan_frontend(root: Path, files: list[Path]) -> dict[str, Any]:
    return frontend_scanner.scan_frontend(
        root,
        files,
        read_text=read_text,
        rel=rel,
        cache=_ACTIVE_SCAN_CACHE,
    )


def scan_backend(root: Path, files: list[Path], config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return backend_scanner.scan_backend(
        root,
        files,
        config,
        read_text=read_text,
        rel=rel,
        path_matches_pattern=path_matches_pattern,
        cache=_ACTIVE_SCAN_CACHE,
    )


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
        "schemaVersion": 2,
        "toolVersion": VERSION,
        "projectRoot": ".",
        "generatedAt": now_iso(),
        "git": git_info(root),
        "frameworks": package.get("frameworks", []),
        "packageName": package.get("packageName"),
        "packages": [
            {"path": item.get("path"), "name": item.get("name"), "frameworks": item.get("frameworks", [])}
            for item in package.get("packages", [])
        ],
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
            "可用时优先使用 GitNexus 和 Understand-Anything 作为图谱来源。",
        ],
    }


def default_config(root: Path, package: dict[str, Any], tooling: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {
        "schemaVersion": 2,
        "scan": {
            "include": ["**/*"],
            "exclude": sorted(EXCLUDED_DIRS),
            "excludeHidden": True,
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


def validate_string_list(value: Any, field: str, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, list)
        or (not value and not allow_empty)
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        fail_usage(f"配置项 {field} 必须是非空字符串数组。")
    return [item.strip() for item in value]


def validate_relative_pattern(pattern: str, field: str) -> None:
    candidate = Path(pattern)
    if candidate.is_absolute() or ".." in candidate.parts:
        fail_usage(f"配置项 {field} 只能使用项目内相对模式：{pattern}")


def validate_project_config(config: dict[str, Any]) -> None:
    scan = config.get("scan", {})
    if not isinstance(scan, dict):
        fail_usage("配置项 scan 必须是 JSON 对象。")
    includes = validate_string_list(scan.get("include", ["**/*"]), "scan.include")
    excludes = validate_string_list(scan.get("exclude", sorted(EXCLUDED_DIRS)), "scan.exclude", allow_empty=True)
    if not isinstance(scan.get("excludeHidden", True), bool):
        fail_usage("配置项 scan.excludeHidden 必须是布尔值。")
    for idx, pattern in enumerate(includes):
        validate_relative_pattern(pattern, f"scan.include[{idx}]")
    for idx, pattern in enumerate(excludes):
        validate_relative_pattern(pattern, f"scan.exclude[{idx}]")

    backend = config.get("backend", {})
    if not isinstance(backend, dict):
        fail_usage("配置项 backend 必须是 JSON 对象。")
    entrypoint_rules = backend.get("entrypointRules", [])
    if not isinstance(entrypoint_rules, list):
        fail_usage("配置项 backend.entrypointRules 必须是数组。")
    for idx, rule in enumerate(entrypoint_rules):
        if not isinstance(rule, dict):
            fail_usage(f"backend.entrypointRules[{idx}] 必须是 JSON 对象。")
        rule_type = rule.get("type")
        pattern = rule.get("pattern")
        if rule_type not in {"annotation", "call", "path", "regex"}:
            fail_usage(f"backend.entrypointRules[{idx}].type 不受支持：{rule_type}")
        if not isinstance(pattern, str) or not pattern.strip():
            fail_usage(f"backend.entrypointRules[{idx}].pattern 必须是非空字符串。")
        if rule_type == "path":
            validate_relative_pattern(pattern, f"backend.entrypointRules[{idx}].pattern")
        else:
            try:
                re.compile(pattern)
            except re.error as exc:
                fail_usage(f"backend.entrypointRules[{idx}] 正则无效：{exc}")

    rules = config.get("rules", {})
    if not isinstance(rules, dict):
        fail_usage("配置项 rules 必须是 JSON 对象。")
    for level in ("hard", "preferred", "inferred", "candidate"):
        if not isinstance(rules.get(level, []), list):
            fail_usage(f"配置项 rules.{level} 必须是数组。")
    for idx, rule in enumerate(rules.get("hard", [])):
        if isinstance(rule, str):
            continue
        if not isinstance(rule, dict):
            fail_usage(f"rules.hard[{idx}] 必须是字符串或 JSON 对象。")
        check = rule.get("check")
        if check is None:
            continue
        if not isinstance(check, dict):
            fail_usage(f"rules.hard[{idx}].check 必须是 JSON 对象。")
        check_type = check.get("type")
        if check_type not in HARD_CHECK_TYPES:
            fail_usage(f"rules.hard[{idx}].check.type 不受支持：{check_type}")
        field = "pattern" if check_type in {"forbid-regex", "require-regex"} else "path"
        value = check.get(field)
        if not isinstance(value, str) or not value.strip():
            fail_usage(f"rules.hard[{idx}].check.{field} 必须是非空字符串。")
        if field == "pattern":
            try:
                re.compile(value)
            except re.error as exc:
                fail_usage(f"rules.hard[{idx}].check.pattern 正则无效：{exc}")
        else:
            validate_relative_pattern(value, f"rules.hard[{idx}].check.path")
        for list_field in ("include", "exclude"):
            if list_field in check:
                patterns = validate_string_list(
                    check[list_field],
                    f"rules.hard[{idx}].check.{list_field}",
                    allow_empty=list_field == "exclude",
                )
                for pattern_idx, pattern in enumerate(patterns):
                    validate_relative_pattern(pattern, f"rules.hard[{idx}].check.{list_field}[{pattern_idx}]")

    quality = config.get("quality", {})
    if not isinstance(quality, dict):
        fail_usage("配置项 quality 必须是 JSON 对象。")
    commands = quality.get("commands", [])
    if not isinstance(commands, list):
        fail_usage("配置项 quality.commands 必须是数组。")
    for idx, command in enumerate(commands):
        if not isinstance(command, dict) or not isinstance(command.get("command"), str) or not command.get("command", "").strip():
            fail_usage(f"quality.commands[{idx}] 必须包含非空 command 字段。")
    timeout = quality.get("timeoutSeconds", 120)
    if not isinstance(timeout, int) or timeout <= 0:
        fail_usage("配置项 quality.timeoutSeconds 必须是正整数。")


def merge_quality_commands(existing: list[dict[str, Any]], detected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manual = [item for item in existing if item.get("source") not in {"package.json", "inferred"}]
    merged: list[dict[str, Any]] = []
    seen = set()
    for item in manual + detected:
        command = item.get("command")
        if command and command not in seen:
            merged.append(item)
            seen.add(command)
    return merged


def prepare_project_config(root: Path, package: dict[str, Any], tooling: dict[str, Any]) -> dict[str, Any]:
    path = project_dir(root) / "config.json"
    defaults = default_config(root, package, tooling)
    if not path.exists():
        config = defaults
    else:
        config = load_json_strict(path, "项目智能配置")
        validate_project_config(config)
        # schema v1 stored machine-specific tooling paths in the team config.
        config.pop("tooling", None)
        config["schemaVersion"] = 2
        scan = config.setdefault("scan", defaults["scan"])
        if scan.get("include") == LEGACY_SCAN_INCLUDE:
            scan["include"] = ["**/*"]
        scan.setdefault("include", ["**/*"])
        scan.setdefault("exclude", sorted(EXCLUDED_DIRS))
        scan.setdefault("excludeHidden", True)
        config.setdefault("backend", defaults["backend"])
        config.setdefault("rules", defaults["rules"])
        quality = config.setdefault("quality", {})
        quality["commands"] = merge_quality_commands(quality.get("commands", []), detect_quality_commands(root, package))
    config.pop("tooling", None)
    config["schemaVersion"] = 2
    validate_project_config(config)
    return config


def read_project_config(root: Path) -> dict[str, Any]:
    path = project_dir(root) / "config.json"
    if not path.exists():
        fail_usage("未找到 .project-intel/config.json。请先运行 project-intel init。")
    config = load_json_strict(path, "项目智能配置")
    validate_project_config(config)
    if config.get("scan", {}).get("include") == LEGACY_SCAN_INCLUDE:
        config["scan"]["include"] = ["**/*"]
    return config


def dominant_parent(paths: list[str], min_ratio: float = 0.8) -> Optional[tuple[str, int, int]]:
    """返回占比最高的父目录（目录、命中数、总数），占比不足时返回 None。"""
    parents = [str(Path(p).parent.as_posix()) for p in paths if p]
    if not parents:
        return None
    directory, hits = Counter(parents).most_common(1)[0]
    if hits / len(parents) < min_ratio:
        return None
    return directory, hits, len(parents)


def infer_standards(frontend: dict[str, Any], backend: dict[str, Any]) -> list[dict[str, Any]]:
    """从扫描事实推断项目规范，全部标记为 inferred 等级，需人工确认后升级。"""
    rules: list[dict[str, Any]] = []

    def add(scope: str, category: str, rule: str, evidence: str) -> None:
        rules.append({"scope": scope, "category": category, "rule": rule, "evidence": evidence, "level": "inferred"})

    components = frontend.get("components", [])
    hooks = frontend.get("hooks", [])
    routes = frontend.get("routes", [])
    api_modules = frontend.get("apiModules", [])
    stores = frontend.get("stores", [])
    styles = frontend.get("styles", [])
    redundancy = frontend.get("redundancyCandidates", [])

    # 命名：组件文件命名风格
    comp_names = [c.get("name", "") for c in components if c.get("name")]
    if len(comp_names) >= 3:
        pascal = [n for n in comp_names if re.fullmatch(r"[A-Z][A-Za-z0-9]+", n)]
        kebab = [n for n in comp_names if re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)+", n)]
        for style_name, matched in (("PascalCase", pascal), ("kebab-case", kebab)):
            if len(matched) / len(comp_names) >= 0.8:
                add("frontend", "naming", f"组件文件使用 {style_name} 命名", f"{len(matched)}/{len(comp_names)} 个组件符合")
                break

    # 命名：自定义 Hook
    if len(hooks) >= 2:
        add("frontend", "naming", "自定义 Hook 统一使用 useXxx 命名，一个文件一个 Hook", f"{len(hooks)} 个 Hook 均符合")

    # 目录结构：组件 / Hook / API 模块集中目录
    for label, items in (("公共组件", components), ("自定义 Hook 文件", hooks), ("API 请求模块", api_modules)):
        if len(items) >= 3:
            dom = dominant_parent([item.get("path", "") for item in items])
            if dom:
                directory, hits, total = dom
                add("frontend", "structure", f"{label}统一放在 `{directory}/` 目录", f"{hits}/{total} 个文件位于该目录")
    public_count = sum(1 for item in components if (item.get("scope") or component_scope(item.get("path", ""))) == "public")
    page_local_count = sum(1 for item in components if (item.get("scope") or component_scope(item.get("path", ""))) == "page-local")
    if public_count >= 3 and page_local_count >= 3:
        add(
            "frontend",
            "component-reuse",
            "跨业务复用能力优先沉淀到公共组件目录，页面私有组件仅服务当前业务域",
            f"公共组件 {public_count} 个，页面局部组件 {page_local_count} 个",
        )

    # 请求封装：API 模块统一封装
    if len(api_modules) >= 3:
        signal_counts = Counter(signal for module in api_modules for signal in (module.get("wrappers") or module.get("signals", [])))
        if signal_counts:
            top_signal, hits = signal_counts.most_common(1)[0]
            if hits / len(api_modules) >= 0.5:
                add(
                    "frontend",
                    "request",
                    f"API 请求统一通过 `{top_signal}` 封装发起；组件内不要直接调用 axios/fetch",
                    f"{hits}/{len(api_modules)} 个 API 模块使用 {top_signal}",
                )
        prefix_counts = Counter(prefix.get("value") for module in api_modules for prefix in module.get("servicePrefixes", []) if prefix.get("value"))
        for prefix, hits in prefix_counts.most_common(5):
            if hits >= 1:
                add("frontend", "api-prefix", f"接口服务前缀 `{prefix}` 已在 API 模块中声明，新增接口应复用同域前缀常量", f"{hits} 处声明服务前缀")

    if len(routes) >= 2:
        route_count = sum(route.get("routeCount", len(route.get("routes", []))) for route in routes)
        custom_count = sum(route.get("customNavigationCount", 0) for route in routes)
        add("frontend", "router", "小程序页面入口通过路由/分包配置维护，新增页面需同步路由配置和页面跳转路径", f"{len(routes)} 个路由配置文件，{route_count} 个页面路径")
        if custom_count >= max(3, route_count // 2):
            add("frontend", "router", "业务页面普遍使用自定义导航，新增页面应保持导航风格一致", f"{custom_count}/{route_count} 个页面配置 custom navigation")

    if stores:
        pinia_count = sum(1 for store in stores if store.get("definesStore"))
        if pinia_count:
            add("frontend", "state", "状态管理集中在 stores 目录，新增跨页面状态优先使用既有 Pinia store", f"{pinia_count}/{len(stores)} 个 store 文件使用 defineStore")

    # 样式：硬编码值治理
    hardcoded_total = sum(style.get("count", 0) for style in styles)
    if len(styles) >= 2 and hardcoded_total >= 20:
        add(
            "frontend",
            "style",
            "新增样式应使用主题变量/设计令牌，避免继续新增硬编码颜色和像素值",
            f"检测到 {hardcoded_total} 处硬编码值，分布于 {len(styles)} 个文件",
        )

    # 高频 UI 模式：重复模式应复用
    for candidate in redundancy:
        count = candidate.get("count", 0)
        name = candidate.get("name", "")
        if count >= 3 and name:
            locations = "、".join(candidate.get("locations", [])[:3])
            add(
                "frontend",
                "ui-pattern",
                f"「{name}」模式在项目中重复出现，新页面应复用已有实现或抽取公共组件/Hook",
                f"{count} 处出现，如 {locations}",
            )

    apis = backend.get("apis", [])
    services = backend.get("services", [])
    data_types = backend.get("dataTypes", [])
    repositories = backend.get("repositories", [])
    configs = backend.get("configs", [])
    permission_checks = backend.get("permissionChecks", [])
    transactions = backend.get("transactions", [])
    remote_calls = backend.get("remoteCalls", [])
    messages_jobs = backend.get("messagesJobs", [])
    error_codes = backend.get("errorCodes", [])
    utilities = backend.get("utilities", [])

    # 后端命名：Service / DTO 后缀
    service_names = [s.get("name", "") for s in services if s.get("name")]
    if len(service_names) >= 2:
        matched = [n for n in service_names if n.endswith(("Service", "Manager", "UseCase"))]
        if len(matched) / len(service_names) >= 0.8:
            add("backend", "naming", "服务类使用 Service 等后缀命名", f"{len(matched)}/{len(service_names)} 个服务符合")
    type_names = [t.get("name", "") for t in data_types if t.get("name")]
    if len(type_names) >= 2:
        for suffix in ("DTO", "Dto", "VO", "Entity", "Model"):
            matched = [n for n in type_names if n.endswith(suffix)]
            if len(matched) / len(type_names) >= 0.8:
                add("backend", "naming", f"数据类型使用 {suffix} 后缀命名", f"{len(matched)}/{len(type_names)} 个数据类型符合")
                break

    # 后端分层：Controller→Service→Repository
    if len(apis) >= 2 and len(services) >= 2 and len(repositories) >= 1:
        add(
            "backend",
            "backend-layering",
            "后端遵循 Controller→Service→Repository 分层，新接口按此分层组织，不要跨层直接访问数据",
            f"{len(apis)} 个入口、{len(services)} 个服务、{len(repositories)} 个仓库层文件",
        )
        annotation_hits = sum(1 for api in apis if "RestController" in (api.get("signals") or []))
        if annotation_hits / len(apis) >= 0.8:
            add("backend", "backend-layering", "HTTP 入口统一使用 @RestController 注解风格", f"{annotation_hits}/{len(apis)} 个入口符合")

    if len(apis) >= 1:
        framework_counts = Counter(api.get("framework") for api in apis if api.get("framework"))
        if framework_counts:
            framework, hits = framework_counts.most_common(1)[0]
            add("backend", "backend-api", f"后端入口主要使用 {framework} 风格，新增 API 应跟随同框架入口声明方式", f"{hits}/{len(apis)} 个入口匹配")

    if configs:
        key_count = sum(len(config.get("keys", [])) for config in configs)
        add("backend", "config", "配置项应集中在已有配置文件或配置类中维护，新增配置需同步默认值和环境差异", f"{len(configs)} 个配置文件/类，{key_count} 个配置键候选")

    if permission_checks:
        add("backend", "permission", "已有权限/认证信号需要作为接口改动前置检查，新增入口不能绕过认证边界", f"{len(permission_checks)} 个文件包含权限或认证信号")

    if transactions:
        add("backend", "transaction", "涉及写操作、订单、支付或跨表修改时复用已有事务边界，避免把事务拆散到调用方", f"{len(transactions)} 个文件包含事务信号")

    if remote_calls:
        add("backend", "remote-call", "远程调用应复用已有客户端/适配器，变更前需要检查超时、重试、错误映射和调用链影响", f"{len(remote_calls)} 个文件包含远程调用信号")

    if messages_jobs:
        add("backend", "message-job", "消息消费者和定时任务属于异步入口，修改时需要检查幂等、重试和调度配置", f"{len(messages_jobs)} 个文件包含消息或任务信号")

    if error_codes:
        add("backend", "error-code", "业务异常和错误码应复用既有错误码体系，新增错误需同步前端/调用方可识别的语义", f"{len(error_codes)} 个文件包含错误码或异常信号")

    if utilities:
        add("backend", "utility", "公共工具方法优先放在已有 util/common/helper 目录，业务代码不要复制相同转换、校验或封装逻辑", f"{len(utilities)} 个公共工具候选文件")

    return rules


def render_inferred_rules(rules: list[dict[str, Any]], scope: str) -> str:
    subset = [rule for rule in rules if rule.get("scope") == scope]
    if not subset:
        return "_本次扫描未推断出规范：样本不足或缺少该类信号。_"
    return "\n".join(f"- {rule['rule']}（证据：{rule['evidence']}）" for rule in subset)


def render_components_standard(frontend: dict[str, Any]) -> str:
    components = frontend.get("components", [])
    scope_counts = Counter(c.get("scope") or component_scope(c.get("path", "")) for c in components)
    public_components = [c for c in components if (c.get("scope") or component_scope(c.get("path", ""))) == "public"]
    repeated = [[name, count] for name, count in Counter(c.get("name") for c in components if c.get("name")).most_common(20) if count > 1]
    prop_rows = [[name, count] for name, count in Counter(prop for c in components for prop in c.get("props", [])).most_common(30)]
    emit_rows = [[name, count] for name, count in Counter(emit for c in components for emit in c.get("emits", [])).most_common(30)]
    page_dirs = Counter(path_prefix(c.get("path", ""), 4) for c in components if (c.get("scope") or component_scope(c.get("path", ""))) == "page-local")
    public_rows = [
        [c.get("name"), c.get("path"), ", ".join(c.get("props", [])[:8]), ", ".join(c.get("emits", [])[:8])]
        for c in public_components[:40]
    ]
    return f"""# 组件与复用规范

## 组件分布

{table(["范围", "数量"], [[scope, count] for scope, count in scope_counts.most_common()])}

## 公共组件清单

以下组件位于公共组件目录，新增页面能力前优先检索和复用：

{table(["组件", "路径", "Props", "Emits"], public_rows)}

## 页面局部组件热点

{table(["目录", "组件数"], [[directory, count] for directory, count in page_dirs.most_common(20)])}

## 重名/相似组件候选

重名组件通常意味着跨业务线复制或同类能力未沉淀，默认作为 `candidate` 检查：

{table(["组件名", "出现次数"], repeated)}

## 常见 Props / Emits

{table(["Prop", "出现次数"], prop_rows)}

{table(["Emit", "出现次数"], emit_rows)}

## 约定

- `src/components/**` 下组件视为公共能力，新增前必须先检索是否已有同类组件。
- `src/pages/**/components/**` 下组件视为页面局部能力；跨两个以上业务域重复时应评估沉淀为公共组件。
- 修改公共组件时需要检查 Props、Emits 和所有引用页面，避免破坏订单、政企、信息填写、认证等页面。
- 重名组件和相同页面模式默认是 `candidate`，人工确认后再升级为 `preferred` 或 `hard`。
"""


def render_api_standard(frontend: dict[str, Any]) -> str:
    modules = frontend.get("apiModules", [])
    wrapper_counts = Counter(wrapper for module in modules for wrapper in module.get("wrappers", []))
    signal_counts = Counter(signal for module in modules for signal in module.get("signals", []))
    prefixes = []
    for module in modules:
        for item in module.get("servicePrefixes", []):
            prefixes.append([item.get("name"), item.get("value"), module.get("path")])
    endpoint_prefixes = Counter()
    for module in modules:
        for endpoint in module.get("endpoints", []):
            normalized = re.sub(r"\$\{([^}]+)}", r"${\1}", endpoint)
            endpoint_prefixes[path_prefix(normalized.strip("/"), 2)] += 1
    module_rows = [
        [
            module.get("path"),
            ", ".join(module.get("wrappers", []) or module.get("signals", [])),
            len(module.get("exports", [])),
            "; ".join(module.get("endpoints", [])[:4]),
        ]
        for module in modules[:40]
    ]
    return f"""# API 与请求规范

## 请求封装

{table(["封装/信号", "出现次数"], [[name, count] for name, count in (wrapper_counts + signal_counts).most_common(20)])}

## 服务前缀

{table(["常量", "服务前缀", "来源"], prefixes[:30])}

## 接口路径热点

{table(["接口路径前缀", "出现次数"], [[name, count] for name, count in endpoint_prefixes.most_common(30)])}

## API 模块清单

{table(["模块", "请求封装", "导出函数数", "接口样例"], module_rows)}

## 约定

- 新增接口优先放在 `src/api/<domain>/index.ts` 或既有同域 API 模块中。
- 页面和组件不要直接调用 `uni.request`、`axios` 或裸 `fetch`；优先复用项目请求封装和已有 API 方法。
- 接口参数包装方式应跟随同域模块，例如是否使用数组包裹参数、是否传入 headerInfo、是否关闭缓存。
- 涉及登录态、错误上报、订阅消息、支付链路的接口变更，需要同步检查 `src/api/request.ts` 的拦截、错误处理和缓存逻辑。
"""


def render_router_standard(frontend: dict[str, Any]) -> str:
    routes = frontend.get("routes", [])
    route_rows = [
        [
            route.get("path"),
            ", ".join(route.get("baseUrls", [])),
            route.get("routeCount", len(route.get("routes", []))),
            route.get("customNavigationCount", 0),
            ", ".join(route.get("pluginProviders", [])),
        ]
        for route in routes
    ]
    title_words = Counter(title for route in routes for title in route.get("titlesSample", []))
    return f"""# 路由与分包规范

## 路由模块

{table(["配置文件", "baseUrl", "页面数", "custom 导航数", "插件 provider"], route_rows)}

## 页面标题热点

{table(["标题", "出现次数"], [[name, count] for name, count in title_words.most_common(30)])}

## 约定

- 新增页面优先放入对应 `src/router/modules/subpackages/*` 分包配置，保持 `baseUrl` 与实际页面目录一致。
- 已使用 `navigationStyle: 'custom'` 的业务线新增页面应保持导航风格一致，并复用现有导航组件。
- 使用小程序插件的页面需要在路由配置里保留 provider/version 信息，避免只改页面文件漏改路由配置。
- 页面路径、标题和分包归属是需求影响分析的一部分；改页面入口时需要同步检查跳转 URL 和 `uni.navigateTo/redirectTo` 调用。
"""


def fallback_domain_rows(frontend: dict[str, Any]) -> list[list[Any]]:
    candidates = standards_module.project_domain_candidates(frontend, {}, {})
    return [[item.get("name"), item.get("count"), ", ".join(item.get("paths", [])[:8])] for item in candidates]


def render_domain_flows_standard(frontend: dict[str, Any], graph: dict[str, Any]) -> str:
    understand = graph.get("understandSummary", {}) if isinstance(graph, dict) else {}
    domain_rows = [
        [item.get("name"), item.get("count"), ", ".join(item.get("paths", [])[:8]), "；".join(item.get("summaries", [])[:2])]
        for item in understand.get("domains", [])
    ]
    if not domain_rows:
        domain_rows = fallback_domain_rows(frontend)
    module_rows = [
        [item.get("path"), item.get("name"), item.get("summary"), ", ".join(item.get("tags", []))]
        for item in understand.get("keyModules", [])[:30]
    ]
    prefix_rows = [[prefix, count] for prefix, count in understand.get("topPathPrefixes", [])[:20]]
    return f"""# 业务流与图谱规范

## 业务域候选

以下内容来自 Understand-Anything 图谱摘要和项目轻量扫描，默认是 `inferred/candidate`，用于需求前影响分析：

{table(["业务域", "节点/文件数", "关键路径", "图谱摘要"], domain_rows)}

## 关键模块摘要

{table(["路径", "名称", "摘要", "标签"], module_rows)}

## 图谱路径热点

{table(["路径前缀", "节点数"], prefix_rows)}

## 约定

- 需求涉及任一业务域时，先按项目实际目录、模块和图谱标签定位对应业务域，再查 GitNexus/Understand-Anything 影响面。
- 修改业务流入口时需要同时检查页面、路由、API 模块、store、公共组件和错误处理链路。
- 图谱摘要只作为项目理解和影响分析输入，不替代源码确认；最终实现仍以源码和 `.project-intel/knowledge` 为准。
"""


def render_backend_api_standard(backend: dict[str, Any]) -> str:
    apis = backend.get("apis", [])
    candidates = backend.get("candidateEntrypoints", [])
    framework_rows = [[name, count] for name, count in Counter(api.get("framework") for api in apis if api.get("framework")).most_common()]
    endpoint_prefixes = Counter()
    for api in apis:
        for endpoint in api.get("endpoints", []):
            endpoint_prefixes[path_prefix(str(endpoint).strip("/"), 2)] += 1
    api_rows = [
        [
            api.get("path"),
            api.get("framework"),
            ", ".join(api.get("signals", [])[:6]),
            "; ".join(api.get("endpoints", [])[:6]),
            ", ".join(api.get("methods", [])[:8]),
        ]
        for api in apis[:60]
    ]
    candidate_rows = [[item.get("path"), item.get("reason"), item.get("level")] for item in candidates[:40]]
    return f"""# 后端 API 与入口规范

## 框架入口分布

{table(["框架/入口风格", "文件数"], framework_rows)}

## API/入口清单

{table(["路径", "框架", "入口信号", "路径样例", "方法样例"], api_rows)}

## 路径热点

{table(["路径前缀", "出现次数"], [[name, count] for name, count in endpoint_prefixes.most_common(30)])}

## 非标准入口候选

{table(["路径", "原因", "等级"], candidate_rows)}

## 约定

- 新增 API 入口应跟随同模块已有框架风格，例如 Spring 注解、Nest 装饰器或 router 注册。
- 不要只靠文件名判断入口；handler、facade、adapter、action 等候选入口需要在初始化后人工确认。
- 入口层只做参数接收、权限/校验编排和响应转换，业务编排应下沉到 Service/UseCase。
- 改入口路径时同步检查调用方、路由/网关配置、鉴权配置、测试和接口文档。
"""


def render_backend_services_standard(backend: dict[str, Any]) -> str:
    services = backend.get("services", [])
    method_words = Counter()
    for service in services:
        for method in service.get("methods", []):
            prefix = re.match(r"[a-z]+", str(method))
            if prefix:
                method_words[prefix.group(0)] += 1
    service_rows = [
        [
            service.get("name"),
            service.get("path"),
            ", ".join(service.get("methods", [])[:10]),
            len(service.get("transactions", [])),
            len(service.get("remoteCalls", [])),
            len(service.get("permissionSignals", [])),
        ]
        for service in services[:60]
    ]
    return f"""# 后端 Service 与业务编排规范

## Service 清单

{table(["名称", "路径", "方法样例", "事务信号", "远程调用", "权限信号"], service_rows)}

## 方法命名前缀热点

{table(["前缀", "出现次数"], [[name, count] for name, count in method_words.most_common(30)])}

## 约定

- Controller/API 层不要绕过 Service 直接访问 Repository/Mapper。
- 新增业务流程优先找同域 Service、Manager、UseCase、Facade，复用已有编排方式。
- 涉及写操作、支付、订单、库存、状态机等流程时，先确认事务边界和幂等策略。
- Service 内远程调用要复用已有客户端/适配器，并保留错误映射、超时、重试和日志链路。
"""


def render_backend_models_standard(backend: dict[str, Any]) -> str:
    data_types = backend.get("dataTypes", [])
    kind_rows = [[name, count] for name, count in Counter(item.get("kind") for item in data_types if item.get("kind")).most_common()]
    field_rows = [[name, count] for name, count in Counter(field for item in data_types for field in item.get("fields", [])).most_common(40)]
    annotation_rows = [[name, count] for name, count in Counter(annotation for item in data_types for annotation in item.get("annotations", [])).most_common(30)]
    model_rows = [
        [item.get("name"), item.get("kind"), item.get("path"), ", ".join(item.get("fields", [])[:12]), ", ".join(item.get("annotations", [])[:8])]
        for item in data_types[:60]
    ]
    return f"""# 后端 DTO/VO/Entity 规范

## 类型分布

{table(["类型", "数量"], kind_rows)}

## 数据类型清单

{table(["名称", "类型", "路径", "字段样例", "注解样例"], model_rows)}

## 字段热点

{table(["字段", "出现次数"], field_rows)}

## 注解热点

{table(["注解", "出现次数"], annotation_rows)}

## 约定

- DTO/VO 用于接口入参和出参，Entity/Model 用于持久化或领域状态，不要混用职责。
- 新增字段时同步检查序列化名称、校验注解、默认值、兼容性和前后端字段映射。
- Entity 改动需要检查 Mapper/Repository SQL、数据库迁移、缓存键和历史数据兼容。
- 相同字段组合重复出现时，优先复用已有 DTO/VO 或抽取公共片段。
"""


def render_backend_repository_standard(backend: dict[str, Any]) -> str:
    repositories = backend.get("repositories", [])
    kind_rows = [[name, count] for name, count in Counter(item.get("kind") for item in repositories if item.get("kind")).most_common()]
    sql_rows = [[op, count] for op, count in Counter(op for item in repositories for op in item.get("sqlOps", [])).most_common()]
    repo_rows = [
        [item.get("name"), item.get("kind"), item.get("path"), ", ".join(item.get("methods", [])[:12]), ", ".join(item.get("sqlOps", [])[:8])]
        for item in repositories[:60]
    ]
    return f"""# 后端 Repository/Mapper 规范

## 仓库层分布

{table(["类型", "数量"], kind_rows)}

## Repository/Mapper 清单

{table(["名称", "类型", "路径", "方法/SQL id 样例", "SQL 操作"], repo_rows)}

## SQL 操作热点

{table(["操作", "出现次数"], sql_rows)}

## 约定

- Repository/Mapper 只负责数据访问，不承载业务流程、权限判断或跨服务编排。
- 新增查询优先复用已有方法；确需新增时保持同域命名、参数对象和分页约定。
- 修改 SQL 或 Mapper XML 时检查关联 DTO/Entity 字段、索引、排序、分页和空值行为。
- 写操作必须回看 Service 层事务边界，避免 Repository 内隐式提交破坏业务一致性。
"""


def render_backend_config_standard(backend: dict[str, Any]) -> str:
    configs = backend.get("configs", [])
    key_prefix_rows = []
    key_counter = Counter()
    for config in configs:
        for key in config.get("keys", []):
            key_counter[str(key).split(".")[0]] += 1
    key_prefix_rows = [[name, count] for name, count in key_counter.most_common(40)]
    config_rows = [[item.get("path"), item.get("kind"), ", ".join(item.get("keys", [])[:15])] for item in configs[:80]]
    return f"""# 后端配置规范

## 配置文件/配置类

{table(["路径", "类型", "配置键样例"], config_rows)}

## 配置前缀热点

{table(["前缀", "出现次数"], key_prefix_rows)}

## 约定

- 新增配置项优先放到同域已有配置文件或配置类，并保持前缀命名一致。
- 配置变更需要同步默认值、环境变量、测试环境配置、部署文档和回滚策略。
- 涉及开关、限流、超时、重试、灰度的配置，需要在 review 中说明默认行为。
- 不要把密钥、token、密码或私有地址沉淀到项目规范；这里只保留配置键和路径。
"""


def render_backend_security_standard(backend: dict[str, Any]) -> str:
    checks = backend.get("permissionChecks", [])
    signal_rows = [[name, count] for name, count in Counter(signal for item in checks for signal in item.get("signals", [])).most_common(40)]
    check_rows = [[item.get("path"), ", ".join(item.get("signals", [])[:12]), item.get("level")] for item in checks[:80]]
    return f"""# 后端权限与认证规范

## 权限/认证信号

{table(["路径", "信号样例", "等级"], check_rows)}

## 信号热点

{table(["信号", "出现次数"], signal_rows)}

## 约定

- 新增入口必须检查同模块已有认证、鉴权、token、session、角色和权限注解。
- 权限判断优先复用已有 guard/interceptor/filter/helper，不要在业务方法里复制判断。
- 修改鉴权逻辑时同步检查匿名访问、内部调用、批量接口、管理端和定时任务入口。
- 权限缺失默认是 review 阻断风险；扫描命中仍为 `candidate`，最终以源码和人工确认升级。
"""


def render_backend_transaction_standard(backend: dict[str, Any]) -> str:
    transactions = backend.get("transactions", [])
    signal_rows = [[name, count] for name, count in Counter(signal for item in transactions for signal in item.get("signals", [])).most_common(40)]
    transaction_rows = [[item.get("path"), ", ".join(item.get("signals", [])[:12]), item.get("level")] for item in transactions[:80]]
    return f"""# 后端事务边界规范

## 事务信号

{table(["路径", "信号样例", "等级"], transaction_rows)}

## 信号热点

{table(["信号", "出现次数"], signal_rows)}

## 约定

- 涉及订单、支付、库存、状态变更、多表写入时，先确认已有事务边界。
- 不要把一个原子业务流程拆成多个无保护写操作；异步流程需要说明补偿和幂等。
- 远程调用和事务混用时要特别审查超时、重复提交、回滚语义和最终一致性。
- 新增事务注解或事务模板时同步检查调用链是否经过代理，避免事务不生效。
"""


def render_backend_remote_calls_standard(backend: dict[str, Any]) -> str:
    remote_calls = backend.get("remoteCalls", [])
    signal_rows = [[name, count] for name, count in Counter(signal for item in remote_calls for signal in item.get("signals", [])).most_common(40)]
    remote_rows = [[item.get("path"), ", ".join(item.get("signals", [])[:12]), item.get("level")] for item in remote_calls[:80]]
    return f"""# 后端远程调用规范

## 远程调用信号

{table(["路径", "信号样例", "等级"], remote_rows)}

## 信号热点

{table(["信号", "出现次数"], signal_rows)}

## 约定

- 远程调用优先复用已有 Feign/Dubbo/gRPC/HTTP 客户端或公司内部适配器。
- 新增调用必须检查超时、重试、熔断、错误码映射、日志追踪和调用方降级行为。
- 变更远程接口入参/出参时同步检查 DTO、调用链、Mock、契约测试和下游兼容。
- Review 时把远程调用视为影响面扩大点，优先结合 GitNexus 调用链或图谱上下文确认风险。
"""


def render_backend_async_standard(backend: dict[str, Any]) -> str:
    messages_jobs = backend.get("messagesJobs", [])
    signal_rows = [[name, count] for name, count in Counter(signal for item in messages_jobs for signal in item.get("signals", [])).most_common(40)]
    async_rows = [[item.get("path"), ", ".join(item.get("signals", [])[:12]), item.get("level")] for item in messages_jobs[:80]]
    return f"""# 后端消息与任务规范

## 消息/任务信号

{table(["路径", "信号样例", "等级"], async_rows)}

## 信号热点

{table(["信号", "出现次数"], signal_rows)}

## 约定

- 消息消费者、事件监听器和定时任务都是后端入口，需求影响分析不能只看 HTTP Controller。
- 修改异步入口需要检查幂等、重试、死信/补偿、并发控制、调度频率和监控告警。
- 新增任务配置时同步检查配置文件、部署环境、开关和测试数据隔离。
- 定时任务或消费者调用 Service 时，复用同一套事务、权限边界和错误处理策略。
"""


def render_backend_errors_standard(backend: dict[str, Any]) -> str:
    error_codes = backend.get("errorCodes", [])
    signal_rows = [[name, count] for name, count in Counter(signal for item in error_codes for signal in item.get("signals", [])).most_common(60)]
    error_rows = [[item.get("path"), ", ".join(item.get("signals", [])[:15]), item.get("level")] for item in error_codes[:80]]
    return f"""# 后端错误码与异常规范

## 错误码/异常信号

{table(["路径", "信号样例", "等级"], error_rows)}

## 信号热点

{table(["信号", "出现次数"], signal_rows)}

## 约定

- 新增业务异常前先搜索既有 ErrorCode/ResultCode/ResponseCode 和异常类型。
- 错误码语义需要让前端、调用方和日志排障都能识别，不要只抛通用异常。
- 改错误码或异常映射时同步检查接口响应、重试逻辑、告警、埋点和用户提示。
- 异常处理属于硬规范候选；团队确认后可升级为 `preferred` 或 `hard`。
"""


def render_backend_utilities_standard(backend: dict[str, Any]) -> str:
    utilities = backend.get("utilities", [])
    utility_rows = [[item.get("name"), item.get("path"), ", ".join(item.get("exports", [])[:12])] for item in utilities[:80]]
    dir_rows = [[directory, count] for directory, count in Counter(path_prefix(item.get("path", ""), 4) for item in utilities).most_common(30)]
    return f"""# 后端公共工具规范

## 工具类/公共函数

{table(["名称", "路径", "导出/方法样例"], utility_rows)}

## 工具目录热点

{table(["目录", "数量"], dir_rows)}

## 约定

- 新增转换、校验、签名、时间、序列化、缓存 key 等逻辑前先检索已有工具。
- 工具函数应保持无业务副作用；需要访问数据库、远程服务或上下文时应放回 Service/Adapter。
- 多处复制的工具逻辑默认作为 `candidate` 沉淀建议，人工确认后再升级规则等级。
- 修改公共工具需要检查调用面和单元测试，因为它通常跨模块复用。
"""


def standards_docs(data: dict[str, Any]) -> dict[str, str]:
    frontend = data["frontend"]
    backend = data["backend"]
    config = data["config"]
    graph = data.get("graph", {})
    quality = config.get("quality", {}).get("commands", [])
    inferred_rules = config.get("rules", {}).get("inferred", [])
    docs = {}
    docs["quality.md"] = f"""# 质量检查

规则等级：

- `hard`：已确认的必守规则；带结构化 `check` 的规则自动验证，失败时 `project-intel check` 返回非零
- `preferred`：稳定的项目约定
- `inferred`：扫描器推断，需要人工审查
- `candidate`：非阻塞建议

纯文本 `hard` 规则会在质量报告中标记为 `manual-review`，由 Agent/评审人员核对，不会被 CLI 误判为自动通过或失败。

## 检测到的命令

{table(["类型", "命令", "来源"], [[c.get("kind"), c.get("command"), c.get("source")] for c in quality])}

## 策略

- 优先使用项目已有的 package scripts，而非推断的命令。
- 冗余发现默认为 `candidate`，直到人工升级规则。
- 审查时将项目质量检查与规范和图谱上下文结合使用。
"""
    docs["frontend.md"] = f"""# 前端规范

## 已提取的事实

- 发现的组件数：{len(frontend.get("components", []))}
- 发现的 Hooks 数：{len(frontend.get("hooks", []))}
- 发现的路由文件数：{len(frontend.get("routes", []))}
- 发现的 API 相关模块数：{len(frontend.get("apiModules", []))}
- 发现的状态管理文件数：{len(frontend.get("stores", []))}
- 冗余候选数：{len(frontend.get("redundancyCandidates", []))}

## 细分规范

- 公共组件与页面局部组件：`components.md`
- API 请求封装与服务前缀：`api.md`
- 路由、分包和页面入口：`router.md`
- 业务流与图谱摘要：`domain-flows.md`

## 推断规范

以下规范由扫描器从项目实际代码推断（`inferred` 等级），默认作为项目约定遵循；经人工确认后可升级为 `preferred` 或 `hard`：

{render_inferred_rules(inferred_rules, "frontend")}

## 默认规则

- 添加新组件或 Hook 前，优先复用已有的组件和 Hook。
- 使用项目已有的请求/状态/样式抽象（如果存在）。
- 最终审查前运行检测到的 lint/type/style/format 检查。
- 重复的表格/搜索/对话框/导出/权限模式视为组件或 Hook 抽取的候选。
"""
    docs["backend.md"] = f"""# 后端规范

## 已提取的事实

- 发现的 API/入口模块数：{len(backend.get("apis", []))}
- 发现的服务数：{len(backend.get("services", []))}
- 发现的 DTO/VO/Entity/模型文件数：{len(backend.get("dataTypes", []))}
- 发现的 Repository/Mapper 文件数：{len(backend.get("repositories", []))}
- 发现的配置文件/配置类数：{len(backend.get("configs", []))}
- 发现的权限/认证信号文件数：{len(backend.get("permissionChecks", []))}
- 发现的事务信号文件数：{len(backend.get("transactions", []))}
- 发现的远程调用信号文件数：{len(backend.get("remoteCalls", []))}
- 发现的消息/任务信号文件数：{len(backend.get("messagesJobs", []))}
- 发现的错误码/异常信号文件数：{len(backend.get("errorCodes", []))}
- 发现的公共工具候选数：{len(backend.get("utilities", []))}
- 候选非标准入口点数：{len(backend.get("candidateEntrypoints", []))}

## 细分规范

- API 与入口：`backend-api.md`
- Service 与业务编排：`backend-services.md`
- DTO/VO/Entity：`backend-models.md`
- Repository/Mapper：`backend-repository.md`
- 配置项：`backend-config.md`
- 权限与认证：`backend-security.md`
- 事务边界：`backend-transactions.md`
- 远程调用：`backend-remote-calls.md`
- 消息与任务：`backend-async.md`
- 错误码与异常：`backend-errors.md`
- 公共工具：`backend-utilities.md`

## 推断规范

以下规范由扫描器从项目实际代码推断（`inferred` 等级），默认作为项目约定遵循；经人工确认后可升级为 `preferred` 或 `hard`：

{render_inferred_rules(inferred_rules, "backend")}

## 默认规则

- 通过框架适配器、AST/调用模式和项目特定规则识别入口点。
- 不要仅依赖 `Controller` 命名。
- 保持服务、数据、仓库、权限、事务和配置的边界。
- 升级候选入口点为 hard 标准前需人工确认。
"""
    docs["reuse.md"] = """# 复用与冗余

## 策略

- 实现组件、Hook、API 客户端、服务或工具函数前，先搜索 `.project-intel/knowledge`。
- 重复的 UI、数据转换、校验、请求构建和样式块默认视为 `candidate` 发现。
- 候选升级为 `preferred` 或 `hard` 需人工确认。
"""
    docs["components.md"] = render_components_standard(frontend)
    docs["api.md"] = render_api_standard(frontend)
    docs["router.md"] = render_router_standard(frontend)
    docs["domain-flows.md"] = render_domain_flows_standard(frontend, graph)
    docs["backend-api.md"] = render_backend_api_standard(backend)
    docs["backend-services.md"] = render_backend_services_standard(backend)
    docs["backend-models.md"] = render_backend_models_standard(backend)
    docs["backend-repository.md"] = render_backend_repository_standard(backend)
    docs["backend-config.md"] = render_backend_config_standard(backend)
    docs["backend-security.md"] = render_backend_security_standard(backend)
    docs["backend-transactions.md"] = render_backend_transaction_standard(backend)
    docs["backend-remote-calls.md"] = render_backend_remote_calls_standard(backend)
    docs["backend-async.md"] = render_backend_async_standard(backend)
    docs["backend-errors.md"] = render_backend_errors_standard(backend)
    docs["backend-utilities.md"] = render_backend_utilities_standard(backend)
    return docs


def table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None detected._"
    def clean(cell: Any) -> str:
        if isinstance(cell, (list, tuple, set)):
            value = ", ".join(str(item) for item in cell)
        else:
            value = str(cell or "")
        return testing_module.sanitize_text(value).replace("\n", " ").replace("|", "\\|")
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(clean(cell) for cell in row) + " |")
    return "\n".join(out)


def collect_project_state(
    root: Path,
    package: dict[str, Any],
    tooling: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    global _ACTIVE_SCAN_CACHE
    _TEXT_CACHE.clear()
    cache_path = project_dir(root) / "local" / "scan-cache.json"
    _ACTIVE_SCAN_CACHE = core_module.IncrementalScanCache.load(cache_path)
    files = iter_files(root, config)
    graph_sources = detect_graph_sources(root)
    frontend = scan_frontend(root, files)
    backend = scan_backend(root, files, config)
    rules = config.setdefault("rules", {"hard": [], "preferred": [], "inferred": [], "candidate": []})
    rules["inferred"] = infer_standards(frontend, backend)
    manifest = build_manifest(root, files, package, graph_sources, tooling)
    graph = {
        "schemaVersion": 2,
        "generatedAt": now_iso(),
        "sources": graph_sources,
        "summary": {
            "components": len(frontend.get("components", [])),
            "hooks": len(frontend.get("hooks", [])),
            "apis": len(backend.get("apis", [])),
            "services": len(backend.get("services", [])),
            "candidateEntrypoints": len(backend.get("candidateEntrypoints", [])),
        },
        "gitnexusSummary": next((item for item in graph_sources if item.get("name") == "GitNexus"), {}),
        "understandSummary": understand_graph_summary(root),
    }
    graph["projectDomains"] = standards_module.project_domain_candidates(frontend, backend, graph)
    return {
        "files": files,
        "frontend": frontend,
        "backend": backend,
        "manifest": manifest,
        "graph": graph,
        "scanCache": _ACTIVE_SCAN_CACHE.payload(),
    }


def preview_init(root: Path, with_graph: bool = False, strict: bool = False) -> dict[str, Any]:
    if strict and not with_graph:
        fail_usage("--strict 不能与 --no-graph 同时使用。")
    package = detect_package(root)
    tooling = detect_tooling(root, package)
    config = prepare_project_config(root, package, tooling)
    state = collect_project_state(root, package, tooling, config)
    graph_sources = state["manifest"].get("graphSources", [])
    if strict and with_graph and not any(source.get("status") == "present" for source in graph_sources):
        fail_usage("请求了严格的图谱初始化，但没有有效的 GitNexus 或 Understand-Anything 图谱。")
    return {
        "dryRun": True,
        "manifest": state["manifest"],
        "config": config,
        "graph": state["graph"],
        "wouldWrite": [
            ".project-intel/manifest.json",
            ".project-intel/config.json",
            ".project-intel/knowledge/*.json",
            ".project-intel/graph/project-graph.json",
            ".project-intel/standards/*.md",
            ".project-intel/project-status.md",
            ".project-intel/requirements/<requirement-id>/*.md",
        ],
        "adapterWritesRequireExplicitFlag": True,
        "wouldRunGraph": with_graph and [action.get("analyzeCommand") for action in tooling.get("graphActions", []) if action.get("analyzeCommand")],
    }


def init_project(
    root: Path,
    refresh: bool = False,
    interactive: bool = False,
    setup_missing: bool = False,
    with_graph: bool = False,
    strict: bool = False,
    adapters: bool = False,
    allow_repo_runner: bool = False,
    allow_env_command: bool = False,
    allow_external_path: bool = False,
) -> dict[str, Any]:
    if strict and not with_graph:
        fail_usage("--strict 不能与 --no-graph 同时使用。")
    package = detect_package(root)
    tooling = detect_tooling(root, package)
    config = prepare_project_config(root, package, tooling)
    setup_results = handle_tooling_setup(
        root,
        tooling,
        interactive=interactive,
        setup_missing=setup_missing,
        with_graph=with_graph,
        allow_repo_runner=allow_repo_runner,
        allow_env_command=allow_env_command,
        allow_external_path=allow_external_path,
    )
    if setup_results:
        tooling = detect_tooling(root, package)
    state = collect_project_state(root, package, tooling, config)
    files = state["files"]
    frontend = state["frontend"]
    backend = state["backend"]
    manifest = state["manifest"]
    graph = state["graph"]
    graph_sources = manifest.get("graphSources", [])
    if strict and with_graph and not any(source.get("status") == "present" for source in graph_sources):
        fail_usage("请求了严格的图谱初始化，但没有有效的 GitNexus 或 Understand-Anything 图谱。")
    pdir = project_dir(root)
    for sub in ("standards", "knowledge", "graph", "requirements", "hooks", "cache", "local", "tmp"):
        (pdir / sub).mkdir(parents=True, exist_ok=True)
    ensure_project_intel_gitignore(pdir)
    write_json(pdir / "manifest.json", manifest)
    write_json(pdir / "config.json", config)
    write_json(pdir / "knowledge" / "frontend.json", frontend)
    write_json(pdir / "knowledge" / "backend.json", backend)
    write_json(pdir / "knowledge" / "files.json", file_index(root, files))
    write_json(pdir / "graph" / "project-graph.json", graph)
    write_json(pdir / "local" / "tooling.json", tooling)
    write_json(pdir / "local" / "scan-cache.json", state["scanCache"])
    for name, text in standards_docs({"frontend": frontend, "backend": backend, "config": config, "graph": graph}).items():
        write_text(pdir / "standards" / name, text)
    write_text(
        pdir / "project-status.md",
        build_project_status(root, manifest, frontend, backend, config, tooling, setup_results=setup_results),
    )
    adapter = {"agentFiles": [], "claude": None, "legacyCleanup": []}
    if adapters:
        ensure_gitignore(root)
        adapter = install_claude(root)
    return {
        "manifest": manifest,
        "frontend": frontend,
        "backend": backend,
        "config": config,
        "tooling": tooling,
        "setupResults": setup_results,
        "agentFiles": adapter.get("agentFiles", []),
        "claude": adapter.get("claude"),
        "legacyCleanup": adapter.get("legacyCleanup", []),
    }


def ensure_project_intel_gitignore(pdir: Path) -> None:
    path = pdir / ".gitignore"
    existing = read_text(path)
    existing_rules = {
        line.strip() for line in existing.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    required = ("cache/", "local/", "tmp/", "**/.manifest.lock", "**/.*.tmp")
    missing = [item for item in required if item not in existing_rules]
    if not missing:
        return
    block = "# Project Intelligence local-only files\n" + "\n".join(missing) + "\n"
    body = existing.rstrip() + ("\n\n" if existing.strip() else "") + block
    write_text(path, body)


def ensure_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    additions = [".project-intel/cache/", ".project-intel/local/", ".project-intel/tmp/"]
    raw = path.read_bytes() if path.exists() else b""
    existing = raw.decode("utf-8", errors="ignore")
    existing_rules = {
        line.strip()
        for line in existing.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    def already_ignored(item: str) -> bool:
        item = item.rstrip("/")
        return any(
            rule == item
            or rule.rstrip("/") == item
            or path_matches_pattern(item, rule)
            for rule in existing_rules
        )

    missing = [item for item in additions if not already_ignored(item)]
    if not missing:
        return

    block = "# Project Intelligence local artifacts\n" + "\n".join(missing) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    with path.open("ab") as handle:
        if raw and not raw.endswith((b"\n", b"\r")):
            handle.write(b"\n")
        if raw and existing.strip():
            handle.write(b"\n")
        handle.write(block.encode("utf-8"))
    path.chmod(mode)


def build_init_report(root: Path, manifest: dict[str, Any], frontend: dict[str, Any], backend: dict[str, Any], config: dict[str, Any], tooling: dict[str, Any]) -> str:
    source_rows = [[s.get("name"), s.get("status"), s.get("role"), s.get("path")] for s in manifest.get("graphSources", [])]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    action_rows = [[a.get("tool"), a.get("command"), "yes" if a.get("canRun") else "no"] for a in tooling.get("recommendedActions", [])]
    follow_up_rows = [
        [a.get("tool"), a.get("command"), a.get("refreshCommand") or a.get("fallbackRefreshCommand"), a.get("detail")]
        for a in tooling.get("followUpActions", [])
    ]
    return f"""# 项目智能报告

生成时间：`{manifest.get("generatedAt")}`

项目根目录：`{root}`

## 图谱来源

{table(["来源", "状态", "用途", "路径"], source_rows)}

## 前端概况

- 组件数：{len(frontend.get("components", []))}
- Hooks 数：{len(frontend.get("hooks", []))}
- API 模块数：{len(frontend.get("apiModules", []))}
- 冗余候选数：{len(frontend.get("redundancyCandidates", []))}

## 后端概况

- API / 入口模块数：{len(backend.get("apis", []))}
- 服务数：{len(backend.get("services", []))}
- 数据类型数：{len(backend.get("dataTypes", []))}
- 仓库 / 映射器数：{len(backend.get("repositories", []))}
- 候选入口点数：{len(backend.get("candidateEntrypoints", []))}

## 质量命令

{table(["类型", "命令", "来源"], quality_rows)}

## 推荐的工具操作

{table(["工具", "命令", "可运行"], action_rows)}

## 后续 Agent 步骤

{table(["工具", "图谱命令", "刷新命令", "说明"], follow_up_rows)}
"""


def build_project_status(
    root: Path,
    manifest: dict[str, Any],
    frontend: dict[str, Any],
    backend: dict[str, Any],
    config: dict[str, Any],
    tooling: dict[str, Any],
    *,
    setup_results: Optional[list[dict[str, Any]]] = None,
    quality_report: str = "",
) -> str:
    """Build the single replaceable project-level status view.

    Requirement history never belongs here; it lives in requirements/<id>/manifest.json.
    """
    graph_rows = [
        [item.get("name"), item.get("status"), item.get("path")]
        for item in manifest.get("graphSources", [])
    ]
    quality_commands = [
        [item.get("kind"), item.get("command"), item.get("source")]
        for item in config.get("quality", {}).get("commands", [])
    ]
    setup_rows = [
        [item.get("tool"), item.get("status"), item.get("detail")]
        for item in (setup_results or [])
    ]
    quality_section = quality_report.strip() or "_尚未单独运行项目质量检查。_"
    return f"""# 项目状态

更新时间：`{now_iso()}`

## 项目事实

- 项目：{manifest.get("name") or root.name}
- 索引文件数：{manifest.get("fileCount", 0)}
- 框架：{", ".join(manifest.get("frameworks", []) or ["未识别"])}
- 前端组件：{len(frontend.get("components", []))}
- Hooks：{len(frontend.get("hooks", []))}
- 后端 API：{len(backend.get("apis", []))}
- 服务：{len(backend.get("services", []))}
- 前端冗余候选：{len(frontend.get("redundancyCandidates", []))}
- 后端候选入口：{len(backend.get("candidateEntrypoints", []))}

## 图谱来源

{table(["来源", "状态", "路径"], graph_rows)}

## 质量命令

{table(["类型", "命令", "来源"], quality_commands)}

## 工具准备

{table(["工具", "状态", "说明"], setup_rows) if setup_rows else "_本次没有执行工具安装或初始化。_"}

## 最近质量检查

{quality_section}

## 需求档案

每个需求的需求文档、设计文档、可选计划、测试报告、收口总结和历史状态均位于 `.project-intel/requirements/<需求号>/`；本文件只表示可覆盖的项目级当前状态。
"""


def build_redundancy_report(frontend: dict[str, Any]) -> str:
    rows = [
        [item.get("name"), item.get("count"), ", ".join(item.get("locations", [])[:8]), item.get("level")]
        for item in frontend.get("redundancyCandidates", [])
    ]
    return f"""# 冗余候选

这些发现默认为 `candidate` 级别，不会阻塞开发。

{table(["模式", "数量", "位置", "级别"], rows)}
"""


def build_tooling_report(tooling: dict[str, Any], setup_results: list[dict[str, Any]]) -> str:
    required_rows = [[item.get("name"), item.get("status")] for item in tooling.get("required", [])]
    optional = tooling.get("optional", {})
    pm_rows = [[item.get("name"), item.get("status"), "yes" if item.get("selected") else ""] for item in optional.get("packageManagers", [])]
    quality_rows = [[item.get("kind"), item.get("status"), item.get("command")] for item in optional.get("qualityTools", [])]
    action_rows = [[item.get("tool"), item.get("command"), "yes" if item.get("canRun") else "no"] for item in tooling.get("recommendedActions", [])]
    follow_up_rows = [
        [item.get("tool"), item.get("command"), item.get("refreshCommand") or item.get("fallbackRefreshCommand"), item.get("detail")]
        for item in tooling.get("followUpActions", [])
    ]
    setup_rows = [[item.get("tool"), item.get("status"), item.get("command") or item.get("detail"), item.get("exitCode", "")] for item in setup_results]
    return f"""# 工具报告

生成时间：`{tooling.get("generatedAt")}`

## 必需工具

{table(["工具", "状态"], required_rows)}

## 可选运行时

- Git：`{optional.get("git", {}).get("status")}`
- Node：`{optional.get("node", {}).get("status")}`
- GitNexus：`{optional.get("gitnexus", {}).get("status")}`
- Understand-Anything：`{optional.get("understandAnything", {}).get("status")}`

## 包管理器

{table(["名称", "状态", "已选"], pm_rows)}

## 质量命令

{table(["类型", "状态", "命令"], quality_rows)}

## 推荐操作

{table(["工具", "命令", "可运行"], action_rows)}

## 后续 Agent 步骤

{table(["工具", "图谱命令", "刷新命令", "说明"], follow_up_rows)}

## 安装结果

{table(["工具", "状态", "命令/详情", "退出码"], setup_rows)}

`init` 默认检查图谱工具。已检测到可执行分析命令时会自动运行分析；在交互终端中，未检测到时会询问是否安装/初始化，选择跳过时继续初始化 `.project-intel`。非交互环境不会等待输入；使用 `--setup-missing` 可在用户已授权后跳过询问并直接运行支持的安装/初始化命令。对于只能在 agent 会话里执行的图谱工具，CLI 会把它们列到“后续 Agent 步骤”，但不会把初始化视为失败或反复要求重跑。
"""


def ensure_initialized(root: Path) -> None:
    if not (project_dir(root) / "manifest.json").exists():
        fail_usage("未找到 .project-intel/manifest.json。请先运行 project-intel init。")


def load_project_snapshot(root: Path) -> dict[str, Any]:
    ensure_initialized(root)
    pdir = project_dir(root)
    return {
        "manifest": load_json(pdir / "manifest.json", {}),
        "config": read_project_config(root),
        "frontend": load_json(pdir / "knowledge" / "frontend.json", {}),
        "backend": load_json(pdir / "knowledge" / "backend.json", {}),
        "graph": load_json(pdir / "graph" / "project-graph.json", {}),
    }


def text_has_any(value: str, words: list[str]) -> bool:
    lowered = value.lower()
    return any(word.lower() in lowered for word in words)


def collect_reuse_candidates(snapshot: dict[str, Any], limit: int = 12) -> list[dict[str, str]]:
    frontend = snapshot.get("frontend", {})
    backend = snapshot.get("backend", {})
    candidates: list[dict[str, str]] = []
    for item in frontend.get("components", [])[:limit]:
        candidates.append({"type": "component", "name": str(item.get("name") or ""), "path": str(item.get("path") or "")})
    for item in frontend.get("hooks", [])[:limit]:
        candidates.append({"type": "hook", "name": str(item.get("name") or ""), "path": str(item.get("path") or "")})
    for item in frontend.get("apiModules", [])[:limit]:
        candidates.append({"type": "frontend-api", "name": str(item.get("path") or ""), "path": str(item.get("path") or "")})
    for item in backend.get("services", [])[:limit]:
        candidates.append({"type": "service", "name": str(item.get("name") or ""), "path": str(item.get("path") or "")})
    for item in backend.get("utilities", [])[:limit]:
        candidates.append({"type": "utility", "name": str(item.get("name") or ""), "path": str(item.get("path") or "")})
    return candidates[:limit]


def standard_paths(snapshot: dict[str, Any]) -> list[str]:
    names = [
        "standards/frontend.md",
        "standards/components.md",
        "standards/api.md",
        "standards/router.md",
        "standards/backend.md",
        "standards/backend-api.md",
        "standards/backend-services.md",
        "standards/quality.md",
    ]
    config = snapshot.get("config", {})
    if config.get("rules", {}).get("hard"):
        names.append("config.json#rules.hard")
    return [f".project-intel/{name}" for name in names]


def infer_affected_areas(task: str, snapshot: dict[str, Any]) -> list[str]:
    areas: list[str] = []
    checks = [
        ("frontend", ["页面", "组件", "前端", "vue", "react", "样式", "按钮", "弹框", "表格", "路由"]),
        ("backend", ["后端", "接口", "service", "controller", "dto", "entity", "mapper", "repository"]),
        ("api", ["api", "接口", "请求", "参数", "返回", "响应", "兼容"]),
        ("data", ["数据库", "表", "字段", "缓存", "状态", "数据", "迁移"]),
        ("auth", ["权限", "登录", "认证", "授权", "角色"]),
        ("quality", ["lint", "类型", "测试", "质量", "冗余", "规范"]),
        ("release", ["发布", "回滚", "灰度", "开关", "监控", "告警"]),
    ]
    for name, words in checks:
        if text_has_any(task, words):
            areas.append(name)
    if not areas:
        frontend = snapshot.get("frontend", {})
        backend = snapshot.get("backend", {})
        if frontend.get("components") or frontend.get("hooks"):
            areas.append("frontend")
        if backend.get("apis") or backend.get("services"):
            areas.append("backend")
    return areas or ["unknown"]


def analyze_task_intake(
    root: Path,
    task: str,
    snapshot: Optional[dict[str, Any]] = None,
    track: str = "auto",
    ticket_kind: str = "requirement",
) -> dict[str, Any]:
    if track not in TRACK_CHOICES:
        fail_usage(f"--track 只能是：{', '.join(TRACK_CHOICES)}")
    snapshot = snapshot or load_project_snapshot(root)
    raw = " ".join(task.split())
    lowered = raw.lower()
    reasons: list[str] = []
    risk_flags: list[str] = []
    missing: list[str] = []

    complex_keywords = ["迁移", "重构", "架构", "兼容", "权限", "支付", "数据库", "事务", "缓存", "安全", "灰度", "回滚", "跨端", "多模块", "性能", "并发", "消息", "定时", "发布"]
    quick_keywords = ["文案", "样式", "颜色", "间距", "错别字", "小改", "简单", "日志", "注释", "配置说明"]
    if len(raw) < 12:
        missing.append("需求描述较短，需要在实施前确认目标行为和验收方式。")
    if "?" in raw or "？" in raw:
        missing.append("需求里包含疑问句，需要先澄清再进入实现。")
    if text_has_any(raw, complex_keywords):
        risk_flags.append("涉及复杂或高风险关键词，需要显式检查影响面、兼容性和验证证据。")
    if text_has_any(raw, ["接口", "api", "参数", "返回", "兼容"]):
        risk_flags.append("涉及接口契约，需确认入参、出参、兼容和错误行为。")
    if text_has_any(raw, ["页面", "组件", "弹框", "表格", "样式"]):
        reasons.append("包含页面/组件信号，实施前需要检查可复用组件和页面模式。")
    if text_has_any(raw, ["后端", "service", "controller", "事务", "数据库"]):
        reasons.append("包含后端信号，实施前需要检查分层、事务、错误码和配置。")

    selected_track = track
    if selected_track == "auto":
        if risk_flags or len(raw) > 120 or text_has_any(lowered, complex_keywords):
            selected_track = "complex"
            reasons.append("自动分流为 complex：需求存在较高影响面或需要跨层设计。")
        elif text_has_any(lowered, quick_keywords) and not risk_flags:
            selected_track = "quick"
            reasons.append("自动分流为 quick：需求看起来是局部低风险变更。")
        else:
            selected_track = "standard"
            reasons.append("自动分流为 standard：需要常规 spec/plan 思考，但不强制落盘。")
    else:
        reasons.append(f"用户或调用方显式指定 {selected_track} track。")

    stages_by_track = {
        "quick": ["intake", "spec", "design", "readiness-gate", "test-plan", "task", "test-evidence", "review", "finish", "maintain"],
        "standard": ["intake", "brainstorm-lite", "spec", "design", "plan-in-context", "readiness-gate", "test-plan", "task", "test-evidence", "review", "finish", "maintain"],
        "complex": ["intake", "brainstorm", "spec", "design", "plan", "readiness-gate", "test-plan", "task-or-orchestrate", "test-evidence", "review", "finish", "maintain"],
    }
    if ticket_kind == "bug":
        for stages in stages_by_track.values():
            design_index = stages.index("design")
            stages.insert(design_index, "debug")
    readiness = "needs-clarification" if missing else "ready"
    if selected_track == "complex" and not text_has_any(raw, ["验收", "测试", "兼容", "回滚", "方案", "边界"]):
        readiness = "needs-clarification"
        missing.append("复杂需求需要补充验收、边界、兼容或回滚信息。")

    return {
        "track": selected_track,
        "reasons": reasons,
        "riskFlags": risk_flags,
        "missingInformation": missing,
        "requiredStages": stages_by_track[selected_track],
        "affectedAreas": infer_affected_areas(raw, snapshot),
        "reuseCandidates": collect_reuse_candidates(snapshot),
        "standards": standard_paths(snapshot),
        "readiness": readiness,
    }


def bullet_list(values: list[Any], empty: str = "_无_") -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def build_intake_doc(root: Path, task: str, snapshot: dict[str, Any], analysis: dict[str, Any]) -> str:
    reuse_rows = [[item.get("type"), item.get("name"), item.get("path")] for item in analysis.get("reuseCandidates", [])]
    return f"""# 需求入口分析

生成时间：`{now_iso()}`

## 需求

{truncate(task, 3000)}

## 分流结论

- Track：`{analysis.get("track")}`
- Readiness：`{analysis.get("readiness")}`
- 影响区域：{", ".join(analysis.get("affectedAreas", []))}

## 原因

{bullet_list(analysis.get("reasons", []))}

## 风险与缺口

### 风险标记

{bullet_list(analysis.get("riskFlags", []))}

### 缺失信息

{bullet_list(analysis.get("missingInformation", []))}

## 必经阶段

{bullet_list(analysis.get("requiredStages", []))}

## 复用候选

{table(["类型", "名称", "路径"], reuse_rows)}

## 相关规范

{bullet_list(analysis.get("standards", []))}
"""


def write_intake(root: Path, task: str, track: str = "auto", write_report: bool = False) -> Optional[Path]:
    snapshot = load_project_snapshot(root)
    analysis = analyze_task_intake(root, task, snapshot, track=track)
    body = build_intake_doc(root, task, snapshot, analysis)
    print(body)
    if not write_report:
        return None
    path = project_dir(root) / "reports" / "task-intake.md"
    write_text(path, body)
    print(f"\n已写入需求入口分析：{path}")
    return path


def spec_filename(title: str, suffix: str) -> str:
    return f"{today_slug()}-{slugify(title)}-{suffix}.md"


def build_spec_doc(root: Path, title: str, requirement: str, snapshot: dict[str, Any], track: str = "auto") -> str:
    manifest = snapshot["manifest"]
    config = snapshot["config"]
    frontend = snapshot["frontend"]
    backend = snapshot["backend"]
    analysis = analyze_task_intake(root, requirement, snapshot, track=track)
    graph_rows = [[s.get("name"), s.get("status"), s.get("role")] for s in manifest.get("graphSources", [])]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    reuse_rows = [[item.get("type"), item.get("name"), item.get("path")] for item in analysis.get("reuseCandidates", [])]
    return f"""# {title} 需求文档

生成时间：`{now_iso()}`

Track：`{analysis.get("track")}`
Readiness：`{analysis.get("readiness")}`

## 需求

{truncate(requirement, 3000)}

## 需求入口与范围

- 影响区域：{", ".join(analysis.get("affectedAreas", []))}
- 必经阶段：{", ".join(analysis.get("requiredStages", []))}

### 已知风险

{bullet_list(analysis.get("riskFlags", []))}

### 待澄清信息

{bullet_list(analysis.get("missingInformation", []))}

## 项目上下文

- 项目根目录：`.`
- 框架：{", ".join(manifest.get("frameworks", []) or ["未知"])}
- 组件数：{len(frontend.get("components", []))}
- Hooks 数：{len(frontend.get("hooks", []))}
- API 模块数：{len(frontend.get("apiModules", []))}
- 后端 API 数：{len(backend.get("apis", []))}
- 服务数：{len(backend.get("services", []))}

## 图谱来源

{table(["来源", "状态", "用途"], graph_rows)}

## 复用候选

{table(["类型", "名称", "路径"], reuse_rows)}

## 相关规范

- 添加新抽象前，复用已有的组件、Hook、请求工具、服务和领域模式。
- 冗余发现默认为 `candidate`，除非升级为 `hard`。
- 涉及接口、状态、权限、异常、兼容、缓存或异步行为时，必须在实现前锁定契约。

## 行为契约

- 当前行为：实施前从源码、图谱或现有页面/API 中确认。
- 目标行为：以本需求描述和后续澄清为准。
- 不做事项：没有被明确纳入的重构、视觉改版、接口迁移、强制 hook 拦截和发布动作不在本 spec 默认范围内。
- 输入/输出：涉及 API、组件 Props/Events、DTO/VO 或配置项时，需要列出字段、默认值、错误行为和兼容要求。
- 状态/权限/异常：涉及状态流转、权限校验、支付/订阅/事务/远程调用时，需要补充失败、取消、重试、超时和幂等策略。
- UI 验收：涉及页面时，需要覆盖加载、空态、错误态、禁用态、移动端/桌面端和可访问性可见行为。
- 发布与回滚：涉及数据、权限、远程调用、缓存或开关时，需要说明灰度、回滚和观测方式。

## 质量门禁

{table(["类型", "命令", "来源"], quality_rows)}

## 验收到证据映射

- 功能行为：用对应页面操作、接口调用、单测或集成测试证明。
- 规范复用：说明复用的组件、Hook、服务、API 封装或模式；没有复用时说明原因。
- 测试证据：通过 `project-intel test` 记录目标测试 RED、GREEN、回归/验证，或可复现的人工证据。
- 质量检查：运行 `project-intel check`，必要时运行 lint/type/test/build。
- 维护闭环：测试证据通过后，以 intake 登记的同一需求号写入 review，运行 `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>`，再运行对应的 requirement-aware maintain。
"""


def write_spec(root: Path, title: str, requirement: str, track: str = "auto") -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "specs" / spec_filename(title, "spec")
    write_text(path, build_spec_doc(root, title, requirement, snapshot, track=track))
    print(f"已写入需求文档：{path}")
    return path


def resolve_input_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def build_plan_doc(root: Path, title: str, spec_path: Path, spec_text: str, snapshot: dict[str, Any], track: str = "auto") -> str:
    config = snapshot["config"]
    analysis = analyze_task_intake(root, spec_text, snapshot, track=track)
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    return f"""# {title} 实施计划

生成时间：`{now_iso()}`

来源需求文档：`{spec_path}`

Track：`{analysis.get("track")}`
Readiness：`{analysis.get("readiness")}`

## 概述

{truncate(spec_text, 2500)}

## Readiness Gate

进入代码修改前必须满足：

- 缺失信息已处理：{", ".join(analysis.get("missingInformation", [])) or "无阻塞缺口"}
- 已确认影响区域：{", ".join(analysis.get("affectedAreas", []))}
- 已完成复用检查：组件、Hook、API、服务、工具函数、业务模式。
- 已确认接口/状态/权限/异常/兼容边界；如不涉及，在执行记录中明确说明。
- 已确定验证证据：测试、类型检查、lint、构建、页面截图、接口调用或人工复现路径。

## 任务清单

- [ ] 如果工作区自本计划编写后有变更，使用 `project-intel refresh` 刷新项目上下文。
- [ ] 从 `.project-intel` 识别受影响的模块、组件、Hook、API、服务、路由和规范。
- [ ] 编写新代码前，检查可复用的组件、Hook、服务、请求工具和重复的候选模式。
- [ ] 对 complex track，先完成 readiness gate；如果计划中途发现范围漂移，回到 spec/plan 更新。
- [ ] 调用 `project-test`，写明测试文件、目标 RED 命令与预期失败、GREEN 命令、回归范围或人工证据理由。
- [ ] 每个测试任务映射到 `AC-01` 等编号验收标准，并始终传递 intake 登记的同一需求号。
- [ ] 实现需求行为，同时保持 hard 规范和现有边界。
- [ ] 使用 `project-intel test` 记录 GREEN 和回归/验证证据，再运行 `project-intel check` 及相关的 type/lint/build 命令。
- [ ] 实现完成后运行 `project-intel review --requirement-id "<id>" ... --files <all-actual-changed-files>` 写入当前 diff 的评审结果。
- [ ] 生成或登记收口总结后，运行 `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>` 做收口检查。
- [ ] 收口后运行 `project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>` 刷新事实并关闭需求；需要保留维护历史时加 `--archive`。

## 质量命令

{table(["类型", "命令", "来源"], quality_rows)}
"""


def write_plan(root: Path, title: str, from_spec: str, track: str = "auto") -> Path:
    spec_path = resolve_input_path(root, from_spec)
    if not spec_path.exists():
        fail_usage(f"需求文档文件不存在：{spec_path}")
    snapshot = load_project_snapshot(root)
    spec_text = read_text(spec_path)
    path = project_dir(root) / "plans" / spec_filename(title, "plan")
    write_text(path, build_plan_doc(root, title, spec_path, spec_text, snapshot, track=track))
    print(f"已写入实施计划：{path}")
    return path


def build_task_impact_doc(
    root: Path,
    task: str,
    snapshot: dict[str, Any],
    analysis: Optional[dict[str, Any]] = None,
    *,
    requirement_id: Optional[str] = None,
    test_kind: Optional[str] = None,
    report_action: Optional[str] = None,
    report_path: Optional[str] = None,
    acceptance_ids: Optional[list[str]] = None,
) -> str:
    analysis = analysis or analyze_task_intake(root, task, snapshot)
    manifest = snapshot["manifest"]
    frontend = snapshot["frontend"]
    backend = snapshot["backend"]
    graph_rows = [[s.get("name"), s.get("status"), s.get("role")] for s in manifest.get("graphSources", [])]
    reuse_rows = [[item.get("type"), item.get("name"), item.get("path")] for item in analysis.get("reuseCandidates", [])]
    command_requirement_id = requirement_id or "<id>"
    selected_test_command = ""
    test_contract_guidance = ""
    if requirement_id and test_kind and report_action:
        path_option = f" --report-path {report_path}" if report_action == "register" and report_path else ""
        acceptance_option = f" --acceptance {','.join(acceptance_ids or [])}" if acceptance_ids else ""
        selected_test_command = f"""project-intel test --requirement-id \"{requirement_id}\" --test-kind {test_kind} --report-action {report_action} \\
  --phase verify --files <changed-source-and-test-files>{acceptance_option}{path_option}
"""
        test_contract_guidance = f"已复用确认的测试合同：`{test_kind}` / `{report_action}` / `{', '.join(acceptance_ids or []) or '未登记 AC'}`。"
    else:
        selected_test_command = "# 先完成上方测试合同，再运行以下收口命令。"
        test_contract_guidance = """先用 `project-test` 确认测试类型、报告动作和验收标准映射，再将**用户已选择**的值带入测试命令。

- 对外接口需求必须选择 `service` 或 `both`，不能用 unit 代替。
- `--report-action register` 必须提供 `--report-path <repo-relative-report>`。
- `--acceptance` 必须填写需求档案中已确认的验收标准，不能使用示例编号。
"""
    return f"""# 任务影响

生成时间：`{now_iso()}`

## 任务

{truncate(task, 3000)}

## Intake 分流

- Track：`{analysis.get("track")}`
- Readiness：`{analysis.get("readiness")}`
- 影响区域：{", ".join(analysis.get("affectedAreas", []))}

### 分流原因

{bullet_list(analysis.get("reasons", []))}

### 风险标记

{bullet_list(analysis.get("riskFlags", []))}

### 待澄清信息

{bullet_list(analysis.get("missingInformation", []))}

## 必经阶段

{bullet_list(analysis.get("requiredStages", []))}

## 图谱上下文

{table(["来源", "状态", "用途"], graph_rows)}

## 复用候选

{table(["类型", "名称", "路径"], reuse_rows)}

## 需检查的规范

{bullet_list(analysis.get("standards", []))}

## 测试证据合同

{test_contract_guidance.rstrip()}

## 完成钩子

实现完成后运行：

```bash
{selected_test_command.rstrip()}
project-intel review --requirement-id "{command_requirement_id}" --result passed --summary "<review-summary>" \\
  --files <all-actual-changed-files>
project-intel finish --requirement-id "{command_requirement_id}" --files <all-actual-changed-files>
project-intel maintain --requirement-id "{command_requirement_id}" --files <all-actual-changed-files>
```
"""


def lifecycle_payload(
    root: Path,
    task: str,
    track: str = "auto",
    *,
    requirement_id: Optional[str] = None,
    test_kind: Optional[str] = None,
    report_action: Optional[str] = None,
    report_path: Optional[str] = None,
    acceptance_ids: Optional[list[str]] = None,
    ticket_kind: str = "requirement",
) -> dict[str, Any]:
    snapshot = load_project_snapshot(root)
    analysis = analyze_task_intake(root, task, snapshot, track=track, ticket_kind=ticket_kind)
    body = build_task_impact_doc(
        root,
        task,
        snapshot,
        analysis,
        requirement_id=requirement_id,
        test_kind=test_kind,
        report_action=report_action,
        report_path=report_path,
        acceptance_ids=acceptance_ids,
    )
    return {"analysis": analysis, "body": body}


def write_lifecycle(root: Path, task: str, write_report: bool = False, track: str = "auto") -> Optional[Path]:
    payload = lifecycle_payload(root, task, track=track)
    print(payload["body"])
    if not write_report:
        return None
    path = project_dir(root) / "reports" / "task-impact.md"
    write_text(path, payload["body"])
    print(f"\n已写入任务影响报告：{path}")
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
    return f"""# 调试上下文

生成时间：`{now_iso()}`

## Bug

{truncate(bug, 3000)}

## 系统化调试门禁

在根因调查完成前，不要提出或实施修复。

1. 阅读完整的错误信息、堆栈跟踪、日志和失败的断言。
2. 用精确的步骤或失败的测试复现 bug。
3. 使用 `git diff`、`git status` 和相关提交检查最近的变更。
4. 从症状追溯数据/控制流，找到最初的错误输入、状态、配置或依赖。
5. 与项目中的正常工作示例进行对比。
6. 提出一个假设并测试最小的变更。
7. 根因确认后，添加回归测试并修复根本原因。

## 图谱来源

{table(["来源", "状态", "用途"], graph_rows)}

## 候选检查区域

{table(["类型", "名称", "路径"], candidate_rows)}

## 质量与验证命令

{table(["类型", "命令", "来源"], quality_rows)}

## 优先阅读的项目文件

- `.project-intel/manifest.json`
- `.project-intel/standards/*.md`
- `.project-intel/knowledge/frontend.json`
- `.project-intel/knowledge/backend.json`
- `.project-intel/graph/project-graph.json`
- `.project-intel/project-status.md`

可用时使用 GitNexus 获取调用链、影响和变更代码风险。可用时使用 Understand-Anything 获取架构/领域上下文。
"""


def write_debug_context(root: Path, bug: str, write_report: bool = False) -> Optional[Path]:
    snapshot = load_project_snapshot(root)
    body = build_debug_doc(root, bug, snapshot)
    print(body)
    if not write_report:
        return None
    path = project_dir(root) / "reports" / "debug-context.md"
    write_text(path, body)
    print(f"\n已写入调试上下文报告：{path}")
    return path


def contains_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def normalize_requirement_summary(task: str) -> str:
    summary = " ".join(task.split())
    return truncate(summary or "未填写需求摘要", 500).replace("\n", " ")


def normalize_project_file(root: Path, value: str | Path) -> Optional[str]:
    root_resolved = root.resolve()
    path = Path(value).expanduser()
    candidate = path.resolve() if path.is_absolute() else (root_resolved / path).resolve()
    try:
        rel_path = candidate.relative_to(root_resolved)
    except ValueError:
        return None
    if not rel_path.parts or ".." in rel_path.parts:
        return None
    return rel_path.as_posix()


def should_track_requirement_file(rel_path: str) -> bool:
    if not rel_path:
        return False
    parts = Path(rel_path).parts
    if not parts:
        return False
    if parts[0] in {".git", ".project-intel", ".claude"}:
        return False
    if rel_path in {"AGENTS.md", "CLAUDE.md", ".gitignore"}:
        return False
    return True


def changed_requirement_files(root: Path) -> list[str]:
    files = []
    for line in lifecycle_module.changed_project_files(root, run):
        rel_path = normalize_project_file(root, line)
        if rel_path and should_track_requirement_file(rel_path):
            files.append(rel_path)
    return sorted(dict.fromkeys(files))


def requirement_doc_path(root: Path, rel_path: str) -> Path:
    base_path = project_dir(root) / "requirements" / "files"
    base = base_path.resolve()
    path = (base_path / Path(rel_path + ".md")).resolve()
    if path != base and base not in path.parents:
        fail_usage(f"需求记录路径越出项目目录：{rel_path}")
    return base_path / Path(rel_path + ".md")


def build_file_requirement_doc(rel_path: str, task: str, current: str = "") -> str:
    summary = normalize_requirement_summary(task)
    entry = f"- {now_iso()}：{summary}"
    if current.strip():
        if summary in current:
            return current
        return current.rstrip() + "\n" + entry + "\n"
    return f"""# {rel_path} 需求变更

源文件：`{rel_path}`

这里只维护与该源码文件相关的简短中文需求描述，不记录完整对话、实现日志或长篇方案。

## 需求记录

{entry}
"""


def resolve_requirement_files(root: Path, task: str, files: Optional[list[str]] = None) -> list[str]:
    selected = files if files is not None else changed_requirement_files(root)
    rel_paths = []
    invalid = []
    for item in selected:
        rel_path = normalize_project_file(root, item)
        if rel_path and should_track_requirement_file(rel_path):
            rel_paths.append(rel_path)
        elif files is not None:
            invalid.append(str(item))
    rel_paths = sorted(dict.fromkeys(rel_paths))
    if invalid:
        fail_usage("以下源码路径无效、越出项目目录或不允许记录：" + ", ".join(invalid))
    if rel_paths and task and not contains_cjk(task):
        fail_usage("文件需求沉淀要求使用中文需求描述；请用 --task 传入中文摘要。")
    return rel_paths


def write_file_requirement_docs(root: Path, task: str, rel_paths: list[str]) -> list[Path]:
    written = []
    for rel_path in rel_paths:
        path = requirement_doc_path(root, rel_path)
        write_text(path, build_file_requirement_doc(rel_path, task, read_text(path)))
        written.append(path)
    if written:
        print(f"已更新文件级需求记录：{len(written)} 个文件")
    return written


def update_file_requirement_docs(root: Path, task: str, files: Optional[list[str]] = None) -> list[Path]:
    rel_paths = resolve_requirement_files(root, task, files)
    written = write_file_requirement_docs(root, task, rel_paths)
    if not written and files is not None:
        print("未更新文件级需求记录：没有可记录的源码文件。")
    return written


def build_maintenance_report(root: Path, task: str, refresh_result: dict[str, Any], check_exit: int, run_quality: bool, requirement_docs: list[Path]) -> str:
    manifest = refresh_result.get("manifest", {})
    frontend = refresh_result.get("frontend", {})
    backend = refresh_result.get("backend", {})
    requirement_rows = [[rel(root, path).removeprefix(".project-intel/requirements/files/").removesuffix(".md"), rel(root, path)] for path in requirement_docs]
    requirement_summary = table(["源码文件", "需求记录"], requirement_rows) if requirement_rows else "_本次没有提供或检测到可记录的源码文件，因此未更新文件级需求记录。_"
    return f"""# 维护报告

生成时间：`{now_iso()}`

## 任务

{truncate(task, 3000)}

## 刷新概况

- 索引文件数：{manifest.get("fileCount")}
- 组件数：{len(frontend.get("components", []))}
- Hooks 数：{len(frontend.get("hooks", []))}
- 后端 API 数：{len(backend.get("apis", []))}
- 服务数：{len(backend.get("services", []))}
- 前端冗余候选数：{len(frontend.get("redundancyCandidates", []))}
- 后端候选入口点数：{len(backend.get("candidateEntrypoints", []))}

## 质量

- `project-intel check` 退出码：{check_exit}
- 是否运行了 lint/type/style/format 命令：{"是" if run_quality else "否"}

## 文件级需求沉淀

{requirement_summary}

详情请查看 `.project-intel/reports/frontend-quality.md`。
"""


def maintain_project(
    root: Path,
    task: Optional[str],
    run_quality: bool,
    archive: bool = False,
    files: Optional[list[str]] = None,
    requirement_id: Optional[str] = None,
) -> int:
    ensure_initialized(root)
    requirement_manifest: Optional[dict[str, Any]] = None
    if requirement_id:
        try:
            requirement_manifest = requirements_module.load_requirement(root, requirement_id)
        except requirements_module.RequirementError as exc:
            print(f"需求维护失败：{exc}")
            return 1
        if requirement_manifest.get("state") != "finished":
            print("需求维护失败：只有 finished 状态可以执行 maintain 并进入 closed。")
            return 1
        try:
            requirements_module.validate_finished_freshness(root, requirement_id)
        except requirements_module.RequirementError as exc:
            print(f"需求维护失败：{exc}")
            return 1
        task = task or str(requirement_manifest.get("requirementName") or "")
        if files is None:
            files = [
                item
                for item in requirements_module.capture_requirement_scope(root, requirement_manifest).get("files", [])
                if should_track_requirement_file(item)
            ]
    if not task:
        fail_usage("项目维护必须提供 --task 或 --requirement-id。")
    if not contains_cjk(task):
        fail_usage("项目维护要求使用中文任务摘要；请用 --task 传入中文摘要。")
    if requirement_id:
        init_project(root, refresh=True, with_graph=False)
        check_exit = run_check(root, run_quality=run_quality)
        if check_exit != 0:
            print("需求维护失败：项目状态刷新或检查未通过，需求保持 finished。")
            return check_exit
        try:
            requirements_module.close_requirement(root, requirement_id, check_succeeded=True)
        except requirements_module.RequirementError as exc:
            print(f"需求关闭失败：{exc}")
            return 1
        print(f"需求 {requirement_id} 已关闭；维护结果已写入需求 manifest。")
        return 0
    requirement_files = resolve_requirement_files(root, task, files)
    refresh_result = init_project(root, refresh=True, with_graph=False)
    check_exit = run_check(root, run_quality=run_quality)
    requirement_docs = write_file_requirement_docs(root, task, requirement_files)
    if archive:
        path = project_dir(root) / "maintenance" / spec_filename(task, "maintenance")
    else:
        path = project_dir(root) / "maintenance" / "latest.md"
    write_text(path, build_maintenance_report(root, task, refresh_result, check_exit, run_quality, requirement_docs))
    print(f"已写入维护报告：{path}")
    return check_exit


def finish_changed_files(root: Path, files: Optional[list[str]] = None) -> list[str]:
    selected = files if files is not None else changed_requirement_files(root)
    rel_paths: list[str] = []
    invalid: list[str] = []
    for item in selected:
        rel_path = normalize_project_file(root, item)
        if rel_path and should_track_requirement_file(rel_path):
            rel_paths.append(rel_path)
        elif files is not None:
            invalid.append(str(item))
    if invalid:
        fail_usage("以下源码路径无效、越出项目目录或不允许收口：" + ", ".join(invalid))
    selected_paths = sorted(dict.fromkeys(rel_paths))
    snapshot = requirements_module.capture_scope_snapshot(root)
    if snapshot.get("gitAvailable"):
        actual = sorted(item for item in snapshot.get("files", []) if should_track_requirement_file(item))
        missing = sorted(set(actual) - set(selected_paths))
        if files is not None and missing:
            fail_usage("收口文件范围遗漏实际 Git 变更：" + ", ".join(missing))
        if files is None:
            selected_paths = actual
    return selected_paths


def normalize_test_files(root: Path, files: Optional[list[str]] = None) -> list[str]:
    if not files:
        return []
    normalized: list[str] = []
    invalid: list[str] = []
    for item in files:
        rel_path = normalize_project_file(root, item)
        if rel_path and should_track_requirement_file(rel_path):
            normalized.append(rel_path)
        else:
            invalid.append(str(item))
    if invalid:
        fail_usage("以下测试证据文件无效、越出项目目录或不允许记录：" + ", ".join(invalid))
    return sorted(dict.fromkeys(normalized))


def configured_test_commands(root: Path) -> list[str]:
    config = read_project_config(root)
    return [
        item.get("command", "").strip()
        for item in config.get("quality", {}).get("commands", [])
        if item.get("kind") in {"test", "verify"} and item.get("command", "").strip()
    ]


def run_project_test(
    root: Path,
    task: Optional[str],
    phase: str,
    commands: Optional[list[str]] = None,
    files: Optional[list[str]] = None,
    manual_evidence: str = "",
    expect_failure: str = "",
    project_wide: bool = False,
    requirement_id: Optional[str] = None,
    test_kind: Optional[str] = None,
    report_action: Optional[str] = None,
    report_path: Optional[str] = None,
    acceptance_ids: Optional[list[str]] = None,
    manual_approval: Optional[dict[str, Any]] = None,
) -> tuple[int, dict[str, Any]]:
    ensure_initialized(root)
    requirement_manifest: Optional[dict[str, Any]] = None
    generated_report = False
    if requirement_id:
        try:
            requirement_manifest = requirements_module.load_requirement(root, requirement_id)
            task = task or str(requirement_manifest.get("requirementName") or "")
            if not test_kind or not report_action:
                raise requirements_module.RequirementError("需求级测试必须提供 --test-kind 和 --report-action。")
            if report_action == "later":
                manifest = requirements_module.record_later(root, requirement_id, "test")
                print("测试报告已记录为稍后处理；需求保持阻塞。")
                return 1, {"requirement": manifest, "blocked": True}
            if phase == "manual" and test_kind != "manual":
                raise requirements_module.RequirementError("manual 阶段只能登记 --test-kind manual，不能伪装为 unit/service/both。")
            if test_kind == "manual" and phase != "manual":
                raise requirements_module.RequirementError("--test-kind manual 必须配合 --phase manual。")
            if report_action == "generate":
                requirements_module.generate_artifact(root, requirement_id, "test")
                report_path = str(requirements_module.active_requirement_dir(root, requirement_id).joinpath("test-report.md").relative_to(root))
                generated_report = True
            elif report_action == "register" and not report_path:
                raise requirements_module.RequirementError("--report-action register 必须提供 --report-path。")
        except requirements_module.RequirementError as exc:
            fail_usage(str(exc))
    if not task:
        fail_usage("测试证据必须提供 --task 或 --requirement-id。")
    if not contains_cjk(task):
        fail_usage("测试证据要求使用中文任务摘要；请用 --task 传入中文摘要。")
    if phase not in testing_module.TEST_PHASES:
        fail_usage(f"不支持的测试阶段：{phase}")

    selected_files = normalize_test_files(root, files)
    if not selected_files and not project_wide:
        fail_usage("测试证据必须列出 --files；确实覆盖整个项目时请显式使用 --project-wide。")
    if selected_files and project_wide:
        fail_usage("--files 与 --project-wide 不能同时使用。")
    selected_commands = [item.strip() for item in (commands or []) if item.strip()]
    results: list[dict[str, Any]] = []
    if phase == "manual":
        if expect_failure.strip():
            fail_usage("manual 阶段不能使用 --expect-failure。")
        if selected_commands:
            fail_usage("manual 阶段不能同时传入 --command。")
        if not testing_module.manual_evidence_valid(manual_evidence):
            fail_usage("manual 阶段必须用 --manual-evidence 记录至少 12 个有效字符的操作步骤、输入和观察结果。")
    else:
        if manual_evidence.strip():
            fail_usage("自动测试阶段不能使用 --manual-evidence；请改用 --phase manual。")
        if not selected_commands:
            selected_commands = configured_test_commands(root)
        if not selected_commands:
            fail_usage("未检测到测试命令；请用 --command 指定目标测试，或使用 --phase manual 记录人工证据。")
        if phase == "red" and not expect_failure.strip():
            fail_usage("RED 阶段必须用 --expect-failure 指定预期失败文本或正则。")
        timeout = read_project_config(root).get("quality", {}).get("timeoutSeconds", 120)
        for command in selected_commands:
            code, out, err = run_shell(command, root, timeout=timeout)
            result = {
                "command": command,
                "exitCode": code,
                "stdout": out[-4000:],
                "stderr": err[-4000:],
            }
            result["executedCount"] = testing_module.executed_test_count(result)
            results.append(result)
            print(f"{phase}：`{testing_module.sanitize_text(command)}` → {code}")

    normalized_task = normalize_requirement_summary(task)
    if requirement_id:
        safe_results = [
            {
                **item,
                "command": testing_module.sanitize_text(str(item.get("command") or "")),
                "stdout": testing_module.sanitize_text(str(item.get("stdout") or "")),
                "stderr": testing_module.sanitize_text(str(item.get("stderr") or "")),
                "executedCount": testing_module.executed_test_count(item),
            }
            for item in results
        ]
        safe_manual = testing_module.sanitize_text(manual_evidence.strip())
        entry = {
            "phase": phase,
            "status": "passed" if testing_module.phase_passed(phase, safe_results, safe_manual, expect_failure) else "failed",
            "recordedAt": now_iso(),
            "files": selected_files,
            "projectWide": bool(project_wide),
            "commands": safe_results,
        }
        if safe_manual:
            entry["manualEvidence"] = safe_manual
        if expect_failure.strip():
            entry["expectedFailure"] = testing_module.sanitize_text(expect_failure.strip())
        payload = {"schemaVersion": 2, "task": normalized_task, "entries": [entry]}
        evidence_path = requirements_module.active_requirement_dir(root, requirement_id) / "test-report.md"
    else:
        payload, entry = testing_module.record_test_evidence(
            root,
            normalized_task,
            phase,
            selected_files,
            results,
            manual_evidence=manual_evidence,
            expected_failure=expect_failure,
            project_wide=project_wide,
            now=now_iso(),
            write_json=write_json,
            write_text=write_text,
        )
        evidence_path = testing_module.evidence_markdown_path(root)
    print(f"已更新测试证据：{evidence_path}")
    requirement_result: Optional[dict[str, Any]] = None
    if requirement_id and requirement_manifest is not None and test_kind:
        mapped_acceptance = list(acceptance_ids)
        if not mapped_acceptance:
            fail_usage("需求级测试必须显式传入 --acceptance；不会自动映射全部验收标准。")
        outcome = "failed" if phase == "red" else ("passed" if entry.get("status") == "passed" else "failed")
        command_text = " && ".join(str(item.get("command") or "") for item in entry.get("commands", []))
        detail_text = "\n".join(
            part
            for item in entry.get("commands", [])
            for part in (str(item.get("stdout") or ""), str(item.get("stderr") or ""))
            if part
        ) or str(entry.get("manualEvidence") or "")
        try:
            safe_manual_approval = None
            tested_snapshot = None
            if manual_approval is not None:
                safe_manual_approval = {
                    key: value if key == "approved" else testing_module.sanitize_text(str(value or ""))
                    for key, value in manual_approval.items()
                }
            if generated_report:
                tested_snapshot = requirements_module.capture_requirement_scope(
                    root, requirements_module.load_requirement(root, requirement_id)
                )
                report_display_result = (
                    "expected-failure-observed"
                    if phase == "red" and entry.get("status") == "passed"
                    else outcome
                )
                report_path = requirements_module.append_test_report_execution(
                    root,
                    requirement_id,
                    test_kind=test_kind,
                    result=report_display_result,
                    acceptance_ids=mapped_acceptance,
                    command=testing_module.sanitize_text(command_text),
                    details=testing_module.sanitize_text(detail_text),
                    phase=phase,
                    executed_count=sum(int(item.get("executedCount", 0)) for item in entry.get("commands", [])),
                    files=selected_files,
                    project_wide=project_wide,
                    snapshot=tested_snapshot,
                )
            requirement_result = requirements_module.record_test_result(
                root,
                requirement_id,
                test_kind=test_kind,
                result=outcome,
                acceptance_ids=mapped_acceptance,
                files=selected_files,
                # A user-supplied report becomes an artifact during registration.  Capturing
                # before the state-machine lock would classify that new report as business
                # source drift, so register lets record_test_result capture it atomically.
                snapshot=(
                    None
                    if report_action == "register"
                    else tested_snapshot or requirements_module.capture_requirement_scope(
                        root, requirements_module.load_requirement(root, requirement_id)
                    )
                ),
                command=testing_module.sanitize_text(command_text),
                report_path=report_path,
                manual=safe_manual_approval,
                project_wide=project_wide,
            )
        except requirements_module.RequirementError as exc:
            print(f"需求级测试门禁失败：{exc}")
            return 1, {"evidence": payload, "entry": entry, "requirementError": str(exc)}
    if entry.get("status") != "passed":
        if phase == "red":
            print("RED 阶段未观察到预期失败，或命令本身超时/不可执行。")
        else:
            print("测试证据未通过，请检查命令输出。")
        return 1, {"evidence": payload, "entry": entry, "requirement": requirement_result}
    return 0, {"evidence": payload, "entry": entry, "requirement": requirement_result}


def git_diff_summary(root: Path) -> dict[str, Any]:
    code_status, status, _ = run(["git", "status", "--short"], root, timeout=20)
    code_names, names, _ = run(["git", "diff", "--name-only", "HEAD", "--"], root, timeout=20)
    code_stat, stat, _ = run(["git", "diff", "--stat", "HEAD", "--"], root, timeout=20)
    snapshot = requirements_module.capture_scope_snapshot(root)
    changed_files = snapshot.get("files", []) if snapshot.get("gitAvailable") else (names.splitlines() if code_names == 0 else [])
    return {
        "available": code_status == 0,
        "status": status.splitlines() if code_status == 0 else [],
        "changedFiles": changed_files,
        "stat": stat if code_stat == 0 else "",
        "diffHash": snapshot.get("diffHash"),
        "gitCommit": snapshot.get("gitCommit"),
    }


def build_finish_report(
    root: Path,
    task: str,
    files: list[str],
    check_exit: int,
    run_quality: bool,
    diff_summary: dict[str, Any],
    evidence_status: dict[str, Any],
    requirement_id: Optional[str] = None,
) -> str:
    status_rows = [[line[:2].strip(), line[3:]] for line in diff_summary.get("status", []) if len(line) >= 3]
    file_rows = [[path] for path in files]
    next_files = " ".join(files) if files else "<changed-source-files>"
    maintain_command = (
        f'project-intel maintain --requirement-id "{requirement_id}" --files {next_files}'
        if requirement_id
        else f'project-intel maintain --task "{normalize_requirement_summary(task)}" --files {next_files}'
    )
    return f"""# 任务收口报告

生成时间：`{now_iso()}`

## 任务

{truncate(task, 3000)}

## 变更范围

{table(["源码文件"], file_rows) if file_rows else "_未提供或未检测到可收口的源码文件。_"}

## Git 状态

{table(["状态", "路径"], status_rows) if status_rows else "_当前没有可展示的 git status 变更。_"}

```text
{diff_summary.get("stat") or "无 diff stat"}
```

## 收口检查

- `project-intel check` 退出码：{check_exit}
- 是否运行配置的质量/测试命令：{"是" if run_quality else "否"}
- 测试证据是否必需：{"是" if evidence_status.get("required") else "否"}
- 测试证据门禁：{"通过" if evidence_status.get("ready") else "未通过"}
- RED 失败证据：{"已记录" if evidence_status.get("redObserved") else "未记录或不适用"}
- 完成证据阶段：{evidence_status.get("passingPhase") or "无"}
- 证据说明：{evidence_status.get("reason")}
- 证据报告：`{evidence_status.get("path")}`
- 未自动执行提交、推送、发布、数据库迁移或线上变更。

## 交付前人工确认

- 功能验收证据已经来自本轮新鲜验证，而不是只依赖维护报告。
- 需求范围没有漂移；如已漂移，先回到 spec/plan 更新。
- 涉及接口、权限、数据、缓存、异步、支付、订阅、远程调用或回滚时，已记录兼容和失败行为。
- Review findings 已验证，不盲目应用与当前项目事实冲突的建议。

## 下一步维护

```bash
{maintain_command}
```
"""


def finish_project(
    root: Path,
    task: Optional[str],
    run_quality: bool = False,
    files: Optional[list[str]] = None,
    manual_evidence: str = "",
    requirement_id: Optional[str] = None,
) -> int:
    ensure_initialized(root)
    requirement_manifest: Optional[dict[str, Any]] = None
    if requirement_id:
        try:
            requirement_manifest = requirements_module.load_requirement(root, requirement_id)
        except requirements_module.RequirementError as exc:
            print(f"任务收口失败：{exc}")
            return 1
        task = task or str(requirement_manifest.get("requirementName") or "")
        if manual_evidence.strip():
            fail_usage("需求级人工测试必须先通过 project-intel test --test-kind manual 登记审批式报告。")
    if not task:
        fail_usage("任务收口必须提供 --task 或 --requirement-id。")
    if not contains_cjk(task):
        fail_usage("任务收口要求使用中文任务摘要；请用 --task 传入中文摘要。")
    if requirement_id and requirement_manifest is not None:
        requirement_snapshot = requirements_module.capture_requirement_scope(root, requirement_manifest)
        try:
            selected_files = requirements_module.validate_scope_selection(
                root,
                files if files is not None else list(requirement_snapshot.get("files", [])),
                requirement_snapshot,
            )
        except requirements_module.RequirementError as exc:
            fail_usage(str(exc))
    else:
        selected_files = finish_changed_files(root, files)
    if manual_evidence.strip() and not testing_module.manual_evidence_valid(manual_evidence):
        fail_usage("--manual-evidence 必须记录至少 12 个有效字符的操作步骤、输入和观察结果。")
    quality_results: list[dict[str, Any]] = []
    check_exit = run_check(root, run_quality=run_quality, result_sink=quality_results)
    normalized_task = normalize_requirement_summary(task)
    test_results = [item for item in quality_results if item.get("kind") in {"test", "verify"}]
    if manual_evidence.strip():
        testing_module.record_test_evidence(
            root,
            normalized_task,
            "manual",
            selected_files,
            [],
            manual_evidence=manual_evidence,
            now=now_iso(),
            write_json=write_json,
            write_text=write_text,
        )
    elif test_results:
        testing_module.record_test_evidence(
            root,
            normalized_task,
            "verify",
            selected_files,
            test_results,
            now=now_iso(),
            write_json=write_json,
            write_text=write_text,
        )
    if requirement_id:
        evidence_status = {
            "required": True,
            "ready": False,
            "redObserved": False,
            "passingPhase": "requirement-manifest",
            "path": str(requirements_module.active_manifest_path(root, requirement_id).relative_to(root)),
            "reason": "需求级 finish 门禁尚未执行。",
        }
        if check_exit == 0:
            try:
                requirement_manifest = requirements_module.finish_requirement(root, requirement_id, files=selected_files)
                evidence_status.update({"ready": True, "reason": "需求文档、测试、评审、验收标准、作用域快照和收口总结均已通过。"})
            except requirements_module.RequirementError as exc:
                evidence_status["reason"] = str(exc)
    else:
        evidence_status = testing_module.evaluate_test_evidence(root, normalized_task, selected_files)
    if requirement_id:
        if not evidence_status.get("ready"):
            print("任务收口失败：" + str(evidence_status.get("reason") or "交付证据门禁未通过。"))
        else:
            print(f"需求 {requirement_id} 已完成 finish；结果已写入需求 manifest。")
        return 1 if check_exit != 0 or not evidence_status.get("ready") else 0
    summary = git_diff_summary(root)
    path = project_dir(root) / "reports" / "finish-report.md"
    write_text(path, build_finish_report(root, task, selected_files, check_exit, run_quality, summary, evidence_status, requirement_id))
    print(f"已写入任务收口报告：{path}")
    if not evidence_status.get("ready"):
        print("任务收口失败：" + str(evidence_status.get("reason") or "交付证据门禁未通过。"))
    return 1 if check_exit != 0 or not evidence_status.get("ready") else 0


def hook_script_body(hook_name: str) -> str:
    return f"""#!/bin/sh
{PROJECT_INTEL_HOOK_MARKER}: {hook_name}

if [ "${{PROJECT_INTEL_SKIP_HOOKS:-0}}" = "1" ]; then
  exit 0
fi

SCRIPT="{script_path()}"
if command -v python3 >/dev/null 2>&1 && [ -f "$SCRIPT" ]; then
  PROJECT_INTEL_SKIP_HOOKS=1 python3 "$SCRIPT" refresh >/dev/null 2>&1 || true
  PROJECT_INTEL_SKIP_HOOKS=1 python3 "$SCRIPT" check >/dev/null 2>&1 || true
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
        """# 项目智能钩子

这些钩子模板是可选的。只有在 `project-intel install --hooks --activate-git-hooks` 将包装器安装到 `.git/hooks` 后才会激活。

设置 `PROJECT_INTEL_SKIP_HOOKS=1` 可跳过钩子执行。
""",
    )
    return written


def git_hooks_path(root: Path, *, allow_external: bool = False) -> Optional[Path]:
    code, out, _ = run(["git", "rev-parse", "--git-path", "hooks"], root, timeout=20)
    if code == 0 and out:
        path = Path(out).expanduser()
        resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
        git_dir_code, git_dir_raw, _ = run(["git", "rev-parse", "--git-dir"], root, timeout=20)
        git_dir = (root / git_dir_raw).resolve() if git_dir_code == 0 and git_dir_raw and not Path(git_dir_raw).is_absolute() else Path(git_dir_raw).resolve() if git_dir_raw else None
        expected = (git_dir / "hooks").resolve() if git_dir else None
        return resolved
    fallback = root / ".git" / "hooks"
    return fallback if fallback.exists() else None


def activate_git_hooks(root: Path, *, allow_external: bool = False) -> list[dict[str, Any]]:
    git_hooks = git_hooks_path(root, allow_external=allow_external)
    results = []
    if git_hooks is None or not git_hooks.exists() or not git_hooks.is_dir():
        return [{"hook": "*", "status": "skipped", "detail": "未找到 .git/hooks 目录。"}]
    if git_hooks.is_symlink():
        raise RuntimeError("Git hooks 路径不能是符号链接。")
    git_dir_code, git_dir_raw, _ = run(["git", "rev-parse", "--git-dir"], root, timeout=20)
    if git_dir_code == 0 and git_dir_raw:
        git_dir = (root / git_dir_raw).resolve() if not Path(git_dir_raw).is_absolute() else Path(git_dir_raw).resolve()
        if not allow_external and git_hooks.resolve() != (git_dir / "hooks").resolve():
            raise RuntimeError("Git core.hooksPath 指向仓库外目录；默认拒绝写入。若确实需要，请显式传入 --allow-external-hooks。")
    git_hooks.mkdir(parents=True, exist_ok=True)
    for hook_name in ("post-merge", "post-commit", "pre-push"):
        target = git_hooks / hook_name
        body = hook_script_body(hook_name)
        if target.exists():
            existing = read_text(target)
            if PROJECT_INTEL_HOOK_MARKER not in existing:
                pending = project_dir(root) / "hooks" / f"{hook_name}.pending.sh"
                write_text(pending, body)
                try:
                    pending.chmod(0o755)
                except OSError:
                    pass
                results.append({"hook": hook_name, "status": "conflict", "detail": f"已保留现有钩子；待安装的包装器已写入 {pending}"})
                continue
        write_text(target, body)
        try:
            target.chmod(0o755)
        except OSError:
            pass
        results.append({"hook": hook_name, "status": "installed", "detail": str(target)})
    return results


def agent_project_intelligence_priority_rules() -> str:
    return """## Project Intelligence First

Before any code change, debugging, review, requirement analysis, planning, spec work, or standards update, use the project-level intelligence workflow first.

Prefer available project skills such as:

- `project-brainstorm`
- `project-design`
- `project-spec`
- `project-plan`
- `project-intake`
- `project-task`
- `project-debug`
- `project-review`
- `project-quality`
- `project-knowledge`
- `project-standards`
- `project-finish`
- `project-test`
- `project-maintain`
- `project-orchestrate`
- `project-init`
- `project-refresh`

If skills are exposed through a plugin namespace, use the equivalent `project-intelligence:*` skill. If slash skills are unavailable, follow the same workflow manually with `.project-intel/` and the `project-intel` CLI. Do not rely only on basic file tools when project skills or project facts are available."""


def project_agent_rules() -> str:
    return """## Project Intelligence

This repository uses `.project-intel/` as the project-level fact source.

Project Intelligence is the workflow layer. Tools such as Grep, Read, Edit, Bash, Glob, or Write are only execution tools; using them does not replace the required Project Intelligence workflow.

If a conversation starts as explanation or discussion and later turns into code modification, pause before the first Edit/Write and enter the matching Project Intelligence workflow. Do not continue from discussion mode directly into code changes.

Before implementing, debugging, reviewing, planning, writing specs, answering component/API questions, or modifying behavior:

1. Classify the request and explicitly invoke the matching Project Intelligence skill when available:
   - Requirement intake, task routing, readiness, or scope classification: `project-intake` or `project-intelligence:project-intake`
   - Requirement shaping or brainstorming: `project-brainstorm` or `project-intelligence:project-brainstorm`
   - Source-backed Bug/Requirement development design generation or validation: `project-design` or `project-intelligence:project-design`
   - Requirement/spec/acceptance criteria/impact: `project-spec` or `project-intelligence:project-spec`
   - Implementation plan or checklist: `project-plan` or `project-intelligence:project-plan`
   - Implementation, modification, fix, refactor, or feature work: `project-task` or `project-intelligence:project-task`
   - Test planning, RED/GREEN evidence, regression scope, manual verification, or finish evidence: `project-test` or `project-intelligence:project-test`
   - Bug, error, regression, failed test, or unexpected behavior: `project-debug` or `project-intelligence:project-debug`
   - Code review, PR review, diff review, reuse/quality risk review: `project-review` or `project-intelligence:project-review`
   - Independent planned subtasks, subagent handoffs, task-level review, or parallel read-only investigations: `project-orchestrate` or `project-intelligence:project-orchestrate`
   - Quality, lint, type, format, style, redundancy checks: `project-quality` or `project-intelligence:project-quality`
   - Project knowledge, component/API/service usage, architecture questions: `project-knowledge` or `project-intelligence:project-knowledge`
   - Standards lookup, rule promotion/demotion, hard/preferred/inferred/candidate explanation: `project-standards` or `project-intelligence:project-standards`
   - Task finish, acceptance evidence, release readiness, or completion checks: `project-finish` or `project-intelligence:project-finish`
   - Post-task refresh and lifecycle maintenance: `project-maintain` or `project-intelligence:project-maintain`
   - Initialization of project facts: `project-init` or `project-intelligence:project-init`
   - Fact refresh, or explicitly requested adapter maintenance: `project-refresh` or `project-intelligence:project-refresh`
2. If slash skills are not available or do not trigger automatically, follow the same workflow manually before using execution tools and state which Project Intelligence workflow is being followed.
3. Check `.project-intel/manifest.json` for project metadata and refresh status.
4. Read `.project-intel/project-status.md`, the active `.project-intel/requirements/<id>/manifest.json`, and only the relevant files under `.project-intel/standards/`, `.project-intel/knowledge/`, and `.project-intel/graph/`.
5. Apply `hard` standards as requirements; treat `preferred` as default project style; treat `inferred` and `candidate` as suggestions that need confirmation before enforcement.
6. Prefer existing public components, Hooks, utilities, API wrappers, services, DTO/VO/entity patterns, permission checks, transaction boundaries, and error-code conventions before adding new ones.
7. For implementation work, before the first Edit/Write, ask for requirement ID and name, determine `bug|requirement`, generate a `LOCAL-YYYYMMDD-HHMMSS` ID when no formal ID exists, explicitly confirm external API impact, and collect the requirement/design document actions. Run `project-intel intake --requirement-id "<id>" --requirement-name "<name>" --ticket-kind bug|requirement --external-api yes|no --requirement-action generate|register|later --design-action generate|register|later`; a `register` action must also pass its repository-relative `--requirement-path` or `--design-path`. These choices are persisted in `manifest.workflowSelections`; later sessions must read `requirement status --json` instead of asking again or guessing. First use `project-spec` to create/register `.project-intel/requirements/<id>/requirement.md` and persist matching numbered acceptance criteria. For Bugs, next complete `project-debug` and persist its source-backed root cause with `project-intel requirement diagnose --requirement-id "<id>" --root-cause "<cause>" --evidence <path#symbol>`; a debug narrative alone does not satisfy the gate. Only after that use the persisted action to generate, register, or defer `.project-intel/requirements/<id>/design.md` with `project-design`. The required order is therefore `project-spec` → (`project-debug` plus `requirement diagnose` for Bugs) → `project-design` → `requirement ready`. Generate optional `plan.md` only for complex work or an explicit persistent-plan request, then require a successful `requirement ready` gate. Invoke `project-test` before `project-task` only to select the test type, report action, RED/GREEN command, and evidence scope. Reuse those selected values and only confirmed AC IDs in the CLI; external API work must use `service` or `both`, and `report-action register` requires `--report-path`. In `project-task`, run `project-intel requirement begin --requirement-id "<id>"`; only after the state is `implementing` may the agent generate/register the test report, edit a test file, or execute/record RED. This same-turn handoff is required even when the user asks not to edit yet; complete workflow routing and stop before file changes. Do not ask for requirement identity during knowledge-only explanation or read-only review.
8. Use GitNexus impact/explore/detect_changes tools when available; otherwise use `.project-intel` plus `project-intel lifecycle --task "<requirement>"` or `project-intel query "<symbol-or-feature>"`. `lifecycle` prints context and does not create a shared report.
9. Use `project-orchestrate` only when planned subtasks are independent enough to review separately. Implementation subagents should normally run sequentially; parallel agents are for read-only investigations or disjoint impact analysis.
10. After meaningful code changes, run change review, test evidence, finish, and maintenance with the same requirement ID. `project-test` must record explicit files or `--project-wide`; RED requires `--expect-failure`. External API work requires service tests. Manual tests require approval, reason, steps, input, observation, and screenshot/log path. Persist review with `project-intel review`, ask whether to generate/register/defer `closure-summary.md`, then run `project-intel finish --requirement-id "<id>" --files <all-actual-changed-files>` and `project-intel maintain --requirement-id "<id>" --files <all-actual-changed-files>`. Any code change invalidates stale test/review hashes. `maintain` is allowed only from `finished`, closes only after fact-only refresh/check succeeds, and must not update root adapters unless `refresh --adapters` or `install` was explicitly requested.
11. Do not claim a change is complete, fixed, passing, or ready without fresh evidence from the current turn. `project-intel check` proves Project Intelligence rules; it does not prove business behavior unless the check directly exercises that behavior.
12. For bug investigation, first gather symptoms, reproduce or locate evidence, trace likely paths through project knowledge/graph context, then propose one testable hypothesis and avoid stacked guesses.
13. For review, inspect diff plus `.project-intel` standards/knowledge/graph context and report findings by severity before summaries. Verify review feedback against project reality before applying it.
14. Use `--run-quality` only when real lint/type/style/format checks should run.
15. If GitNexus or Understand-Anything graph context is available, use it for impact analysis and architecture/domain relationships.
Routine refresh and quality state overwrite `.project-intel/project-status.md`. Requirement history stays in `.project-intel/requirements/<id>/`: `requirement.md`, `design.md`, optional `plan.md`, `test-report.md`, `closure-summary.md`, and `manifest.json`. New workflows do not write shared reports, specs, plans, maintenance files, by-id mirrors, or per-source requirement markdown.

Useful CLI fallbacks: `project-intel intake`, `project-intel requirement`, `project-intel lifecycle`, `project-intel query`, `project-intel refresh`, `project-intel check`, `project-intel spec`, `project-intel plan`, `project-intel debug`, `project-intel test`, `project-intel review`, `project-intel finish`, `project-intel requirements`, and `project-intel maintain`."""


def claude_project_agent_rules() -> str:
    rules = project_agent_rules()
    replacements = {
        "Requirement intake, task routing, readiness, or scope classification: `project-intake` or `project-intelligence:project-intake`": "Requirement intake, task routing, readiness, or scope classification: `/project-intake`",
        "Requirement shaping or brainstorming: `project-brainstorm` or `project-intelligence:project-brainstorm`": "Requirement shaping or brainstorming: `/project-brainstorm`",
        "Source-backed Bug/Requirement development design generation or validation: `project-design` or `project-intelligence:project-design`": "Source-backed Bug/Requirement development design generation or validation: `/project-design`",
        "Requirement/spec/acceptance criteria/impact: `project-spec` or `project-intelligence:project-spec`": "Requirement/spec/acceptance criteria/impact: `/project-spec`",
        "Implementation plan or checklist: `project-plan` or `project-intelligence:project-plan`": "Implementation plan or checklist: `/project-plan`",
        "Implementation, modification, fix, refactor, or feature work: `project-task` or `project-intelligence:project-task`": "Implementation, modification, fix, refactor, or feature work: `/project-task`",
        "Test planning, RED/GREEN evidence, regression scope, manual verification, or finish evidence: `project-test` or `project-intelligence:project-test`": "Test planning, RED/GREEN evidence, regression scope, manual verification, or finish evidence: `/project-test`",
        "Bug, error, regression, failed test, or unexpected behavior: `project-debug` or `project-intelligence:project-debug`": "Bug, error, regression, failed test, or unexpected behavior: `/project-debug`",
        "Code review, PR review, diff review, reuse/quality risk review: `project-review` or `project-intelligence:project-review`": "Code review, PR review, diff review, reuse/quality risk review: `/project-review`",
        "Independent planned subtasks, subagent handoffs, task-level review, or parallel read-only investigations: `project-orchestrate` or `project-intelligence:project-orchestrate`": "Independent planned subtasks, subagent handoffs, task-level review, or parallel read-only investigations: `/project-orchestrate`",
        "Quality, lint, type, format, style, redundancy checks: `project-quality` or `project-intelligence:project-quality`": "Quality, lint, type, format, style, redundancy checks: `/project-quality`",
        "Project knowledge, component/API/service usage, architecture questions: `project-knowledge` or `project-intelligence:project-knowledge`": "Project knowledge, component/API/service usage, architecture questions: `/project-knowledge`",
        "Standards lookup, rule promotion/demotion, hard/preferred/inferred/candidate explanation: `project-standards` or `project-intelligence:project-standards`": "Standards lookup, rule promotion/demotion, hard/preferred/inferred/candidate explanation: `/project-standards`",
        "Task finish, acceptance evidence, release readiness, or completion checks: `project-finish` or `project-intelligence:project-finish`": "Task finish, acceptance evidence, release readiness, or completion checks: `/project-finish`",
        "Post-task refresh and lifecycle maintenance: `project-maintain` or `project-intelligence:project-maintain`": "Post-task refresh and lifecycle maintenance: `/project-maintain`",
        "Initialization of project facts: `project-init` or `project-intelligence:project-init`": "Initialization of project facts: `/project-init`",
        "Fact refresh, or explicitly requested adapter maintenance: `project-refresh` or `project-intelligence:project-refresh`": "Fact refresh, or explicitly requested adapter maintenance: `/project-refresh`",
    }
    for old, new in replacements.items():
        rules = rules.replace(old, new)
    # Rule 15 removed — skills come from the plugin, not local copies.
    return rules


def codex_adapter_rules() -> str:
    return """## Project Intelligence

This repository uses `.project-intel/` for project facts, standards, requirement history, test evidence, review, finish, and maintenance.

Use the plugin skill namespace when available:

- Implementation or bug work: `$project-intelligence:project-intake` → `$project-intelligence:project-spec` → `$project-intelligence:project-design` → `$project-intelligence:project-test` → `$project-intelligence:project-task`.
- Debugging: `$project-intelligence:project-debug` before fixing.
- Review only: `$project-intelligence:project-review`; do not finish or maintain from review.
- Completion: `$project-intelligence:project-finish`; run `$project-intelligence:project-maintain` only after finish succeeds.
- Knowledge, standards, quality, refresh, and init use their matching `$project-intelligence:*` skills.

For requirement-level work, carry one requirement ID through every CLI call. Keep readable files under `.project-intel/requirements/<id>/`: `requirement.md`, `design.md`, optional `plan.md`, `test-report.md`, `closure-summary.md`, and `manifest.json`.

`project-intel init` and `project-intel refresh` are fact-only by default. Root adapters are changed only by explicit `project-intel adapters apply`, `project-intel install`, or `project-intel refresh --adapters`."""


def claude_adapter_rules() -> str:
    return """## Project Intelligence

This repository uses `.project-intel/` for project facts and requirement workflow evidence.

Use slash skills when available:

- Implementation or bug work: `/project-intake` → `/project-spec` → `/project-design` → `/project-test` → `/project-task`.
- Debugging: `/project-debug` before fixing.
- Review only: `/project-review`; do not finish or maintain from review.
- Completion: `/project-finish`; run `/project-maintain` only after finish succeeds.
- Knowledge, standards, quality, refresh, and init use their matching `/project-*` skills.

For requirement-level work, keep all readable artifacts in `.project-intel/requirements/<id>/`. `init` and `refresh` are fact-only by default; adapters change only when explicitly requested."""


def nested_claude_adapter_rules() -> str:
    return """# Project Intelligence

Use the root `CLAUDE.md` Project Intelligence block and the `/project-*` plugin skills. Do not keep a second full workflow copy in `.claude/CLAUDE.md`."""


def _adapter_targets(root: Path, target: str) -> list[tuple[str, Path, str, str, str, bool]]:
    requested = {"both": {"codex", "claude"}, "all": {"codex", "claude"}}.get(target, {target})
    targets: list[tuple[str, Path, str, str, bool]] = []
    if "codex" in requested:
        targets.append((
            "codex",
            root / "AGENTS.md",
            codex_adapter_rules(),
            AGENT_PROJECT_INTEL_BLOCK_START,
            AGENT_PROJECT_INTEL_BLOCK_END,
            True,
        ))
    if "claude" in requested:
        targets.append((
            "claude",
            root / "CLAUDE.md",
            claude_adapter_rules(),
            PROJECT_INTEL_BLOCK_START,
            PROJECT_INTEL_BLOCK_END,
            True,
        ))
        targets.append((
            "claude-nested",
            root / ".claude" / "CLAUDE.md",
            nested_claude_adapter_rules(),
            PROJECT_INTEL_BLOCK_START,
            PROJECT_INTEL_BLOCK_END,
            False,
        ))
    return targets


def adapters_preview(root: Path, target: str = "both") -> dict[str, Any]:
    return adapters_apply(root, target=target, dry_run=True)


def adapters_status(root: Path, target: str = "both") -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    ok = True
    for name, path, block, start, end, _prepend in _adapter_targets(root, target):
        try:
            current = _read_adapter_text(root, path)
            managed = f"{start}\n{block.strip()}\n{end}"
            status = "current" if managed in current else "missing" if start not in current else "drifted"
            if current.count(start) != current.count(end):
                status = "malformed"
            elif current.count(start) > 1:
                status = "duplicate"
            entries.append({
                "target": name,
                "path": _adapter_relative_path(root, path),
                "status": status,
                "managedSha256": hashlib.sha256(managed.encode("utf-8")).hexdigest(),
            })
            ok = ok and status == "current"
        except Exception as exc:
            entries.append({"target": name, "path": str(path), "status": "error", "error": str(exc)})
            ok = False
    return {"ok": ok, "target": target, "entries": entries}


def adapters_apply(root: Path, target: str = "both", *, dry_run: bool = False) -> dict[str, Any]:
    """Preflight every adapter then commit all writes, rolling back on failure."""
    staged: list[dict[str, Any]] = []
    for name, path, block, start, end, prepend in _adapter_targets(root, target):
        _assert_safe_adapter_path(root, path)
        current = _read_adapter_text(root, path)
        next_text = current
        if name == "codex":
            next_text, _ = _replace_single_managed_block(next_text, "", PROJECT_INTEL_BLOCK_START, PROJECT_INTEL_BLOCK_END)
            next_text = next_text.strip()
        managed = f"{start}\n{block.strip()}\n{end}"
        next_text, action = _replace_single_managed_block(next_text, managed, start, end, prepend=prepend)
        staged.append({
            "target": name,
            "path": path,
            "relative": _adapter_relative_path(root, path),
            "before": current,
            "existed": path.exists(),
            "after": next_text,
            "action": action if next_text.rstrip() != current.rstrip() else "unchanged",
            "changed": next_text.rstrip() != current.rstrip(),
            "sha256": hashlib.sha256(managed.encode("utf-8")).hexdigest(),
        })
    if dry_run:
        return {"ok": True, "dryRun": True, "target": target, "entries": [{k: v for k, v in item.items() if k not in {"path", "before", "after", "existed"}} for item in staged]}
    written: list[dict[str, Any]] = []
    try:
        for item in staged:
            if not item["changed"]:
                continue
            _write_adapter_text(root, item["path"], item["after"])
            written.append(item)
    except Exception:
        for item in reversed(written):
            try:
                if item["existed"]:
                    _write_adapter_text(root, item["path"], item["before"])
                elif item["path"].exists():
                    item["path"].unlink()
            except OSError:
                pass
        raise
    entries = []
    for item in staged:
        public = {k: v for k, v in item.items() if k not in {"path", "before", "after", "existed", "relative"}}
        public["path"] = item["relative"]
        entries.append(public)
    return {"ok": True, "dryRun": False, "target": target, "entries": entries}


def adapters_remove(root: Path, target: str = "both", *, dry_run: bool = False) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for name, path, _block, start, end, _prepend in _adapter_targets(root, target):
        if not path.exists():
            results.append({"target": name, "path": _adapter_relative_path(root, path), "action": "absent", "changed": False})
            continue
        result = remove_adapter_managed_block(root, path, start, end, dry_run=dry_run)
        result["target"] = name
        results.append(result)
        if name == "codex":
            cleanup = remove_adapter_managed_block(root, path, PROJECT_INTEL_BLOCK_START, PROJECT_INTEL_BLOCK_END, dry_run=dry_run)
            if cleanup.get("changed"):
                cleanup["target"] = "codex-legacy"
                results.append(cleanup)
    return {"ok": True, "dryRun": dry_run, "target": target, "entries": results}


def write_agent_entrypoints(root: Path) -> list[str]:
    agents = root / "AGENTS.md"
    claude = root / "CLAUDE.md"
    adapters_apply(root, target="both")
    return [str(agents), str(claude)]


def install_claude(root: Path, hooks: bool = False, activate_hooks: bool = False, *, allow_external_hooks: bool = False) -> dict[str, Any]:
    claude = _assert_safe_managed_path(root, ".claude", label="Claude 适配器")
    claude.mkdir(parents=True, exist_ok=True)
    legacy_cleanup = cleanup_legacy_local_skills(root)
    nested = claude / "CLAUDE.md"
    legacy_generated = f"# 项目智能\n\n{claude_project_agent_rules()}".strip()
    if _read_adapter_text(root, nested).strip() == legacy_generated:
        write_text(nested, "")
    adapter_result = adapters_apply(root, target="both")
    agent_files = [str(root / item["path"]) for item in adapter_result.get("entries", [])]
    hook_templates = write_hook_templates(root) if hooks or activate_hooks else []
    hook_results = activate_git_hooks(root, allow_external=allow_external_hooks) if activate_hooks else []
    return {
        "claude": str(claude),
        "agentFiles": agent_files,
        "adapters": adapter_result,
        "hookTemplates": [str(path) for path in hook_templates],
        "hookResults": hook_results,
        "legacyCleanup": legacy_cleanup,
    }


def hard_rule_text(rule: Any, index: int) -> tuple[str, str]:
    if isinstance(rule, str):
        return f"hard-{index + 1}", rule
    return str(rule.get("id") or f"hard-{index + 1}"), str(rule.get("rule") or rule.get("description") or "未命名 hard 规则")


def selected_hard_rule_files(root: Path, config: dict[str, Any], check: dict[str, Any]) -> list[Path]:
    includes = check.get("include") or ["**/*"]
    excludes = check.get("exclude") or []
    return [
        path
        for path in iter_files(root, config)
        if path_matches_any(rel(root, path), includes) and not path_matches_any(rel(root, path), excludes)
    ]


def run_hard_rule_checks(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, rule in enumerate(config.get("rules", {}).get("hard", [])):
        rule_id, description = hard_rule_text(rule, index)
        check = rule.get("check") if isinstance(rule, dict) else None
        if not check:
            results.append({"id": rule_id, "rule": description, "status": "manual-review", "evidence": "未配置机器检查条件"})
            continue
        check_type = check["type"]
        if check_type in {"forbid-regex", "require-regex"}:
            regex = re.compile(check["pattern"])
            matches: list[str] = []
            for path in selected_hard_rule_files(root, config, check):
                body = read_text(path)
                match = regex.search(body)
                if match:
                    line = body.count("\n", 0, match.start()) + 1
                    matches.append(f"{rel(root, path)}:{line}")
                    if len(matches) >= 20:
                        break
            failed = bool(matches) if check_type == "forbid-regex" else not matches
            evidence = ", ".join(matches) if matches else "未找到匹配"
        else:
            matched_paths = []
            for path in root.glob(check["path"]):
                try:
                    resolved = path.resolve()
                    resolved.relative_to(root.resolve())
                except (OSError, ValueError):
                    continue
                matched_paths.append(rel(root, resolved))
                if len(matched_paths) >= 20:
                    break
            failed = not matched_paths if check_type == "require-file" else bool(matched_paths)
            evidence = ", ".join(matched_paths) if matched_paths else "未找到匹配路径"
        results.append(
            {
                "id": rule_id,
                "rule": description,
                "status": "failed" if failed else "passed",
                "evidence": evidence,
            }
        )
    return results


def markdown_command_output(result: dict[str, Any]) -> str:
    stdout = testing_module.sanitize_text(str(result.get("stdout") or "")).replace("```", "`` `")
    stderr = testing_module.sanitize_text(str(result.get("stderr") or "")).replace("```", "`` `")
    command = testing_module.sanitize_text(str(result.get("command") or ""))
    sections = [f"### {result.get('kind') or 'command'}", "", f"命令：`{command}`", ""]
    if stdout:
        sections.extend(["stdout：", "", "```text", stdout, "```", ""])
    if stderr:
        sections.extend(["stderr：", "", "```text", stderr, "```", ""])
    if not stdout and not stderr:
        sections.append("_命令没有输出。_")
    return "\n".join(sections).rstrip()


def run_check(root: Path, run_quality: bool, result_sink: Optional[list[dict[str, Any]]] = None) -> int:
    ensure_initialized(root)
    pdir = project_dir(root)
    config = read_project_config(root)
    frontend = load_json(pdir / "knowledge" / "frontend.json", {})
    backend = load_json(pdir / "knowledge" / "backend.json", {})
    hard_results = run_hard_rule_checks(root, config)
    quality_results: list[dict[str, Any]] = []
    exit_code = 1 if any(item.get("status") == "failed" for item in hard_results) else 0
    commands = config.get("quality", {}).get("commands", [])
    timeout = config.get("quality", {}).get("timeoutSeconds", 120)
    if run_quality:
        for item in commands:
            cmd = item.get("command", "")
            code, out, err = run_shell(cmd, root, timeout=timeout)
            quality_results.append({"kind": item.get("kind"), "command": cmd, "exitCode": code, "stdout": out[-4000:], "stderr": err[-4000:]})
            if code != 0:
                exit_code = 1
    if result_sink is not None:
        result_sink.extend(quality_results)
    report = build_quality_report(
        quality_results,
        frontend,
        backend,
        hard_results=hard_results,
        configured_commands=len(commands),
        run_quality=run_quality,
    )
    manifest = load_json(pdir / "manifest.json", {})
    tooling = load_json(pdir / "local" / "tooling.json", {})
    write_text(
        pdir / "project-status.md",
        build_project_status(root, manifest, frontend, backend, config, tooling, quality_report=report),
    )
    print(f"项目智能检查完成：{pdir / 'project-status.md'}")
    return exit_code


def build_quality_report(
    results: list[dict[str, Any]],
    frontend: dict[str, Any],
    backend: dict[str, Any],
    hard_results: Optional[list[dict[str, Any]]] = None,
    configured_commands: int = 0,
    run_quality: bool = False,
) -> str:
    results = [
        {
            **item,
            "command": testing_module.sanitize_text(str(item.get("command") or "")),
            "stdout": testing_module.sanitize_text(str(item.get("stdout") or "")),
            "stderr": testing_module.sanitize_text(str(item.get("stderr") or "")),
        }
        for item in results
    ]
    rows = [[r.get("kind"), r.get("command"), r.get("exitCode")] for r in results]
    hard_rows = [[r.get("id"), r.get("rule"), r.get("status"), r.get("evidence")] for r in (hard_results or [])]
    redundancy = frontend.get("redundancyCandidates", [])
    if rows:
        command_summary = table(["类型", "命令", "退出码"], rows)
    elif configured_commands and not run_quality:
        command_summary = f"_检测到 {configured_commands} 条质量命令，本次未使用 `--run-quality`，因此没有执行。_"
    else:
        command_summary = "_项目未配置可运行的质量命令。_"
    outputs = "\n\n".join(markdown_command_output(result) for result in results) or "_本次没有命令输出。_"
    return f"""# 质量报告

## Hard 规范

{table(["ID", "规则", "状态", "证据"], hard_rows)}

`failed` 会导致检查失败；`manual-review` 必须由 Agent/评审人员核对，但不会被 CLI 误判为失败。

## 命令

{command_summary}

## 命令输出

{outputs}

## 冗余

- 前端冗余候选数：{len(redundancy)}
- 后端候选入口点数：{len(backend.get("candidateEntrypoints", []))}

冗余发现默认为 `candidate`，除非团队策略升级，否则不会导致检查失败。
"""


def query_project(root: Path, text: str) -> int:
    pdir = project_dir(root)
    if not (pdir / "manifest.json").exists():
        fail_usage("未找到 .project-intel。请先运行 project-intel init。")
    needle = text.lower()
    matches: list[tuple[str, str, int]] = []
    for path in lifecycle_module.query_paths(pdir):
        body = read_text(path)
        context = lifecycle_module.match_context(body, needle)
        if context:
            snippet, line = context
            matches.append((rel(root, path), snippet, line))
    if not matches:
        print("未找到直接匹配的项目智能结果。请尝试更宽泛的关键词或刷新知识库。")
        return 0
    for name, snippet, line in matches[:10]:
        print(f"\n## {name}:{line}\n")
        print(snippet)
    return 0


def report_graph_tools(root: Path, as_json: bool = False) -> int:
    package = detect_package(root)
    tooling = detect_tooling(root, package)
    print_graph_tools_report(tooling, as_json=as_json)
    return 0


def marketplace_bundle_root() -> Optional[Path]:
    candidates = [script_path().parent, *script_path().parents]
    for candidate in candidates:
        if (candidate / ".agents" / "plugins" / "marketplace.json").is_file() and (candidate / ".claude-plugin" / "marketplace.json").is_file():
            return candidate
    return None


def agent_install_commands(target: str) -> dict[str, list[list[str]]]:
    bundle = marketplace_bundle_root()
    source = str(bundle) if bundle else "crayonYYxm/project-intelligence"
    commands: dict[str, list[list[str]]] = {}
    if target in {"codex", "all"}:
        commands["codex"] = [
            ["codex", "plugin", "marketplace", "add", source],
            ["codex", "plugin", "add", "project-intelligence@project-intelligence", "--json"],
        ]
    if target in {"claude", "all"}:
        commands["claude"] = [
            ["claude", "plugin", "marketplace", "add", source],
            ["claude", "plugin", "install", "project-intelligence@project-intelligence"],
        ]
    return commands


def install_agent_plugin(root: Path, target: str, dry_run: bool = False) -> tuple[int, dict[str, Any]]:
    commands = agent_install_commands(target)
    results: list[dict[str, Any]] = []
    exit_code = 0
    for platform, platform_commands in commands.items():
        executable = platform
        if not command_exists(executable):
            results.append({"target": platform, "status": "missing", "detail": f"未找到 {executable} CLI"})
            exit_code = 1
            continue
        for command in platform_commands:
            rendered = " ".join(command)
            if dry_run:
                results.append({"target": platform, "status": "planned", "command": rendered})
                continue
            code, out, err = run(command, root, timeout=180)
            combined = (out + "\n" + err).lower()
            already_exists = "already" in combined and any(token in combined for token in ("exist", "added", "configured", "installed"))
            status = "present" if code != 0 and already_exists else "ok" if code == 0 else "failed"
            results.append({
                "target": platform,
                "status": status,
                "command": testing_module.sanitize_text(rendered),
                "exitCode": code,
                "stdout": testing_module.sanitize_text(out[-3000:]),
                "stderr": testing_module.sanitize_text(err[-3000:]),
            })
            if status == "failed":
                exit_code = 1
                break
    return exit_code, {
        "target": target,
        "dryRun": dry_run,
        "bundleRoot": str(marketplace_bundle_root()) if marketplace_bundle_root() else None,
        "results": results,
        "restartRequired": not dry_run and exit_code == 0,
    }


def doctor_report(root: Path) -> dict[str, Any]:
    package = detect_package(root)
    tooling = detect_tooling(root, package)
    config_path = project_dir(root) / "config.json"
    config = load_json(config_path, {}) if config_path.exists() else {}
    return {
        "version": VERSION,
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "project": {
            "path": ".",
            "initialized": (project_dir(root) / "manifest.json").is_file(),
            "configSchemaVersion": config.get("schemaVersion"),
            "frameworks": package.get("frameworks", []),
            "packages": package.get("packages", []),
        },
        "pluginBundle": {"available": marketplace_bundle_root() is not None},
        "tooling": core_module.sanitize_tooling(tooling),
        "graphSources": detect_graph_sources(root),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="project-intel", description="项目智能 CLI")
    parser.add_argument("--project", help="项目根目录，默认为当前目录。")
    parser.add_argument("--version", action="store_true", help="打印版本号")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="初始化 .project-intel")
    init.add_argument("--interactive", action="store_true", help="显式要求在交互终端询问是否准备缺失图谱工具（init 默认已自动启用）")
    init.add_argument("--setup-missing", action="store_true", help="对缺失的可选图谱工具跳过询问并运行支持的安装/初始化命令")
    init.add_argument("--with-graph", action="store_true", default=True, help="检查图谱工具并运行已安装的分析器（init 默认启用）")
    init.add_argument("--no-graph", dest="with_graph", action="store_false", help="跳过图谱工具初始化")
    init.add_argument("--allow-repo-runner", action="store_true", help="允许执行项目仓库内发现的图谱 runner")
    init.add_argument("--allow-env-command", action="store_true", help="允许执行环境变量提供的图谱命令")
    init.add_argument("--allow-external-path", action="store_true", help="允许图谱命令引用项目外绝对路径")
    init.add_argument("--strict", action="store_true", help="--with-graph 未产生任何图谱来源时失败")
    init.add_argument("--dry-run", action="store_true", help="只分析将生成的项目事实，不写入文件或运行图谱命令")
    refresh = sub.add_parser("refresh", help="从当前工作区刷新 .project-intel")
    refresh.add_argument("--with-graph", action="store_true", help="刷新前运行已安装的图谱分析器；不会安装缺失工具")
    refresh.add_argument("--allow-repo-runner", action="store_true", help="允许执行项目仓库内发现的图谱 runner")
    refresh.add_argument("--allow-env-command", action="store_true", help="允许执行环境变量提供的图谱命令")
    refresh.add_argument("--allow-external-path", action="store_true", help="允许图谱命令引用项目外绝对路径")
    refresh.add_argument("--adapters", action="store_true", help="显式更新 AGENTS.md、CLAUDE.md 和根 .gitignore 适配器")
    install = sub.add_parser("install", help="安装 Claude 兼容的项目入口")
    install.add_argument("--hooks", action="store_true", help="在 .project-intel/hooks 下生成可选的 Git 钩子模板")
    install.add_argument("--activate-git-hooks", action="store_true", help="将项目智能包装器安装到 .git/hooks（不覆盖自定义钩子）")
    install.add_argument("--allow-external-hooks", action="store_true", help="显式允许 core.hooksPath 指向仓库外目录")
    adapters = sub.add_parser("adapters", help="预览、应用或移除 Codex/Claude 根入口适配器")
    adapters_sub = adapters.add_subparsers(dest="adapters_command", required=True)
    adapters_status_parser = adapters_sub.add_parser("status", help="检查适配器当前状态")
    adapters_status_parser.add_argument("--target", choices=("codex", "claude", "both"), default="both")
    adapters_status_parser.add_argument("--check", action="store_true", help="状态非 current 时返回非零")
    adapters_preview_parser = adapters_sub.add_parser("preview", help="预览将写入的适配器块")
    adapters_preview_parser.add_argument("--target", choices=("codex", "claude", "both"), default="both")
    adapters_apply_parser = adapters_sub.add_parser("apply", help="应用适配器块")
    adapters_apply_parser.add_argument("--target", choices=("codex", "claude", "both"), default="both")
    adapters_remove_parser = adapters_sub.add_parser("remove", help="移除 Project Intelligence 管理块")
    adapters_remove_parser.add_argument("--target", choices=("codex", "claude", "both"), default="both")
    check = sub.add_parser("check", help="运行项目智能检查")
    check.add_argument("--run-quality", action="store_true", help="实际运行检测到的 lint/type/style/format 命令")
    check.add_argument("--dry-run", action="store_true", help="只预览检查配置，不写入 project-status.md")
    intake = sub.add_parser("intake", help="分析需求入口、任务分流和 readiness")
    intake.add_argument("--task", help="兼容的中文任务摘要；需求级流程可使用 --requirement-name")
    intake.add_argument("--requirement-id", help="正式需求号；省略时需求级流程生成 LOCAL 时间编号")
    intake.add_argument("--requirement-name", help="需求名称")
    intake.add_argument("--ticket-kind", choices=("bug", "requirement"), default="requirement", help="单据类型；默认 requirement")
    intake.add_argument("--external-api", choices=("yes", "no"), help="明确确认是否影响对外接口")
    intake.add_argument("--requirement-action", choices=("generate", "register", "later"), help="需求文档动作")
    intake.add_argument("--requirement-path", help="requirement-action=register 时的仓库相对路径")
    intake.add_argument("--design-action", choices=("generate", "register", "later"), help="设计文档动作")
    intake.add_argument("--design-path", help="design-action=register 时的仓库相对路径")
    intake.add_argument("--track", choices=TRACK_CHOICES, default="auto", help="显式指定 quick/standard/complex；默认自动判断")
    intake.add_argument("--write", action="store_true", help="仅旧 --legacy 模式写入共享 intake 报告")
    intake.add_argument("--legacy", action="store_true", help="显式使用旧的非需求级兼容流程")
    spec = sub.add_parser("spec", help="为需求档案设置编号验收标准")
    spec.add_argument("--requirement-id", help="需求号；新流程不会创建独立 specs 目录")
    spec.add_argument("--criterion", action="append", help="AC-01:说明；可重复")
    spec.add_argument("--title")
    spec.add_argument("--from", dest="requirement")
    spec.add_argument("--track", choices=TRACK_CHOICES, default="auto", help="显式指定 quick/standard/complex；默认自动判断")
    spec.add_argument("--legacy", action="store_true", help="显式使用旧 specs 目录兼容流程")
    plan = sub.add_parser("plan", help="按需在需求目录生成 plan.md")
    plan.add_argument("--requirement-id", help="需求号；新流程写入 requirements/<id>/plan.md")
    plan.add_argument("--title")
    plan.add_argument("--from-spec")
    plan.add_argument("--track", choices=TRACK_CHOICES, default="auto", help="显式指定 quick/standard/complex；默认自动判断")
    plan.add_argument("--replace", action="store_true", help="显式覆盖已有 plan.md")
    plan.add_argument("--legacy", action="store_true", help="显式使用旧 plans 目录兼容流程")
    lifecycle = sub.add_parser("lifecycle", help="输出任务影响分析")
    lifecycle.add_argument("--task", help="任务摘要；传入 --requirement-id 时默认读取已登记的需求名称")
    lifecycle.add_argument("--requirement-id", help="复用该需求已确认的验收标准；与测试参数一起生成准确的收口命令")
    lifecycle.add_argument("--track", choices=TRACK_CHOICES, default="auto", help="显式指定 quick/standard/complex；默认自动判断")
    lifecycle.add_argument("--test-kind", choices=("unit", "service", "both", "manual"), help="已确认的测试类型；不会擅自默认 unit")
    lifecycle.add_argument("--report-action", choices=("generate", "register", "later"), help="已确认的报告动作；不会擅自默认 generate")
    lifecycle.add_argument("--report-path", help="report-action=register 时的仓库相对报告路径")
    lifecycle.add_argument("--acceptance", action="append", help="已确认的验收标准；默认使用需求档案全部 AC")
    lifecycle.add_argument("--write", action="store_true", help="仅旧 --legacy 模式写入共享影响报告")
    lifecycle.add_argument("--legacy", action="store_true", help="显式使用旧 reports 目录兼容写入")
    debug = sub.add_parser("debug", help="输出系统化调试上下文")
    debug.add_argument("--bug", required=True)
    debug.add_argument("--write", action="store_true", help="仅旧 --legacy 模式写入共享调试报告")
    debug.add_argument("--legacy", action="store_true", help="显式使用旧 reports 目录兼容写入")
    test = sub.add_parser("test", help="运行并记录 RED/GREEN/回归/验证测试证据")
    test.add_argument("--task", help="兼容的中文任务摘要；需求级流程可从 manifest 读取")
    test.add_argument("--requirement-id", help="将测试证据写入指定需求档案")
    test.add_argument("--test-kind", choices=("unit", "service", "manual"), help="需求级测试证据类型；both 只能用于测试契约")
    test.add_argument("--report-action", choices=("generate", "register", "later"), help="测试报告动作")
    test.add_argument("--report-path", help="report-action=register 时的仓库相对路径")
    test.add_argument("--acceptance", action="append", help="覆盖的验收标准，可重复或使用逗号分隔")
    test.add_argument("--phase", required=True, choices=testing_module.TEST_PHASES, help="测试阶段：red/green/regression/verify/manual")
    test.add_argument(
        "--command",
        dest="test_commands",
        action="append",
        help="要执行的目标测试命令；可重复。未提供时使用检测到的 test/verify 命令",
    )
    test.add_argument("--files", nargs="*", help="该证据覆盖的源码和测试文件")
    test.add_argument("--project-wide", action="store_true", help="显式声明证据覆盖整个项目")
    test.add_argument("--expect-failure", default="", help="RED 阶段必须匹配的预期失败文本或正则")
    test.add_argument("--manual-evidence", default="", help="manual 阶段的可复现人工验证说明")
    test.add_argument("--manual-approved", action="store_true", help="用户已批准以人工测试作为例外证据")
    test.add_argument("--manual-category", choices=("visual", "device", "hardware", "configuration"), help="允许人工例外的场景类别")
    test.add_argument("--manual-reason", default="", help="无法合理自动化的原因")
    test.add_argument("--manual-steps", default="", help="可复现操作步骤")
    test.add_argument("--manual-input", default="", help="测试输入")
    test.add_argument("--manual-observation", default="", help="实际观察结果")
    test.add_argument("--manual-evidence-path", default="", help="截图或日志的仓库相对路径")
    test.add_argument("--legacy", action="store_true", help="显式使用旧的非需求级兼容流程")
    requirement = sub.add_parser("requirement", help="维护需求级档案和状态机")
    requirement_sub = requirement.add_subparsers(dest="requirement_command", required=True)
    requirement_status = requirement_sub.add_parser("status", help="查看需求状态和门禁")
    requirement_status.add_argument("--requirement-id", required=True)
    requirement_query = requirement_sub.add_parser("query", help="按业务文件或状态查询需求历史")
    requirement_query.add_argument("--file", dest="file_path", help="仓库内业务文件路径")
    requirement_query.add_argument("--state", choices=requirements_module.STATES, help="需求状态")
    requirement_migrate = requirement_sub.add_parser("migrate", help="将旧 by-id 档案迁移到直接需求目录")
    requirement_migrate.add_argument("--apply", action="store_true", help="实际执行迁移；默认只预览")
    requirement_generate = requirement_sub.add_parser("generate", help="生成需求级产物")
    requirement_generate.add_argument("--requirement-id", required=True)
    requirement_generate.add_argument(
        "--type", required=True,
        choices=("requirement", "design", "plan", "test", "closure", "requirement-design"),
    )
    requirement_generate.add_argument(
        "--replace",
        action="store_true",
        help="显式覆盖已有规范文档；默认拒绝覆盖用户内容",
    )
    requirement_add = requirement_sub.add_parser("add", help="登记已有需求级产物")
    requirement_add.add_argument("--requirement-id", required=True)
    requirement_add.add_argument(
        "--type", required=True,
        choices=("requirement", "design", "plan", "unit-test", "service-test", "manual-test", "closure", "requirement-design"),
    )
    requirement_add.add_argument("--path", required=True)
    requirement_add.add_argument("--result", choices=("passed", "failed"))
    requirement_add.add_argument("--acceptance", action="append")
    requirement_add.add_argument("--files", nargs="*", default=[], help="测试报告覆盖的源码和测试文件")
    requirement_add.add_argument("--project-wide", action="store_true", help="显式声明测试报告覆盖整个项目")
    requirement_add.add_argument("--manual-approved", action="store_true")
    requirement_add.add_argument("--manual-category", choices=("visual", "device", "hardware", "configuration"))
    requirement_add.add_argument("--manual-reason", default="")
    requirement_add.add_argument("--manual-steps", default="")
    requirement_add.add_argument("--manual-input", default="")
    requirement_add.add_argument("--manual-observation", default="")
    requirement_add.add_argument("--manual-evidence-path", default="")
    requirement_acceptance = requirement_sub.add_parser("acceptance", help="维护独立于设计文档的验收标准")
    requirement_acceptance_sub = requirement_acceptance.add_subparsers(dest="acceptance_command", required=True)
    requirement_acceptance_set = requirement_acceptance_sub.add_parser("set", help="原子替换需求验收标准")
    requirement_acceptance_set.add_argument("--requirement-id", required=True)
    requirement_acceptance_set.add_argument("--criterion", action="append", required=True, help="AC-01:说明；可重复")
    requirement_test_contract = requirement_sub.add_parser("test-contract", help="维护实现前测试契约")
    requirement_test_contract_sub = requirement_test_contract.add_subparsers(dest="test_contract_command", required=True)
    requirement_test_contract_set = requirement_test_contract_sub.add_parser("set", help="设置测试类型、报告动作和 AC 映射")
    requirement_test_contract_set.add_argument("--requirement-id", required=True)
    requirement_test_contract_set.add_argument("--kind", required=True, choices=("unit", "service", "manual", "both"))
    requirement_test_contract_set.add_argument("--report-action", required=True, choices=("generate", "register", "later"))
    requirement_test_contract_set.add_argument("--acceptance", action="append")
    requirement_test_contract_set.add_argument("--report-path")
    requirement_ready = requirement_sub.add_parser("ready", help="通过实施前 readiness 门禁")
    requirement_ready.add_argument("--requirement-id", required=True)
    requirement_ready.add_argument("--resolution", required=True)
    requirement_begin = requirement_sub.add_parser("begin", help="进入 implementing 状态")
    requirement_begin.add_argument("--requirement-id", required=True)
    requirement_diagnose = requirement_sub.add_parser("diagnose", help="登记 Bug 根因和源码证据")
    requirement_diagnose.add_argument("--requirement-id", required=True)
    requirement_diagnose.add_argument("--root-cause", required=True)
    requirement_diagnose.add_argument(
        "--evidence",
        action="append",
        required=True,
        help="仓库相对源码路径，可用 path#symbol；可重复",
    )
    requirement_defer = requirement_sub.add_parser("defer", help="将需求级产物记录为稍后处理并保留阻塞")
    requirement_defer.add_argument("--requirement-id", required=True)
    requirement_defer.add_argument(
        "--type", required=True,
        choices=("requirement", "design", "test", "closure", "requirement-design"),
    )
    requirement_reopen = requirement_sub.add_parser("reopen", help="重新打开需求并废弃下游证据")
    requirement_reopen.add_argument("--requirement-id", required=True)
    requirement_reopen.add_argument("--reason", required=True)
    requirement_amend = requirement_sub.add_parser("amend", help="显式修改已登记的需求关键信息并废弃下游证据")
    requirement_amend.add_argument("--requirement-id", required=True)
    requirement_amend.add_argument("--requirement-name")
    requirement_amend.add_argument("--track", choices=TRACK_CHOICES)
    requirement_amend.add_argument("--ticket-kind", choices=("bug", "requirement"))
    requirement_amend.add_argument("--external-api", choices=("yes", "no"))
    requirement_amend.add_argument("--requirement-action", choices=("generate", "register", "later"))
    requirement_amend.add_argument("--requirement-path")
    requirement_amend.add_argument("--design-action", choices=("generate", "register", "later"))
    requirement_amend.add_argument("--design-path")
    requirement_amend.add_argument("--reason", required=True)
    requirement_resolve = requirement_sub.add_parser("resolve-finding", help="按稳定 ID 解决评审问题")
    requirement_resolve.add_argument("--requirement-id", required=True)
    requirement_resolve.add_argument("--finding-id", action="append", required=True)
    requirement_resolve.add_argument("--resolved-by", required=True)
    requirement_resolve.add_argument("--resolution", required=True)
    review = sub.add_parser("review", help="登记需求级代码评审结果")
    review.add_argument("--requirement-id", required=True)
    review.add_argument("--result", required=True, choices=("passed", "failed"))
    review.add_argument("--summary", required=True)
    review.add_argument("--finding", action="append", default=[], help="critical:说明、important:说明 或 minor:说明")
    review.add_argument("--files", nargs="*", default=[])
    review.add_argument("--dry-run", action="store_true", help="只检查评审参数和当前需求，不写入 manifest")
    finish = sub.add_parser("finish", help="任务完成后生成收口报告")
    finish.add_argument("--task", help="兼容的中文任务摘要；需求级流程从 manifest 读取")
    finish.add_argument("--requirement-id", help="执行需求级 finish 强门禁")
    finish.add_argument("--run-quality", action="store_true", help="实际运行检测到的 lint/type/style/format/test/verify 命令")
    finish.add_argument("--files", nargs="*", help="本次需求实际影响的源码文件；用于收口范围展示")
    finish.add_argument("--manual-evidence", default="", help="没有自动测试时，记录可复现的人工验证证据")
    finish.add_argument("--dry-run", action="store_true", help="只检查 finish 门禁，不写入状态")
    finish.add_argument("--legacy", action="store_true", help="显式使用旧的非需求级兼容流程")
    maintain = sub.add_parser("maintain", help="任务完成后刷新项目智能")
    maintain.add_argument("--task", help="兼容的中文任务摘要；需求级流程从 manifest 读取")
    maintain.add_argument("--requirement-id", help="只有 finished 状态才允许维护并关闭")
    maintain.add_argument("--run-quality", action="store_true", help="实际运行检测到的 lint/type/style/format/test/verify 命令")
    maintain.add_argument("--archive", action="store_true", help="仅旧 --legacy 模式保留维护历史")
    maintain.add_argument("--files", nargs="*", help="本次需求实际影响的源码文件；用于维护每个文件唯一的简短中文需求记录")
    maintain.add_argument("--dry-run", action="store_true", help="只检查 maintain 前置状态，不关闭需求")
    maintain.add_argument("--legacy", action="store_true", help="显式使用旧的非需求级兼容流程")
    requirements = sub.add_parser("requirements", help="按源码文件维护简短中文需求记录")
    requirements.add_argument("--task", required=True, help="中文需求摘要")
    requirements.add_argument("--files", nargs="+", required=True, help="要沉淀需求的源码文件")
    requirements.add_argument("--legacy", action="store_true", help="显式使用旧 requirements/files 兼容流程")
    query = sub.add_parser("query", help="搜索项目智能产物")
    query.add_argument("text")
    graph_tools = sub.add_parser("graph-tools", help="查询可选图谱工具的状态与命令")
    graph_tools.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    doctor = sub.add_parser("doctor", help="诊断运行时、项目和图谱工具状态")
    doctor.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    agent = sub.add_parser("agent", help="显式安装 Claude/Codex 插件")
    agent_sub = agent.add_subparsers(dest="agent_command", required=True)
    agent_install = agent_sub.add_parser("install", help="安装插件到 Claude、Codex 或两者")
    agent_install.add_argument("--target", choices=("codex", "claude", "all"), default="all")
    agent_install.add_argument("--dry-run", action="store_true", help="只输出将执行的安装命令")
    sub.add_parser("version", help="打印版本号")
    return parser


def comma_values(values: Optional[list[str]]) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(item.strip() for item in str(value).split(",") if item.strip())
    return sorted(dict.fromkeys(result))


def parse_review_findings(values: list[str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for value in values:
        severity, separator, text = value.partition(":")
        if not separator:
            severity, separator, text = value.partition("：")
        if not separator:
            fail_usage("--finding 必须使用 critical:说明、important:说明 或 minor:说明。")
        findings.append({"severity": severity.strip().lower(), "text": text.strip(), "resolved": False})
    return findings


def parse_acceptance_values(values: list[str]) -> list[dict[str, str]]:
    criteria: list[dict[str, str]] = []
    for value in values:
        identifier, separator, description = str(value).partition(":")
        if not separator:
            identifier, separator, description = str(value).partition("：")
        if not separator:
            fail_usage("--criterion 必须使用 AC-01:说明 格式。")
        criteria.append({"id": identifier.strip(), "description": description.strip()})
    return criteria


def legacy_workflow_warning(command: str) -> None:
    print(f"提示：{command} 正在使用 --legacy 兼容模式；该模式不具备需求级强门禁。")


def require_legacy(args: argparse.Namespace, command: str) -> None:
    if not getattr(args, "legacy", False):
        fail_usage(f"{command} 未提供 --requirement-id；如需使用旧流程必须显式传入 --legacy。")


def dispatch_command(args: argparse.Namespace, root: Path, json_mode: bool) -> tuple[int, Any]:
    if args.command == "version" or args.version:
        print(VERSION)
        return 0, {"version": VERSION}
    if args.command == "init":
        if (args.setup_missing or args.interactive) and not args.with_graph:
            fail_usage("--setup-missing/--interactive 不能与 --no-graph 同时使用。")
        if args.strict and not args.with_graph:
            fail_usage("--strict 不能与 --no-graph 同时使用。")
        if args.dry_run:
            result = preview_init(root, with_graph=args.with_graph, strict=args.strict)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0, result
        result = init_project(
            root,
            refresh=False,
            interactive=args.interactive or (args.with_graph and not args.setup_missing),
            setup_missing=args.setup_missing,
            with_graph=args.with_graph,
            strict=args.strict,
            allow_repo_runner=args.allow_repo_runner,
            allow_env_command=args.allow_env_command,
            allow_external_path=args.allow_external_path,
        )
        print(f"已初始化 .project-intel，索引了 {result['manifest']['fileCount']} 个文本文件。")
        if result.get("agentFiles"):
            print("已维护项目级 Agent 入口：" + ", ".join(result["agentFiles"]))
        if result.get("legacyCleanup"):
            print("已清理旧版本地 skill 残留：" + ", ".join(result["legacyCleanup"]))
        return 0, result
    if args.command == "refresh":
        ensure_initialized(root)
        if args.adapters:
            result = adapters_apply(root, target="both")
            print("已维护项目级 Agent 入口：" + ", ".join(item["path"] for item in result.get("entries", [])))
            return 0, result
        result = init_project(
            root,
            refresh=True,
            with_graph=args.with_graph,
            adapters=False,
            allow_repo_runner=args.allow_repo_runner,
            allow_env_command=args.allow_env_command,
            allow_external_path=args.allow_external_path,
        )
        print(f"已刷新 .project-intel，索引了 {result['manifest']['fileCount']} 个文本文件。")
        if result.get("agentFiles"):
            print("已维护项目级 Agent 入口：" + ", ".join(result["agentFiles"]))
        if result.get("legacyCleanup"):
            print("已清理旧版本地 skill 残留：" + ", ".join(result["legacyCleanup"]))
        return 0, result
    if args.command == "install":
        result = install_claude(root, hooks=args.hooks, activate_hooks=args.activate_git_hooks, allow_external_hooks=args.allow_external_hooks)
        print(f"已安装 Claude 适配器到 {result['claude']}")
        if result.get("agentFiles"):
            print("已维护项目级 Agent 入口：" + ", ".join(result["agentFiles"]))
        if result.get("legacyCleanup"):
            print("已清理旧版本地 skill 残留：" + ", ".join(result["legacyCleanup"]))
        if result.get("hookTemplates"):
            print(f"已生成钩子模板：{len(result['hookTemplates'])}")
        for item in result.get("hookResults", []):
            print(f"{item.get('hook')}：{item.get('status')} - {item.get('detail')}")
        return 0, result
    if args.command == "adapters":
        try:
            if args.adapters_command == "status":
                result = adapters_status(root, target=args.target)
                if not json_mode:
                    for item in result.get("entries", []):
                        print(f"{item.get('target')}\t{item.get('status')}\t{item.get('path')}")
                return (1 if args.check and not result.get("ok") else 0), result
            if args.adapters_command == "preview":
                result = adapters_preview(root, target=args.target)
                if not json_mode:
                    for item in result.get("entries", []):
                        print(f"{item.get('target')}\t{item.get('action')}\t{item.get('path')}")
                return 0, result
            if args.adapters_command == "apply":
                result = adapters_apply(root, target=args.target)
                if not json_mode:
                    print("已维护项目级 Agent 入口：" + ", ".join(item["path"] for item in result.get("entries", [])))
                return 0, result
            if args.adapters_command == "remove":
                result = adapters_remove(root, target=args.target)
                if not json_mode:
                    for item in result.get("entries", []):
                        print(f"{item.get('target')}\t{item.get('action')}\t{item.get('path')}")
                return 0, result
        except RuntimeError as exc:
            fail_usage(str(exc))
    if args.command == "check":
        if args.dry_run:
            result = doctor_report(root)
            return 0, {"dryRun": True, "check": result}
        code = run_check(root, args.run_quality)
        return code, {"report": ".project-intel/project-status.md"}
    if args.command == "intake":
        if args.write and not args.legacy:
            fail_usage("需求级 intake 不再写入共享 reports；如需旧兼容报告请显式使用 --legacy。")
        effective_task = args.task or args.requirement_name
        if not effective_task:
            fail_usage("intake 必须提供 --task 或 --requirement-name。")
        path = write_intake(root, effective_task, track=args.track, write_report=args.write)
        analysis = analyze_task_intake(
            root,
            effective_task,
            load_project_snapshot(root),
            track=args.track,
            ticket_kind=args.ticket_kind,
        )
        requirement_manifest = None
        if args.requirement_id or args.requirement_name:
            if not args.requirement_name:
                fail_usage("需求级 intake 必须提供 --requirement-name。")
            if args.external_api is None:
                fail_usage("需求级 intake 必须用 --external-api yes|no 明确确认对外接口影响。")
            try:
                requirement_manifest = requirements_module.create_requirement(
                    root,
                    args.requirement_id,
                    args.requirement_name,
                    track=analysis.get("track") or args.track,
                    external_api=args.external_api == "yes",
                    external_api_source="user",
                    ticket_kind=args.ticket_kind,
                    requirement_action=args.requirement_action,
                    requirement_path=args.requirement_path,
                    design_action=args.design_action,
                    design_path=args.design_path,
                )
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
        else:
            # Read-only task classification is not a lifecycle mutation and stays available without --legacy.
            if args.legacy:
                legacy_workflow_warning("intake")
        return 0, {"path": str(path) if path else None, "requirement": requirement_manifest, **analysis}
    if args.command == "spec":
        if args.requirement_id:
            if not args.criterion:
                fail_usage("需求级 spec 必须至少提供一个 --criterion AC-01:说明。")
            try:
                result = requirements_module.set_acceptance_criteria(
                    root, args.requirement_id, parse_acceptance_values(args.criterion)
                )
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
            return 0, result
        require_legacy(args, "spec")
        legacy_workflow_warning("spec")
        if not args.title or not args.requirement:
            fail_usage("旧 spec 兼容模式必须提供 --title 和 --from。")
        path = write_spec(root, args.title, args.requirement, track=args.track)
        return 0, {"path": str(path)}
    if args.command == "plan":
        if args.requirement_id:
            try:
                result = requirements_module.generate_artifact(
                    root,
                    args.requirement_id,
                    "plan",
                    replace=bool(args.replace),
                )
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
            return 0, result
        require_legacy(args, "plan")
        legacy_workflow_warning("plan")
        if not args.title or not args.from_spec:
            fail_usage("旧 plan 兼容模式必须提供 --title 和 --from-spec。")
        path = write_plan(root, args.title, args.from_spec, track=args.track)
        return 0, {"path": str(path)}
    if args.command == "lifecycle":
        if args.write and not args.legacy:
            fail_usage("lifecycle 默认只输出；写入旧 reports 必须显式使用 --legacy。")
        if not args.task and not args.requirement_id:
            fail_usage("lifecycle 必须提供 --task 或 --requirement-id。")
        if any((args.test_kind, args.report_action, args.report_path, args.acceptance)) and not args.requirement_id:
            fail_usage("lifecycle 指定测试合同必须同时提供 --requirement-id，避免使用未确认的验收标准。")
        if bool(args.test_kind) != bool(args.report_action):
            fail_usage("lifecycle 的 --test-kind 与 --report-action 必须同时提供。")
        requirement_manifest = None
        acceptance_ids: list[str] = []
        task = args.task
        if args.requirement_id:
            try:
                requirement_manifest = requirements_module.load_requirement(root, args.requirement_id)
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
            task = task or str(requirement_manifest.get("requirementName") or "")
            known_acceptance = [str(item.get("id")) for item in requirement_manifest.get("acceptanceCriteria", []) if item.get("id")]
            acceptance_ids = comma_values(args.acceptance) or known_acceptance
            unknown_acceptance = sorted(set(acceptance_ids) - set(known_acceptance))
            if unknown_acceptance:
                fail_usage("lifecycle 指定的验收标准未在需求档案确认：" + ", ".join(unknown_acceptance))
            if args.report_action == "register" and not args.report_path:
                fail_usage("lifecycle 的 --report-action register 必须提供 --report-path。")
            if requirement_manifest.get("externalApiImpact", {}).get("value") and args.test_kind and args.test_kind not in {"service", "both"}:
                fail_usage("对外接口需求必须选择 --test-kind service 或 both。")
        payload = lifecycle_payload(
            root,
            task or "",
            track=args.track,
            requirement_id=args.requirement_id,
            test_kind=args.test_kind,
            report_action=args.report_action,
            report_path=args.report_path,
            acceptance_ids=acceptance_ids,
            ticket_kind=str(requirement_manifest.get("ticketKind") or "requirement") if requirement_manifest else "requirement",
        )
        print(payload["body"])
        path = None
        if args.write:
            path = project_dir(root) / "reports" / "task-impact.md"
            write_text(path, payload["body"])
            print(f"\n已写入任务影响报告：{path}")
        return 0, {"path": str(path) if path else None, **payload["analysis"]}
    if args.command == "debug":
        if args.write and not args.legacy:
            fail_usage("debug 默认只输出；写入旧 reports 必须显式使用 --legacy。")
        path = write_debug_context(root, args.bug, write_report=args.write)
        return 0, {"path": str(path) if path else None}
    if args.command == "requirement":
        try:
            if args.requirement_command == "status":
                result = requirements_module.status_payload(root, args.requirement_id)
            elif args.requirement_command == "query":
                if not args.file_path and not args.state:
                    raise requirements_module.RequirementError("requirement query 至少提供 --file 或 --state。")
                result = requirements_module.query_requirements(root, file_path=args.file_path, state=args.state)
                if not json_mode:
                    if not result:
                        print("未找到匹配的需求档案。")
                    for item in result:
                        print(f"{item.get('requirementId')}\t{item.get('state')}\t{item.get('requirementName')}")
                return 0, result
            elif args.requirement_command == "migrate":
                result = requirements_module.migrate_layout(root, dry_run=not args.apply)
                if not json_mode:
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                return (0 if result.get("ok") else 1), result
            elif args.requirement_command == "generate":
                result = requirements_module.generate_artifact(
                    root,
                    args.requirement_id,
                    args.type,
                    replace=bool(args.replace),
                )
            elif args.requirement_command == "add":
                manual = None
                if args.type == "manual-test":
                    manual = {
                        "approved": bool(args.manual_approved),
                        "category": args.manual_category,
                        "reason": args.manual_reason,
                        "steps": args.manual_steps,
                        "input": args.manual_input,
                        "observation": args.manual_observation,
                        "evidencePath": args.manual_evidence_path,
                    }
                result = requirements_module.register_artifact(
                    root,
                    args.requirement_id,
                    args.type,
                    args.path,
                    result=args.result,
                    acceptance_ids=comma_values(args.acceptance),
                    files=args.files,
                    project_wide=args.project_wide,
                    manual=manual,
                )
            elif args.requirement_command == "acceptance":
                if args.acceptance_command != "set":
                    return 2, None
                result = requirements_module.set_acceptance_criteria(
                    root,
                    args.requirement_id,
                    parse_acceptance_values(args.criterion),
                )
            elif args.requirement_command == "test-contract":
                if args.test_contract_command != "set":
                    return 2, None
                result = requirements_module.set_test_contract(
                    root,
                    args.requirement_id,
                    kind=args.kind,
                    report_action=args.report_action,
                    acceptance_ids=comma_values(args.acceptance),
                    report_path=args.report_path,
                )
            elif args.requirement_command == "ready":
                result = requirements_module.ready_requirement(root, args.requirement_id, args.resolution)
            elif args.requirement_command == "begin":
                result = requirements_module.begin_requirement(root, args.requirement_id)
            elif args.requirement_command == "diagnose":
                result = requirements_module.record_diagnosis(
                    root,
                    args.requirement_id,
                    root_cause=args.root_cause,
                    evidence=args.evidence,
                )
            elif args.requirement_command == "defer":
                result = requirements_module.record_later(root, args.requirement_id, args.type)
            elif args.requirement_command == "reopen":
                result = requirements_module.reopen_requirement(root, args.requirement_id, args.reason)
            elif args.requirement_command == "amend":
                external_api = None if args.external_api is None else args.external_api == "yes"
                result = requirements_module.amend_requirement(
                    root,
                    args.requirement_id,
                    requirement_name=args.requirement_name,
                    track=args.track,
                    ticket_kind=args.ticket_kind,
                    external_api=external_api,
                    external_api_source="user",
                    requirement_action=args.requirement_action,
                    requirement_path=args.requirement_path,
                    design_action=args.design_action,
                    design_path=args.design_path,
                    reason=args.reason,
                )
            elif args.requirement_command == "resolve-finding":
                result = requirements_module.resolve_review_findings(
                    root,
                    args.requirement_id,
                    comma_values(args.finding_id),
                    resolved_by=args.resolved_by,
                    resolution=args.resolution,
                )
            else:
                return 2, None
        except requirements_module.RequirementError as exc:
            fail_usage(str(exc))
        print(f"需求 {args.requirement_id}：{result.get('state')}")
        return 0, result
    if args.command == "test":
        if not args.requirement_id:
            require_legacy(args, "test")
            legacy_workflow_warning("test")
        manual_approval = None
        if args.test_kind == "manual":
            manual_approval = {
                "approved": bool(args.manual_approved),
                "category": args.manual_category,
                "reason": args.manual_reason,
                "steps": args.manual_steps,
                "input": args.manual_input,
                "observation": args.manual_observation,
                "evidencePath": args.manual_evidence_path,
            }
            if not args.manual_evidence:
                args.manual_evidence = "；".join(
                    part for part in (args.manual_steps, args.manual_input, args.manual_observation, args.manual_evidence_path) if part
                )
        return run_project_test(
            root,
            args.task,
            args.phase,
            commands=args.test_commands,
            files=args.files,
            manual_evidence=args.manual_evidence,
            expect_failure=args.expect_failure,
            project_wide=args.project_wide,
            requirement_id=args.requirement_id,
            test_kind=args.test_kind,
            report_action=args.report_action,
            report_path=args.report_path,
            acceptance_ids=comma_values(args.acceptance),
            manual_approval=manual_approval,
        )
    if args.command == "review":
        if args.dry_run:
            try:
                manifest = requirements_module.load_requirement(root, args.requirement_id)
                snapshot = requirements_module.capture_requirement_scope(root, manifest)
                result = {
                    "dryRun": True,
                    "requirementId": args.requirement_id,
                    "state": manifest.get("state"),
                    "files": args.files,
                    "findings": parse_review_findings(args.finding),
                    "diffHash": snapshot.get("diffHash"),
                }
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
            return 0, result
        try:
            result = requirements_module.record_review(
                root,
                args.requirement_id,
                result=args.result,
                summary=args.summary,
                findings=parse_review_findings(args.finding),
                files=args.files,
                snapshot=requirements_module.capture_requirement_scope(
                    root, requirements_module.load_requirement(root, args.requirement_id)
                ),
            )
        except requirements_module.RequirementError as exc:
            fail_usage(str(exc))
        return 0 if result.get("state") == "reviewed" else 1, result
    if args.command == "finish":
        if not args.requirement_id:
            if not args.task:
                fail_usage("finish 必须提供 --task 或 --requirement-id。")
            require_legacy(args, "finish")
            legacy_workflow_warning("finish")
        if args.dry_run and args.requirement_id:
            try:
                manifest = requirements_module.load_requirement(root, args.requirement_id)
                snapshot = requirements_module.capture_requirement_scope(root, manifest)
                requirements_module.validate_scope_selection(
                    root,
                    args.files if args.files is not None else list(snapshot.get("files", [])),
                    snapshot,
                )
                requirements_module.validate_finished_freshness(root, args.requirement_id)
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
            return 0, {"dryRun": True, "requirementId": args.requirement_id, "state": manifest.get("state")}
        code = finish_project(
            root,
            args.task,
            run_quality=args.run_quality,
            files=args.files,
            manual_evidence=args.manual_evidence,
            requirement_id=args.requirement_id,
        )
        return code, {
            "report": (
                str(requirements_module.active_manifest_path(root, args.requirement_id).relative_to(root))
                if args.requirement_id else ".project-intel/reports/finish-report.md"
            )
        }
    if args.command == "maintain":
        if not args.requirement_id:
            if not args.task:
                fail_usage("maintain 必须提供 --task 或 --requirement-id。")
            require_legacy(args, "maintain")
            legacy_workflow_warning("maintain")
        if args.dry_run and args.requirement_id:
            try:
                requirements_module.validate_finished_freshness(root, args.requirement_id)
                manifest = requirements_module.load_requirement(root, args.requirement_id)
                if manifest.get("state") != "finished":
                    raise requirements_module.RequirementError("maintain 只能从 finished 状态开始。")
            except requirements_module.RequirementError as exc:
                fail_usage(str(exc))
            return 0, {"dryRun": True, "requirementId": args.requirement_id, "state": manifest.get("state")}
        code = maintain_project(
            root,
            args.task,
            args.run_quality,
            archive=args.archive,
            files=args.files,
            requirement_id=args.requirement_id,
        )
        return code, {
            "maintenance": (
                str(requirements_module.active_manifest_path(root, args.requirement_id).relative_to(root))
                if args.requirement_id else ".project-intel/maintenance/latest.md"
            )
        }
    if args.command == "requirements":
        require_legacy(args, "requirements")
        legacy_workflow_warning("requirements")
        paths = update_file_requirement_docs(root, args.task, args.files)
        return 0, {"paths": [str(path) for path in paths]}
    if args.command == "query":
        code = query_project(root, args.text)
        return code, {"query": args.text}
    if args.command == "graph-tools":
        if json_mode:
            tooling = detect_tooling(root, detect_package(root))
            return 0, tooling.get("graphActions", [])
        code = report_graph_tools(root, as_json=False)
        return code, None
    if args.command == "doctor":
        result = doctor_report(root)
        if not json_mode:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0, result
    if args.command == "agent" and args.agent_command == "install":
        code, result = install_agent_plugin(root, args.target, dry_run=args.dry_run)
        if not json_mode:
            for item in result["results"]:
                print(f"{item.get('target')}：{item.get('status')} - {item.get('command') or item.get('detail')}")
            if result.get("restartRequired"):
                print("插件已安装；请启动新的 Codex/Claude Code 会话加载 skills。")
        return code, result
    return 2, None


def main(argv: list[str]) -> int:
    clean_argv, json_mode = extract_global_json(argv)
    if "--version" in clean_argv and len(clean_argv) == 1:
        if json_mode:
            print(json.dumps(json_envelope("version", 0, {"version": VERSION}), ensure_ascii=False))
        else:
            print(VERSION)
        return 0
    if not json_mode:
        parser = build_parser()
        args = parser.parse_args(clean_argv)
        root = project_root(args.project)
        code, _ = dispatch_command(args, root, False)
        return code
    parser = build_parser()
    output = io.StringIO()
    errors = io.StringIO()
    command = "unknown"
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try:
            args = parser.parse_args(clean_argv)
            command = args.command
            root = project_root(args.project)
            code, result = dispatch_command(args, root, True)
        except SystemExit as exc:
            code = int(exc.code) if isinstance(exc.code, int) else 2
            result = {"error": errors.getvalue().strip() or output.getvalue().strip() or str(exc) or "command failed"}
        except Exception as exc:
            # JSON callers must never receive a raw traceback or a partial non-JSON response.
            # Expected gate failures use exit code 2 above; unexpected runtime errors use 1.
            code = 1
            result = {"error": str(exc) or exc.__class__.__name__}
    print(json.dumps(json_envelope(command, code, result, output.getvalue()), ensure_ascii=False, indent=2, default=str))
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
