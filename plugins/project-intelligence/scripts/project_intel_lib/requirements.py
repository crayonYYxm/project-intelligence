from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from . import design_documents, requirement_documents
from .testing import sanitize_text


SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1
STATES = (
    "draft", "specified", "designed", "ready", "implementing", "verified", "reviewed", "finished", "closed",
    "documented",  # schema v1 兼容状态；schema v2 不再写入。
)
ARTIFACT_FILES = {
    "requirement": "requirement.md",
    "design": "design.md",
    "requirement-design": "design.md",
    "plan": "plan.md",
    "test": "test-report.md",
    "test-report": "test-report.md",
    "unit-test": "test-report.md",
    "service-test": "test-report.md",
    "manual-test": "test-report.md",
    "closure": "closure-summary.md",
}
ARTIFACT_SUFFIXES = {
    "requirement": {".md"},
    "design": {".md"},
    "requirement-design": {".md"},
    "plan": {".md"},
    "unit-test": {".md", ".txt", ".json", ".xml"},
    "service-test": {".md", ".txt", ".json", ".xml"},
    "manual-test": {".md", ".txt", ".json", ".xml"},
    "closure": {".md"},
}
TEST_KINDS = {"unit", "service", "manual"}
TEST_CONTRACT_KINDS = {"unit", "service", "both", "manual"}
WORKFLOW_ACTIONS = {"generate", "register", "later"}
PASSING_RESULTS = {"passed"}
BLOCKING_FINDINGS = {"critical", "important"}
MANUAL_REQUIRED_FIELDS = ("approved", "category", "reason", "steps", "input", "observation", "evidencePath")
MANUAL_CATEGORIES = {"visual", "device", "hardware", "configuration"}
MANUAL_EVIDENCE_PATH_MARKERS = {
    "artifact", "artifacts", "evidence", "evidences", "log", "logs",
    "screenshot", "screenshots", "test-evidence", "test-evidences",
}
REPORT_PATH_MARKERS = {
    "artifact",
    "artifacts",
    "coverage",
    "evidence",
    "report",
    "reports",
    "result",
    "results",
    "surefire-reports",
    "test-report",
    "test-reports",
    "test-result",
    "test-results",
}
PRODUCTION_PATH_MARKERS = {"app", "apps", "client", "lib", "libs", "package", "packages", "server", "service", "services", "src"}
CLOSURE_REQUIRED_SECTIONS = (
    "需求结果",
    "变更范围",
    "验收标准结果",
    "测试证据",
    "评审结论",
    "人工例外",
    "遗留问题",
    "复盘结论",
)
PLAN_REQUIRED_SECTIONS = (
    "实施范围",
    "输入基线",
    "文件级变更",
    "实施步骤",
    "测试与验收映射",
    "风险与回滚",
)
DELIVERY_ARTIFACT_TYPES = {
    "requirement",
    "design",
    "requirement-design",
    "plan",
    "test",
    "unit-test",
    "service-test",
    "manual-test",
    "closure",
    "manual-evidence",
}
DELIVERY_ARTIFACT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".xml",
    ".log",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
}


