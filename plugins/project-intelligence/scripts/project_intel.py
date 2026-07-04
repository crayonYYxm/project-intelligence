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


VERSION = "0.1.3"
UNDERSTAND_AGENT_COMMAND = "/understand . --language zh"
UNDERSTAND_REPO = "Egonex-AI/Understand-Anything"
UNDERSTAND_CODEX_INSTALL_COMMAND = "curl -fsSL https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.sh | bash -s codex"
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


def upsert_managed_block(path: Path, block: str) -> None:
    current = read_text(path)
    managed = f"{PROJECT_INTEL_BLOCK_START}\n{block.strip()}\n{PROJECT_INTEL_BLOCK_END}"
    pattern = re.compile(
        rf"{re.escape(PROJECT_INTEL_BLOCK_START)}.*?{re.escape(PROJECT_INTEL_BLOCK_END)}",
        re.DOTALL,
    )
    if pattern.search(current):
        next_text = pattern.sub(managed, current).rstrip()
    elif current.strip():
        next_text = current.rstrip() + "\n\n" + managed
    else:
        next_text = managed
    write_text(path, next_text)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def project_root(arg: str | None) -> Path:
    root = Path(arg or os.getcwd()).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"项目路径不是目录：{root}")
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
    claude_cache = home / ".claude" / "plugins" / "cache"
    if claude_cache.exists():
        candidates.extend(claude_cache.glob("*/understand-anything"))
        candidates.extend(claude_cache.glob("*/understand-anything/*"))
    roots = []
    for candidate in candidates:
        if str(candidate) and (candidate / "package.json").exists() and (candidate / "pnpm-workspace.yaml").exists():
            roots.append(candidate)
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
    installed = load_json(Path.home() / ".claude" / "plugins" / "installed_plugins.json", {})
    plugins = installed.get("plugins", {}) if isinstance(installed, dict) else {}
    enabled_plugins = load_json(Path.home() / ".claude" / "settings.json", {}).get("enabledPlugins", {})
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
    code, out, _ = run(["claude", "plugin", "list"], Path.home(), timeout=20)
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
    home = Path.home()
    for root in roots:
        text = str(root)
        if root == home / ".understand-anything-plugin" or ".codex/understand-anything" in text or ".agents/skills" in text:
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
        powershell_command = (
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            '"iwr -useb https://raw.githubusercontent.com/Egonex-AI/Understand-Anything/main/install.ps1 | iex"'
        )
        if command_exists("powershell") or command_exists("pwsh"):
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
    elif command_exists("gitnexus"):
        gitnexus_command = "gitnexus analyze"
    gitnexus_install_command = "npx gitnexus analyze" if command_exists("npx") else None

    actions = [
        {
            "tool": "GitNexus",
            "reason": "符号级调用、影响分析、PR/变更风险",
            "state": "installed" if gitnexus_command else "installable" if gitnexus_install_command else "missing",
            "stateLabel": "已安装，可直接分析" if gitnexus_command else "可下载并运行分析" if gitnexus_install_command else "不可用",
            "analyzeCommand": gitnexus_command,
            "installCommand": gitnexus_install_command,
            "canAnalyze": bool(gitnexus_command),
            "canInstall": bool(gitnexus_install_command),
        }
    ]

    ua_roots = understand_plugin_roots()
    ua_claude_installs = claude_understand_installs()
    ua_command = understand_analyze_command()
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


