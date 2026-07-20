from __future__ import annotations

import json
import hashlib
import html
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


TEST_PHASES = ("red", "green", "regression", "verify", "manual")
PASSING_PHASES = {"green", "regression", "verify", "manual"}
COMMAND_ERROR_CODES = {2, 3, 4, 5, 124, 126, 127}
MIN_MANUAL_EVIDENCE_LENGTH = 12


def evidence_json_path(root: Path) -> Path:
    return root / ".project-intel" / "reports" / "test-evidence.json"


def evidence_markdown_path(root: Path) -> Path:
    return root / ".project-intel" / "reports" / "test-evidence.md"


def load_test_evidence(root: Path) -> dict[str, Any]:
    path = evidence_json_path(root)
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def manual_evidence_valid(value: str) -> bool:
    compact = "".join(character.lower() for character in value if character.isalnum())
    generic = {
        "已手动验证",
        "手动验证通过",
        "验证通过",
        "测试通过",
        "manualverificationpassed",
        "testedmanually",
    }
    return len(compact) >= MIN_MANUAL_EVIDENCE_LENGTH and compact not in generic


SECRET_KEY_PATTERN = (
    r"authorization|cookie|token|access[_-]?token|refresh[_-]?token|password|secret|"
    r"api[_-]?key|aws[_-]?secret[_-]?access[_-]?key|aws[_-]?access[_-]?key[_-]?id|"
    r"party[_-]?id|phone|mobile|phone[_-]?(?:no|number)|mobile[_-]?(?:no|number)|"
    r"id[_-]?card|identity[_-]?(?:card|number)|cert(?:ificate)?[_-]?(?:no|number)"
)
SECRET_VALUE_PATTERN = r'''(?:"[^"]*"|'[^']*'|[^\s,;&]+)'''
RAW_SECRET_PATTERNS = (
    # Personal access tokens and service credentials often appear in raw command
    # output, without a surrounding `token=` key.  Treat their distinctive public
    # formats as secrets before persisting any evidence.
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", re.I),
    re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b", re.I),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", re.I),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b", re.I),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b", re.I),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b", re.I),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\b(?:rk|sk)_live_[A-Za-z0-9]{16,}\b", re.I),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
)
DATABASE_URL_PATTERN = re.compile(
    r"(?i)\b((?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://)([^:@/\s]+):([^@/\s]+)@"
)
URL_USERINFO_PATTERN = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)([^/@\s]+)@")
MAINLAND_MOBILE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d[-\s]?\d{4}[-\s]?\d{4}(?!\d)"
)
PRC_IDENTITY_PATTERN = re.compile(
    r"(?<![0-9A-Za-z])(?:"
    r"[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]"
    r"|[1-9]\d{7}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}"
    r")(?![0-9A-Za-z])"
)