class RequirementError(RuntimeError):
    """Raised when a requirement workflow gate rejects an operation."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_requirement_id(now: Optional[datetime] = None) -> str:
    value = now or datetime.now()
    return value.strftime("LOCAL-%Y%m%d-%H%M%S")


def normalize_requirement_id(value: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        raise RequirementError("需求号不能为空。")
    if candidate in {".", ".."} or "/" in candidate or "\\" in candidate:
        raise RequirementError("需求号不能包含路径分隔符或路径穿越。")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", candidate):
        raise RequirementError("需求号只能包含字母、数字、点、下划线和连字符，且最长 100 个字符。")
    return candidate


def canonicalize_ticket_id(value: Optional[str], ticket_kind: str) -> str:
    if ticket_kind not in {"bug", "requirement"}:
        raise RequirementError("ticket kind 只能是 bug 或 requirement。")
    raw = str(value or "").strip()
    if not raw:
        return generate_requirement_id()
    if raw.isdigit():
        raw = ("bug" if ticket_kind == "bug" else "req") + raw
    return normalize_requirement_id(raw)


def _assert_safe_internal_path(root: Path, path: Path) -> Path:
    """Reject path traversal and every symlink component below the repository root."""
    root_absolute = Path(os.path.abspath(root))
    path_absolute = Path(os.path.abspath(path))
    try:
        relative = path_absolute.relative_to(root_absolute)
    except ValueError as exc:
        raise RequirementError(f"需求档案路径越出项目目录：{path}") from exc
    cursor = root_absolute
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RequirementError(f"需求档案路径不能包含符号链接：{cursor}")
        if not cursor.exists():
            break
    try:
        path_absolute.resolve(strict=False).relative_to(root_absolute.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise RequirementError(f"需求档案路径越出项目目录：{path}") from exc
    return path_absolute


def requirement_root(root: Path) -> Path:
    return _assert_safe_internal_path(root, root / ".project-intel" / "requirements")


def requirement_dir(root: Path, requirement_id: str) -> Path:
    return _assert_safe_internal_path(
        root,
        requirement_root(root) / normalize_requirement_id(requirement_id),
    )


def manifest_path(root: Path, requirement_id: str) -> Path:
    return requirement_dir(root, requirement_id) / "manifest.json"


def legacy_requirement_dir(root: Path, requirement_id: str) -> Path:
    return _assert_safe_internal_path(
        root,
        requirement_root(root) / "by-id" / normalize_requirement_id(requirement_id),
    )


def legacy_manifest_path(root: Path, requirement_id: str) -> Path:
    return legacy_requirement_dir(root, requirement_id) / "manifest.json"


def active_manifest_path(root: Path, requirement_id: str) -> Path:
    current = manifest_path(root, requirement_id)
    if current.is_file():
        return current
    legacy = legacy_manifest_path(root, requirement_id)
    return legacy if legacy.is_file() else current


def active_requirement_dir(root: Path, requirement_id: str) -> Path:
    return active_manifest_path(root, requirement_id).parent


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


class _RequirementLock:
    def __init__(
        self,
        directory: Path,
        timeout: float = 5.0,
        *,
        filename: str = ".manifest.lock",
    ) -> None:
        # Keep lock handles outside requirement directories so Windows can move
        # a legacy directory while the requirement remains exclusively locked.
        lock_parent = directory.parent.parent if directory.parent.name == "by-id" else directory.parent
        self.path = lock_parent / f".{directory.name}{filename}"
        self.timeout = timeout
        self.fd: Optional[int] = None

    def __enter__(self) -> "_RequirementLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(self.fd, f"{os.getpid()}\n".encode("ascii"))
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 60:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() >= deadline:
                    raise RequirementError(f"需求档案正被其他任务更新：{self.path.parent.name}")
                time.sleep(0.02)

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    _atomic_write(path, _json_bytes(manifest))


def load_requirement(root: Path, requirement_id: str) -> dict[str, Any]:
    path = active_manifest_path(root, requirement_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RequirementError(f"未找到需求档案：{normalize_requirement_id(requirement_id)}") from exc
    except json.JSONDecodeError as exc:
        raise RequirementError(f"需求档案 JSON 损坏：{path}") from exc
    if not isinstance(payload, dict) or payload.get("schemaVersion") not in {LEGACY_SCHEMA_VERSION, SCHEMA_VERSION}:
        raise RequirementError(f"不支持的需求档案格式：{path}")
    payload.setdefault("ticketKind", "requirement")
    payload.setdefault("sourceTickets", [])
    payload.setdefault("changedFiles", [])
    payload.setdefault("diagnosis", None)
    payload.setdefault("finishResult", None)
    payload.setdefault("maintenanceResult", None)
    payload.setdefault("baselineScope", None)
    return payload


def _mutate(root: Path, requirement_id: str, callback: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    path = active_manifest_path(root, requirement_id)
    directory = path.parent
    with _RequirementLock(directory):
        manifest = load_requirement(root, requirement_id)
        callback(manifest)
        manifest["revision"] = int(manifest.get("revision", 0)) + 1
        manifest["updatedAt"] = now_iso()
        _write_manifest(path, manifest)
    return manifest


def _set_state(manifest: dict[str, Any], state: str) -> None:
    if state not in STATES:
        raise RequirementError(f"未知需求状态：{state}")
    manifest["state"] = state
    manifest.setdefault("stateTimestamps", {})[state] = now_iso()


def _prepare_document_selection(
    root: Path,
    document_type: str,
    action: Optional[str],
    path_value: Optional[str],
) -> Optional[dict[str, Any]]:
    if action is None:
        if path_value:
            raise RequirementError("只有 action=register 时才能提供已有文档路径。")
        return None
    if action not in WORKFLOW_ACTIONS:
        raise RequirementError("文档动作只能是 generate、register 或 later。")
    relative: Optional[str] = None
    if action == "register":
        if not path_value:
            raise RequirementError("文档动作 register 必须提供仓库内已有文件路径。")
        _, relative = _resolve_repo_file(root, path_value)
        if Path(relative).suffix.lower() != ".md":
            raise RequirementError(f"{document_type} 的 register 路径必须是 Markdown 文件。")
    elif path_value:
        raise RequirementError("只有文档动作 register 可以提供已有文件路径。")
    return {
        "action": action,
        "path": relative,
        "status": "selected",
        "selectedAt": now_iso(),
    }


def _selection_matches(current: Any, requested: dict[str, Any]) -> bool:
    return isinstance(current, dict) and all(
        current.get(key) == requested.get(key)
        for key in ("action", "path")
    )


def _assert_document_selection(
    manifest: dict[str, Any],
    key: str,
    operation: str,
    *,
    source_path: Optional[str] = None,
) -> None:
    selection = manifest.get("workflowSelections", {}).get(key)
    if not isinstance(selection, dict):
        return
    action = selection.get("action")
    if operation == "generate" and action != "generate":
        raise RequirementError(f"{key} 已选择 {action}；如需改为 generate，请先使用 requirement amend。")
    if operation == "register" and action not in {"generate", "register"}:
        raise RequirementError(f"{key} 已选择 {action}；如需登记文档，请先使用 requirement amend。")
    if operation == "register" and action == "register":
        selected_path = str(selection.get("path") or "")
        if selected_path and source_path and selected_path != source_path:
            raise RequirementError(
                f"{key} 已选择登记路径 {selected_path}；如需改用 {source_path}，请先使用 requirement amend。"
            )


def _mark_document_selection(
    manifest: dict[str, Any],
    key: str,
    *,
    default_action: str,
    status: str,
    artifact_path: Optional[str] = None,
    source_path: Optional[str] = None,
) -> None:
    selections = manifest.setdefault("workflowSelections", {})
    current = dict(selections.get(key) or {})
    current.setdefault("action", default_action)
    current.setdefault("path", None)
    current.setdefault("selectedAt", now_iso())
    current["status"] = status
    current["updatedAt"] = now_iso()
    if artifact_path:
        current["artifactPath"] = artifact_path
    if source_path:
        current["path"] = source_path
    selections[key] = current


def create_requirement(
    root: Path,
    requirement_id: Optional[str],
    requirement_name: str,
    *,
    track: str = "standard",
    external_api: Optional[bool] = False,
    external_api_source: str = "user",
    ticket_kind: str = "requirement",
    requirement_action: Optional[str] = None,
    requirement_path: Optional[str] = None,
    design_action: Optional[str] = None,
    design_path: Optional[str] = None,
) -> dict[str, Any]:
    identifier = canonicalize_ticket_id(requirement_id, ticket_kind)
    name = sanitize_text(" ".join(str(requirement_name or "").split()))
    if not name:
        raise RequirementError("需求名称不能为空。")
    if track not in {"quick", "standard", "complex", "auto"}:
        raise RequirementError("track 只能是 auto、quick、standard 或 complex。")
    requested_selections = {
        key: selection
        for key, selection in {
            "requirement": _prepare_document_selection(root, "requirement", requirement_action, requirement_path),
            "design": _prepare_document_selection(root, "design", design_action, design_path),
        }.items()
        if selection is not None
    }
    path = manifest_path(root, identifier)
    if not path.is_file() and legacy_manifest_path(root, identifier).is_file():
        path = legacy_manifest_path(root, identifier)
    directory = path.parent
    with _RequirementLock(directory):
        if path.exists():
            current = load_requirement(root, identifier)
            current_external = current.get("externalApiImpact", {})
            if current.get("requirementName") != name:
                raise RequirementError(f"需求号 {identifier} 已绑定其他需求名称；如需修改请使用 requirement amend。")
            if (
                current.get("track") != track
                or current.get("ticketKind", "requirement") != ticket_kind
                or bool(current_external.get("value")) != bool(external_api)
                or bool(current_external.get("confirmed")) != bool(external_api is not None)
            ):
                raise RequirementError(f"需求号 {identifier} 已存在且关键信息不同；如需修改请使用 requirement amend。")
            current_selections = current.get("workflowSelections", {})
            if any(
                not _selection_matches(current_selections.get(key), selection)
                for key, selection in requested_selections.items()
            ):
                raise RequirementError(f"需求号 {identifier} 已存在且文档动作不同；如需修改请使用 requirement amend。")
            return current
        created = now_iso()
        baseline = capture_scope_snapshot(root)
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "revision": 1,
            "requirementId": identifier,
            "requirementName": name,
            "ticketKind": ticket_kind,
            "track": track,
            "externalApiImpact": {
                "confirmed": bool(external_api is not None),
                "value": bool(external_api),
                "source": external_api_source,
            },
            "state": "draft",
            "readiness": {"blockers": [], "resolutions": []},
            "sourceTickets": [],
            "acceptanceCriteria": [],
            "artifacts": [],
            "testContract": {
                "kind": None,
                "reportAction": None,
                "acceptanceIds": [],
                "reportPath": None,
                "status": "pending",
                "recordedAt": created,
                "source": "pending",
            },
            "testEvidence": [],
            "reviewRounds": [],
            "scopeSnapshots": [],
            "changedFiles": [],
            "diagnosis": None,
            "finishResult": None,
            "maintenanceResult": None,
            "workflowSelections": requested_selections,
            "currentDiffHash": None,
            "baselineDiffHash": baseline.get("diffHash"),
            "baselineCommit": baseline.get("gitCommit"),
            "baselineScope": {
                "diffHash": baseline.get("diffHash"),
                "gitCommit": baseline.get("gitCommit"),
                "entries": list(baseline.get("entries") or []),
            },
            "history": [],
            "stateTimestamps": {"draft": created},
            "createdAt": created,
            "updatedAt": created,
        }
        _write_manifest(path, manifest)
    return manifest


def amend_requirement(
    root: Path,
    requirement_id: str,
    *,
    requirement_name: Optional[str] = None,
    track: Optional[str] = None,
    external_api: Optional[bool] = None,
    external_api_source: str = "user",
    ticket_kind: Optional[str] = None,
    requirement_action: Optional[str] = None,
    requirement_path: Optional[str] = None,
    design_action: Optional[str] = None,
    design_path: Optional[str] = None,
    reason: str = "",
) -> dict[str, Any]:
    clean_reason = sanitize_text(" ".join(str(reason or "").split()))
    if not clean_reason:
        raise RequirementError("amend 必须记录修改原因。")
    if track is not None and track not in {"quick", "standard", "complex", "auto"}:
        raise RequirementError("track 只能是 auto、quick、standard 或 complex。")
    if ticket_kind is not None and ticket_kind not in {"bug", "requirement"}:
        raise RequirementError("ticket kind 只能是 bug 或 requirement。")
    requested_selections = {
        key: selection
        for key, selection in {
            "requirement": _prepare_document_selection(root, "requirement", requirement_action, requirement_path),
            "design": _prepare_document_selection(root, "design", design_action, design_path),
        }.items()
        if selection is not None
    }

    def mutate(manifest: dict[str, Any]) -> None:
        before = {
            "requirementName": manifest.get("requirementName"),
            "ticketKind": manifest.get("ticketKind", "requirement"),
            "track": manifest.get("track"),
            "externalApiImpact": dict(manifest.get("externalApiImpact", {})),
            "workflowSelections": json.loads(json.dumps(manifest.get("workflowSelections", {}))),
        }
        if requirement_name is not None:
            clean_name = sanitize_text(" ".join(str(requirement_name or "").split()))
            if not clean_name:
                raise RequirementError("需求名称不能为空。")
            manifest["requirementName"] = clean_name
        if track is not None:
            manifest["track"] = track
        if ticket_kind is not None:
            manifest["ticketKind"] = ticket_kind
        if external_api is not None:
            manifest["externalApiImpact"] = {
                "confirmed": True,
                "value": bool(external_api),
                "source": external_api_source,
            }
        if requested_selections:
            if manifest.get("state") not in {"draft", "specified"}:
                raise RequirementError("需求已进入下游状态；修改文档动作前请先 reopen。")
            selections = manifest.setdefault("workflowSelections", {})
            for key, selection in requested_selections.items():
                current = selections.get(key)
                if _selection_matches(current, selection):
                    continue
                if isinstance(current, dict) and current.get("status") == "completed":
                    raise RequirementError(f"{key} 文档已经完成；如需重新选择请先 reopen。")
                selections[key] = selection
        after = {
            "requirementName": manifest.get("requirementName"),
            "ticketKind": manifest.get("ticketKind", "requirement"),
            "track": manifest.get("track"),
            "externalApiImpact": dict(manifest.get("externalApiImpact", {})),
            "workflowSelections": json.loads(json.dumps(manifest.get("workflowSelections", {}))),
        }
        if before == after:
            raise RequirementError("amend 没有产生任何变化。")
        for evidence in manifest.get("testEvidence", []):
            evidence["valid"] = False
            evidence["invalidatedAt"] = now_iso()
            evidence["invalidatedReason"] = "需求关键信息已修改。"
        for review in manifest.get("reviewRounds", []):
            review["valid"] = False
            review["invalidatedAt"] = now_iso()
            review["invalidatedReason"] = "需求关键信息已修改。"
        manifest["finishResult"] = None
        manifest["maintenanceResult"] = None
        design_affecting = (
            before.get("requirementName") != after.get("requirementName")
            or before.get("ticketKind") != after.get("ticketKind")
            or before.get("externalApiImpact") != after.get("externalApiImpact")
        )
        legacy_design = any(
            artifact.get("type") in {"design", "requirement-design"}
            and artifact.get("status") not in {"draft", "stale", "failed"}
            and not isinstance(artifact.get("validation"), dict)
            for artifact in manifest.get("artifacts", [])
        )
        if design_affecting or legacy_design:
            for artifact in manifest.get("artifacts", []):
                artifact_kind = artifact.get("type")
                invalid_design = artifact_kind in {"design", "requirement-design"} and (
                    design_affecting or not isinstance(artifact.get("validation"), dict)
                )
                invalid_requirement = design_affecting and artifact_kind == "requirement"
                if invalid_design or invalid_requirement:
                    artifact["status"] = "stale"
                    artifact["invalidatedAt"] = now_iso()
                    artifact["invalidatedReason"] = (
                        "需求名称、类型或接口影响已修改。"
                        if design_affecting else "旧版设计在 amend 后必须按 0.3.0 模板重新验证。"
                    )
            for selection in manifest.get("workflowSelections", {}).values():
                if not isinstance(selection, dict):
                    continue
                selection["status"] = "stale"
                selection["invalidatedAt"] = now_iso()
                selection["invalidatedReason"] = (
                    "需求名称、类型或接口影响已修改。"
                    if design_affecting else "旧版设计必须重新验证。"
                )
            manifest["diagnosis"] = None
        manifest.setdefault("history", []).append({
            "action": "amend",
            "reason": clean_reason,
            "before": before,
            "after": after,
            "recordedAt": now_iso(),
        })
        if design_affecting or legacy_design:
            _set_state(
                manifest,
                "draft"
                if design_affecting or manifest.get("schemaVersion") == LEGACY_SCHEMA_VERSION
                else "specified",
            )
        elif manifest.get("state") in {"verified", "reviewed", "finished", "closed"}:
            _set_state(manifest, _best_document_state(root, manifest))

    return _mutate(root, requirement_id, mutate)


def _resolve_repo_file(root: Path, value: str) -> tuple[Path, str]:
    raw = str(value or "").strip()
    if not raw or re.match(r"^[a-z][a-z0-9+.-]*://", raw, re.I):
        raise RequirementError("产物必须登记仓库内的本地文件，不能是空路径或 URL。")
    root_resolved = root.resolve()
    candidate = Path(raw)
    path = candidate if candidate.is_absolute() else root / candidate
    try:
        root_stat = root_resolved.stat()
        for parent in [path, *path.parents]:
            try:
                parent_resolved = parent.resolve(strict=False)
                if parent_resolved == root_resolved.parent:
                    break
                parent_resolved.relative_to(root_resolved)
            except (OSError, ValueError):
                continue
            if parent.is_symlink() and parent_resolved != root_resolved:
                raise RequirementError(f"产物路径包含指向项目外的符号链接：{raw}")
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(root_resolved).as_posix()
    except (OSError, ValueError) as exc:
        raise RequirementError(f"产物路径不存在或越出项目目录：{raw}") from exc
    if root_resolved.stat().st_dev != root_stat.st_dev or root_resolved.stat().st_ino != root_stat.st_ino:
        raise RequirementError("项目根目录在路径解析期间发生变化。")
    if not resolved.is_file() or resolved.stat().st_size <= 0:
        raise RequirementError(f"产物文件不存在或为空：{raw}")
    return resolved, relative


def _test_report_path_valid(relative: str) -> bool:
    path = Path(relative)
    tokens = {part.lower().replace("_", "-") for part in path.parts}
    stem = path.stem.lower().replace("_", "-")
    if tokens & REPORT_PATH_MARKERS:
        return True
    return any(marker in stem for marker in ("coverage", "junit", "report", "result", "test-report"))


def _external_report_artifact_path_valid(relative: str) -> bool:
    path = Path(str(relative or "").replace("\\", "/"))
    directories = {part.lower().replace("_", "-") for part in path.parts[:-1]}
    return bool(directories & REPORT_PATH_MARKERS) and not bool(directories & PRODUCTION_PATH_MARKERS)


def _delivery_document_artifact_path_valid(relative: str, artifact_type: str) -> bool:
    """Keep validated human-facing documents out of business-code evidence.

    A caller must not be able to hide a production file merely by registering it
    as an artifact.  Delivery documents are Markdown-only and must not live
    below a conventional production source directory.  Their contents are
    validated separately when they are registered.
    """
    if artifact_type not in {"requirement", "design", "requirement-design", "plan", "closure"}:
        return False
    path = Path(str(relative or "").replace("\\", "/"))
    directories = {part.lower().replace("_", "-") for part in path.parts[:-1]}
    return path.suffix.lower() == ".md" and not bool(directories & PRODUCTION_PATH_MARKERS)


def _normalized_report_result(value: Any) -> Optional[str]:
    normalized = str(value or "").strip().lower()
    if normalized in {"passed", "pass", "success", "successful", "ok", "通过", "成功"}:
        return "passed"
    if normalized in {"failed", "fail", "failure", "error", "errors", "失败", "错误"}:
        return "failed"
    return None


def _json_report_result(payload: Any) -> Optional[str]:
    explicit: list[str] = []
    failure_counts: list[int] = []
    test_counts: list[int] = []

    def visit(value: Any, key: str = "") -> None:
        normalized_key = str(key).strip().lower().replace("_", "-")
        if normalized_key in {"result", "status", "outcome"}:
            result = _normalized_report_result(value)
            if result:
                explicit.append(result)
        if normalized_key in {"failures", "failed", "errors", "error-count"} and isinstance(value, (int, float)):
            failure_counts.append(int(value))
        if normalized_key in {"tests", "test-count", "total", "testcases"} and isinstance(value, (int, float)):
            test_counts.append(int(value))
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    if "failed" in explicit or any(value > 0 for value in failure_counts):
        return "failed"
    if "passed" in explicit:
        return "passed"
    if failure_counts and all(value == 0 for value in failure_counts) and any(value > 0 for value in test_counts):
        return "passed"
    return None


def _xml_report_result(root: ET.Element) -> Optional[str]:
    explicit: list[str] = []
    failure_count = 0
    test_count = 0
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"failure", "error"}:
            failure_count += 1
        for key, value in element.attrib.items():
            normalized_key = str(key).lower().replace("_", "-")
            if normalized_key in {"result", "status", "outcome"}:
                result = _normalized_report_result(value)
                if result:
                    explicit.append(result)
            if normalized_key in {"failures", "errors"}:
                try:
                    failure_count += int(value)
                except (TypeError, ValueError):
                    pass
            if normalized_key in {"tests", "testcases", "total"}:
                try:
                    test_count = max(test_count, int(value))
                except (TypeError, ValueError):
                    pass
    if "failed" in explicit or failure_count > 0:
        return "failed"
    if "passed" in explicit or test_count > 0:
        return "passed"
    return None


def _text_report_result(content: str) -> Optional[str]:
    labels = re.findall(
        r"(?im)^\s*(?:[-*]\s*)?(?:result|status|outcome|结果|状态)\s*[:：=]\s*(passed|pass|success|ok|failed|fail|error|通过|成功|失败|错误)(?:\b|$)",
        content,
    )
    if labels:
        return _normalized_report_result(labels[-1])
    for line in reversed(content.splitlines()):
        lowered = line.lower()
        failed_counts = [int(value) for value in re.findall(r"(?<!\d)(\d+)\s+(?:tests?\s+)?(?:failed|failures?|errors?)\b", lowered)]
        failed_counts += [int(value) for value in re.findall(r"(?:failures?|errors?|失败(?:数)?)\s*[:：=]\s*(\d+)", lowered)]
        passed_counts = [int(value) for value in re.findall(r"(?<!\d)(\d+)\s+(?:tests?\s+)?passed\b", lowered)]
        passed_counts += [int(value) for value in re.findall(r"(?:passed|通过(?:数)?)\s*[:：=]\s*(\d+)", lowered)]
        if any(value > 0 for value in failed_counts):
            return "failed"
        if any(value > 0 for value in passed_counts):
            return "passed"
    if re.search(r"(?i)\b(?:failed|failure|error)\b|测试失败|执行失败", content):
        return "failed"
    if re.search(r"(?i)\b(?:passed|success|successful)\b|测试通过|执行成功", content):
        return "passed"
    return None


def _report_execution_count(path: Path) -> int:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        counts: list[int] = []

        def visit(value: Any, key: str = "") -> None:
            normalized_key = str(key).strip().lower().replace("_", "-")
            if normalized_key in {"tests", "test-count", "total", "testcases", "executed", "executed-tests"} and isinstance(value, (int, float)):
                counts.append(max(0, int(value)))
            if isinstance(value, dict):
                for child_key, child in value.items():
                    visit(child, str(child_key))
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(payload)
        return max(counts, default=0)
    if suffix == ".xml":
        report_root = ET.parse(path).getroot()
        counts: list[int] = []
        for element in report_root.iter():
            for key, value in element.attrib.items():
                if str(key).lower().replace("_", "-") in {"tests", "testcases", "total", "executed"}:
                    try:
                        counts.append(max(0, int(value)))
                    except (TypeError, ValueError):
                        pass
        return max(counts, default=0)
    content = path.read_text(encoding="utf-8", errors="ignore")
    counts = [
        int(value)
        for pattern in (
            r"(?im)(?<!\d)(\d+)\s+(?:tests?\s+)?(?:passed|failed|errors?)\b",
            r"(?im)(?:tests?|testcases?|测试用例(?:数)?|执行测试数|已执行测试数)\s*[:：=]\s*(\d+)",
            r"(?im)(?:通过(?:数)?|失败(?:数)?)\s*[:：=]\s*(\d+)",
        )
        for value in re.findall(pattern, content)
    ]
    return max(counts, default=0)


def _declared_test_kinds(path: Path) -> set[str]:
    content = path.read_text(encoding="utf-8", errors="ignore").lower()
    kinds: set[str] = set()
    if re.search(r"\bmanual(?:\s+test)?\b|人工测试|手工测试|真机测试", content):
        kinds.add("manual")
    if re.search(r"\bservice(?:\s+test)?\b|接口测试|服务测试|api\s+test", content):
        kinds.add("service")
    if re.search(r"\bunit(?:\s+test)?\b|单元测试", content):
        kinds.add("unit")
    return kinds


def _validate_test_report_file(
    path: Path,
    relative: str,
    expected_result: Optional[str] = None,
    expected_test_kind: Optional[str] = None,
) -> str:
    if not _test_report_path_valid(relative):
        raise RequirementError("测试报告路径必须位于 reports/test-results/coverage/evidence 等报告目录，或使用明确的 report/result 文件名。")
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            content = json.dumps(payload, ensure_ascii=False).lower()
            structural = any(marker in content for marker in ('"tests"', '"testcases"', '"suites"', '"stats"', '"results"'))
            actual_result = _json_report_result(payload)
        elif suffix == ".xml":
            report_root = ET.parse(path).getroot()
            tag = report_root.tag.rsplit("}", 1)[-1].lower()
            structural = any(marker in tag for marker in ("test", "suite", "report", "result"))
            actual_result = _xml_report_result(report_root)
        else:
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            structural = any(marker in content for marker in ("test", "测试", "单元", "接口", "service", "manual"))
            actual_result = _text_report_result(content)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        raise RequirementError(f"测试报告格式无效：{relative}") from exc
    if not structural or actual_result is None:
        raise RequirementError("测试报告必须包含可识别的测试结构和通过/失败结果。")
    executed_count = _report_execution_count(path)
    if actual_result == "passed" and expected_test_kind != "manual" and executed_count <= 0:
        raise RequirementError("测试报告显示通过，但已执行测试用例数为 0。")
    declared_kinds = _declared_test_kinds(path)
    if expected_test_kind in {"unit", "service", "both"} and "manual" in declared_kinds:
        raise RequirementError("人工测试报告不能登记为 unit/service/both 自动测试证据。")
    if expected_test_kind == "manual" and "manual" not in declared_kinds:
        raise RequirementError("manual-test 必须登记明确标识为人工测试的报告。")
    if expected_test_kind == "unit" and declared_kinds == {"service"}:
        raise RequirementError("服务测试报告不能登记为 unit-test。")
    if expected_test_kind == "service" and declared_kinds == {"unit"}:
        raise RequirementError("单元测试报告不能登记为 service-test。")
    if expected_result and actual_result != expected_result:
        raise RequirementError(f"测试报告实际结果为 {actual_result}，与登记结果 {expected_result} 不一致。")
    return actual_result


def _canonicalize_test_report(
    root: Path,
    manifest: dict[str, Any],
    path: Path,
    relative: str,
    *,
    test_kind: str,
    result: str,
    acceptance_ids: list[str],
    files: Optional[list[str]] = None,
    project_wide: bool = False,
) -> tuple[Path, str, Optional[str]]:
    """Append an accepted report to the readable summary and retain immutable evidence."""
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        return path, relative, None
    canonical_path = active_requirement_dir(root, str(manifest.get("requirementId") or "")) / "test-report.md"
    if path.resolve() == canonical_path.resolve():
        return path, relative, None
    scope_manifest = {
        **manifest,
        "artifacts": [
            *manifest.get("artifacts", []),
            {
                "type": f"{test_kind}-test" if test_kind != "both" else "service-test",
                "path": canonical_path.relative_to(root).as_posix(),
                "sourcePath": relative,
            },
        ],
    }
    report_snapshot = capture_requirement_scope(root, scope_manifest)
    commit_label = str(report_snapshot.get("gitCommit") or "未知")
    diff_label = str(report_snapshot.get("evidenceDiffHash") or report_snapshot.get("diffHash") or "未知")
    with _RequirementLock(canonical_path.parent, filename=".test-report.lock"):
        evidence_directory = canonical_path.parent / "evidence"
        _assert_safe_internal_path(root, evidence_directory)
        digest = file_sha256(path)
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", path.name).strip("-.") or "report.txt"
        evidence_path = evidence_directory / f"{test_kind}-{digest[:12]}-{safe_name}"
        safe_source = sanitize_text(path.read_text(encoding="utf-8", errors="ignore")).replace("```", "`` `")
        _atomic_write(evidence_path, safe_source.encode("utf-8"))
        evidence_relative = evidence_path.relative_to(root).as_posix()
        if canonical_path.is_file() and canonical_path.stat().st_size > 0:
            body = canonical_path.read_text(encoding="utf-8", errors="ignore").rstrip()
        else:
            body = _test_report_text(manifest).rstrip()
        executed_count = _report_execution_count(path)
        status_label = "通过" if result == "passed" else "失败"
        scope_label = "全项目" if project_wide else ", ".join(f"`{item}`" for item in (files or [])) or "未记录"
        body = re.sub(r"(?m)^- 当前状态：.*$", f"- 当前状态：最近一次登记为{status_label}", body, count=1)
        body += (
            f"\n\n### {now_iso()} · 登记已有 {test_kind} 报告\n\n"
            f"- 结果：{result}\n"
            f"- 已执行测试数：{executed_count}\n"
            f"- 验收标准：{', '.join(acceptance_ids) or '未映射'}\n"
            f"- 覆盖范围：{scope_label}\n"
            f"- Git 提交：`{commit_label}`\n"
            f"- 代码快照：`{diff_label}`\n"
            f"- 来源文件：`{relative}`\n"
            f"- 归档证据：`{evidence_relative}`\n"
        )
        _atomic_write(canonical_path, (body.rstrip() + "\n").encode("utf-8"))
        canonical_relative = canonical_path.relative_to(root).as_posix()
        _validate_test_report_file(
            canonical_path,
            canonical_relative,
            expected_result=result,
            expected_test_kind=test_kind,
        )
    return canonical_path, canonical_relative, evidence_relative


def _validate_closure_file(path: Path, manifest: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    headings = design_documents.parse_headings(lines)
    errors: list[str] = []
    section_bodies: dict[str, str] = {}
    for name in CLOSURE_REQUIRED_SECTIONS:
        heading = design_documents.find_heading(headings, design_documents.normalize_heading(name))
        if heading is None:
            errors.append(f"缺少章节：{name}")
            continue
        body = design_documents.section_text(lines, heading)
        section_bodies[name] = body
        if not design_documents.has_meaningful_content(body):
            errors.append(f"章节为空：{name}")
    if str(manifest.get("requirementId") or "") not in text:
        errors.append("缺少需求号")
    for criterion in manifest.get("acceptanceCriteria", []):
        identifier = str(criterion.get("id") or "")
        if identifier and identifier not in text:
            errors.append(f"缺少验收标准结果：{identifier}")
        elif identifier and not re.search(
            rf"(?im)^\s*[-*]\s*{re.escape(identifier)}\s*[:：].*(?:通过|passed)",
            section_bodies.get("验收标准结果", ""),
        ):
            errors.append(f"验收标准未明确标记通过：{identifier}")
    test_lines = [line for line in section_bodies.get("测试证据", "").splitlines() if line.strip().startswith(("-", "*"))]
    latest_test_line = test_lines[-1] if test_lines else section_bodies.get("测试证据", "")
    if not re.search(r"通过|\bpassed\b", latest_test_line, re.I):
        errors.append("测试证据章节没有通过结论")
    review_lines = [line for line in section_bodies.get("评审结论", "").splitlines() if line.strip().startswith(("-", "*"))]
    latest_review_line = review_lines[-1] if review_lines else section_bodies.get("评审结论", "")
    if not re.search(r"通过|\bpassed\b", latest_review_line, re.I):
        errors.append("评审结论章节没有通过结论")
    for label, pattern in design_documents.PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"存在未收口占位内容：{label}")
    design_documents.check_sensitive_content(text, errors)
    if errors:
        raise RequirementError("收口总结验证失败：" + "；".join(errors))


def _validate_plan_file(path: Path, manifest: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    headings = design_documents.parse_headings(lines)
    sections: dict[str, str] = {}
    errors: list[str] = []
    for name in PLAN_REQUIRED_SECTIONS:
        heading = design_documents.find_heading(headings, design_documents.normalize_heading(name))
        if heading is None:
            errors.append(f"缺少章节：{name}")
            continue
        body = design_documents.section_text(lines, heading)
        sections[name] = body
        if not design_documents.has_meaningful_content(body):
            errors.append(f"章节为空：{name}")
    requirement_id = str(manifest.get("requirementId") or "")
    requirement_name = str(manifest.get("requirementName") or "")
    if requirement_id not in text:
        errors.append("缺少需求号")
    if requirement_name not in text:
        errors.append("缺少需求名称")
    baseline = sections.get("输入基线", "")
    for filename in ("requirement.md", "design.md"):
        if filename not in baseline:
            errors.append(f"输入基线缺少 {filename}")
    mapping = sections.get("测试与验收映射", "")
    for criterion in manifest.get("acceptanceCriteria", []):
        identifier = str(criterion.get("id") or "")
        description = str(criterion.get("description") or "")
        if identifier and identifier not in text:
            errors.append(f"实施计划缺少验收标准：{identifier}")
        if description and description not in text:
            errors.append(f"实施计划中的验收标准描述与 manifest 不一致：{identifier}")
        if identifier and identifier not in mapping:
            errors.append(f"测试映射缺少验收标准：{identifier}")
    if sections.get("实施步骤") and not re.search(r"(?m)^\s*\d+[.)、]", sections["实施步骤"]):
        errors.append("实施步骤必须使用编号列表")
    for token in re.findall(r"`([^`]+)`", sections.get("文件级变更", "")):
        candidate = token.strip().replace("\\", "/")
        if candidate.startswith(("/", "../")) or "/../" in f"/{candidate}":
            errors.append(f"文件级变更包含越界路径：{candidate}")
    for label, pattern in design_documents.PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"存在未完成占位内容：{label}")
    design_documents.check_sensitive_content(text, errors)
    if errors:
        raise RequirementError("实施计划验证失败：" + "；".join(dict.fromkeys(errors)))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def set_acceptance_criteria(
    root: Path,
    requirement_id: str,
    criteria: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in criteria:
        identifier = str(item.get("id") or "").strip().upper()
        description = sanitize_text(" ".join(str(item.get("description") or "").split()))
        if not re.fullmatch(r"AC-\d{2,}", identifier):
            raise RequirementError("验收标准 ID 必须使用 AC-01 形式。")
        if identifier in seen:
            raise RequirementError(f"验收标准 ID 重复：{identifier}")
        if not description:
            raise RequirementError(f"验收标准说明不能为空：{identifier}")
        seen.add(identifier)
        normalized.append({"id": identifier, "description": description, "status": "pending"})
    if not normalized:
        raise RequirementError("至少需要一项验收标准。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"draft", "specified"}:
            raise RequirementError("只有 draft/specified 状态可以设置验收标准；下游需求请先 reopen。")
        manifest["acceptanceCriteria"] = normalized
    return _mutate(root, requirement_id, mutate)


def set_test_contract(
    root: Path,
    requirement_id: str,
    *,
    kind: str,
    report_action: str,
    acceptance_ids: Optional[list[str]] = None,
    report_path: Optional[str] = None,
) -> dict[str, Any]:
    clean_kind = str(kind or "").strip()
    clean_action = str(report_action or "").strip()
    if clean_kind not in TEST_CONTRACT_KINDS:
        raise RequirementError("测试契约类型只能是 unit、service、manual 或 both。")
    if clean_action not in WORKFLOW_ACTIONS:
        raise RequirementError("测试报告动作只能是 generate、register 或 later。")
    if clean_action == "register" and not str(report_path or "").strip():
        raise RequirementError("report-action=register 必须提供 report path。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"draft", "specified", "designed", "documented", "ready"}:
            raise RequirementError("测试契约只能在实现前设置；下游需求请先 reopen。")
        if manifest.get("externalApiImpact", {}).get("value") and clean_kind not in {"service", "both"}:
            raise RequirementError("对外接口需求必须选择 service 或 both 测试契约。")
        known = {str(item.get("id")) for item in manifest.get("acceptanceCriteria", []) if item.get("id")}
        selected = sorted(dict.fromkeys(acceptance_ids or []))
        unknown = sorted(set(selected) - known)
        if unknown:
            raise RequirementError("测试契约引用了未知验收标准：" + ", ".join(unknown))
        if not selected:
            raise RequirementError("测试契约必须显式映射至少一项验收标准。")
        normalized_report_path = None
        if report_path:
            _, normalized_report_path = _resolve_repo_file(root, report_path)
        manifest["testContract"] = {
            "kind": clean_kind,
            "reportAction": clean_action,
            "acceptanceIds": selected,
            "reportPath": normalized_report_path,
            "status": "deferred" if clean_action == "later" else "selected",
            "recordedAt": now_iso(),
            "source": "explicit",
        }
        if clean_action == "later":
            blockers = manifest.setdefault("readiness", {}).setdefault("blockers", [])
            blockers.append({
                "id": f"BLOCK-{len(blockers) + 1:02d}",
                "artifactType": "test",
                "reason": "测试报告动作选择稍后处理。",
                "recordedAt": now_iso(),
                "resolution": None,
                "resolvedAt": None,
            })
        elif manifest.get("readiness"):
            _resolve_blockers(manifest, "test", "测试契约已确认。")

    return _mutate(root, requirement_id, mutate)


def record_diagnosis(
    root: Path,
    requirement_id: str,
    *,
    root_cause: str,
    evidence: list[str],
) -> dict[str, Any]:
    clean_cause = sanitize_text(" ".join(str(root_cause or "").split()))
    if len(clean_cause) < 12:
        raise RequirementError("Bug 根因必须提供至少 12 个有效字符的可验证说明。")
    normalized_evidence: list[dict[str, Any]] = []
    for raw in evidence:
        path_value, separator, symbol = str(raw or "").strip().partition("#")
        path, relative = _resolve_repo_file(root, path_value)
        clean_symbol = sanitize_text(symbol.strip()) if separator else ""
        if clean_symbol:
            symbol_name = clean_symbol.rsplit(".", 1)[-1]
            content = path.read_text(encoding="utf-8", errors="ignore")
            if not re.search(rf"\b{re.escape(symbol_name)}\b", content):
                raise RequirementError(f"根因证据符号不存在：{relative}#{clean_symbol}")
        normalized_evidence.append({
            "path": relative,
            "symbol": clean_symbol or None,
            "sha256": file_sha256(path),
        })
    if not normalized_evidence:
        raise RequirementError("Bug 根因必须至少登记一项仓库内源码证据。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("ticketKind") != "bug":
            raise RequirementError("只有 Bug 需求需要登记 diagnosis。")
        if manifest.get("state") not in {"specified", "designed", "documented"}:
            raise RequirementError("必须先完成 requirement.md，才能登记 Bug 根因。")
        if manifest.get("state") in {"designed", "documented"}:
            for artifact in manifest.get("artifacts", []):
                if artifact.get("type") in {"design", "requirement-design"} and artifact.get("status") != "stale":
                    artifact["status"] = "stale"
                    artifact["invalidatedAt"] = now_iso()
                    artifact["invalidatedReason"] = "Bug 根因在设计文档之后确认，必须据此重新登记设计。"
            _set_state(manifest, "specified")
        manifest["diagnosis"] = {
            "status": "confirmed",
            "rootCause": clean_cause,
            "evidence": normalized_evidence,
            "recordedAt": now_iso(),
        }
        manifest.setdefault("history", []).append({
            "action": "record-diagnosis",
            "rootCause": clean_cause,
            "evidence": normalized_evidence,
            "recordedAt": now_iso(),
        })

    return _mutate(root, requirement_id, mutate)


def _upsert_artifact(
    manifest: dict[str, Any],
    artifact_type: str,
    relative: str,
    digest: str,
    source: str,
    *,
    status: str = "registered",
    test_kind: Optional[str] = None,
    result: Optional[str] = None,
    acceptance_ids: Optional[list[str]] = None,
    document_kind: Optional[str] = None,
    validation: Optional[dict[str, Any]] = None,
    source_path: Optional[str] = None,
    evidence_path: Optional[str] = None,
) -> None:
    record = {
        "type": artifact_type,
        "path": relative,
        "source": source,
        "status": status,
        "sha256": digest,
        "recordedAt": now_iso(),
    }
    if test_kind:
        record["testKind"] = test_kind
    if result:
        record["result"] = result
    if acceptance_ids is not None:
        record["acceptanceIds"] = sorted(dict.fromkeys(acceptance_ids))
    if document_kind:
        record["documentKind"] = document_kind
    if validation is not None:
        record["validation"] = validation
    if source_path and source_path != relative:
        record["sourcePath"] = source_path
    if evidence_path and evidence_path != relative:
        record["evidencePath"] = evidence_path
    artifacts = manifest.setdefault("artifacts", [])
    for index in range(len(artifacts) - 1, -1, -1):
        if artifacts[index].get("type") == artifact_type and artifacts[index].get("path") == relative:
            if not record.get("sourcePath") and artifacts[index].get("sourcePath"):
                record["sourcePath"] = artifacts[index]["sourcePath"]
            if not record.get("evidencePath") and artifacts[index].get("evidencePath"):
                record["evidencePath"] = artifacts[index]["evidencePath"]
            artifacts[index] = record
            return
    artifacts.append(record)


def _test_report_text(manifest: dict[str, Any]) -> str:
    criteria = "\n".join(f"- {item['id']}：计划验证，尚未执行。" for item in manifest.get("acceptanceCriteria", []))
    return f"""# {manifest['requirementName']} · 测试报告