def setup_missing_tools(root: Path, tooling: dict[str, Any], with_graph: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in tooling.get("recommendedActions", []):
        tool = action.get("tool")
        if not action.get("canRun"):
            results.append({"tool": tool, "status": "skipped", "detail": f"未检测到可运行的 {tool} 命令。"})
            continue
        if action.get("installOptions"):
            option = choose_install_option(action, auto_approve=True)
            if option:
                results.extend(run_install_option(root, action, option))
            continue
        command = action.get("command") or ("npx gitnexus analyze" if tool == "GitNexus" else None)
        if not command:
            results.append({"tool": tool, "status": "skipped", "detail": f"未检测到可运行的 {tool} 命令。"})
            continue
        results.append(run_graph_command(root, action, command))
    return results


def run_graph_command(root: Path, action: dict[str, Any], command: str) -> dict[str, Any]:
    code, out, err = run_shell(command, root, timeout=300)
    return {
        "tool": action.get("tool"),
        "status": "ok" if code == 0 else "failed",
        "command": command,
        "exitCode": code,
        "stdout": out[-4000:],
        "stderr": err[-4000:],
    }


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


def setup_graph_tools(root: Path, tooling: dict[str, Any], auto_approve: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in tooling.get("graphActions", []):
        tool = action.get("tool")
        analyze_command = action.get("analyzeCommand")
        state = action.get("state")

        if analyze_command:
            print(f"{tool} 已安装，开始运行分析：{analyze_command}")
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

        print(f"开始准备并执行 {tool}：{install_option.get('command')}")
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


def handle_tooling_setup(root: Path, tooling: dict[str, Any], interactive: bool, setup_missing: bool, with_graph: bool) -> list[dict[str, Any]]:
    if tooling_has_missing_optional(tooling):
        print_tooling_summary(tooling)
    if not with_graph:
        return []
    return setup_graph_tools(root, tooling, auto_approve=setup_missing)


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
            "recommendation": "审查重复使用是否应复用或抽取为组件/Hook；默认不阻塞。",
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
            entrypoint_candidates.append({"path": rp, "reason": "路径/名称暗示非标准入口点", "level": "candidate"})
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
        sources.append({"name": "GitNexus", "path": ".gitnexus", "role": "符号调用、影响、变更风险", "status": "present"})
    else:
        sources.append({"name": "GitNexus", "path": ".gitnexus", "role": "符号调用、影响、变更风险", "status": "missing"})
    ua_graph = root / ".understand-anything" / "knowledge-graph.json"
    if ua_graph.exists():
        graph = load_json(ua_graph, {})
        sources.append(
            {
                "name": "Understand-Anything",
                "path": ".understand-anything/knowledge-graph.json",
                "role": "架构、模块、领域流、入职",
                "status": "present",
                "nodes": len(graph.get("nodes", []) or []),
                "edges": len(graph.get("edges", []) or []),
            }
        )
    else:
        sources.append({"name": "Understand-Anything", "path": ".understand-anything/knowledge-graph.json", "role": "架构、模块、领域流、入职", "status": "missing"})
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
            "project-intelligence 不读取或集成 .cgraphx 数据。",
            "可用时优先使用 GitNexus 和 Understand-Anything 作为图谱来源。",
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
    docs["quality.md"] = f"""# 质量检查

规则等级：

- `hard`：已确认的规则，会导致 `project-intel check` 失败
- `preferred`：稳定的项目约定
- `inferred`：扫描器推断，需要人工审查
- `candidate`：非阻塞建议

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
- 冗余候选数：{len(frontend.get("redundancyCandidates", []))}

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
- 候选非标准入口点数：{len(backend.get("candidateEntrypoints", []))}

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
    return docs


def table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_None detected._"
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell or "") for cell in row) + " |")
    return "\n".join(out)


def init_project(root: Path, refresh: bool = False, interactive: bool = False, setup_missing: bool = False, with_graph: bool = True, strict: bool = False) -> dict[str, Any]:
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
        raise SystemExit("请求了严格的图谱初始化，但没有 GitNexus 或 Understand-Anything 图谱。")
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
    agent_files = write_agent_entrypoints(root)
    return {"manifest": manifest, "frontend": frontend, "backend": backend, "config": config, "tooling": tooling, "setupResults": setup_results, "agentFiles": agent_files}


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

`init` 会检查图谱工具。已检测到可执行分析命令时会自动运行分析；未检测到时会询问是否安装/初始化，选择跳过时继续初始化 `.project-intel`。使用 `--setup-missing` 可跳过询问并直接运行支持的安装/初始化命令。对于只能在 agent 会话里执行的图谱工具，CLI 会把它们列到“后续 Agent 步骤”，但不会把初始化视为失败或反复要求重跑。
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
    return f"""# {title} 需求文档

生成时间：`{now_iso()}`

## 需求

{truncate(requirement, 3000)}

## 项目上下文

- 项目根目录：`{root}`
- 框架：{", ".join(manifest.get("frameworks", []) or ["未知"])}
- 组件数：{len(frontend.get("components", []))}
- Hooks 数：{len(frontend.get("hooks", []))}
- API 模块数：{len(frontend.get("apiModules", []))}
- 后端 API 数：{len(backend.get("apis", []))}
- 服务数：{len(backend.get("services", []))}

## 图谱来源

{table(["来源", "状态", "用途"], graph_rows)}

## 相关规范

- 添加新抽象前，复用已有的组件、Hook、请求工具、服务和领域模式。
- 冗余发现默认为 `candidate`，除非升级为 `hard`。
- 不要读取或依赖 `.cgraphx`。

## 质量门禁

{table(["类型", "命令", "来源"], quality_rows)}

## 验收标准

- 实现满足所述需求。
- 已检查相关的项目规范和可复用能力。
- 运行了项目质量检查，或明确说明了跳过原因。
- 任务完成后刷新 `.project-intel`，以捕获新的事实和候选。
"""


def write_spec(root: Path, title: str, requirement: str) -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "specs" / spec_filename(title, "spec")
    write_text(path, build_spec_doc(root, title, requirement, snapshot))
    print(f"已写入需求文档：{path}")
    return path


def resolve_input_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def build_plan_doc(root: Path, title: str, spec_path: Path, spec_text: str, snapshot: dict[str, Any]) -> str:
    config = snapshot["config"]
    quality_rows = [[c.get("kind"), c.get("command"), c.get("source")] for c in config.get("quality", {}).get("commands", [])]
    return f"""# {title} 实施计划

生成时间：`{now_iso()}`

来源需求文档：`{spec_path}`

## 概述

{truncate(spec_text, 2500)}

## 任务清单

- [ ] 如果工作区自本计划编写后有变更，使用 `project-intel refresh` 刷新项目上下文。
- [ ] 从 `.project-intel` 识别受影响的模块、组件、Hook、API、服务、路由和规范。
- [ ] 编写新代码前，检查可复用的组件、Hook、服务、请求工具和重复的候选模式。
- [ ] 根据项目测试配置添加或更新针对性测试。
- [ ] 实现需求行为，同时保持 hard 规范和现有边界。
- [ ] 运行 `project-intel check` 及相关的项目 test/type/lint 命令。
- [ ] 实现完成后运行 `project-intel maintain --task "{title}"` 以刷新知识库和维护报告。

## 质量命令

{table(["类型", "命令", "来源"], quality_rows)}
"""


def write_plan(root: Path, title: str, from_spec: str) -> Path:
    spec_path = resolve_input_path(root, from_spec)
    if not spec_path.exists():
        raise SystemExit(f"需求文档文件不存在：{spec_path}")
    snapshot = load_project_snapshot(root)
    spec_text = read_text(spec_path)
    path = project_dir(root) / "plans" / spec_filename(title, "plan")
    write_text(path, build_plan_doc(root, title, spec_path, spec_text, snapshot))
    print(f"已写入实施计划：{path}")
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
    return f"""# 任务影响

生成时间：`{now_iso()}`

## 任务

{truncate(task, 3000)}

## 图谱上下文

{table(["来源", "状态", "用途"], graph_rows)}

## 复用候选

{table(["类型", "名称", "路径"], reuse_rows)}

## 需检查的规范

- `.project-intel/standards/frontend.md`
- `.project-intel/standards/backend.md`
- `.project-intel/standards/reuse.md`
- `.project-intel/standards/quality.md`

## 完成钩子

实现完成后运行：

```bash
python3 /Users/xumeng/plugins/project-intelligence/scripts/project_intel.py maintain --task "{task[:120].replace('"', "'")}"
```
"""


def write_lifecycle(root: Path, task: str) -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "reports" / "task-impact.md"
    write_text(path, build_task_impact_doc(root, task, snapshot))
    print(f"已写入任务影响报告：{path}")
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
- `.project-intel/reports/tooling-report.md`

可用时使用 GitNexus 获取调用链、影响和变更代码风险。可用时使用 Understand-Anything 获取架构/领域上下文。不要读取或依赖 `.cgraphx`。
"""


def write_debug_context(root: Path, bug: str) -> Path:
    snapshot = load_project_snapshot(root)
    path = project_dir(root) / "reports" / "debug-context.md"
    write_text(path, build_debug_doc(root, bug, snapshot))
    print(f"已写入调试上下文报告：{path}")
    return path


def build_maintenance_report(root: Path, task: str, refresh_result: dict[str, Any], check_exit: int, run_quality: bool) -> str:
    manifest = refresh_result.get("manifest", {})
    frontend = refresh_result.get("frontend", {})
    backend = refresh_result.get("backend", {})
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

详情请查看 `.project-intel/reports/frontend-quality.md`。
"""


def maintain_project(root: Path, task: str, run_quality: bool) -> int:
    refresh_result = init_project(root, refresh=True)
    check_exit = run_check(root, run_quality=run_quality)
    path = project_dir(root) / "maintenance" / spec_filename(task, "maintenance")
    write_text(path, build_maintenance_report(root, task, refresh_result, check_exit, run_quality))
    print(f"已写入维护报告：{path}")
    return check_exit


def hook_script_body(hook_name: str) -> str:
    return f"""#!/bin/sh
# 项目智能钩子：{hook_name}

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
        """# 项目智能钩子

这些钩子模板是可选的。只有在 `project-intel install --hooks --activate-git-hooks` 将包装器安装到 `.git/hooks` 后才会激活。

设置 `PROJECT_INTEL_SKIP_HOOKS=1` 可跳过钩子执行。
""",
    )
    return written


def activate_git_hooks(root: Path) -> list[dict[str, Any]]:
    git_hooks = root / ".git" / "hooks"
    results = []
    if not git_hooks.exists() or not git_hooks.is_dir():
        return [{"hook": "*", "status": "skipped", "detail": "未找到 .git/hooks 目录。"}]
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
                results.append({"hook": hook_name, "status": "conflict", "detail": f"已保留现有钩子；待安装的包装器已写入 {pending}"})
                continue
        write_text(target, body)
        try:
            target.chmod(0o755)
        except OSError:
            pass
        results.append({"hook": hook_name, "status": "installed", "detail": str(target)})
    return results


def project_agent_rules() -> str:
    return """## Project Intelligence

This repository uses `.project-intel/` as the project-level fact source.

Project Intelligence is the workflow layer. Tools such as Grep, Read, Edit, Bash, Glob, or Write are only execution tools; using them does not replace the required Project Intelligence workflow.

If a conversation starts as explanation or discussion and later turns into code modification, pause before the first Edit/Write and enter the matching Project Intelligence workflow. Do not continue from discussion mode directly into code changes.

Before implementing, debugging, reviewing, planning, writing specs, answering component/API questions, or modifying behavior:

1. Classify the request and explicitly invoke the matching Project Intelligence skill when available:
   - Requirement shaping or brainstorming: `/project-intelligence:project-brainstorm`
   - Requirement/spec/acceptance criteria/impact: `/project-intelligence:project-spec`
   - Implementation plan or checklist: `/project-intelligence:project-plan`
   - Implementation, modification, fix, refactor, or feature work: `/project-intelligence:project-task`
   - Bug, error, regression, failed test, or unexpected behavior: `/project-intelligence:project-debug`
   - Code review, PR review, diff review, reuse/quality risk review: `/project-intelligence:project-review`
   - Quality, lint, type, format, style, redundancy checks: `/project-intelligence:project-quality`
   - Project knowledge, component/API/service usage, architecture questions: `/project-intelligence:project-knowledge`
   - Standards lookup, rule promotion/demotion, hard/preferred/inferred/candidate explanation: `/project-intelligence:project-standards`
   - Post-task refresh and lifecycle maintenance: `/project-intelligence:project-maintain`
   - Initialization or refresh of project facts: `/project-intelligence:project-refresh`
2. If slash skills are not available or do not trigger automatically, follow the same workflow manually before using execution tools and state which Project Intelligence workflow is being followed.
3. Check `.project-intel/manifest.json` for project metadata and refresh status.
4. Read only the relevant files under `.project-intel/standards/`, `.project-intel/knowledge/`, `.project-intel/graph/`, and `.project-intel/reports/`.
5. Apply `hard` standards as requirements; treat `preferred` as default project style; treat `inferred` and `candidate` as suggestions that need confirmation before enforcement.
6. Prefer existing public components, Hooks, utilities, API wrappers, services, DTO/VO/entity patterns, permission checks, transaction boundaries, and error-code conventions before adding new ones.
7. For implementation work, before the first Edit/Write, run the `project-task` workflow: check reuse, affected modules, relevant standards, and impact. Use GitNexus impact/explore/detect_changes tools when available; otherwise use `.project-intel` plus `project-intel lifecycle --task "<requirement>"` or `project-intel query "<symbol-or-feature>"`.
8. After meaningful code changes, run change review and maintenance: inspect the diff, run `project-intel check`, and run or recommend `project-intel maintain --task "<summary>"`.
9. For bug investigation, first gather symptoms, reproduce or locate evidence, trace likely paths through project knowledge/graph context, then propose fixes.
10. For review, inspect diff plus `.project-intel` standards/knowledge/graph context and report findings by severity before summaries.
11. Use `--run-quality` only when real lint/type/style/format checks should run.
12. If GitNexus or Understand-Anything graph context is available, use it for impact analysis and architecture/domain relationships.
13. Do not read or rely on `.cgraphx`; do not use `cgraphx explore` or cgraphx `detect_changes` as a Project Intelligence fallback.

Useful CLI fallbacks: `project-intel query`, `project-intel refresh`, `project-intel check`, `project-intel spec`, `project-intel plan`, `project-intel debug`, and `project-intel maintain`."""


def write_agent_entrypoints(root: Path) -> list[str]:
    targets = [root / "AGENTS.md", root / "CLAUDE.md"]
    rules = project_agent_rules()
    for target in targets:
        upsert_managed_block(target, rules)
    return [str(target) for target in targets]


def install_claude(root: Path, hooks: bool = False, activate_hooks: bool = False) -> dict[str, Any]:
    claude = root / ".claude"
    skills = claude / "skills"
    standards = claude / "standards"
    skills.mkdir(parents=True, exist_ok=True)
    standards.mkdir(parents=True, exist_ok=True)
    agent_rules = project_agent_rules()
    agent_files = write_agent_entrypoints(root)
    write_text(
        claude / "CLAUDE.md",
        f"""# 项目智能

{agent_rules}
""",
    )
    skill_template = """---
name: {name}
description: {description}
---

# {title}

以 `.project-intel` 作为项目事实来源。从 `.project-intel/manifest.json` 开始，然后只读取相关的规范、知识 JSON、报告和图谱摘要。

不要使用 `.cgraphx`。可用时优先使用 GitNexus 获取符号级影响，使用 Understand-Anything 获取架构/领域上下文。
"""
    entries = [
        ("project-task", "实现、修改、修复、重构或添加项目功能时使用，需要复用、规范、组件、API、服务或图谱上下文。需求开发, 功能开发, 实现需求, 开发任务, 做需求, 写功能。", "项目任务"),
        ("project-brainstorm", "塑造项目需求、脑暴方案、明确范围或在编写代码前选择实现方向时使用。需求脑暴, 脑暴, 讨论需求。", "需求脑暴"),
        ("project-spec", "编写或更新项目需求文档、设计说明、验收标准或任务影响摘要时使用。需求文档, 需求设计, 需求涉及关系和规范。", "需求文档"),
        ("project-plan", "将已批准的项目需求或规格转化为包含项目规范和验证步骤的实施计划时使用。技术方案, 实施计划, 开发计划。", "实施计划"),
        ("project-debug", "调查 bug、错误、测试失败、回归、异常行为或调试问题时使用。查询bug, 排查bug, 定位问题。", "调试"),
        ("project-maintain", "项目任务完成或需要刷新规范、知识库、报告、钩子或生命周期产物时使用。维护, 项目维护, 更新知识库。", "项目维护"),
        ("project-review", "根据项目规范、图谱影响、质量检查、冗余和测试审查代码变更时使用。代码审查, 代码评审, PR审查, 代码检查, review, review代码。", "代码审查"),
        ("project-knowledge", "回答项目结构、组件、API、服务、模块、规范或业务流程相关问题时使用。项目知识, 项目结构, 项目架构。", "项目知识"),
        ("project-refresh", "更新或初始化项目规范、知识库、图谱摘要和报告时使用。刷新, 更新, 刷新项目, 更新项目。", "刷新项目"),
        ("project-standards", "查询、说明、确认、升级或降级项目规范和规则等级时使用。项目规范, 规范, 代码规范, 标准。", "项目规范"),
        ("project-quality", "运行或解读前端/后端 lint、类型、格式、样式、冗余和规范检查时使用。质量检查, 代码质量, 检查工具。", "质量检查"),
    ]
    for name, desc, title in entries:
        write_text(skills / f"{name}.md", skill_template.format(name=name, description=desc, title=title))
    write_text(standards / "project-intelligence.md", "Project standards are generated under `.project-intel/standards/`.\n")
    hook_templates = write_hook_templates(root) if hooks or activate_hooks else []
    hook_results = activate_git_hooks(root) if activate_hooks else []
    return {
        "claude": str(claude),
        "agentFiles": agent_files + [str(claude / "CLAUDE.md")],
        "hookTemplates": [str(path) for path in hook_templates],
        "hookResults": hook_results,
    }


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
    print(f"项目智能检查完成：{pdir / 'reports' / 'frontend-quality.md'}")
    return exit_code


def build_quality_report(results: list[dict[str, Any]], frontend: dict[str, Any], backend: dict[str, Any]) -> str:
    rows = [[r.get("kind"), r.get("command"), r.get("exitCode")] for r in results]
    redundancy = frontend.get("redundancyCandidates", [])
    return f"""# 质量报告

## 命令

{table(["类型", "命令", "退出码"], rows) if rows else "_已检测到质量命令但未运行，或未配置任何命令。_"}

## 冗余

- 前端冗余候选数：{len(redundancy)}
- 后端候选入口点数：{len(backend.get("candidateEntrypoints", []))}

冗余发现默认为 `candidate`，除非团队策略升级，否则不会导致检查失败。
"""


def query_project(root: Path, text: str) -> int:
    pdir = project_dir(root)
    if not (pdir / "manifest.json").exists():
        print("未找到 .project-intel。请先运行 project-intel init。")
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
        print("未找到直接匹配的项目智能结果。请尝试更宽泛的关键词或刷新知识库。")
        return 0
    for name, snippet in matches[:10]:
        print(f"\n## {name}\n")
        print(snippet)
    return 0


def report_graph_tools(root: Path, as_json: bool = False) -> int:
    package = detect_package(root)
    tooling = detect_tooling(root, package)
    print_graph_tools_report(tooling, as_json=as_json)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="project-intel", description="项目智能 CLI")
    parser.add_argument("--project", help="项目根目录，默认为当前目录。")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="初始化 .project-intel")
    init.add_argument("--interactive", action="store_true", help="兼容参数；init 默认会在缺失图谱工具时询问")
    init.add_argument("--setup-missing", action="store_true", help="对缺失的可选图谱工具跳过询问并运行支持的安装/初始化命令")
    init.add_argument("--with-graph", action="store_true", default=True, help="启用图谱工具检查、安装询问和已安装工具自动分析，默认启用")
    init.add_argument("--no-graph", dest="with_graph", action="store_false", help="跳过图谱工具初始化")
    init.add_argument("--strict", action="store_true", help="--with-graph 未产生任何图谱来源时失败")
    sub.add_parser("refresh", help="从当前工作区刷新 .project-intel")
    install = sub.add_parser("install", help="安装 Claude 兼容的项目入口")
    install.add_argument("--hooks", action="store_true", help="在 .project-intel/hooks 下生成可选的 Git 钩子模板")
    install.add_argument("--activate-git-hooks", action="store_true", help="将项目智能包装器安装到 .git/hooks（不覆盖自定义钩子）")
    check = sub.add_parser("check", help="运行项目智能检查")
    check.add_argument("--run-quality", action="store_true", help="实际运行检测到的 lint/type/style/format 命令")
    spec = sub.add_parser("spec", help="在 .project-intel/specs 下写入需求文档")
    spec.add_argument("--title", required=True)
    spec.add_argument("--from", dest="requirement", required=True)
    plan = sub.add_parser("plan", help="在 .project-intel/plans 下写入实施计划")
    plan.add_argument("--title", required=True)
    plan.add_argument("--from-spec", required=True)
    lifecycle = sub.add_parser("lifecycle", help="写入任务影响报告")
    lifecycle.add_argument("--task", required=True)
    debug = sub.add_parser("debug", help="写入系统化调试上下文报告")
    debug.add_argument("--bug", required=True)
    maintain = sub.add_parser("maintain", help="任务完成后刷新项目智能")
    maintain.add_argument("--task", required=True)
    maintain.add_argument("--run-quality", action="store_true", help="实际运行检测到的 lint/type/style/format 命令")
    query = sub.add_parser("query", help="搜索项目智能产物")
    query.add_argument("text")
    graph_tools = sub.add_parser("graph-tools", help="查询可选图谱工具的状态与命令")
    graph_tools.add_argument("--json", action="store_true", help="以 JSON 输出图谱工具信息")
    sub.add_parser("version", help="打印版本号")
    args = parser.parse_args(argv)
    root = project_root(args.project)
    if args.command == "version":
        print(VERSION)
        return 0
    if args.command == "init":
        result = init_project(root, refresh=False, interactive=args.interactive, setup_missing=args.setup_missing, with_graph=args.with_graph, strict=args.strict)
        print(f"已初始化 .project-intel，索引了 {result['manifest']['fileCount']} 个文本文件。")
        if result.get("agentFiles"):
            print("已维护项目级 Agent 入口：" + ", ".join(result["agentFiles"]))
        return 0
    if args.command == "refresh":
        result = init_project(root, refresh=True)
        print(f"已刷新 .project-intel，索引了 {result['manifest']['fileCount']} 个文本文件。")
        if result.get("agentFiles"):
            print("已维护项目级 Agent 入口：" + ", ".join(result["agentFiles"]))
        return 0
    if args.command == "install":
        result = install_claude(root, hooks=args.hooks, activate_hooks=args.activate_git_hooks)
        print(f"已安装 Claude 适配器到 {result['claude']}")
        if result.get("agentFiles"):
            print("已维护项目级 Agent 入口：" + ", ".join(result["agentFiles"]))
        if result.get("hookTemplates"):
            print(f"已生成钩子模板：{len(result['hookTemplates'])}")
        for item in result.get("hookResults", []):
            print(f"{item.get('hook')}：{item.get('status')} - {item.get('detail')}")
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
    if args.command == "graph-tools":
        return report_graph_tools(root, as_json=args.json)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