def _find_unescaped(value: str, character: str, start: int) -> int:
    index = start
    while True:
        index = value.find(character, index)
        if index < 0:
            return -1
        backslashes = 0
        cursor = index - 1
        while cursor >= 0 and value[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return index
        index += 1


def _redact_header_values(value: str, header: str) -> str:
    """Redact a complete header value while preserving a quoted shell command suffix."""
    pattern = re.compile(rf"(?i)\b{re.escape(header)}\s*:\s*")
    parts: list[str] = []
    cursor = 0
    while True:
        match = pattern.search(value, cursor)
        if match is None:
            parts.append(value[cursor:])
            break
        parts.append(value[cursor:match.end()])
        delimiter = value[match.start() - 1] if match.start() > 0 else ""
        if delimiter in {"'", '"'}:
            end = _find_unescaped(value, delimiter, match.end())
        else:
            newline_positions = [
                position
                for position in (value.find("\n", match.end()), value.find("\r", match.end()))
                if position >= 0
            ]
            end = min(newline_positions) if newline_positions else len(value)
        if end < 0:
            end = len(value)
        parts.append("[REDACTED]")
        cursor = end
    return "".join(parts)


def _redact_url_userinfo(match: re.Match[str]) -> str:
    userinfo = match.group(2)
    if "[REDACTED]" in userinfo:
        return match.group(0)
    replacement = "[REDACTED]:[REDACTED]" if ":" in userinfo else "[REDACTED]"
    return f"{match.group(1)}{replacement}@"


def sanitize_text(value: str) -> str:
    text = str(value or "")
    text = _redact_header_values(text, "Authorization")
    text = _redact_header_values(text, "Cookie")
    text = re.sub(
        rf'''(?i)((?:["']?)(?:{SECRET_KEY_PATTERN})(?:["']?)\s*[:=]\s*)(?!\[REDACTED\]){SECRET_VALUE_PATTERN}''',
        lambda match: f"{match.group(1)}[REDACTED]",
        text,
    )
    text = re.sub(
        rf"(?i)(--(?:{SECRET_KEY_PATTERN})(?:=|\s+))(?!\[REDACTED\]){SECRET_VALUE_PATTERN}",
        lambda match: f"{match.group(1)}[REDACTED]",
        text,
    )
    text = re.sub(
        rf"(?i)(\b[A-Za-z_][A-Za-z0-9_]*(?:TOKEN|PASSWORD|SECRET|API_KEY)\s*=\s*)(?!\[REDACTED\]){SECRET_VALUE_PATTERN}",
        lambda match: f"{match.group(1)}[REDACTED]",
        text,
    )
    text = re.sub(
        rf"(?i)(\bAWS_(?:SECRET_ACCESS_KEY|ACCESS_KEY_ID)\s*=\s*)(?!\[REDACTED\]){SECRET_VALUE_PATTERN}",
        lambda match: f"{match.group(1)}[REDACTED]",
        text,
    )
    text = DATABASE_URL_PATTERN.sub(lambda match: f"{match.group(1)}[REDACTED]:[REDACTED]@", text)
    text = URL_USERINFO_PATTERN.sub(_redact_url_userinfo, text)
    for pattern in RAW_SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    text = PRC_IDENTITY_PATTERN.sub("[REDACTED]", text)
    text = MAINLAND_MOBILE_PATTERN.sub("[REDACTED]", text)
    return text


def executed_test_count(result: dict[str, Any]) -> int:
    """Extract a real test count from recognised test-framework output.

    A zero exit code proves only that a command succeeded.  It must not turn a
    shell builtin, formatter, compiler, or an empty test selection into delivery
    evidence.  Unknown formats intentionally return zero and must use a
    registered structured report instead.
    """
    text = "\n".join((str(result.get("stdout") or ""), str(result.get("stderr") or "")))
    patterns = (
        r"(?im)^\s*Ran\s+(\d+)\s+tests?\b",                    # unittest
        r"(?im)\b(\d+)\s+passed\b",                            # pytest / many CLIs
        r"(?im)\bTests?\s+run:\s*(\d+)\b",                     # Maven Surefire
        r"(?im)\b(\d+)\s+tests?\s+(?:completed|passed)\b",     # Gradle / text reports
        r"(?im)\b(?:tests?|test cases?)\s*[:=]\s*(\d+)\b",     # Jest / Vitest summaries
        r'"(?:tests|testCount|numTotalTests)"\s*:\s*(\d+)',     # JSON reporters
    )
    counts = [int(match.group(1)) for pattern in patterns for match in re.finditer(pattern, text)]
    return max(counts, default=0)


def _markdown_literal(value: Any, *, line_break: str = "<br>") -> str:
    safe = sanitize_text(str(value or "")).replace("\r\n", "\n").replace("\r", "\n")
    escaped = html.escape(safe, quote=True)
    escaped = escaped.replace("|", "&#124;").replace("`", "&#96;")
    escaped = escaped.replace("[", "&#91;").replace("]", "&#93;")
    return escaped.replace("\n", line_break)


def _markdown_code(value: Any) -> str:
    return f"<code>{_markdown_literal(value)}</code>"


def _markdown_fence(value: Any) -> tuple[str, str]:
    safe = sanitize_text(str(value or ""))
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", safe)), default=0)
    fence = "`" * max(3, longest + 1)
    return fence, safe


def _hash_files(root: Path, files: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for item in files:
        path = root / item
        if not path.is_file():
            hashes[item] = "<missing>"
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        hashes[item] = digest.hexdigest()
    return hashes


def phase_passed(
    phase: str,
    results: list[dict[str, Any]],
    manual_evidence: str = "",
    expected_failure: str = "",
) -> bool:
    if phase == "manual":
        return manual_evidence_valid(manual_evidence)
    if not results:
        return False
    codes = [int(item.get("exitCode", 1)) for item in results]
    if phase == "red":
        if not expected_failure.strip() or not all(code != 0 and code not in COMMAND_ERROR_CODES for code in codes):
            return False
        try:
            pattern = re.compile(expected_failure, re.I | re.S)
        except re.error:
            return False
        return all(pattern.search("\n".join((str(item.get("stdout") or ""), str(item.get("stderr") or "")))) for item in results)
    return all(code == 0 and executed_test_count(item) > 0 for code, item in zip(codes, results))


def render_test_evidence(payload: dict[str, Any]) -> str:
    lines = [
        "# 测试证据",
        "",
        f"任务：{_markdown_code(payload.get('task') or '_未记录_')}",
        "",
        f"更新时间：{_markdown_code(payload.get('updatedAt') or 'unknown')}",
        "",
        "| 阶段 | 状态 | 命令/人工证据 | 文件范围 |",
        "| --- | --- | --- | --- |",
    ]
    for entry in payload.get("entries", []):
        commands = entry.get("commands", [])
        command_text = "<br>".join(
            f"{_markdown_code(item.get('command'))} → {_markdown_literal(item.get('exitCode'))}"
            f"（{_markdown_literal(item.get('executedCount', 0))} tests）"
            for item in commands
        )
        if not command_text:
            command_text = _markdown_literal(entry.get("manualEvidence") or "_")
        files = "<br>".join(_markdown_code(item) for item in entry.get("files", []))
        if not files:
            files = "项目级" if entry.get("projectWide") else "未记录"
        lines.append(
            f"| {_markdown_literal(entry.get('phase'))} | {_markdown_literal(entry.get('status'))} | "
            f"{command_text} | {files} |"
        )
    lines.extend(
        [
            "",
            "## 最近输出",
            "",
        ]
    )
    for entry in payload.get("entries", [])[-4:]:
        for result in entry.get("commands", []):
            output = "\n".join(part for part in (result.get("stdout", ""), result.get("stderr", "")) if part).strip()
            if not output:
                continue
            fence, output = _markdown_fence(output)
            lines.extend(
                [
                    f"### {_markdown_literal(entry.get('phase'), line_break=' ')} · 执行输出",
                    "",
                    f"命令：{_markdown_code(result.get('command'))}",
                    "",
                    f"{fence}text",
                    output,
                    fence,
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def record_test_evidence(
    root: Path,
    task: str,
    phase: str,
    files: list[str],
    results: list[dict[str, Any]],
    *,
    manual_evidence: str = "",
    expected_failure: str = "",
    project_wide: bool = False,
    now: str,
    write_json: Callable[[Path, Any], None],
    write_text: Callable[[Path, str], None],
) -> tuple[dict[str, Any], dict[str, Any]]:
    current = load_test_evidence(root)
    entries = current.get("entries", []) if current.get("task") == task else []
    safe_results = [
        {
            **item,
            "command": sanitize_text(str(item.get("command") or "")),
            "stdout": sanitize_text(str(item.get("stdout") or "")),
            "stderr": sanitize_text(str(item.get("stderr") or "")),
            "executedCount": executed_test_count(item),
        }
        for item in results
    ]
    safe_manual = sanitize_text(manual_evidence.strip())
    entry = {
        "phase": phase,
        "status": "passed" if phase_passed(phase, safe_results, safe_manual, expected_failure) else "failed",
        "recordedAt": now,
        "files": sorted(dict.fromkeys(files)),
        "fileHashes": _hash_files(root, files),
        "projectWide": bool(project_wide),
        "commands": safe_results,
    }
    if safe_manual:
        entry["manualEvidence"] = safe_manual
    if expected_failure.strip():
        entry["expectedFailure"] = sanitize_text(expected_failure.strip())
    payload = {
        "schemaVersion": 1,
        "task": task,
        "createdAt": current.get("createdAt", now) if current.get("task") == task else now,
        "updatedAt": now,
        "entries": (entries + [entry])[-50:],
    }
    write_json(evidence_json_path(root), payload)
    write_text(evidence_markdown_path(root), render_test_evidence(payload))
    return payload, entry


def _parse_time(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def evaluate_test_evidence(root: Path, task: str, files: list[str]) -> dict[str, Any]:
    payload = load_test_evidence(root)
    status = {
        "required": bool(files),
        "ready": not files,
        "taskMatches": payload.get("task") == task,
        "redObserved": False,
        "passingPhase": None,
        "path": str(evidence_markdown_path(root).relative_to(root)),
        "reason": "没有源码变更，不要求测试证据。" if not files else "未找到与当前任务匹配的通过证据。",
    }
    if not files or payload.get("task") != task:
        return status

    selected = set(files)
    latest_source_mtime = max(
        ((root / item).stat().st_mtime for item in files if (root / item).exists()),
        default=0.0,
    )
    for entry in payload.get("entries", []):
        evidence_files = set(entry.get("files", []))
        covers_selected_files = bool(entry.get("projectWide")) or bool(evidence_files and selected.issubset(evidence_files))
        if entry.get("phase") == "red" and entry.get("status") == "passed" and covers_selected_files:
            status["redObserved"] = True
        if entry.get("phase") not in PASSING_PHASES or entry.get("status") != "passed":
            continue
        if not covers_selected_files:
            continue
        file_hashes = entry.get("fileHashes")
        if isinstance(file_hashes, dict) and file_hashes != _hash_files(root, sorted(evidence_files)):
            continue
        recorded = _parse_time(entry.get("recordedAt", ""))
        if recorded is None or recorded.timestamp() + 0.001 < latest_source_mtime:
            continue
        status.update(
            {
                "ready": True,
                "passingPhase": entry.get("phase"),
                "reason": "已找到与当前任务、文件范围和源码时间匹配的通过证据。",
            }
        )
    if not status["ready"] and payload:
        status["reason"] = "现有证据与当前任务、文件范围或源码更新时间不匹配。"
    return status