- 需求号：`{manifest['requirementId']}`
- 当前状态：计划中

## 测试计划

{criteria or '- 等需求验收标准登记后补充测试映射。'}

## 执行记录

尚未执行。只有写入实际命令、结果和验收标准映射后，本文档才可作为完成证据。
"""


def _closure_text(root: Path, manifest: dict[str, Any]) -> str:
    covered = set()
    for evidence in manifest.get("testEvidence", []):
        if evidence.get("valid") and evidence.get("result") == "passed":
            covered.update(evidence.get("acceptanceIds", []))
    criteria = "\n".join(
        f"- {item['id']}：{'通过' if item['id'] in covered else '待确认'} — {item['description']}"
        for item in manifest.get("acceptanceCriteria", [])
    )
    snapshot = capture_requirement_scope(root, manifest)
    business_files = "\n".join(
        f"- `{item}`" for item in snapshot.get("evidenceFiles", snapshot.get("files", []))
    )
    delivery_paths = sorted(dict.fromkeys(
        str(item.get("path") or "")
        for item in manifest.get("artifacts", [])
        if item.get("type") in DELIVERY_ARTIFACT_TYPES
        and item.get("status") not in {"stale", "failed"}
        and item.get("path")
    ))
    delivery_files = "\n".join(f"- `{item}`" for item in delivery_paths)
    changed_files = (
        "### 业务源码与测试变更\n\n"
        + (business_files or "- 当前 Git 工作区没有待交付的业务源码变更。")
        + "\n\n### 需求交付文档\n\n"
        + (delivery_files or "- 尚未登记需求交付文档。")
    )
    valid_tests = [item for item in manifest.get("testEvidence", []) if item.get("valid")]
    tests = "\n".join(
        "- {id}：{kind} / {result}；验收标准：{acceptance}；报告：{report}".format(
            id=item.get("id") or "测试证据",
            kind=item.get("testKind") or "unknown",
            result=item.get("result") or "unknown",
            acceptance=", ".join(item.get("acceptanceIds", [])) or "未映射",
            report=item.get("reportPath") or "由命令执行记录提供",
        )
        for item in valid_tests
    )
    valid_reviews = [item for item in manifest.get("reviewRounds", []) if item.get("valid")]
    reviews = "\n".join(
        f"- {item.get('id') or '评审'}：{item.get('result') or 'unknown'} — {sanitize_text(str(item.get('summary') or '未提供摘要'))}"
        for item in valid_reviews
    )
    manual_items = [item for item in valid_tests if item.get("testKind") == "manual" and item.get("manual")]
    manual = "\n".join(
        "- 已批准人工例外：{reason}；证据：`{evidence}`".format(
            reason=sanitize_text(str(item.get("manual", {}).get("reason") or "未记录原因")),
            evidence=str(item.get("manual", {}).get("evidencePath") or "未记录路径"),
        )
        for item in manual_items
    )
    unresolved = [
        str(item.get("reason") or item.get("text") or item.get("id") or "未说明问题")
        for item in manifest.get("readiness", {}).get("blockers", [])
        if not item.get("resolvedAt")
    ]
    unresolved.extend(
        str(finding.get("text") or finding.get("id") or "未说明评审问题")
        for review in valid_reviews
        for finding in review.get("findings", [])
        if finding.get("severity") in BLOCKING_FINDINGS and not finding.get("resolved")
    )
    remaining = "\n".join(f"- {sanitize_text(item)}" for item in unresolved)
    final_state = manifest.get("state") in {"finished", "closed"}
    result_text = (
        "当前需求已通过设计、测试、评审、验收标准和收口门禁。"
        if final_state
        else "当前实现、测试和评审记录已汇总，等待 `project-finish` 对当前 Git 快照执行最终门禁。"
    )
    conclusion = (
        f"需求已进入 `{manifest.get('state')}` 状态；本文件与 manifest 当前证据一致。"
        if final_state
        else "本次变更已按同一需求号关联设计、验收标准、测试和评审；最终是否完成以当前快照的 `project-finish` 结果为准。"
    )
    return f"""# {manifest['requirementName']} · 复盘收口总结

