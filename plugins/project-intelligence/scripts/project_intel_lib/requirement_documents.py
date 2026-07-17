from __future__ import annotations

import re
from typing import Any, Optional

from . import design_documents


COMMON_SECTIONS = (
    "文档信息",
    "背景与现状",
    "目标",
    "业务场景",
    "范围",
    "非目标",
    "业务规则与异常边界",
    "验收标准",
    "外部接口影响",
    "待确认事项",
)

BUG_SECTIONS = (
    "复现条件",
    "当前行为",
    "预期行为",
)


def scaffold_text(identifier: str, name: str, kind: str) -> str:
    kind_label = "Bug" if kind == "bug" else "Requirement"
    bug_sections = ""
    if kind == "bug":
        bug_sections = """
## 复现条件

※请补充可复现前置条件和操作步骤※

## 当前行为

※请补充当前错误行为※

## 预期行为

※请补充修复后的目标行为※

"""
    return f"""# {identifier} {name} 需求文档

## 文档信息

- 需求号：`{identifier}`
- 需求名称：{name}
- 单据类型：{kind_label}

## 背景与现状

※请补充业务背景和当前行为※

## 目标

※请补充可验证的目标行为※

## 业务场景

※请补充主要场景、参与方和触发条件※

## 范围

※请补充本次包含的范围※

## 非目标

※请补充明确不包含的范围；确实没有时写“无”并说明依据※

{bug_sections}## 业务规则与异常边界

※请补充业务规则、权限、状态和异常边界※

## 验收标准

※请使用 AC-01、AC-02 格式列出验收标准※

## 外部接口影响

※请说明是否影响对外接口及确认依据※

## 待确认事项

※请列出待确认事项；没有时写“无”※
"""


def _acceptance_ids(text: str) -> set[str]:
    return {item.upper() for item in re.findall(r"\bAC-\d{2,}\b", text, re.I)}


DOCUMENT_INFO_RE = re.compile(
    r"^\s*[-*]\s*(需求号|需求名称|单据类型)\s*[:：]\s*(.*?)\s*$",
    re.I,
)
AC_LINE_RE = re.compile(r"^\s*[-*]\s*(AC-\d{2,})\s*[:：]\s*(.*?)\s*$", re.I)
PENDING_MARKER_RE = re.compile(r"(?:待|需|仍需|尚需)(?:确认|补充|澄清|决定)|未确认|未提供|未取得|无法核验")
NO_PENDING_RE = re.compile(r"^(?:无|没有|不涉及|无待确认事项)(?:[\s，,。；;:：]|$)")


def _plain_value(value: str) -> str:
    return re.sub(r"[*_~`]", "", value).strip()


