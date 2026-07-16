from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from . import design_documents
from .testing import sanitize_text


SCHEMA_VERSION = 1
STATES = ("draft", "documented", "ready", "implementing", "verified", "reviewed", "finished", "closed")
ARTIFACT_FILES = {
    "requirement-design": "requirement-design.md",
    "test": "test-report.md",
    "test-report": "test-report.md",
    "unit-test": "test-report.md",
    "service-test": "test-report.md",
    "manual-test": "test-report.md",
    "closure": "closure-summary.md",
}
ARTIFACT_SUFFIXES = {
    "requirement-design": {".md"},
    "unit-test": {".md", ".txt", ".json", ".xml"},
    "service-test": {".md", ".txt", ".json", ".xml"},
    "manual-test": {".md", ".txt", ".json", ".xml"},
    "closure": {".md"},
}
TEST_KINDS = {"unit", "service", "both", "manual"}
PASSING_RESULTS = {"passed"}
BLOCKING_FINDINGS = {"critical", "important"}
MANUAL_REQUIRED_FIELDS = ("approved", "category", "reason", "steps", "input", "observation", "evidencePath")
MANUAL_CATEGORIES = {"visual", "device", "hardware", "configuration"}
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


def requirement_root(root: Path) -> Path:
    return root / ".project-intel" / "requirements" / "by-id"


def requirement_dir(root: Path, requirement_id: str) -> Path:
    return requirement_root(root) / normalize_requirement_id(requirement_id)