- 需求号：`{manifest['requirementId']}`
- 当前状态：{manifest.get('state')}

## 需求结果

{result_text}

## 变更范围

{changed_files}

## 验收标准结果

{criteria or '- 尚未登记验收标准。'}

## 测试证据

{tests or '- 尚未登记有效测试证据。'}

## 评审结论

{reviews or '- 尚未登记有效评审。'}

## 人工例外

{manual or '- 无人工测试例外。'}

## 遗留问题

{remaining or '- 无已知未解决阻塞项。'}

## 复盘结论

{conclusion}
"""


def _refresh_closure_artifact(root: Path, manifest: dict[str, Any]) -> None:
    closures = [
        item
        for item in manifest.get("artifacts", [])
        if item.get("type") == "closure" and item.get("status") != "stale"
    ]
    if not closures:
        return
    artifact = closures[-1]
    path, relative = _resolve_repo_file(root, str(artifact.get("path") or ""))
    if artifact.get("source") == "generated":
        body = _closure_text(root, manifest)
    else:
        body = path.read_text(encoding="utf-8", errors="ignore")
        status_line = f"- 当前状态：{manifest.get('state')}"
        if re.search(r"(?m)^- 当前状态：.*$", body):
            body = re.sub(r"(?m)^- 当前状态：.*$", status_line, body, count=1)
        else:
            lines = body.splitlines()
            lines.insert(1, "\n" + status_line)
            body = "\n".join(lines)
        body = re.sub(
            r"(?s)\n## 系统收口状态\n.*\Z",
            "",
            body.rstrip(),
        )
        body += (
            "\n\n## 系统收口状态\n\n"
            f"- 状态：{manifest.get('state')}\n"
            f"- 更新时间：{now_iso()}\n"
            "- 结论：当前文档已通过需求级收口门禁。\n"
        )
    _atomic_write(path, (body.rstrip() + "\n").encode("utf-8"))
    artifact["path"] = relative
    artifact["sha256"] = file_sha256(path)
    artifact["status"] = "closed" if manifest.get("state") == "closed" else "finished"
    artifact["updatedAt"] = now_iso()


def _canonical_artifact_type(artifact_type: str) -> str:
    aliases = {
        "requirement-design": "design",
        "test-report": "test",
    }
    return aliases.get(artifact_type, artifact_type)


def _assert_artifact_state(manifest: dict[str, Any], normalized_type: str) -> None:
    state = str(manifest.get("state") or "")
    if state == "closed":
        raise RequirementError("需求已 closed；如需修改产物请先 reopen。")
    allowed = {
        "requirement": {"draft", "specified"},
        "design": {"specified", "designed", "documented"},
        "plan": {"designed", "ready"},
        "unit-test": {"implementing", "verified"},
        "service-test": {"implementing", "verified"},
        "manual-test": {"implementing", "verified"},
        "closure": {"reviewed", "finished"},
    }
    if state in allowed.get(normalized_type, set()):
        return
    messages = {
        "requirement": "需求已进入下游状态；替换 requirement.md 前请先 reopen。",
        "design": "需求已进入下游状态；替换 design.md 前请先 reopen。",
        "plan": "plan.md 只能在设计完成后登记。",
        "unit-test": "测试报告只能在 implementing 或 verified 状态登记。",
        "service-test": "测试报告只能在 implementing 或 verified 状态登记。",
        "manual-test": "测试报告只能在 implementing 或 verified 状态登记。",
        "closure": "只有评审通过后才能登记复盘收口总结。",
    }
    raise RequirementError(messages.get(normalized_type, f"当前状态不能登记 {normalized_type}。"))


def _plan_text(manifest: dict[str, Any]) -> str:
    criteria = "\n".join(
        f"| {item.get('id')} | {item.get('description')} | [待补充测试类型] | [待补充命令或步骤] |"
        for item in manifest.get("acceptanceCriteria", [])
    )
    return f"""# {manifest['requirementId']} {manifest['requirementName']} 实施计划

> 状态：草稿。补全所有 `[待补充]` 内容后，使用 `requirement add --type plan` 重新登记。

## 实施范围

本计划只覆盖 `{manifest['requirementName']}` 在已确认需求与设计中的实现范围；不扩大需求边界。

## 输入基线

- 需求文档：`requirement.md`
- 设计文档：`design.md`
- 需求号：`{manifest['requirementId']}`

## 文件级变更

| 仓库相对路径 | 符号或区域 | 修改目的 | 对应 AC |
| --- | --- | --- | --- |
| `[待补充路径]` | `[待补充符号]` | `[待补充修改目的]` | `[待补充 AC]` |

## 实施步骤

1. [待补充具体代码改动、顺序和依赖。]
2. [待补充测试或验证实现。]
3. [待补充发布、兼容或数据处理动作；不涉及也要说明。]

## 测试与验收映射

| 验收标准 | 说明 | 测试类型 | 命令或人工步骤 |
| --- | --- | --- | --- |
{criteria or '| [待补充 AC] | [待补充说明] | [待补充测试类型] | [待补充命令或步骤] |'}

## 风险与回滚