def _parse_document_info(body: str, errors: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in body.splitlines():
        match = DOCUMENT_INFO_RE.match(line)
        if not match:
            continue
        key, value = match.group(1), _plain_value(match.group(2))
        if key in values:
            errors.append(f"文档信息字段重复：{key}。")
            continue
        values[key] = value
    for key in ("需求号", "需求名称", "单据类型"):
        if not values.get(key):
            errors.append(f"文档信息缺少字段：{key}。")
    return values


def _normalize_kind(value: str) -> Optional[str]:
    normalized = re.sub(r"[\s_-]+", "", value).lower()
    if normalized in {"bug", "defect", "缺陷", "故障"}:
        return "bug"
    if normalized in {"requirement", "req", "需求"}:
        return "requirement"
    return None


def _parse_acceptance_criteria(body: str, errors: list[str]) -> dict[str, str]:
    criteria: dict[str, str] = {}
    for line in body.splitlines():
        match = AC_LINE_RE.match(line)
        if not match:
            if re.search(r"\bAC-\d+\b", line, re.I):
                errors.append(f"验收标准格式无效：{line.strip()}。")
            continue
        identifier = match.group(1).upper()
        description = _plain_value(match.group(2))
        if identifier in criteria:
            errors.append(f"验收标准编号重复：{identifier}。")
        elif not description:
            errors.append(f"验收标准描述不能为空：{identifier}。")
        else:
            criteria[identifier] = description
    if not criteria:
        errors.append("需求文档至少需要一项带非空描述的验收标准。")
    return criteria


def _expected_criteria(
    acceptance_ids: list[str],
    acceptance_criteria: Optional[list[dict[str, Any]]],
) -> tuple[set[str], dict[str, str]]:
    descriptions: dict[str, str] = {}
    if acceptance_criteria is not None:
        for item in acceptance_criteria:
            if not isinstance(item, dict):
                continue
            identifier = str(item.get("id") or "").strip().upper()
            description = _plain_value(str(item.get("description") or ""))
            if identifier:
                descriptions[identifier] = description
    identifiers = {
        str(item).strip().upper()
        for item in acceptance_ids
        if str(item).strip()
    }
    identifiers.update(descriptions)
    return identifiers, descriptions


def _parse_external_api_impact(body: str) -> tuple[Optional[bool], bool]:
    compact = re.sub(r"\s+", "", body)
    if not compact:
        return None, False
    negative = bool(re.search(r"不影响(?:对外|外部)接口|(?:对外|外部)接口无影响|不涉及(?:对外|外部)接口|仅调整内部|确认为否|(?:^|[:：])否(?:[;；。，,]|$)", compact))
    positive = bool(re.search(r"(?<!不)(?:影响|涉及)(?:对外|外部)接口|新增(?:对外|外部)接口|修改(?:对外|外部)接口|确认为是|(?:^|[:：])是(?:[;；。，,]|$)", compact))
    if negative and positive:
        return None, True
    if negative:
        return False, False
    if positive:
        return True, False
    return None, False


def _pending_blockers(body: str) -> list[str]:
    compact = " ".join(line.strip() for line in body.splitlines() if line.strip())
    if not compact:
        return ["待确认事项章节为空。"]
    if NO_PENDING_RE.match(compact) and not PENDING_MARKER_RE.search(compact):
        return []
    return [f"待确认事项未解决：{compact[:240]}"]


def _critical_content_blockers(sections: dict[str, str]) -> list[str]:
    blockers: list[str] = []
    for name, body in sections.items():
        if name == "待确认事项":
            continue
        for line in body.splitlines():
            compact = line.strip()
            if not compact or not PENDING_MARKER_RE.search(compact):
                continue
            if re.search(r"(?:无需|不需|已确认|已补充|已澄清)", compact):
                continue
            blockers.append(f"关键内容未确认（{name}）：{compact[:200]}")
    return list(dict.fromkeys(blockers))


def validate(
    text: str,
    *,
    kind: str,
    expected_id: str,
    expected_name: str,
    acceptance_ids: list[str],
    acceptance_criteria: Optional[list[dict[str, Any]]] = None,
    expected_external_api: Optional[bool] = None,
) -> dict[str, Any]:
    lines = text.splitlines()
    headings = design_documents.parse_headings(lines)
    errors: list[str] = []
    warnings: list[str] = []
    required = COMMON_SECTIONS + (BUG_SECTIONS if kind == "bug" else ())
    sections = design_documents.collect_sections(lines, headings, required, errors)
    title = next((line.strip() for line in lines if line.strip().startswith("# ")), "")
    expected_title = f"# {expected_id} {expected_name} 需求文档"
    if title != expected_title:
        errors.append(f"需求文档标题与 manifest 不一致；应为“{expected_title}”。")

    info = _parse_document_info(sections.get("文档信息", ""), errors)
    if info.get("需求号") and info["需求号"] != expected_id:
        errors.append(f"文档信息中的需求号与 manifest 不一致：{info['需求号']}。")
    if info.get("需求名称") and info["需求名称"] != expected_name:
        errors.append("文档信息中的需求名称与 manifest 不一致。")
    document_kind = _normalize_kind(info.get("单据类型", ""))
    if info.get("单据类型") and document_kind is None:
        errors.append("文档信息中的单据类型只能是 Bug 或 Requirement。")
    elif document_kind is not None and document_kind != kind:
        errors.append("文档信息中的单据类型与 manifest 不一致。")

    present_criteria = _parse_acceptance_criteria(sections.get("验收标准", ""), errors)
    present_ids = set(present_criteria)
    expected_ids, expected_descriptions = _expected_criteria(acceptance_ids, acceptance_criteria)
    missing = sorted(expected_ids - present_ids)
    if missing:
        errors.append("需求文档缺少验收标准：" + ", ".join(missing) + "。")
    extra = sorted(present_ids - expected_ids)
    if extra:
        errors.append("需求文档包含 manifest 未登记的验收标准：" + ", ".join(extra) + "。")
    for identifier in sorted(expected_ids & present_ids):
        if identifier in expected_descriptions and present_criteria[identifier] != expected_descriptions[identifier]:
            errors.append(f"验收标准 {identifier} 的描述与 manifest 不一致。")

    external_api_impact, external_api_conflict = _parse_external_api_impact(sections.get("外部接口影响", ""))
    if external_api_conflict:
        errors.append("外部接口影响同时包含“影响”和“不影响”的矛盾描述，必须明确消歧。")
    elif external_api_impact is None:
        errors.append("外部接口影响必须明确写明“影响”或“不影响”及依据。")
    elif expected_external_api is not None and external_api_impact is not expected_external_api:
        errors.append("需求文档的外部接口影响与 manifest 不一致。")

    blocking_issues = _pending_blockers(sections.get("待确认事项", ""))
    blocking_issues.extend(_critical_content_blockers(sections))
    blocking_issues = list(dict.fromkeys(blocking_issues))
    errors.extend(blocking_issues)
    for label, pattern in design_documents.PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"存在未完成内容：{label}。")
    design_documents.check_sensitive_content(text, errors)
    return {
        "ok": not errors,
        "kind": kind,
        "errors": list(dict.fromkeys(errors)),
        "warnings": warnings,
        "acceptanceIds": sorted(present_ids),
        "acceptanceCriteria": [
            {"id": identifier, "description": present_criteria[identifier]}
            for identifier in sorted(present_criteria)
        ],
        "documentIdentity": {
            "requirementId": info.get("需求号"),
            "requirementName": info.get("需求名称"),
            "ticketKind": document_kind,
            "externalApiImpact": external_api_impact,
        },
        "blockingIssues": blocking_issues,
    }