def manifest_path(root: Path, requirement_id: str) -> Path:
    return requirement_dir(root, requirement_id) / "manifest.json"


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
    def __init__(self, directory: Path, timeout: float = 5.0) -> None:
        self.path = directory / ".manifest.lock"
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
    path = manifest_path(root, requirement_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RequirementError(f"未找到需求档案：{normalize_requirement_id(requirement_id)}") from exc
    except json.JSONDecodeError as exc:
        raise RequirementError(f"需求档案 JSON 损坏：{path}") from exc
    if not isinstance(payload, dict) or payload.get("schemaVersion") != SCHEMA_VERSION:
        raise RequirementError(f"不支持的需求档案格式：{path}")
    payload.setdefault("ticketKind", "requirement")
    return payload


def _mutate(root: Path, requirement_id: str, callback: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    directory = requirement_dir(root, requirement_id)
    path = directory / "manifest.json"
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


def create_requirement(
    root: Path,
    requirement_id: Optional[str],
    requirement_name: str,
    *,
    track: str = "standard",
    external_api: Optional[bool] = False,
    external_api_source: str = "user",
    ticket_kind: str = "requirement",
) -> dict[str, Any]:
    identifier = canonicalize_ticket_id(requirement_id, ticket_kind)
    name = sanitize_text(" ".join(str(requirement_name or "").split()))
    if not name:
        raise RequirementError("需求名称不能为空。")
    if track not in {"quick", "standard", "complex", "auto"}:
        raise RequirementError("track 只能是 auto、quick、standard 或 complex。")
    directory = requirement_dir(root, identifier)
    path = directory / "manifest.json"
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
            "acceptanceCriteria": [],
            "artifacts": [],
            "testEvidence": [],
            "reviewRounds": [],
            "scopeSnapshots": [],
            "currentDiffHash": None,
            "baselineDiffHash": baseline.get("diffHash"),
            "baselineCommit": baseline.get("gitCommit"),
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
    reason: str = "",
) -> dict[str, Any]:
    clean_reason = sanitize_text(" ".join(str(reason or "").split()))
    if not clean_reason:
        raise RequirementError("amend 必须记录修改原因。")
    if track is not None and track not in {"quick", "standard", "complex", "auto"}:
        raise RequirementError("track 只能是 auto、quick、standard 或 complex。")
    if ticket_kind is not None and ticket_kind not in {"bug", "requirement"}:
        raise RequirementError("ticket kind 只能是 bug 或 requirement。")

    def mutate(manifest: dict[str, Any]) -> None:
        before = {
            "requirementName": manifest.get("requirementName"),
            "ticketKind": manifest.get("ticketKind", "requirement"),
            "track": manifest.get("track"),
            "externalApiImpact": dict(manifest.get("externalApiImpact", {})),
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
        after = {
            "requirementName": manifest.get("requirementName"),
            "ticketKind": manifest.get("ticketKind", "requirement"),
            "track": manifest.get("track"),
            "externalApiImpact": dict(manifest.get("externalApiImpact", {})),
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
        design_affecting = (
            before.get("requirementName") != after.get("requirementName")
            or before.get("ticketKind") != after.get("ticketKind")
            or before.get("externalApiImpact") != after.get("externalApiImpact")
        )
        legacy_design = any(
            artifact.get("type") == "requirement-design"
            and artifact.get("status") not in {"draft", "stale", "failed"}
            and not isinstance(artifact.get("validation"), dict)
            for artifact in manifest.get("artifacts", [])
        )
        if design_affecting or legacy_design:
            for artifact in manifest.get("artifacts", []):
                if artifact.get("type") == "requirement-design" and (design_affecting or not isinstance(artifact.get("validation"), dict)):
                    artifact["status"] = "stale"
                    artifact["invalidatedAt"] = now_iso()
                    artifact["invalidatedReason"] = (
                        "需求名称、类型或接口影响已修改。"
                        if design_affecting else "旧版设计在 amend 后必须按 0.3.0 模板重新验证。"
                    )
        manifest.setdefault("history", []).append({
            "action": "amend",
            "reason": clean_reason,
            "before": before,
            "after": after,
            "recordedAt": now_iso(),
        })
        if design_affecting or legacy_design:
            _set_state(manifest, "draft")
        elif manifest.get("state") in {"verified", "reviewed", "finished", "closed"}:
            _set_state(manifest, "documented" if _has_valid_design(root, manifest) else "draft")

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


def _validate_test_report_file(path: Path, relative: str) -> None:
    if not _test_report_path_valid(relative):
        raise RequirementError("测试报告路径必须位于 reports/test-results/coverage/evidence 等报告目录，或使用明确的 report/result 文件名。")
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            content = json.dumps(payload, ensure_ascii=False).lower()
            structural = any(marker in content for marker in ('"tests"', '"testcases"', '"suites"', '"stats"', '"results"'))
            outcome = any(marker in content for marker in ('"passed"', '"failed"', '"failures"', '"errors"', '"status"'))
        elif suffix == ".xml":
            root = ET.parse(path).getroot()
            tag = root.tag.rsplit("}", 1)[-1].lower()
            attributes = {str(key).lower() for key in root.attrib}
            structural = any(marker in tag for marker in ("test", "suite", "report", "result"))
            outcome = bool(attributes & {"tests", "failures", "errors", "passed", "failed", "status"})
        else:
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            structural = any(marker in content for marker in ("test", "测试", "单元", "接口", "service", "manual"))
            outcome = any(marker in content for marker in ("pass", "fail", "通过", "失败", "结果", "执行"))
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        raise RequirementError(f"测试报告格式无效：{relative}") from exc
    if not structural or not outcome:
        raise RequirementError("测试报告必须包含可识别的测试结构和通过/失败结果。")


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
        if manifest.get("state") not in {"draft", "documented"}:
            raise RequirementError("只有 draft/documented 状态可以设置验收标准；下游需求请先 reopen。")
        manifest["acceptanceCriteria"] = normalized
        if _has_valid_design(root, manifest):
            _set_state(manifest, "documented")

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
    artifacts = manifest.setdefault("artifacts", [])
    for index in range(len(artifacts) - 1, -1, -1):
        if artifacts[index].get("type") == artifact_type and artifacts[index].get("path") == relative:
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


def _closure_text(manifest: dict[str, Any]) -> str:
    covered = set()
    for evidence in manifest.get("testEvidence", []):
        if evidence.get("valid") and evidence.get("result") == "passed":
            covered.update(evidence.get("acceptanceIds", []))
    criteria = "\n".join(
        f"- {item['id']}：{'通过' if item['id'] in covered else '待确认'} — {item['description']}"
        for item in manifest.get("acceptanceCriteria", [])
    )
    return f"""# {manifest['requirementName']} · 复盘收口总结

- 需求号：`{manifest['requirementId']}`
- 需求结果：等待 finish 门禁确认

## 变更范围

以需求 manifest 中最新作用域快照为准。

## 验收标准结果

{criteria or '- 尚未登记验收标准。'}

## 测试证据

已记录 {len(manifest.get('testEvidence', []))} 轮测试证据。

## 人工例外

{('- 存在人工测试证据，详见 test-report.md。' if any(item.get('testKind') == 'manual' for item in manifest.get('testEvidence', [])) else '- 无。')}

## 遗留问题

- 无已知阻塞项；如存在遗留问题，必须在 finish 前补充。

## 复盘结论

需求文档、测试、评审和收口材料必须同时满足门禁后才能关闭。
"""


def generate_artifact(root: Path, requirement_id: str, artifact_type: str) -> dict[str, Any]:
    normalized_type = "test" if artifact_type == "test-report" else artifact_type
    if normalized_type not in {"requirement-design", "test", "closure"}:
        raise RequirementError("可生成的产物类型只能是 requirement-design、test 或 closure。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") == "closed":
            raise RequirementError("需求已 closed；如需修改产物请先 reopen。")
        if normalized_type == "requirement-design" and manifest.get("state") not in {"draft", "documented"}:
            raise RequirementError("需求已进入下游状态；修改需求设计前请先 reopen。")
        if normalized_type == "test" and manifest.get("state") not in {"implementing", "verified"}:
            raise RequirementError("测试报告只能在 implementing 或 verified 状态生成。")
        if normalized_type == "closure" and manifest.get("state") not in {"reviewed", "finished"}:
            raise RequirementError("只有评审通过后才能生成复盘收口总结。")
        directory = requirement_dir(root, requirement_id)
        filename = ARTIFACT_FILES[normalized_type]
        if normalized_type == "requirement-design":
            filename = design_documents.design_filename(
                manifest["requirementId"],
                manifest["requirementName"],
                manifest.get("ticketKind", "requirement"),
            )
        path = directory / filename
        if normalized_type == "requirement-design":
            body = design_documents.scaffold_text(
                manifest["requirementId"],
                manifest["requirementName"],
                manifest.get("ticketKind", "requirement"),
            )
        elif normalized_type == "test":
            body = _test_report_text(manifest)
        else:
            body = _closure_text(manifest)
        if normalized_type != "test" or not path.is_file() or path.stat().st_size == 0:
            _atomic_write(path, body.encode("utf-8"))
        relative = path.relative_to(root).as_posix()
        artifact_status = "draft" if normalized_type in {"requirement-design", "test"} else "registered"
        _upsert_artifact(
            manifest,
            normalized_type,
            relative,
            file_sha256(path),
            "generated",
            status=artifact_status,
            document_kind=manifest.get("ticketKind", "requirement") if normalized_type == "requirement-design" else None,
            validation={"ok": False, "scaffold": True, "errors": ["脚手架必须由 project-design 补全并重新登记。"]}
            if normalized_type == "requirement-design" else None,
        )
        if normalized_type == "requirement-design":
            _set_state(manifest, "draft")
        elif normalized_type == "closure":
            _resolve_blockers(manifest, "closure", "复盘收口总结已生成。")

    return _mutate(root, requirement_id, mutate)


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
    if artifact_type not in {"requirement-design", "unit-test", "service-test", "manual-test", "closure"}:
        raise RequirementError("不支持的产物类型。")
    path, relative = _resolve_repo_file(root, path_value)
    allowed_suffixes = ARTIFACT_SUFFIXES.get(artifact_type, set())
    if path.suffix.lower() not in allowed_suffixes:
        raise RequirementError(f"{artifact_type} 产物不接受源码文件或未知格式：{relative}")
    test_kind = artifact_type.removesuffix("-test") if artifact_type.endswith("-test") else None
    if artifact_type.endswith("-test") and result not in {"passed", "failed"}:
        raise RequirementError("测试产物必须通过 --result 登记 passed 或 failed。")
    acceptance_ids = acceptance_ids or []
    files = files or []
    current = load_requirement(root, requirement_id)
    design_validation = None
    if artifact_type == "requirement-design":
        design_validation = design_documents.validate(
            path.read_text(encoding="utf-8", errors="ignore"),
            root,
            relative,
            current.get("ticketKind", "requirement"),
            expected_id=current.get("requirementId"),
            expected_name=current.get("requirementName"),
        )
        if not design_validation.get("ok"):
            raise RequirementError("设计文档验证失败：" + "；".join(design_validation.get("errors", [])))
    if test_kind:
        normalized_files = _normalize_scope_files(root, files)
        _validate_test_report_file(path, relative)
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

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") == "closed":
            raise RequirementError("需求已 closed；如需登记产物请先 reopen。")
        if artifact_type == "requirement-design" and manifest.get("state") not in {"draft", "documented"}:
            raise RequirementError("需求已进入下游状态；替换需求设计前请先 reopen。")
        if artifact_type.endswith("-test") and manifest.get("state") not in {"implementing", "verified"}:
            raise RequirementError("测试报告只能在 implementing 或 verified 状态登记。")
        if artifact_type == "closure" and manifest.get("state") not in {"reviewed", "finished"}:
            raise RequirementError("只有评审通过后才能登记复盘收口总结。")
        _upsert_artifact(
            manifest,
            artifact_type,
            relative,
            file_sha256(path),
            "registered",
            test_kind=test_kind,
            result=result,
            acceptance_ids=acceptance_ids,
            document_kind=current.get("ticketKind", "requirement") if artifact_type == "requirement-design" else None,
            validation=design_validation if artifact_type == "requirement-design" else None,
        )
        if artifact_type == "requirement-design":
            _set_state(manifest, "documented")
            _resolve_blockers(manifest, "requirement-design", "已登记需求与设计文档。")
        elif artifact_type == "closure":
            _resolve_blockers(manifest, "closure", "已登记复盘收口总结。")

    manifest = _mutate(root, requirement_id, mutate)
    if test_kind:
        snapshot = capture_scope_snapshot(root)
        manifest = record_test_result(
            root,
            requirement_id,
            test_kind=test_kind,
            result=str(result),
            acceptance_ids=acceptance_ids or [],
            files=files,
            snapshot=snapshot,
            report_path=relative,
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
    if artifact_type not in {"requirement-design", "test", "closure"}:
        raise RequirementError("later 只支持 requirement-design、test 或 closure。")

    def mutate(manifest: dict[str, Any]) -> None:
        allowed = {
            "requirement-design": {"draft", "documented"},
            "test": {"implementing", "verified"},
            "closure": {"reviewed"},
        }
        if manifest.get("state") not in allowed[artifact_type]:
            raise RequirementError(f"当前状态不能将 {artifact_type} 记录为稍后处理。")
        blockers = manifest.setdefault("readiness", {}).setdefault("blockers", [])
        blockers.append({
            "id": f"BLOCK-{len(blockers) + 1:02d}",
            "artifactType": artifact_type,
            "reason": f"{artifact_type} 选择稍后处理。",
            "recordedAt": now_iso(),
            "resolution": None,
            "resolvedAt": None,
        })

    return _mutate(root, requirement_id, mutate)


def ready_requirement(root: Path, requirement_id: str, resolution: str) -> dict[str, Any]:
    clean_resolution = sanitize_text(" ".join(str(resolution or "").split()))
    if not clean_resolution:
        raise RequirementError("进入 ready 必须记录非空的确认或阻塞解决说明。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") != "documented":
            raise RequirementError("只有 documented 状态可以进入 ready。")
        if not manifest.get("acceptanceCriteria"):
            raise RequirementError("需求 manifest 缺少编号验收标准。")
        if not _has_valid_design(root, manifest):
            raise RequirementError("缺少当前有效且验证通过的需求与设计文档。")
        unresolved = [blocker for blocker in manifest.get("readiness", {}).get("blockers", []) if not blocker.get("resolvedAt")]
        if unresolved:
            raise RequirementError("仍有未解决的 readiness 阻塞项：" + ", ".join(str(item.get("id")) for item in unresolved))
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
        unresolved = [item for item in manifest.get("readiness", {}).get("blockers", []) if not item.get("resolvedAt")]
        if unresolved:
            raise RequirementError("仍有未解决的 readiness 阻塞项。")
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


def capture_scope_snapshot(root: Path, exclude_paths: Optional[list[str]] = None) -> dict[str, Any]:
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
    entries = sorted({(item["status"], item["path"], item["sha256"]): item for item in entries}.values(), key=lambda item: (item["path"], item["status"]))
    if code != 0 or commit_code != 0:
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
    # `.project-intel` is already excluded by `_business_path`. Registered
    # artifacts outside that directory must remain visible so a business file
    # cannot disappear from the delivery scope merely by being called a report.
    return capture_scope_snapshot(root)


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
    actual = set(current.get("files", []))
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
    return True


def _test_gate_satisfied(manifest: dict[str, Any]) -> bool:
    all_valid = [item for item in manifest.get("testEvidence", []) if item.get("valid")]
    if not all_valid or all_valid[-1].get("result") not in PASSING_RESULTS:
        return False
    valid = [item for item in all_valid if item.get("result") in PASSING_RESULTS]
    if manifest.get("externalApiImpact", {}).get("value"):
        return any(item.get("testKind") in {"service", "both"} for item in valid)
    return any(item.get("testKind") in {"unit", "service", "both"} or (item.get("testKind") == "manual" and _manual_valid(item.get("manual"))) for item in valid)


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
    manual: Optional[dict[str, Any]] = None,
    project_wide: bool = False,
) -> dict[str, Any]:
    if test_kind not in TEST_KINDS:
        raise RequirementError("test-kind 只能是 unit、service、both 或 manual。")
    if result not in {"passed", "failed"}:
        raise RequirementError("测试结果只能是 passed 或 failed。")
    if test_kind == "manual" and not _manual_valid(manual):
        raise RequirementError("人工测试必须包含审批、原因、步骤、输入、观察结果和截图/日志路径。")
    if test_kind == "manual" and manual is not None:
        _, evidence_relative = _resolve_repo_file(root, str(manual.get("evidencePath") or ""))
        manual = {
            key: value if key == "approved" else evidence_relative if key == "evidencePath" else sanitize_text(str(value or ""))
            for key, value in manual.items()
        }
    current_manifest = load_requirement(root, requirement_id)
    selected = _normalize_scope_files(root, files)
    if report_path:
        report_file, normalized_report_path = _resolve_repo_file(root, report_path)
        _validate_test_report_file(report_file, normalized_report_path)
        if normalized_report_path in selected:
            raise RequirementError("测试报告路径不能同时作为被测试的业务文件范围。")
        report_path = normalized_report_path
    current_snapshot = capture_requirement_scope(root, current_manifest)
    if not current_snapshot.get("gitAvailable") or not current_snapshot.get("diffHash"):
        raise RequirementError("无法读取 Git 状态，不能登记需求级测试证据。")
    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") not in {"implementing", "verified"}:
            raise RequirementError("只有 implementing 或 verified 状态可以登记测试结果。")
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
            "diffHash": current_snapshot.get("diffHash"),
            "evidenceDiffHash": current_snapshot.get("diffHash"),
            "gitCommit": current_snapshot.get("gitCommit"),
            "evidenceCommit": current_snapshot.get("gitCommit"),
            "recordedAt": now_iso(),
            "valid": True,
        }
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
        manifest.setdefault("scopeSnapshots", []).append({"kind": "test", **current_snapshot})
        manifest["currentDiffHash"] = current_snapshot.get("diffHash")
        if report_path:
            path, relative = _resolve_repo_file(root, report_path)
            _upsert_artifact(
                manifest,
                f"{test_kind}-test" if test_kind != "both" else "service-test",
                relative,
                file_sha256(path),
                "registered",
                test_kind=test_kind,
                result=result,
                acceptance_ids=acceptance_ids,
            )
        if result == "failed":
            _set_state(manifest, "implementing")
        elif _test_gate_satisfied(manifest):
            _set_state(manifest, "verified")

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
) -> str:
    path = requirement_dir(root, requirement_id) / "test-report.md"
    if not path.is_file():
        raise RequirementError("尚未生成 test-report.md。")

    def mutate(manifest: dict[str, Any]) -> None:
        current = path.read_text(encoding="utf-8")
        body = (
            current.rstrip()
            + f"\n\n### {now_iso()} · {test_kind}\n\n"
            + f"- 结果：{result}\n"
            + f"- 验收标准：{', '.join(acceptance_ids) or '未映射'}\n"
            + f"- 命令：`{sanitize_text(command) or '人工测试'}`\n\n"
            + "```text\n"
            + (sanitize_text(details).strip() or "无额外输出")
            + "\n```\n"
        )
        _atomic_write(path, body.encode("utf-8"))
        relative = path.relative_to(root).as_posix()
        _upsert_artifact(
            manifest,
            "test",
            relative,
            file_sha256(path),
            "generated",
            status="executed" if result == "passed" else "failed",
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
            "files": selected,
            "diffHash": current_snapshot.get("diffHash"),
            "evidenceDiffHash": current_snapshot.get("diffHash"),
            "gitCommit": current_snapshot.get("gitCommit"),
            "evidenceCommit": current_snapshot.get("gitCommit"),
            "recordedAt": now_iso(),
            "valid": True,
        })
        manifest.setdefault("scopeSnapshots", []).append({"kind": "review", **current_snapshot})
        manifest["currentDiffHash"] = current_snapshot.get("diffHash")
        if effective_result == "passed":
            _set_state(manifest, "reviewed")
        else:
            _set_state(manifest, "verified")

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