- 风险：[待补充失败模式、兼容性或影响范围。]
- 观测：[待补充日志、指标或验证入口。]
- 回滚：[待补充可执行的恢复步骤。]
- 证据：验证结果写入同一需求目录的 `test-report.md`；范围漂移时先 reopen。
"""


def generate_artifact(
    root: Path,
    requirement_id: str,
    artifact_type: str,
    *,
    replace: bool = False,
) -> dict[str, Any]:
    normalized_type = _canonical_artifact_type(artifact_type)
    if normalized_type not in {"requirement", "design", "plan", "test", "closure"}:
        raise RequirementError("可生成的产物类型只能是 requirement、design、plan、test 或 closure。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") == "closed":
            raise RequirementError("需求已 closed；如需修改产物请先 reopen。")
        if normalized_type == "requirement" and manifest.get("state") not in {"draft", "specified"}:
            raise RequirementError("需求已进入下游状态；修改需求文档前请先 reopen。")
        if normalized_type == "design" and manifest.get("state") not in {"specified", "designed"}:
            raise RequirementError("必须先完成 requirement.md，才能生成设计文档。")
        if normalized_type == "plan" and manifest.get("state") not in {"designed", "ready"}:
            raise RequirementError("实施计划只能在设计完成后生成。")
        if normalized_type == "test" and manifest.get("state") not in {"implementing", "verified"}:
            raise RequirementError("测试报告只能在 implementing 或 verified 状态生成。")
        if normalized_type == "closure" and manifest.get("state") not in {"reviewed", "finished"}:
            raise RequirementError("只有评审通过后才能生成复盘收口总结。")
        directory = active_requirement_dir(root, requirement_id)
        filename = ARTIFACT_FILES[normalized_type]
        path = directory / filename
        preserve_existing_test = False
        if normalized_type != "test" and path.is_file() and path.stat().st_size > 0 and not replace:
            raise RequirementError(
                f"{filename} 已存在；为避免覆盖用户内容，请登记现有文件，确需重建时显式使用 --replace。"
            )
        if normalized_type in {"requirement", "design"}:
            _assert_document_selection(manifest, normalized_type, "generate")
        if normalized_type == "requirement":
            body = requirement_documents.scaffold_text(
                manifest["requirementId"],
                manifest["requirementName"],
                manifest.get("ticketKind", "requirement"),
            )
        elif normalized_type == "design":
            body = design_documents.scaffold_text(
                manifest["requirementId"],
                manifest["requirementName"],
                manifest.get("ticketKind", "requirement"),
            )
        elif normalized_type == "plan":
            body = _plan_text(manifest)
        elif normalized_type == "test":
            body = _test_report_text(manifest)
        else:
            body = _closure_text(root, manifest)
        if normalized_type == "test":
            with _RequirementLock(directory, filename=".test-report.lock"):
                preserve_existing_test = path.is_file() and path.stat().st_size > 0
                if not preserve_existing_test:
                    _atomic_write(path, body.encode("utf-8"))
        else:
            _atomic_write(path, body.encode("utf-8"))
        relative = path.relative_to(root).as_posix()
        if preserve_existing_test and any(
            item.get("type") == "test"
            and item.get("path") == relative
            and item.get("status") in {"executed", "observed", "failed", "passed"}
            for item in manifest.get("artifacts", [])
        ):
            _resolve_blockers(manifest, "test", "保留已有测试报告和执行状态。")
            return
        artifact_status = "draft" if normalized_type in {"requirement", "design", "plan", "test"} else "registered"
        _upsert_artifact(
            manifest,
            normalized_type,
            relative,
            file_sha256(path),
            "generated",
            status=artifact_status,
            document_kind=manifest.get("ticketKind", "requirement") if normalized_type in {"requirement", "design"} else None,
            validation={
                "ok": False,
                "scaffold": True,
                "errors": [f"{normalized_type} 脚手架必须补全并重新登记。"],
            }
            if normalized_type in {"requirement", "design", "plan"} else None,
        )
        if normalized_type == "requirement":
            _set_state(manifest, "draft")
        elif normalized_type == "design":
            _set_state(manifest, "specified")
        elif normalized_type == "closure":
            _resolve_blockers(manifest, "closure", "复盘收口总结已生成。")
        if normalized_type in {"requirement", "design"}:
            _mark_document_selection(
                manifest,
                normalized_type,
                default_action="generate",
                status="generated",
                artifact_path=relative,
            )

    return _mutate(root, requirement_id, mutate)


def _validate_delivery_document(
    root: Path,
    manifest: dict[str, Any],
    normalized_type: str,
    path: Path,
    relative: str,
) -> dict[str, Any]:
    if normalized_type == "requirement":
        validation = requirement_documents.validate(
            path.read_text(encoding="utf-8", errors="ignore"),
            kind=manifest.get("ticketKind", "requirement"),
            expected_id=str(manifest.get("requirementId") or ""),
            expected_name=str(manifest.get("requirementName") or ""),
            acceptance_ids=[
                str(item.get("id")) for item in manifest.get("acceptanceCriteria", []) if item.get("id")
            ],
            acceptance_criteria=list(manifest.get("acceptanceCriteria") or []),
            expected_external_api=(
                bool(manifest.get("externalApiImpact", {}).get("value"))
                if manifest.get("externalApiImpact", {}).get("confirmed")
                else None
            ),
        )
        if not validation.get("ok"):
            raise RequirementError("需求文档验证失败：" + "；".join(validation.get("errors", [])))
        return validation
    if normalized_type == "design":
        if manifest.get("schemaVersion") == SCHEMA_VERSION and not _has_valid_requirement(root, manifest):
            raise RequirementError("必须先登记当前有效的 requirement.md，才能登记设计文档。")
        validation = design_documents.validate(
            path.read_text(encoding="utf-8", errors="ignore"),
            root,
            relative,
            manifest.get("ticketKind", "requirement"),
            expected_id=manifest.get("requirementId"),
            expected_name=manifest.get("requirementName"),
        )
        if not validation.get("ok"):
            raise RequirementError("设计文档验证失败：" + "；".join(validation.get("errors", [])))
        return validation
    if normalized_type == "plan":
        _validate_plan_file(path, manifest)
        return {"ok": True, "validatedAt": now_iso(), "schema": "plan-v1"}
    if normalized_type == "closure":
        _validate_closure_file(path, manifest)
        return {"ok": True, "validatedAt": now_iso(), "schema": "closure-v1"}
    raise RequirementError(f"不支持的交付文档类型：{normalized_type}")


def _register_delivery_document(
    root: Path,
    requirement_id: str,
    normalized_type: str,
    source_relative: str,
) -> dict[str, Any]:
    manifest_file = active_manifest_path(root, requirement_id)
    directory = manifest_file.parent
    with _RequirementLock(directory):
        locked_manifest_file = active_manifest_path(root, requirement_id)
        if locked_manifest_file != manifest_file:
            raise RequirementError("需求档案目录在登记期间发生变化，请重试。")
        manifest = load_requirement(root, requirement_id)
        _assert_artifact_state(manifest, normalized_type)
        source_path, registered_from = _resolve_repo_file(root, source_relative)
        if normalized_type in {"requirement", "design"}:
            _assert_document_selection(
                manifest,
                normalized_type,
                "register",
                source_path=registered_from,
            )
        source_before_validation = source_path.read_bytes()
        validation = _validate_delivery_document(
            root,
            manifest,
            normalized_type,
            source_path,
            registered_from,
        )
        source_bytes = source_path.read_bytes()
        if source_before_validation != source_bytes:
            raise RequirementError("交付文档在验证期间发生变化，请重新检查后登记。")
        canonical_path = directory / ARTIFACT_FILES[normalized_type]
        canonical_relative = canonical_path.relative_to(root).as_posix()
        copy_required = source_path.resolve() != canonical_path.resolve()
        canonical_existed = canonical_path.is_file()
        canonical_backup = canonical_path.read_bytes() if canonical_existed else b""
        try:
            if copy_required:
                _atomic_write(canonical_path, source_bytes)
            digest = hashlib.sha256(source_bytes).hexdigest()
            _upsert_artifact(
                manifest,
                normalized_type,
                canonical_relative,
                digest,
                "registered",
                document_kind=(
                    manifest.get("ticketKind", "requirement")
                    if normalized_type in {"requirement", "design"}
                    else None
                ),
                validation=validation,
                source_path=registered_from,
            )
            if normalized_type == "requirement":
                _set_state(manifest, "specified")
                _resolve_blockers(manifest, "requirement", "已登记需求文档。")
            elif normalized_type == "design":
                _set_state(manifest, "designed")
                _resolve_blockers(manifest, "design", "已登记开发设计文档。")
                _resolve_blockers(manifest, "requirement-design", "已登记开发设计文档。")
            elif normalized_type == "closure":
                _resolve_blockers(manifest, "closure", "已登记复盘收口总结。")
            if normalized_type in {"requirement", "design"}:
                _mark_document_selection(
                    manifest,
                    normalized_type,
                    default_action="register",
                    status="completed",
                    artifact_path=canonical_relative,
                    source_path=registered_from,
                )
            manifest["revision"] = int(manifest.get("revision", 0)) + 1
            manifest["updatedAt"] = now_iso()
            _write_manifest(manifest_file, manifest)
        except Exception:
            if copy_required:
                if canonical_existed:
                    _atomic_write(canonical_path, canonical_backup)
                else:
                    try:
                        canonical_path.unlink()
                    except FileNotFoundError:
                        pass
            raise
    return manifest


def register_artifact(
    root: Path,
    requirement_id: str,
    artifact_type: str,
    path_value: str,
    *,
    result: Optional[str] = None,
    acceptance_ids: Optional[list[str]] = None,
    files: Optional[list[str]] = None,
    project_wide: bool = False,
    manual: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    normalized_type = _canonical_artifact_type(artifact_type)
    if normalized_type not in {"requirement", "design", "plan", "unit-test", "service-test", "manual-test", "closure"}:
        raise RequirementError("不支持的产物类型。")
    path, relative = _resolve_repo_file(root, path_value)
    registered_from = relative
    archived_evidence_path: Optional[str] = None
    allowed_suffixes = ARTIFACT_SUFFIXES.get(normalized_type, set())
    if path.suffix.lower() not in allowed_suffixes:
        raise RequirementError(f"{normalized_type} 产物不接受源码文件或未知格式：{relative}")
    if normalized_type in {"requirement", "design", "plan", "closure"}:
        return _register_delivery_document(root, requirement_id, normalized_type, relative)
    test_kind = normalized_type.removesuffix("-test") if normalized_type.endswith("-test") else None
    if normalized_type.endswith("-test") and result not in {"passed", "failed"}:
        raise RequirementError("测试产物必须通过 --result 登记 passed 或 failed。")
    acceptance_ids = acceptance_ids or []
    files = files or []
    current = load_requirement(root, requirement_id)
    _assert_artifact_state(current, normalized_type)
    if test_kind:
        normalized_files = _normalize_scope_files(root, files)
        _validate_test_report_file(
            path,
            relative,
            expected_result=result,
            expected_test_kind=test_kind,
        )
        if relative in normalized_files:
            raise RequirementError("测试报告路径不能同时作为被测试的业务文件范围。")
        known = {item.get("id") for item in current.get("acceptanceCriteria", [])}
        unknown = sorted(set(acceptance_ids) - known)
        if unknown:
            raise RequirementError("测试证据引用了未知验收标准：" + ", ".join(unknown))
        if not project_wide and not normalized_files:
            raise RequirementError("登记测试报告必须提供 --files，或显式使用 --project-wide。")
        if test_kind == "manual":
            if not _manual_valid(manual):
                raise RequirementError("人工测试必须包含审批、类别、原因、步骤、输入、观察结果和截图/日志路径。")
            _resolve_repo_file(root, str((manual or {}).get("evidencePath") or ""))
        path, relative, archived_evidence_path = _canonicalize_test_report(
            root,
            current,
            path,
            relative,
            test_kind=test_kind,
            result=str(result),
            acceptance_ids=acceptance_ids,
            files=normalized_files,
            project_wide=project_wide,
        )

    def mutate(manifest: dict[str, Any]) -> None:
        _assert_artifact_state(manifest, normalized_type)
        _upsert_artifact(
            manifest,
            normalized_type,
            relative,
            file_sha256(path),
            "registered",
            test_kind=test_kind,
            result=result,
            acceptance_ids=acceptance_ids,
            source_path=registered_from,
            evidence_path=archived_evidence_path,
        )
        if normalized_type.endswith("-test"):
            _resolve_blockers(manifest, "test", "已登记并验证测试报告。")

    manifest = _mutate(root, requirement_id, mutate)
    if test_kind:
        snapshot = capture_requirement_scope(root, manifest)
        manifest = record_test_result(
            root,
            requirement_id,
            test_kind=test_kind,
            result=str(result),
            acceptance_ids=acceptance_ids or [],
            files=files,
            snapshot=snapshot,
            report_path=relative,
            report_source_path=archived_evidence_path,
            report_original_path=registered_from,
            manual=manual,
            project_wide=project_wide,
        )
    return manifest


def _resolve_blockers(manifest: dict[str, Any], artifact_type: str, resolution: str) -> None:
    for blocker in manifest.setdefault("readiness", {}).setdefault("blockers", []):
        if blocker.get("artifactType") == artifact_type and not blocker.get("resolvedAt"):
            blocker["resolution"] = resolution
            blocker["resolvedAt"] = now_iso()


def record_later(root: Path, requirement_id: str, artifact_type: str) -> dict[str, Any]:
    normalized_type = _canonical_artifact_type(artifact_type)
    if normalized_type not in {"requirement", "design", "test", "closure"}:
        raise RequirementError("later 只支持 requirement、design、test 或 closure。")

    def mutate(manifest: dict[str, Any]) -> None:
        allowed = {
            "requirement": {"draft", "specified"},
            "design": {"draft", "specified", "designed", "documented"},
            "test": {"implementing", "verified"},
            "closure": {"reviewed"},
        }
        if manifest.get("state") not in allowed[normalized_type]:
            raise RequirementError(f"当前状态不能将 {normalized_type} 记录为稍后处理。")
        if normalized_type in {"requirement", "design"}:
            selection = manifest.get("workflowSelections", {}).get(normalized_type)
            if isinstance(selection, dict) and selection.get("action") != "later":
                raise RequirementError(
                    f"{normalized_type} 已选择 {selection.get('action')}；如需改为 later，请先使用 requirement amend。"
                )
        blockers = manifest.setdefault("readiness", {}).setdefault("blockers", [])
        blockers.append({
            "id": f"BLOCK-{len(blockers) + 1:02d}",
            "artifactType": normalized_type,
            "reason": f"{normalized_type} 选择稍后处理。",
            "recordedAt": now_iso(),
            "resolution": None,
            "resolvedAt": None,
        })
        if normalized_type in {"requirement", "design"}:
            _mark_document_selection(
                manifest,
                normalized_type,
                default_action="later",
                status="deferred",
            )

    return _mutate(root, requirement_id, mutate)


def _assert_readiness_inputs(root: Path, manifest: dict[str, Any]) -> None:
    if not manifest.get("acceptanceCriteria"):
        raise RequirementError("需求 manifest 缺少编号验收标准。")
    if manifest.get("schemaVersion") == SCHEMA_VERSION and not _has_valid_requirement(root, manifest):
        raise RequirementError("缺少当前有效且验证通过的需求文档。")
    if not _has_valid_design(root, manifest):
        raise RequirementError("缺少当前有效且验证通过的设计文档。")
    plan_status = plan_validation_status(root, manifest)
    if plan_status.get("present") and not plan_status.get("ok"):
        raise RequirementError("已选择生成实施计划，但 plan.md 尚未有效登记：" + "；".join(plan_status.get("errors", [])))
    if manifest.get("ticketKind") == "bug":
        diagnosis = manifest.get("diagnosis") if isinstance(manifest.get("diagnosis"), dict) else {}
        if diagnosis.get("status") != "confirmed" or not diagnosis.get("rootCause") or not diagnosis.get("evidence"):
            raise RequirementError("Bug 必须先通过 project-debug 确认根因并登记 diagnosis。")
    contract = manifest.get("testContract") if isinstance(manifest.get("testContract"), dict) else None
    if manifest.get("schemaVersion") == SCHEMA_VERSION:
        if not contract:
            raise RequirementError("缺少实现前测试契约；请先运行 requirement test-contract set。")
        if contract.get("status") in {"pending", "deferred"} or contract.get("source") != "explicit":
            raise RequirementError("测试报告选择稍后处理，不能进入 ready。")
        if not contract.get("acceptanceIds"):
            raise RequirementError("测试契约必须显式映射验收标准。")
        if manifest.get("externalApiImpact", {}).get("value") and contract.get("kind") not in {"service", "both"}:
            raise RequirementError("对外接口需求必须选择 service 或 both 测试契约。")
    unresolved = [blocker for blocker in manifest.get("readiness", {}).get("blockers", []) if not blocker.get("resolvedAt")]
    if unresolved:
        raise RequirementError("仍有未解决的 readiness 阻塞项：" + ", ".join(str(item.get("id")) for item in unresolved))


def ready_requirement(root: Path, requirement_id: str, resolution: str) -> dict[str, Any]:
    clean_resolution = sanitize_text(" ".join(str(resolution or "").split()))
    if not clean_resolution:
        raise RequirementError("进入 ready 必须记录非空的确认或阻塞解决说明。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"designed", "documented"}:
            raise RequirementError("只有需求文档和设计文档均完成的 designed 状态可以进入 ready。")
        _assert_readiness_inputs(root, manifest)
        manifest.setdefault("readiness", {}).setdefault("resolutions", []).append({
            "resolution": clean_resolution,
            "recordedAt": now_iso(),
        })
        _set_state(manifest, "ready")

    return _mutate(root, requirement_id, mutate)


def begin_requirement(root: Path, requirement_id: str) -> dict[str, Any]:
    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") != "ready":
            raise RequirementError("需求必须先通过 ready 门禁才能开始实现。")
        _assert_readiness_inputs(root, manifest)
        if not manifest.get("externalApiImpact", {}).get("confirmed"):
            raise RequirementError("开始实现前必须明确确认是否影响对外接口。")
        _set_state(manifest, "implementing")

    return _mutate(root, requirement_id, mutate)


def _git(root: Path, args: list[str]) -> tuple[int, bytes]:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False
        )
    except OSError:
        return 127, b""
    return completed.returncode, completed.stdout


def _business_path(path: str) -> bool:
    clean = path.strip().replace("\\", "/")
    return bool(clean) and not clean.startswith(".project-intel/") and not clean.startswith(".git/")


def _committed_scope_entries(
    root: Path,
    baseline_commit: Optional[str],
    current_commit: Optional[str],
    excluded: set[str],
) -> tuple[bool, list[dict[str, Any]]]:
    baseline = str(baseline_commit or "").strip()
    current = str(current_commit or "").strip()
    if not baseline or not current or baseline == current:
        return True, []
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", baseline) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", current):
        return False, []
    code, raw = _git(root, ["diff", "--name-status", "-z", "--find-renames", baseline, current, "--"])
    if code != 0:
        return False, []
    tokens = raw.decode("utf-8", errors="replace").split("\0")
    entries: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if not status:
            continue
        kind = status[:1]
        if kind in {"R", "C"}:
            if index + 1 >= len(tokens):
                return False, []
            old_path, new_path = tokens[index], tokens[index + 1]
            index += 2
            candidates = [(new_path, status)]
            if kind == "R":
                candidates.insert(0, (old_path, "D"))
        else:
            if index >= len(tokens):
                return False, []
            candidates = [(tokens[index], status)]
            index += 1
        for item, item_status in candidates:
            normalized = item.replace("\\", "/")
            if not _business_path(normalized) or normalized in excluded:
                continue
            candidate = root / item
            digest = file_sha256(candidate) if candidate.is_file() else "<deleted>"
            entries.append({"status": item_status, "path": item, "sha256": digest})
    return True, entries


def capture_scope_snapshot(
    root: Path,
    exclude_paths: Optional[list[str]] = None,
    *,
    baseline_commit: Optional[str] = None,
) -> dict[str, Any]:
    excluded = {str(item).replace("\\", "/") for item in (exclude_paths or [])}
    code, raw = _git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    entries: list[dict[str, Any]] = []
    commit_code, commit_raw = _git(root, ["rev-parse", "HEAD"])
    commit = commit_raw.decode("utf-8", errors="ignore").strip() if commit_code == 0 else None
    if code == 0:
        tokens = raw.decode("utf-8", errors="replace").split("\0")
        index = 0
        while index < len(tokens):
            token = tokens[index]
            index += 1
            if not token:
                continue
            status = token[:2]
            path = token[3:] if len(token) > 3 else ""
            paths = [path]
            if ("R" in status or "C" in status) and index < len(tokens) and tokens[index]:
                paths.append(tokens[index])
                index += 1
            for item in paths:
                if not _business_path(item) or item.replace("\\", "/") in excluded:
                    continue
                candidate = root / item
                digest = file_sha256(candidate) if candidate.is_file() else "<deleted>"
                entries.append({"status": status, "path": item, "sha256": digest})
    committed_ok, committed_entries = _committed_scope_entries(root, baseline_commit, commit, excluded)
    by_path = {str(item.get("path") or ""): item for item in committed_entries}
    for item in entries:
        by_path[str(item.get("path") or "")] = item
    entries = sorted(by_path.values(), key=lambda item: (item["path"], item["status"]))
    if code != 0 or commit_code != 0 or not committed_ok:
        return {
            "capturedAt": now_iso(),
            "gitAvailable": False,
            "gitCommit": None,
            "diffHash": None,
            "files": [],
            "entries": [],
        }
    encoded = json.dumps({"commit": commit, "entries": entries}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "capturedAt": now_iso(),
        "gitAvailable": True,
        "gitCommit": commit,
        "diffHash": hashlib.sha256(encoded).hexdigest(),
        "files": sorted(dict.fromkeys(item["path"] for item in entries)),
        "entries": entries,
    }


def capture_requirement_scope(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    snapshot = capture_scope_snapshot(root, baseline_commit=manifest.get("baselineCommit"))
    baseline_scope = manifest.get("baselineScope") if isinstance(manifest.get("baselineScope"), dict) else {}
    baseline_signatures = {
        (
            str(item.get("path") or "").replace("\\", "/"),
            str(item.get("sha256") or ""),
        )
        for item in baseline_scope.get("entries", [])
        if isinstance(item, dict)
    }
    delta_entries = [
        item
        for item in snapshot.get("entries", [])
        if (
            str(item.get("path") or "").replace("\\", "/"),
            str(item.get("sha256") or ""),
        ) not in baseline_signatures
    ]
    snapshot["baselineFiles"] = sorted({item[0] for item in baseline_signatures if item[0]})
    snapshot["entries"] = delta_entries
    snapshot["files"] = sorted({str(item.get("path") or "") for item in delta_entries if item.get("path")})
    artifact_paths: set[str] = set()
    requirement_prefix = active_requirement_dir(root, str(manifest.get("requirementId") or "")).relative_to(root).as_posix().rstrip("/") + "/"
    for item in manifest.get("artifacts", []):
        if item.get("type") not in DELIVERY_ARTIFACT_TYPES:
            continue
        artifact_type = str(item.get("type") or "")
        for key in ("path", "sourcePath"):
            value = str(item.get(key) or "").replace("\\", "/")
            if (
                value
                and (value.startswith(requirement_prefix) or _delivery_document_artifact_path_valid(value, artifact_type))
                and Path(value).suffix.lower() in DELIVERY_ARTIFACT_SUFFIXES
            ):
                artifact_paths.add(value)
        if item.get("type") == "manual-evidence":
            for key in ("path", "sourcePath"):
                manual_value = str(item.get(key) or "").replace("\\", "/")
                if manual_value and _manual_evidence_path_valid(manual_value):
                    artifact_paths.add(manual_value)
        if item.get("type") in {"test", "unit-test", "service-test", "manual-test"}:
            for key in ("path", "sourcePath", "evidencePath"):
                report_value = str(item.get(key) or "").replace("\\", "/")
                if report_value and _external_report_artifact_path_valid(report_value):
                    artifact_paths.add(report_value)
    for evidence in manifest.get("testEvidence", []):
        original_report = str(evidence.get("reportOriginalPath") or "").replace("\\", "/")
        if original_report and _external_report_artifact_path_valid(original_report):
            artifact_paths.add(original_report)
    changed = set(snapshot.get("files", []))
    snapshot["artifactFiles"] = sorted(changed & artifact_paths)
    snapshot["evidenceFiles"] = sorted(changed - artifact_paths)
    evidence_entries = [
        item for item in snapshot.get("entries", [])
        if str(item.get("path") or "").replace("\\", "/") not in artifact_paths
    ]
    snapshot["evidenceEntries"] = evidence_entries
    if snapshot.get("gitAvailable"):
        encoded = json.dumps(
            {"commit": snapshot.get("gitCommit"), "entries": evidence_entries},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        snapshot["evidenceDiffHash"] = hashlib.sha256(encoded).hexdigest()
    else:
        snapshot["evidenceDiffHash"] = None
    return snapshot


def _scope_identity(snapshot: dict[str, Any]) -> tuple[Any, Any]:
    return (
        snapshot.get("evidenceDiffHash") or snapshot.get("diffHash"),
        snapshot.get("gitCommit"),
    )


def _require_same_scope(expected: dict[str, Any], actual: dict[str, Any], operation: str) -> None:
    if not actual.get("gitAvailable") or not (actual.get("evidenceDiffHash") or actual.get("diffHash")):
        raise RequirementError(f"无法读取 Git 状态，不能{operation}。")
    if _scope_identity(expected) != _scope_identity(actual):
        raise RequirementError(f"{operation}期间代码或 Git 提交发生变化；旧快照已拒绝，请重新执行。")


def _normalize_scope_files(root: Path, files: list[str]) -> list[str]:
    normalized: list[str] = []
    root_resolved = root.resolve()
    for value in files:
        raw = str(value or "").strip()
        if not raw:
            continue
        candidate = Path(raw)
        path = candidate if candidate.is_absolute() else root / candidate
        try:
            relative = path.resolve(strict=False).relative_to(root_resolved).as_posix()
        except ValueError as exc:
            raise RequirementError(f"文件范围越出项目目录：{raw}") from exc
        if _business_path(relative):
            normalized.append(relative)
    return sorted(dict.fromkeys(normalized))


def validate_scope_selection(root: Path, files: list[str], snapshot: Optional[dict[str, Any]] = None) -> list[str]:
    current = snapshot or capture_scope_snapshot(root)
    if not current.get("gitAvailable") or not current.get("diffHash"):
        raise RequirementError("无法读取 Git 状态，不能生成可追踪的需求证据。")
    selected = _normalize_scope_files(root, files)
    actual = set(current.get("evidenceFiles", current.get("files", [])))
    missing = sorted(actual - set(selected))
    if missing:
        raise RequirementError("提交的文件范围遗漏实际 Git 变更：" + ", ".join(missing))
    return selected or sorted(actual)


def _manual_valid(manual: Optional[dict[str, Any]]) -> bool:
    if not isinstance(manual, dict) or manual.get("approved") is not True:
        return False
    if manual.get("category") not in MANUAL_CATEGORIES:
        return False
    for key in MANUAL_REQUIRED_FIELDS[1:]:
        if not str(manual.get(key) or "").strip():
            return False
    reason = sanitize_text(str(manual.get("reason") or "")).strip()
    steps = sanitize_text(str(manual.get("steps") or "")).strip()
    observation = sanitize_text(str(manual.get("observation") or "")).strip()
    combined = reason + steps + sanitize_text(str(manual.get("input") or "")).strip() + observation
    if len(reason) < 8 or len(steps) < 8 or len(observation) < 8 or len(combined) < 32:
        return False
    if not _manual_evidence_path_valid(str(manual.get("evidencePath") or "")):
        return False
    return True


def _manual_evidence_path_valid(relative: str) -> bool:
    path = Path(str(relative or "").replace("\\", "/"))
    parts = {part.lower().replace("_", "-") for part in path.parts[:-1]}
    return bool(parts & MANUAL_EVIDENCE_PATH_MARKERS) and path.suffix.lower() in DELIVERY_ARTIFACT_SUFFIXES


def _current_test_evidence(
    manifest: dict[str, Any],
    evidence_hash: Optional[str] = None,
) -> list[dict[str, Any]]:
    return [
        item
        for item in manifest.get("testEvidence", [])
        if item.get("valid")
        and (
            not evidence_hash
            or (item.get("evidenceDiffHash") or item.get("diffHash")) == evidence_hash
        )
    ]


def _test_channels(test_kind: Any) -> tuple[str, ...]:
    kind = str(test_kind or "")
    if kind == "both":
        return ("unit", "service")
    return (kind,) if kind in {"unit", "service", "manual"} else ()


def _test_gate_for_records(manifest: dict[str, Any], records: list[dict[str, Any]]) -> bool:
    if not records:
        return False
    latest_by_channel: dict[str, dict[str, Any]] = {}
    for item in records:
        for channel in _test_channels(item.get("testKind")):
            latest_by_channel[channel] = item
    if not latest_by_channel or any(
        item.get("result") not in PASSING_RESULTS
        for item in latest_by_channel.values()
    ):
        return False
    contract = manifest.get("testContract") if isinstance(manifest.get("testContract"), dict) else None
    if not contract or contract.get("source") != "explicit" or contract.get("status") != "selected":
        return False
    required = set(_test_channels(contract.get("kind")))
    if not required or not required.issubset(set(latest_by_channel)):
        return False
    contract_acceptance = set(contract.get("acceptanceIds") or [])
    covered: set[str] = set()
    for item in latest_by_channel.values():
        covered.update(str(value) for value in item.get("acceptanceIds", []))
    if not contract_acceptance or not contract_acceptance.issubset(covered):
        return False
    if manifest.get("externalApiImpact", {}).get("value"):
        return "service" in latest_by_channel
    return any(
        channel in {"unit", "service"}
        or (channel == "manual" and _manual_valid(item.get("manual")))
        for channel, item in latest_by_channel.items()
    )


def _test_gate_satisfied(manifest: dict[str, Any], evidence_hash: Optional[str] = None) -> bool:
    return _test_gate_for_records(manifest, _current_test_evidence(manifest, evidence_hash))


def record_test_result(
    root: Path,
    requirement_id: str,
    *,
    test_kind: str,
    result: str,
    acceptance_ids: list[str],
    files: list[str],
    snapshot: Optional[dict[str, Any]] = None,
    command: str = "",
    report_path: Optional[str] = None,
    report_source_path: Optional[str] = None,
    report_original_path: Optional[str] = None,
    manual: Optional[dict[str, Any]] = None,
    project_wide: bool = False,
) -> dict[str, Any]:
    if test_kind not in TEST_KINDS:
        raise RequirementError("test-kind 只能是 unit、service 或 manual；both 只能用于测试契约。")
    if result not in {"passed", "failed"}:
        raise RequirementError("测试结果只能是 passed 或 failed。")
    if test_kind == "manual" and not _manual_valid(manual):
        raise RequirementError("人工测试必须包含审批、原因、步骤、输入、观察结果和截图/日志路径。")
    manual_evidence_relative: Optional[str] = None
    if test_kind == "manual" and manual is not None:
        _, evidence_relative = _resolve_repo_file(root, str(manual.get("evidencePath") or ""))
        manual_evidence_relative = evidence_relative
        manual = {
            key: value if key == "approved" else evidence_relative if key == "evidencePath" else sanitize_text(str(value or ""))
            for key, value in manual.items()
        }
    current_manifest = load_requirement(root, requirement_id)
    contract = current_manifest.get("testContract") if isinstance(current_manifest.get("testContract"), dict) else None
    if not contract or contract.get("source") != "explicit" or contract.get("status") != "selected":
        raise RequirementError("测试契约尚未显式确认，不能登记需求级测试证据。")
    if not acceptance_ids:
        raise RequirementError("需求级通过测试必须显式传入 --acceptance 映射。")
    if test_kind not in _test_channels(contract.get("kind")):
        raise RequirementError("测试证据类型与已确认的测试契约不一致。")
    selected = _normalize_scope_files(root, files)
    if report_path:
        report_file, normalized_report_path = _resolve_repo_file(root, report_path)
        report_original_path = report_original_path or normalized_report_path
        validation_file = report_file
        validation_relative = normalized_report_path
        if report_source_path:
            validation_file, validation_relative = _resolve_repo_file(root, report_source_path)
        _validate_test_report_file(
            validation_file,
            validation_relative,
            expected_result=result,
            expected_test_kind=test_kind,
        )
        if normalized_report_path in selected:
            raise RequirementError("测试报告路径不能同时作为被测试的业务文件范围。")
        if not report_source_path:
            report_file, normalized_report_path, report_source_path = _canonicalize_test_report(
                root,
                current_manifest,
                report_file,
                normalized_report_path,
                test_kind=test_kind,
                result=result,
                acceptance_ids=acceptance_ids,
                files=selected,
                project_wide=project_wide,
            )
        report_path = normalized_report_path
    scope_manifest = current_manifest
    if report_path or manual_evidence_relative:
        extra_artifacts: list[dict[str, Any]] = []
        if report_path:
            extra_artifacts.append({
                "type": f"{test_kind}-test" if test_kind != "both" else "service-test",
                "path": report_path,
                "sourcePath": report_original_path,
                "evidencePath": report_source_path,
            })
        if manual_evidence_relative:
            extra_artifacts.append({
                "type": "manual-evidence",
                "path": manual_evidence_relative,
            })
        scope_manifest = {
            **current_manifest,
            "artifacts": [
                *current_manifest.get("artifacts", []),
                *extra_artifacts,
            ],
        }
    current_snapshot = capture_requirement_scope(root, scope_manifest)
    if not current_snapshot.get("gitAvailable") or not current_snapshot.get("diffHash"):
        raise RequirementError("无法读取 Git 状态，不能登记需求级测试证据。")
    if snapshot is not None:
        _require_same_scope(snapshot, current_snapshot, "登记测试证据")
    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"implementing", "verified"}:
            raise RequirementError("只有 implementing 或 verified 状态可以登记测试结果。")
        locked_scope_manifest = manifest
        if report_path or manual_evidence_relative:
            locked_scope_manifest = {
                **manifest,
                "artifacts": [
                    *manifest.get("artifacts", []),
                    *extra_artifacts,
                ],
            }
        locked_snapshot = capture_requirement_scope(root, locked_scope_manifest)
        _require_same_scope(current_snapshot, locked_snapshot, "登记测试证据")
        known = {item.get("id") for item in manifest.get("acceptanceCriteria", [])}
        unknown = sorted(set(acceptance_ids) - known)
        if unknown:
            raise RequirementError("测试证据引用了未知验收标准：" + ", ".join(unknown))
        record = {
            "id": f"TEST-{len(manifest.get('testEvidence', [])) + 1:02d}",
            "testKind": test_kind,
            "result": result,
            "acceptanceIds": sorted(dict.fromkeys(acceptance_ids)),
            "files": selected,
            "projectWide": bool(project_wide),
            "command": sanitize_text(command),
            "reportPath": report_path,
            "diffHash": locked_snapshot.get("diffHash"),
            "evidenceDiffHash": locked_snapshot.get("evidenceDiffHash") or locked_snapshot.get("diffHash"),
            "gitCommit": locked_snapshot.get("gitCommit"),
            "evidenceCommit": locked_snapshot.get("gitCommit"),
            "recordedAt": now_iso(),
            "valid": True,
        }
        if report_source_path:
            source_file, source_relative = _resolve_repo_file(root, report_source_path)
            record["reportSourcePath"] = source_relative
            record["reportSha256"] = file_sha256(source_file)
        if report_original_path:
            _, original_relative = _resolve_repo_file(root, report_original_path)
            record["reportOriginalPath"] = original_relative
        if manual:
            record["manual"] = manual
            evidence_path, evidence_relative = _resolve_repo_file(root, str(manual.get("evidencePath") or ""))
            _upsert_artifact(
                manifest,
                "manual-evidence",
                evidence_relative,
                file_sha256(evidence_path),
                "registered",
                status="passed" if result == "passed" else "failed",
                test_kind="manual",
                result=result,
                acceptance_ids=acceptance_ids,
            )
        manifest.setdefault("testEvidence", []).append(record)
        manifest.setdefault("scopeSnapshots", []).append({"kind": "test", **locked_snapshot})
        manifest["currentDiffHash"] = locked_snapshot.get("diffHash")
        if report_path:
            path, relative = _resolve_repo_file(root, report_path)
            artifact_type = f"{test_kind}-test" if test_kind != "both" else "service-test"
            already_registered = next(
                (
                    item
                    for item in reversed(manifest.get("artifacts", []))
                    if item.get("type") == artifact_type
                    and item.get("path") == relative
                    and report_source_path
                    and item.get("evidencePath") == report_source_path
                ),
                None,
            )
            if already_registered is None:
                _upsert_artifact(
                    manifest,
                    artifact_type,
                    relative,
                    file_sha256(path),
                    "registered",
                    test_kind=test_kind,
                    result=result,
                    acceptance_ids=acceptance_ids,
                    source_path=report_original_path,
                    evidence_path=report_source_path,
                )
        _resolve_blockers(manifest, "test", "测试报告和通过证据已登记。")
        if result == "failed":
            _set_state(manifest, "implementing")
        elif _test_gate_satisfied(
            manifest,
            locked_snapshot.get("evidenceDiffHash") or locked_snapshot.get("diffHash"),
        ):
            _set_state(manifest, "verified")
        else:
            _set_state(manifest, "implementing")
        final_snapshot = capture_requirement_scope(root, manifest)
        _require_same_scope(locked_snapshot, final_snapshot, "登记测试证据")

    return _mutate(root, requirement_id, mutate)


def append_test_report_execution(
    root: Path,
    requirement_id: str,
    *,
    test_kind: str,
    result: str,
    acceptance_ids: list[str],
    command: str,
    details: str,
    phase: str = "",
    executed_count: int = 1,
    files: Optional[list[str]] = None,
    project_wide: bool = False,
    snapshot: Optional[dict[str, Any]] = None,
) -> str:
    path = active_requirement_dir(root, requirement_id) / "test-report.md"
    if not path.is_file():
        raise RequirementError("尚未生成 test-report.md。")

    def mutate(manifest: dict[str, Any]) -> None:
        with _RequirementLock(path.parent, filename=".test-report.lock"):
            current = path.read_text(encoding="utf-8")
            safe_command = sanitize_text(command).replace("`", "ˋ").strip() or "人工测试"
            safe_details = sanitize_text(details).strip() or "无额外输出"
            longest_ticks = max((len(item) for item in re.findall(r"`+", safe_details)), default=0)
            fence = "`" * max(3, longest_ticks + 1)
            phase_label = phase or "execution"
            scope_label = "全项目" if project_wide else ", ".join(f"`{item}`" for item in (files or [])) or "未记录"
            commit_label = str((snapshot or {}).get("gitCommit") or "未知")
            diff_label = str((snapshot or {}).get("evidenceDiffHash") or (snapshot or {}).get("diffHash") or "未知")
            if result == "expected-failure-observed":
                status_label = "RED 预期失败已观察，尚未完成 GREEN"
                artifact_status = "observed"
            elif result == "passed":
                status_label = "最近一次执行通过"
                artifact_status = "executed"
            else:
                status_label = "最近一次执行失败"
                artifact_status = "failed"
            current = re.sub(r"(?m)^- 当前状态：.*$", f"- 当前状态：{status_label}", current, count=1)
            body = (
                current.rstrip()
                + f"\n\n### {now_iso()} · {phase_label} / {test_kind}\n\n"
                + f"- 结果：{result}\n"
                + f"- 已执行测试数：{max(0, int(executed_count))}\n"
                + f"- 验收标准：{', '.join(acceptance_ids) or '未映射'}\n"
                + f"- 覆盖范围：{scope_label}\n"
                + f"- Git 提交：`{commit_label}`\n"
                + f"- 代码快照：`{diff_label}`\n"
                + f"- 命令：`{safe_command}`\n\n"
                + f"{fence}text\n"
                + safe_details
                + f"\n{fence}\n"
            )
            _atomic_write(path, body.encode("utf-8"))
        relative = path.relative_to(root).as_posix()
        _upsert_artifact(
            manifest,
            "test",
            relative,
            file_sha256(path),
            "generated",
            status=artifact_status,
            test_kind=test_kind,
            result=result,
            acceptance_ids=acceptance_ids,
        )
        _resolve_blockers(manifest, "test", "测试报告已执行并更新。")

    _mutate(root, requirement_id, mutate)
    return path.relative_to(root).as_posix()


def record_review(
    root: Path,
    requirement_id: str,
    *,
    result: str,
    summary: str,
    findings: list[dict[str, Any]],
    files: list[str],
    snapshot: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    if result not in {"passed", "failed"}:
        raise RequirementError("评审结果只能是 passed 或 failed。")
    clean_summary = sanitize_text(" ".join(str(summary or "").split()))
    if not clean_summary:
        raise RequirementError("评审摘要不能为空。")
    current_manifest = load_requirement(root, requirement_id)
    current_snapshot = capture_requirement_scope(root, current_manifest)
    if snapshot and snapshot.get("diffHash") != current_snapshot.get("diffHash"):
        raise RequirementError("调用方提供的评审快照已过期，必须重新读取当前 Git 状态。")
    selected = validate_scope_selection(root, files, current_snapshot)
    normalized_findings: list[dict[str, Any]] = []
    for finding in findings:
        severity = str(finding.get("severity") or "").lower()
        text = sanitize_text(" ".join(str(finding.get("text") or "").split()))
        if severity not in {"critical", "important", "minor"} or not text:
            raise RequirementError("评审 finding 必须使用 critical、important 或 minor 并包含说明。")
        normalized_findings.append({"severity": severity, "text": text, "resolved": bool(finding.get("resolved", False))})

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"verified", "reviewed"}:
            raise RequirementError("只有 verified 状态可以登记交付评审。")
        locked_snapshot = capture_requirement_scope(root, manifest)
        _require_same_scope(current_snapshot, locked_snapshot, "登记评审")
        locked_selected = validate_scope_selection(root, files, locked_snapshot)
        unresolved = [item for item in normalized_findings if item["severity"] in BLOCKING_FINDINGS and not item["resolved"]]
        effective_result = "failed" if unresolved else result
        round_number = len(manifest.get("reviewRounds", [])) + 1
        for index, finding in enumerate(normalized_findings, 1):
            finding["id"] = f"FINDING-{round_number:02d}-{index:02d}"
        manifest.setdefault("reviewRounds", []).append({
            "id": f"REVIEW-{round_number:02d}",
            "result": effective_result,
            "summary": clean_summary,
            "findings": normalized_findings,
            "files": locked_selected,
            "diffHash": locked_snapshot.get("diffHash"),
            "evidenceDiffHash": locked_snapshot.get("evidenceDiffHash") or locked_snapshot.get("diffHash"),
            "gitCommit": locked_snapshot.get("gitCommit"),
            "evidenceCommit": locked_snapshot.get("gitCommit"),
            "recordedAt": now_iso(),
            "valid": True,
        })
        manifest.setdefault("scopeSnapshots", []).append({"kind": "review", **locked_snapshot})
        manifest["currentDiffHash"] = locked_snapshot.get("diffHash")
        if effective_result == "passed":
            _set_state(manifest, "reviewed")
        else:
            _set_state(manifest, "verified")
        final_snapshot = capture_requirement_scope(root, manifest)
        _require_same_scope(locked_snapshot, final_snapshot, "登记评审")

    return _mutate(root, requirement_id, mutate)


def resolve_review_findings(
    root: Path,
    requirement_id: str,
    finding_ids: list[str],
    *,
    resolved_by: str,
    resolution: str,
) -> dict[str, Any]:
    identifiers = sorted({str(item or "").strip() for item in finding_ids if str(item or "").strip()})
    clean_resolved_by = sanitize_text(" ".join(str(resolved_by or "").split()))
    clean_resolution = sanitize_text(" ".join(str(resolution or "").split()))
    if not identifiers:
        raise RequirementError("至少提供一个需要解决的 finding ID。")
    if not clean_resolved_by or not clean_resolution:
        raise RequirementError("解决 finding 必须记录 resolved-by 和 resolution。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"verified", "reviewed"}:
            raise RequirementError("只有 verified 或 reviewed 状态可以解决评审问题。")
        indexed = {
            str(finding.get("id")): finding
            for review in manifest.get("reviewRounds", [])
            if review.get("valid")
            for finding in review.get("findings", [])
            if finding.get("id")
        }
        missing = [identifier for identifier in identifiers if identifier not in indexed]
        if missing:
            raise RequirementError("未找到有效的评审问题：" + ", ".join(missing))
        resolved_at = now_iso()
        for identifier in identifiers:
            finding = indexed[identifier]
            finding["resolved"] = True
            finding["resolvedBy"] = clean_resolved_by
            finding["resolution"] = clean_resolution
            finding["resolvedAt"] = resolved_at
        manifest.setdefault("history", []).append({
            "action": "resolve-review-findings",
            "findingIds": identifiers,
            "resolvedBy": clean_resolved_by,
            "resolution": clean_resolution,
            "recordedAt": resolved_at,
        })
        if manifest.get("state") == "reviewed":
            _set_state(manifest, "verified")

    return _mutate(root, requirement_id, mutate)


def _artifact_is_current(root: Path, artifact: dict[str, Any]) -> bool:
    try:
        path, _ = _resolve_repo_file(root, str(artifact.get("path") or ""))
    except RequirementError:
        return False
    return file_sha256(path) == artifact.get("sha256")


def _current_test_artifact(
    root: Path,
    manifest: dict[str, Any],
    report_path: Optional[str],
) -> Optional[dict[str, Any]]:
    candidates = [
        item
        for item in manifest.get("artifacts", [])
        if item.get("type") in {"test", "unit-test", "service-test", "manual-test"}
        and (not report_path or item.get("path") == report_path)
    ]
    ordered = [item for item in candidates if item.get("type") != "test"] + [
        item for item in candidates if item.get("type") == "test"
    ]
    return next((item for item in reversed(ordered) if _artifact_is_current(root, item)), None)


def _validated_passing_test_evidence(
    root: Path,
    manifest: dict[str, Any],
    evidence_hash: Optional[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current = _current_test_evidence(manifest, evidence_hash)
    validated: list[dict[str, Any]] = []
    for item in current:
        if item.get("result") != "passed":
            continue
        report_source = str(item.get("reportSourcePath") or "").strip()
        report_path = str(item.get("reportPath") or "").strip()
        report_value = report_source or report_path
        artifact: Optional[dict[str, Any]] = None
        if not report_value:
            artifact = _current_test_artifact(root, manifest, None)
            report_value = str((artifact or {}).get("path") or "")
        if not report_value:
            continue
        try:
            report_file, relative = _resolve_repo_file(root, report_value)
            if report_source:
                expected_digest = str(item.get("reportSha256") or "")
                if manifest.get("schemaVersion") == SCHEMA_VERSION and not expected_digest:
                    continue
                if expected_digest and file_sha256(report_file) != expected_digest:
                    continue
            else:
                artifact = artifact or _current_test_artifact(root, manifest, report_path or report_value)
                if artifact is None:
                    continue
            _validate_test_report_file(
                report_file,
                relative,
                expected_result="passed",
                expected_test_kind=str(item.get("testKind") or "") or None,
            )
        except RequirementError:
            continue
        validated.append(item)
    return current, validated


def _test_gate_with_current_reports(
    root: Path,
    manifest: dict[str, Any],
    evidence_hash: Optional[str],
) -> tuple[bool, list[dict[str, Any]]]:
    current, validated = _validated_passing_test_evidence(root, manifest, evidence_hash)
    validated_objects = {id(item) for item in validated}
    effective = [
        item
        if item.get("result") != "passed" or id(item) in validated_objects
        else {**item, "result": "failed"}
        for item in current
    ]
    return _test_gate_for_records(manifest, effective), validated


def requirement_validation_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = [
        item for item in manifest.get("artifacts", [])
        if item.get("type") == "requirement" and item.get("status") not in {"draft", "stale", "failed"}
    ]
    if not artifacts:
        if manifest.get("schemaVersion") == LEGACY_SCHEMA_VERSION:
            return {"ok": True, "legacy": True, "warnings": ["v1 需求没有独立 requirement.md；迁移后必须补齐。"]}
        return {"ok": False, "legacy": False, "errors": ["缺少已登记的 requirement.md。"]}
    artifact = artifacts[-1]
    if not _artifact_is_current(root, artifact):
        return {"ok": False, "legacy": False, "errors": ["requirement.md 不存在或内容哈希已变化。"]}
    validation = artifact.get("validation")
    if not isinstance(validation, dict):
        return {"ok": False, "legacy": False, "errors": ["requirement.md 缺少结构验证记录。"]}
    path, relative = _resolve_repo_file(root, str(artifact.get("path") or ""))
    validation = requirement_documents.validate(
        path.read_text(encoding="utf-8", errors="ignore"),
        kind=manifest.get("ticketKind", "requirement"),
        expected_id=str(manifest.get("requirementId") or ""),
        expected_name=str(manifest.get("requirementName") or ""),
        acceptance_ids=[
            str(item.get("id")) for item in manifest.get("acceptanceCriteria", []) if item.get("id")
        ],
        acceptance_criteria=list(manifest.get("acceptanceCriteria") or []),
        expected_external_api=(
            bool(manifest.get("externalApiImpact", {}).get("value"))
            if manifest.get("externalApiImpact", {}).get("confirmed")
            else None
        ),
    )
    return {
        "ok": bool(validation.get("ok")),
        "legacy": False,
        "kind": validation.get("kind") or manifest.get("ticketKind", "requirement"),
        "file": relative,
        "errors": list(validation.get("errors") or []),
        "warnings": list(validation.get("warnings") or []),
    }


def _has_valid_requirement(root: Path, manifest: dict[str, Any]) -> bool:
    return bool(requirement_validation_status(root, manifest).get("ok"))


def design_validation_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    designs = [
        item for item in manifest.get("artifacts", [])
        if item.get("type") in {"design", "requirement-design"} and item.get("status") not in {"draft", "stale", "failed"}
    ]
    if not designs:
        return {"ok": False, "legacy": False, "errors": ["缺少已登记的需求与设计文档。"]}
    artifact = designs[-1]
    if not _artifact_is_current(root, artifact):
        return {"ok": False, "legacy": False, "errors": ["需求与设计文档不存在或内容哈希已变化。"]}
    validation = artifact.get("validation")
    if not isinstance(validation, dict):
        return {"ok": True, "legacy": True, "warnings": ["该文档由 0.3.0 以前版本登记，重新登记时必须通过新模板校验。"]}
    if (
        manifest.get("ticketKind", "requirement") == "requirement"
        and validation.get("schema") != design_documents.REQUIREMENT_V2_SCHEMA
    ):
        return {
            "ok": True,
            "legacy": True,
            "warnings": ["该 Requirement 文档由 requirement-crm-v2 之前版本登记；当前生命周期可继续，重新登记、amend 或 reopen 后必须通过 v2 校验。"],
        }
    path, relative = _resolve_repo_file(root, str(artifact.get("path") or ""))
    validation = design_documents.validate(
        path.read_text(encoding="utf-8", errors="ignore"),
        root,
        relative,
        manifest.get("ticketKind", "requirement"),
        expected_id=manifest.get("requirementId"),
        expected_name=manifest.get("requirementName"),
    )
    return {
        "ok": bool(validation.get("ok")),
        "legacy": False,
        "kind": validation.get("kind") or artifact.get("documentKind"),
        "file": relative,
        "errors": list(validation.get("errors") or []),
        "warnings": list(validation.get("warnings") or []),
    }


def _has_valid_design(root: Path, manifest: dict[str, Any]) -> bool:
    return bool(design_validation_status(root, manifest).get("ok"))


def plan_validation_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    plans = [
        item
        for item in manifest.get("artifacts", [])
        if item.get("type") == "plan" and item.get("status") not in {"stale", "failed"}
    ]
    if not plans:
        return {"ok": True, "present": False, "optional": True, "warnings": []}
    artifact = plans[-1]
    if artifact.get("status") == "draft":
        return {
            "ok": False,
            "present": True,
            "optional": True,
            "errors": ["plan.md 仍是脚手架草稿；补全后必须重新登记。"],
        }
    if not _artifact_is_current(root, artifact):
        return {
            "ok": False,
            "present": True,
            "optional": True,
            "errors": ["plan.md 不存在或内容哈希已变化。"],
        }
    try:
        path, relative = _resolve_repo_file(root, str(artifact.get("path") or ""))
        _validate_plan_file(path, manifest)
    except RequirementError as exc:
        return {
            "ok": False,
            "present": True,
            "optional": True,
            "errors": [str(exc)],
        }
    return {
        "ok": True,
        "present": True,
        "optional": True,
        "file": relative,
        "validatedAt": now_iso(),
        "warnings": [],
    }


def _best_document_state(root: Path, manifest: dict[str, Any]) -> str:
    """Return the strongest reusable document state without reviving downstream evidence."""
    if manifest.get("schemaVersion") == LEGACY_SCHEMA_VERSION:
        return "documented" if _has_valid_design(root, manifest) else "draft"
    if _has_valid_requirement(root, manifest) and _has_valid_design(root, manifest):
        return "designed"
    if _has_valid_requirement(root, manifest):
        return "specified"
    return "draft"


def finish_requirement(root: Path, requirement_id: str, *, files: list[str]) -> dict[str, Any]:
    current_manifest = load_requirement(root, requirement_id)
    snapshot = capture_requirement_scope(root, current_manifest)
    selected = validate_scope_selection(root, files, snapshot)

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") != "reviewed":
            raise RequirementError("需求必须先达到 reviewed 状态才能 finish。")
        locked_snapshot = capture_requirement_scope(root, manifest)
        _require_same_scope(snapshot, locked_snapshot, "完成需求")
        locked_selected = validate_scope_selection(root, files, locked_snapshot)
        unresolved_blockers = [item for item in manifest.get("readiness", {}).get("blockers", []) if not item.get("resolvedAt")]
        if unresolved_blockers:
            raise RequirementError("仍有未解决的 readiness 阻塞项。")
        if not _has_valid_design(root, manifest):
            raise RequirementError("缺少当前有效的需求与设计文档。")
        if manifest.get("schemaVersion") == SCHEMA_VERSION and not _has_valid_requirement(root, manifest):
            raise RequirementError("缺少当前有效的 requirement.md。")
        evidence_hash = locked_snapshot.get("evidenceDiffHash") or locked_snapshot.get("diffHash")
        test_gate_ok, valid_tests = _test_gate_with_current_reports(root, manifest, evidence_hash)
        if not test_gate_ok:
            raise RequirementError("测试证据类型、最新结果或测试报告完整性不满足当前快照门禁。")
        if not valid_tests:
            raise RequirementError("缺少当前有效且已通过的测试报告文件。")
        valid_reviews = [item for item in manifest.get("reviewRounds", []) if item.get("valid") and item.get("result") == "passed"]
        actual_files = set(locked_snapshot.get("evidenceFiles", locked_snapshot.get("files", [])))
        if actual_files and not any(
            (item.get("evidenceDiffHash") or item.get("diffHash")) == evidence_hash
            and (item.get("projectWide") or actual_files.issubset(set(item.get("files", []))))
            for item in valid_tests
        ):
            raise RequirementError("测试证据文件范围未覆盖全部实际 Git 变更。")
        if not valid_reviews or (valid_reviews[-1].get("evidenceDiffHash") or valid_reviews[-1].get("diffHash")) != evidence_hash:
            raise RequirementError("评审证据与当前 Git 变更不一致，必须重新评审。")
        unresolved_findings = [
            finding
            for review in manifest.get("reviewRounds", [])
            if review.get("valid")
            for finding in review.get("findings", [])
            if finding.get("severity") in BLOCKING_FINDINGS and not finding.get("resolved")
        ]
        if unresolved_findings:
            raise RequirementError("仍有未解决的 critical/important 评审问题。")
        covered: set[str] = set()
        for evidence in valid_tests:
            if (evidence.get("evidenceDiffHash") or evidence.get("diffHash")) == evidence_hash:
                covered.update(evidence.get("acceptanceIds", []))
        expected = {item.get("id") for item in manifest.get("acceptanceCriteria", [])}
        if expected - covered:
            raise RequirementError("以下验收标准缺少通过证据：" + ", ".join(sorted(expected - covered)))
        closures = [item for item in manifest.get("artifacts", []) if item.get("type") == "closure" and item.get("status") not in {"stale"}]
        if not closures or not _artifact_is_current(root, closures[-1]):
            raise RequirementError("缺少当前有效的复盘收口总结文件。")
        closure_file, _ = _resolve_repo_file(root, str(closures[-1].get("path") or ""))
        _validate_closure_file(closure_file, manifest)
        manifest["currentDiffHash"] = locked_snapshot.get("diffHash")
        manifest.setdefault("scopeSnapshots", []).append({"kind": "finish", **locked_snapshot, "selectedFiles": locked_selected})
        selected_set = set(locked_selected)
        manifest["changedFiles"] = [
            {
                "status": item.get("status"),
                "path": item.get("path"),
                "oldPath": item.get("oldPath"),
                "sha256": item.get("sha256"),
                "recordedAt": now_iso(),
            }
            for item in locked_snapshot.get("entries", [])
            if item.get("path") in selected_set or item.get("oldPath") in selected_set
        ]
        manifest["finishResult"] = {
            "status": "passed",
            "diffHash": locked_snapshot.get("diffHash"),
            "gitCommit": locked_snapshot.get("gitCommit"),
            "files": locked_selected,
            "recordedAt": now_iso(),
        }
        for criterion in manifest.get("acceptanceCriteria", []):
            criterion["status"] = "passed"
        _set_state(manifest, "finished")
        _refresh_closure_artifact(root, manifest)
        final_snapshot = capture_requirement_scope(root, manifest)
        _require_same_scope(locked_snapshot, final_snapshot, "完成需求")

    return _mutate(root, requirement_id, mutate)


def _validate_finished_invariants(
    root: Path,
    manifest: dict[str, Any],
    snapshot: dict[str, Any],
) -> None:
    if manifest.get("schemaVersion") == SCHEMA_VERSION and not _has_valid_requirement(root, manifest):
        raise RequirementError("需求文档已删除、篡改或验证失效，不能关闭需求。")
    if not _has_valid_design(root, manifest):
        raise RequirementError("设计文档已删除、篡改或验证失效，不能关闭需求。")
    if any(
        not item.get("resolvedAt")
        for item in manifest.get("readiness", {}).get("blockers", [])
    ):
        raise RequirementError("仍有未解决的 readiness 阻塞项，不能关闭需求。")
    evidence_hash = snapshot.get("evidenceDiffHash") or snapshot.get("diffHash")
    test_gate_ok, valid_tests = _test_gate_with_current_reports(root, manifest, evidence_hash)
    if not test_gate_ok:
        raise RequirementError("当前快照不再满足测试类型、最新结果或测试报告完整性门禁。")
    covered = {
        acceptance_id
        for item in valid_tests
        for acceptance_id in item.get("acceptanceIds", [])
    }
    expected = {item.get("id") for item in manifest.get("acceptanceCriteria", [])}
    if expected - covered:
        raise RequirementError("当前有效测试报告缺少验收标准证据，不能关闭需求。")
    current_reviews = [
        item
        for item in manifest.get("reviewRounds", [])
        if item.get("valid")
        and item.get("result") == "passed"
        and (item.get("evidenceDiffHash") or item.get("diffHash")) == evidence_hash
    ]
    if not current_reviews:
        raise RequirementError("当前快照缺少有效通过评审，不能关闭需求。")
    if any(
        finding.get("severity") in BLOCKING_FINDINGS and not finding.get("resolved")
        for review in manifest.get("reviewRounds", [])
        if review.get("valid")
        for finding in review.get("findings", [])
    ):
        raise RequirementError("仍有未解决的 critical/important 评审问题。")
    closures = [
        item
        for item in manifest.get("artifacts", [])
        if item.get("type") == "closure" and item.get("status") != "stale"
    ]
    if not closures or not _artifact_is_current(root, closures[-1]):
        raise RequirementError("复盘收口总结已删除、篡改或失效，不能关闭需求。")
    closure_file, _ = _resolve_repo_file(root, str(closures[-1].get("path") or ""))
    _validate_closure_file(closure_file, manifest)
    finish_result = manifest.get("finishResult") if isinstance(manifest.get("finishResult"), dict) else {}
    if finish_result.get("status") != "passed" or finish_result.get("diffHash") != snapshot.get("diffHash"):
        raise RequirementError("finish 结果与当前 Git 快照不一致，不能关闭需求。")
    if any(item.get("status") != "passed" for item in manifest.get("acceptanceCriteria", [])):
        raise RequirementError("仍有验收标准未通过，不能关闭需求。")


def validate_finished_freshness(root: Path, requirement_id: str) -> dict[str, Any]:
    current_manifest = load_requirement(root, requirement_id)
    if current_manifest.get("state") != "finished":
        raise RequirementError("只有 finished 状态可以执行维护和关闭。")
    current_snapshot = capture_requirement_scope(root, current_manifest)
    finish_snapshots = [item for item in current_manifest.get("scopeSnapshots", []) if item.get("kind") == "finish"]
    if not finish_snapshots:
        raise RequirementError("缺少 finish 作用域快照，不能关闭需求。")
    if not current_snapshot.get("gitAvailable") or not current_snapshot.get("diffHash"):
        raise RequirementError("无法读取 Git 状态，不能关闭需求。")
    if finish_snapshots[-1].get("diffHash") != current_snapshot.get("diffHash"):
        raise RequirementError("finish 后代码或 Git 提交发生变化，必须重新测试、评审和 finish。")
    _validate_finished_invariants(root, current_manifest, current_snapshot)
    return current_snapshot


def close_requirement(root: Path, requirement_id: str, *, check_succeeded: bool) -> dict[str, Any]:
    if not check_succeeded:
        raise RequirementError("维护检查失败，需求保持 finished 状态。")

    current_snapshot = validate_finished_freshness(root, requirement_id)

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") != "finished":
            raise RequirementError("只有 finished 状态可以进入 closed。")
        finish_snapshots = [item for item in manifest.get("scopeSnapshots", []) if item.get("kind") == "finish"]
        locked_snapshot = capture_requirement_scope(root, manifest)
        if finish_snapshots[-1].get("diffHash") != locked_snapshot.get("diffHash"):
            raise RequirementError("finish 后代码或 Git 提交发生变化，必须重新测试、评审和 finish。")
        _validate_finished_invariants(root, manifest, locked_snapshot)
        manifest["maintenanceResult"] = {
            "status": "passed",
            "diffHash": locked_snapshot.get("diffHash"),
            "gitCommit": locked_snapshot.get("gitCommit"),
            "recordedAt": now_iso(),
        }
        _set_state(manifest, "closed")
        _refresh_closure_artifact(root, manifest)

    return _mutate(root, requirement_id, mutate)


def reopen_requirement(root: Path, requirement_id: str, reason: str) -> dict[str, Any]:
    clean_reason = sanitize_text(" ".join(str(reason or "").split()))
    if not clean_reason:
        raise RequirementError("reopen 必须记录原因。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") in {"draft", "specified", "designed", "documented"}:
            raise RequirementError("当前需求尚未进入可 reopen 的下游状态。")
        previous = manifest.get("state")
        for evidence in manifest.get("testEvidence", []):
            evidence["valid"] = False
            evidence["invalidatedAt"] = now_iso()
            evidence["invalidatedReason"] = clean_reason
        for review in manifest.get("reviewRounds", []):
            review["valid"] = False
            review["invalidatedAt"] = now_iso()
            review["invalidatedReason"] = clean_reason
        legacy_design_invalidated = False
        for artifact in manifest.get("artifacts", []):
            if artifact.get("type") == "closure":
                artifact["status"] = "stale"
                artifact["invalidatedAt"] = now_iso()
                artifact["invalidatedReason"] = clean_reason
            elif (
                artifact.get("type") in {"design", "requirement-design"}
                and artifact.get("status") not in {"draft", "stale", "failed"}
                and not isinstance(artifact.get("validation"), dict)
            ):
                artifact["status"] = "stale"
                artifact["invalidatedAt"] = now_iso()
                artifact["invalidatedReason"] = "旧版设计在 reopen 后必须按 0.3.0 模板重新验证。"
                legacy_design_invalidated = True
        for key in ("test", "closure"):
            selection = manifest.get("workflowSelections", {}).get(key)
            if isinstance(selection, dict):
                selection["status"] = "stale"
                selection["invalidatedAt"] = now_iso()
                selection["invalidatedReason"] = clean_reason
        if legacy_design_invalidated:
            selection = manifest.get("workflowSelections", {}).get("design")
            if isinstance(selection, dict):
                selection["status"] = "stale"
                selection["invalidatedAt"] = now_iso()
                selection["invalidatedReason"] = "旧版设计必须重新验证。"
        manifest.setdefault("history", []).append({
            "action": "reopen",
            "fromState": previous,
            "reason": clean_reason,
            "recordedAt": now_iso(),
        })
        manifest["currentDiffHash"] = None
        manifest["finishResult"] = None
        manifest["maintenanceResult"] = None
        _set_state(manifest, "draft" if legacy_design_invalidated else _best_document_state(root, manifest))

    return _mutate(root, requirement_id, mutate)


def status_payload(root: Path, requirement_id: str) -> dict[str, Any]:
    manifest = load_requirement(root, requirement_id)
    unresolved = [item for item in manifest.get("readiness", {}).get("blockers", []) if not item.get("resolvedAt")]
    current_scope = capture_requirement_scope(root, manifest)
    test_gate_ok, _ = _test_gate_with_current_reports(
        root,
        manifest,
        current_scope.get("evidenceDiffHash") or current_scope.get("diffHash"),
    )
    return {
        "requirementId": manifest.get("requirementId"),
        "requirementName": manifest.get("requirementName"),
        "directory": active_requirement_dir(root, str(manifest.get("requirementId") or requirement_id)).relative_to(root).as_posix(),
        "ticketKind": manifest.get("ticketKind", "requirement"),
        "state": manifest.get("state"),
        "revision": manifest.get("revision"),
        "externalApiImpact": manifest.get("externalApiImpact"),
        "acceptanceCriteria": manifest.get("acceptanceCriteria", []),
        "requirementArtifact": next(
            (item for item in reversed(manifest.get("artifacts", [])) if item.get("type") == "requirement"),
            None,
        ),
        "requirementValidation": requirement_validation_status(root, manifest),
        "designArtifact": next(
            (item for item in reversed(manifest.get("artifacts", [])) if item.get("type") in {"design", "requirement-design"}),
            None,
        ),
        "designValidation": design_validation_status(root, manifest),
        "planArtifact": next(
            (item for item in reversed(manifest.get("artifacts", [])) if item.get("type") == "plan"),
            None,
        ),
        "planValidation": plan_validation_status(root, manifest),
        "testContract": manifest.get("testContract"),
        "diagnosis": manifest.get("diagnosis"),
        "unresolvedBlockers": unresolved,
        "artifacts": manifest.get("artifacts", []),
        "testGateSatisfied": test_gate_ok,
        "latestReview": (manifest.get("reviewRounds") or [None])[-1],
        "changedFiles": manifest.get("changedFiles", []),
        "finishResult": manifest.get("finishResult"),
        "maintenanceResult": manifest.get("maintenanceResult"),
        "workflowSelections": manifest.get("workflowSelections", {}),
        "currentDiffHash": current_scope.get("diffHash"),
    }


def record_changed_files(root: Path, requirement_id: str, snapshot: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    current = load_requirement(root, requirement_id)
    scope = snapshot or capture_requirement_scope(root, current)
    evidence_paths = set(scope.get("evidenceFiles", scope.get("files", [])))
    changed = [
        {
            "status": item.get("status"),
            "path": item.get("path"),
            "sha256": item.get("sha256"),
            "recordedAt": now_iso(),
        }
        for item in scope.get("entries", [])
        if item.get("path") in evidence_paths
    ]

    def mutate(manifest: dict[str, Any]) -> None:
        manifest["changedFiles"] = changed
        manifest.setdefault("history", []).append({
            "action": "record-changed-files",
            "files": [item.get("path") for item in changed],
            "recordedAt": now_iso(),
        })

    return _mutate(root, requirement_id, mutate)


def _requirement_manifest_files(root: Path) -> list[Path]:
    direct = requirement_root(root)
    result: list[Path] = []

    def collect(base: Path, *, skip_by_id: bool = False) -> None:
        if base.is_symlink() or not base.is_dir():
            return
        try:
            safe_base = _assert_safe_internal_path(root, base)
        except RequirementError:
            return
        for directory in safe_base.iterdir():
            if (skip_by_id and directory.name == "by-id") or directory.is_symlink() or not directory.is_dir():
                continue
            manifest = directory / "manifest.json"
            if manifest.is_symlink() or not manifest.is_file():
                continue
            try:
                result.append(_assert_safe_internal_path(root, manifest))
            except RequirementError:
                continue

    collect(direct, skip_by_id=True)
    collect(direct / "by-id")
    return sorted(dict.fromkeys(result))


def query_requirements(
    root: Path,
    *,
    file_path: Optional[str] = None,
    state: Optional[str] = None,
) -> list[dict[str, Any]]:
    normalized_file = None
    if file_path:
        normalized = _normalize_scope_files(root, [file_path])
        if not normalized:
            raise RequirementError("文件查询必须提供仓库内业务文件路径。")
        normalized_file = normalized[0]
    matches: list[dict[str, Any]] = []
    for path in _requirement_manifest_files(root):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("schemaVersion") not in {LEGACY_SCHEMA_VERSION, SCHEMA_VERSION}:
            continue
        try:
            if normalize_requirement_id(str(payload.get("requirementId") or "")) != path.parent.name:
                continue
        except RequirementError:
            continue
        if state and payload.get("state") != state:
            continue
        changed = payload.get("changedFiles", [])
        if normalized_file and not any(
            normalized_file in {item.get("path"), item.get("oldPath")}
            for item in changed if isinstance(item, dict)
        ):
            continue
        matches.append({
            "requirementId": payload.get("requirementId"),
            "requirementName": payload.get("requirementName"),
            "state": payload.get("state"),
            "manifest": path.relative_to(Path(os.path.abspath(root))).as_posix(),
            "changedFiles": changed,
        })
    return sorted(matches, key=lambda item: str(item.get("requirementId") or ""))


def migrate_layout(root: Path, *, dry_run: bool = True) -> dict[str, Any]:
    legacy_root = _assert_safe_internal_path(root, requirement_root(root) / "by-id")
    actions: list[dict[str, str]] = []
    conflicts: list[str] = []
    conflict_details: list[str] = []
    prepared: list[dict[str, Any]] = []
    unmapped = [
        path.relative_to(root).as_posix()
        for path in (
            root / ".project-intel" / "specs",
            root / ".project-intel" / "plans",
            root / ".project-intel" / "reports",
            root / ".project-intel" / "maintenance",
            root / ".project-intel" / "requirements" / "files",
        )
        if path.exists()
    ]
    if legacy_root.is_dir():
        for source in sorted(path for path in legacy_root.iterdir() if path.is_dir()):
            try:
                identifier = normalize_requirement_id(source.name)
            except RequirementError:
                conflicts.append(source.relative_to(root).as_posix())
                conflict_details.append(f"无法识别旧需求目录：{source.relative_to(root).as_posix()}")
                continue
            destination = requirement_root(root) / identifier
            action = {
                "action": "move-requirement",
                "source": source.relative_to(root).as_posix(),
                "destination": destination.relative_to(root).as_posix(),
            }
            actions.append(action)
            if destination.exists():
                conflicts.append(destination.relative_to(root).as_posix())
                conflict_details.append(f"目标目录已存在：{destination.relative_to(root).as_posix()}")
                continue
            symlinks = [path for path in source.rglob("*") if path.is_symlink()]
            if source.is_symlink() or symlinks:
                conflicts.append(source.relative_to(root).as_posix())
                conflict_details.append(f"旧需求目录包含符号链接：{source.relative_to(root).as_posix()}")
                continue
            manifest_file = source / "manifest.json"
            try:
                original_bytes = manifest_file.read_bytes()
                payload = json.loads(original_bytes.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                conflicts.append(manifest_file.relative_to(root).as_posix())
                conflict_details.append(f"旧 manifest 无法读取：{manifest_file.relative_to(root).as_posix()} ({exc})")
                continue
            try:
                payload_identifier = normalize_requirement_id(str(payload.get("requirementId") or "")) if isinstance(payload, dict) else ""
            except RequirementError:
                payload_identifier = ""
            if (
                not isinstance(payload, dict)
                or payload.get("schemaVersion") not in {LEGACY_SCHEMA_VERSION, SCHEMA_VERSION}
                or payload_identifier != identifier
            ):
                conflicts.append(manifest_file.relative_to(root).as_posix())
                conflict_details.append(f"旧 manifest 格式或需求号不一致：{manifest_file.relative_to(root).as_posix()}")
                continue
            old_prefix = action["source"].rstrip("/") + "/"
            new_prefix = action["destination"].rstrip("/") + "/"

            def rewrite(value: Any) -> Any:
                if isinstance(value, dict):
                    return {key: rewrite(item) for key, item in value.items()}
                if isinstance(value, list):
                    return [rewrite(item) for item in value]
                if isinstance(value, str) and value.startswith(old_prefix):
                    return new_prefix + value[len(old_prefix):]
                return value

            transformed = rewrite(payload)
            transformed.setdefault("history", []).append({
                "action": "migrate-layout-v2",
                "from": action["source"],
                "to": action["destination"],
                "recordedAt": now_iso(),
            })
            transformed["revision"] = int(transformed.get("revision", 0)) + 1
            transformed["updatedAt"] = now_iso()
            prepared.append({
                "action": action,
                "source": source,
                "destination": destination,
                "payload": transformed,
                "originalBytes": original_bytes,
            })
    if conflicts:
        return {
            "ok": False,
            "dryRun": dry_run,
            "actions": actions,
            "conflicts": sorted(dict.fromkeys(conflicts)),
            "conflictDetails": conflict_details,
            "unmappedLegacyPaths": unmapped,
        }
    if not dry_run:
        moved: list[dict[str, Any]] = []
        try:
            with _RequirementLock(requirement_root(root)), ExitStack() as locks:
                for item in prepared:
                    item["lock"] = locks.enter_context(_RequirementLock(item["source"]))
                try:
                    for item in prepared:
                        source = item["source"]
                        destination = item["destination"]
                        manifest_file = source / "manifest.json"
                        if (
                            not source.is_dir()
                            or destination.exists()
                            or manifest_file.read_bytes() != item["originalBytes"]
                            or any(path.is_symlink() for path in source.rglob("*"))
                        ):
                            raise RequirementError(f"迁移前目录状态发生变化：{source.relative_to(root).as_posix()}")
                    for item in prepared:
                        source = item["source"]
                        destination = item["destination"]
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(source, destination)
                        moved.append(item)
                        _write_manifest(destination / "manifest.json", item["payload"])
                except Exception:
                    for item in reversed(moved):
                        destination = item["destination"]
                        source = item["source"]
                        if destination.exists() and not source.exists():
                            os.replace(destination, source)
                        _atomic_write(source / "manifest.json", item["originalBytes"])
                    raise
        except Exception as exc:
            raise RequirementError(f"需求档案迁移失败：{exc}；已回滚") from exc
        try:
            legacy_root.rmdir()
        except OSError:
            pass
    return {
        "ok": True,
        "dryRun": dry_run,
        "actions": actions,
        "conflicts": [],
        "conflictDetails": [],
        "unmappedLegacyPaths": unmapped,
    }