def design_validation_status(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    designs = [
        item for item in manifest.get("artifacts", [])
        if item.get("type") == "requirement-design" and item.get("status") not in {"draft", "stale", "failed"}
    ]
    if not designs:
        return {"ok": False, "legacy": False, "errors": ["缺少已登记的需求与设计文档。"]}
    artifact = designs[-1]
    if not _artifact_is_current(root, artifact):
        return {"ok": False, "legacy": False, "errors": ["需求与设计文档不存在或内容哈希已变化。"]}
    validation = artifact.get("validation")
    if not isinstance(validation, dict):
        return {"ok": True, "legacy": True, "warnings": ["该文档由 0.3.0 以前版本登记，重新登记时必须通过新模板校验。"]}
    return {
        "ok": bool(validation.get("ok")),
        "legacy": False,
        "kind": validation.get("kind") or artifact.get("documentKind"),
        "file": artifact.get("path"),
        "errors": list(validation.get("errors") or []),
        "warnings": list(validation.get("warnings") or []),
    }


def _has_valid_design(root: Path, manifest: dict[str, Any]) -> bool:
    return bool(design_validation_status(root, manifest).get("ok"))


def finish_requirement(root: Path, requirement_id: str, *, files: list[str]) -> dict[str, Any]:
    current_manifest = load_requirement(root, requirement_id)
    snapshot = capture_requirement_scope(root, current_manifest)
    selected = validate_scope_selection(root, files, snapshot)

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") != "reviewed":
            raise RequirementError("需求必须先达到 reviewed 状态才能 finish。")
        unresolved_blockers = [item for item in manifest.get("readiness", {}).get("blockers", []) if not item.get("resolvedAt")]
        if unresolved_blockers:
            raise RequirementError("仍有未解决的 readiness 阻塞项。")
        if not _has_valid_design(root, manifest):
            raise RequirementError("缺少当前有效的需求与设计文档。")
        if not _test_gate_satisfied(manifest):
            raise RequirementError("测试类型或通过结果不满足需求门禁。")
        reports = [
            item for item in manifest.get("artifacts", [])
            if item.get("type") in {"test", "unit-test", "service-test", "manual-test"}
            and item.get("result") == "passed"
            and item.get("status") not in {"draft", "stale", "failed"}
        ]
        if not reports or not any(_artifact_is_current(root, item) for item in reports):
            raise RequirementError("缺少当前有效且已通过的测试报告文件。")
        valid_tests = [item for item in manifest.get("testEvidence", []) if item.get("valid") and item.get("result") == "passed"]
        valid_reviews = [item for item in manifest.get("reviewRounds", []) if item.get("valid") and item.get("result") == "passed"]
        if not valid_tests or valid_tests[-1].get("diffHash") != snapshot.get("diffHash"):
            raise RequirementError("测试证据与当前 Git 变更不一致，必须重新测试。")
        actual_files = set(snapshot.get("files", []))
        if actual_files and not any(
            item.get("diffHash") == snapshot.get("diffHash")
            and (item.get("projectWide") or actual_files.issubset(set(item.get("files", []))))
            for item in valid_tests
        ):
            raise RequirementError("测试证据文件范围未覆盖全部实际 Git 变更。")
        if not valid_reviews or valid_reviews[-1].get("diffHash") != snapshot.get("diffHash"):
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
            if evidence.get("diffHash") == snapshot.get("diffHash"):
                covered.update(evidence.get("acceptanceIds", []))
        expected = {item.get("id") for item in manifest.get("acceptanceCriteria", [])}
        if expected - covered:
            raise RequirementError("以下验收标准缺少通过证据：" + ", ".join(sorted(expected - covered)))
        closures = [item for item in manifest.get("artifacts", []) if item.get("type") == "closure" and item.get("status") not in {"stale"}]
        if not closures or not _artifact_is_current(root, closures[-1]):
            raise RequirementError("缺少当前有效的复盘收口总结文件。")
        manifest["currentDiffHash"] = snapshot.get("diffHash")
        manifest.setdefault("scopeSnapshots", []).append({"kind": "finish", **snapshot, "selectedFiles": selected})
        for criterion in manifest.get("acceptanceCriteria", []):
            criterion["status"] = "passed"
        _set_state(manifest, "finished")

    return _mutate(root, requirement_id, mutate)


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
    return current_snapshot


def close_requirement(root: Path, requirement_id: str, *, check_succeeded: bool) -> dict[str, Any]:
    if not check_succeeded:
        raise RequirementError("维护检查失败，需求保持 finished 状态。")

    current_snapshot = validate_finished_freshness(root, requirement_id)

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") != "finished":
            raise RequirementError("只有 finished 状态可以进入 closed。")
        finish_snapshots = [item for item in manifest.get("scopeSnapshots", []) if item.get("kind") == "finish"]
        if finish_snapshots[-1].get("diffHash") != current_snapshot.get("diffHash"):
            raise RequirementError("finish 后代码或 Git 提交发生变化，必须重新测试、评审和 finish。")
        _set_state(manifest, "closed")

    return _mutate(root, requirement_id, mutate)


def reopen_requirement(root: Path, requirement_id: str, reason: str) -> dict[str, Any]:
    clean_reason = sanitize_text(" ".join(str(reason or "").split()))
    if not clean_reason:
        raise RequirementError("reopen 必须记录原因。")

    def mutate(manifest: dict[str, Any]) -> None:
        if manifest.get("state") in {"draft", "documented"}:
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
                artifact.get("type") == "requirement-design"
                and artifact.get("status") not in {"draft", "stale", "failed"}
                and not isinstance(artifact.get("validation"), dict)
            ):
                artifact["status"] = "stale"
                artifact["invalidatedAt"] = now_iso()
                artifact["invalidatedReason"] = "旧版设计在 reopen 后必须按 0.3.0 模板重新验证。"
                legacy_design_invalidated = True
        manifest.setdefault("history", []).append({
            "action": "reopen",
            "fromState": previous,
            "reason": clean_reason,
            "recordedAt": now_iso(),
        })
        manifest["currentDiffHash"] = None
        _set_state(manifest, "documented" if not legacy_design_invalidated and _has_valid_design(root, manifest) else "draft")

    return _mutate(root, requirement_id, mutate)


def status_payload(root: Path, requirement_id: str) -> dict[str, Any]:
    manifest = load_requirement(root, requirement_id)
    unresolved = [item for item in manifest.get("readiness", {}).get("blockers", []) if not item.get("resolvedAt")]
    return {
        "requirementId": manifest.get("requirementId"),
        "requirementName": manifest.get("requirementName"),
        "ticketKind": manifest.get("ticketKind", "requirement"),
        "state": manifest.get("state"),
        "revision": manifest.get("revision"),
        "externalApiImpact": manifest.get("externalApiImpact"),
        "acceptanceCriteria": manifest.get("acceptanceCriteria", []),
        "designArtifact": next(
            (item for item in reversed(manifest.get("artifacts", [])) if item.get("type") == "requirement-design"),
            None,
        ),
        "designValidation": design_validation_status(root, manifest),
        "unresolvedBlockers": unresolved,
        "artifacts": manifest.get("artifacts", []),
        "testGateSatisfied": _test_gate_satisfied(manifest),
        "latestReview": (manifest.get("reviewRounds") or [None])[-1],
        "currentDiffHash": capture_requirement_scope(root, manifest).get("diffHash"),
    }
