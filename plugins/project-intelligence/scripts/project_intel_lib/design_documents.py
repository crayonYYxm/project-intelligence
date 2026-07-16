from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional


class UsageError(RuntimeError):
    pass


HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(?:(?:\d+(?:\\?\.\d+)*)\\?[.、]?\s+)?(.+?)\s*$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")
REQUIREMENT_HEADINGS = (
    "需求问题概述",
    "需求描述",
    "需求提出部门及联系人",
    "电信需求负责人",
    "需求适用范围",
    "需求期望完成时间",
    "设计相关选项",
    "场景分析",
    "风险考虑",
    "实现方案",
    "数据模型",
    "表结构设计",
    "新增模型汇总",
    "表结构描述",
    "建表语句",
    "表数据转储策略",
    "界面设计",
)
REQUIREMENT_FORBIDDEN_HEADINGS = (
    "文档信息",
    "代码现状与影响分析",
    "源码证据",
    "调用链",
    "文件和符号级改动",
    "兼容性与异常处理",
    "风险观测与回滚",
    "测试设计",
    "验收标准",
    "差异与待确认事项",
)
REQUIREMENT_OPTION_FIELDS = (
    "任务类型",
    "需求协调人",
    "设计负责人",
    "涉及中心",
    "评审模式",
    "模型变动",
    "代码走查",
    "接口变动",
    "界面变动",
    "是否联调",
)
BUG_HEADINGS = (
    "bug现象",
    "原因分析",
    "修复方案",
    "改造思路",
    "新旧代码对照",
    "逻辑变更说明",
    "影响范围",
    "风险评估",
)
BUG_FORBIDDEN_HEADINGS = (
    "文档信息",
    "代码现状与影响分析",
    "源码证据",
    "接口设计",
    "数据模型",
    "界面设计",
    "测试设计",
    "验收标准",
    "差异与待确认事项",
)
BUG_MAX_LINES = 140
PLACEHOLDER_PATTERNS = (
    ("TODO/TBD/FIXME", re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.I)),
    ("模板标记", re.compile(r"※[^※\n]+※")),
    ("待填写文本", re.compile(r"(?:待填写|待补充|请填写|在此填写)")),
)
STRONG_SENSITIVE_PATTERNS = (
    ("Bearer 凭据", re.compile(r"\bBearer\s+(?!<|\*|REDACTED\b)[A-Za-z0-9._~+/=-]{12,}", re.I)),
    ("URL 内嵌凭据", re.compile(r"://[^/\s:@]+:[^/\s@]+@")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("私钥", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("身份证号", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("partyId 实值", re.compile(r'''(?i)["']?partyId["']?\s*[:=]\s*["']?\d{6,}''')),
)
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r'''(?i)\b(authorization|cookie|password|passwd|secret|api[_-]?key|'''
    r'''access[_-]?token|refresh[_-]?token)\b\s*[:=]\s*["']?([^\s,"'}]+)'''
)
SAFE_VALUE_MARKERS = ("<", "${", "***", "redacted", "masked", "example", "示例", "虚构", "待确认")


def normalize_heading(value: str) -> str:
    value = re.sub(r"[*_~]", "", value)
    value = re.sub(r"^\d+(?:\\?\.\d+)*\\?[.、]?\s*", "", value)
    return re.sub(r"[\s，,、/／:：\-—_]+", "", value).lower()


def parse_headings(lines: list[str]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            headings.append({
                "level": len(match.group(1)),
                "name": match.group(2).strip(),
                "normalized": normalize_heading(match.group(2)),
                "start": index,
                "end": len(lines),
            })
    for index, heading in enumerate(headings):
        for next_heading in headings[index + 1 :]:
            if next_heading["level"] <= heading["level"]:
                heading["end"] = next_heading["start"]
                break
    return headings


def find_heading(headings: list[dict[str, Any]], normalized_name: str) -> Optional[dict[str, Any]]:
    return next((item for item in headings if item["normalized"] == normalized_name), None)


def section_text(lines: list[str], heading: Optional[dict[str, Any]]) -> str:
    if heading is None:
        return ""
    return "\n".join(lines[heading["start"] + 1 : heading["end"]]).strip()


def has_meaningful_content(value: str) -> bool:
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped or HEADING_RE.match(stripped) or TABLE_SEPARATOR_RE.match(stripped):
            continue
        if re.search(r"[A-Za-z0-9\u4e00-\u9fff]", stripped):
            return True
    return False


def resolve_repo(value: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.exists() or not candidate.is_dir():
        raise UsageError(f"目标仓库不存在或不是目录：{value}")
    result = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise UsageError(f"目标路径不是 Git 仓库：{value}")
    return Path(result.stdout.strip()).resolve(strict=True)


def resolve_document(value: str, repo: Path) -> tuple[Path, str]:
    candidate = Path(value).expanduser()
    path = candidate if candidate.is_absolute() else repo / candidate
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(repo).as_posix()
    except (OSError, ValueError) as exc:
        raise UsageError(f"设计文档不存在或位于目标仓库之外：{value}") from exc
    if not resolved.is_file() or resolved.suffix.lower() != ".md" or resolved.stat().st_size <= 0:
        raise UsageError(f"设计文档必须是仓库内非空的 Markdown 文件：{value}")
    return resolved, relative


def infer_kind(text: str, headings: list[dict[str, Any]], requested: str) -> tuple[Optional[str], list[str]]:
    errors: list[str] = []
    has_bug = (
        find_heading(headings, normalize_heading("BUG 现象")) is not None
        or re.search(r"(?im)^#\s+bug[^\s]*\s+", text) is not None
    )
    has_requirement = find_heading(headings, normalize_heading("场景分析")) is not None
    if requested != "auto":
        return requested, errors
    if has_bug == has_requirement:
        errors.append("无法唯一识别 Bug 或 Requirement；请补充单据类型和对应条件章节。")
        return None, errors
    return ("bug" if has_bug else "requirement"), errors


def inline_code_values(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"`([^`\n]+)`", text)]


def source_evidence_values(text: str) -> list[str]:
    ignored = {"待确认", "不涉及", "无", "none", "n/a"}
    return [value for value in inline_code_values(text) if value.strip().lower() not in ignored]


def check_sensitive_content(text: str, errors: list[str]) -> None:
    for label, pattern in STRONG_SENSITIVE_PATTERNS:
        if pattern.search(text):
            errors.append(f"检测到未脱敏的敏感信息：{label}。")
    for match in CREDENTIAL_ASSIGNMENT_RE.finditer(text):
        value = match.group(2).strip().lower()
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        line = text[line_start : len(text) if line_end < 0 else line_end].lower()
        if not any(marker in value or marker in line for marker in SAFE_VALUE_MARKERS):
            errors.append(f"检测到未脱敏的敏感字段赋值：{match.group(1)}。")


def collect_sections(
    lines: list[str],
    headings: list[dict[str, Any]],
    required: tuple[str, ...],
    errors: list[str],
) -> dict[str, str]:
    sections: dict[str, str] = {}
    for name in required:
        aliases = (name, "新旧代码完整对照") if name == "新旧代码对照" else (name,)
        heading = None
        for alias in aliases:
            heading = find_heading(headings, normalize_heading(alias))
            if heading is not None:
                break
        if heading is None:
            errors.append(f"缺少必选章节：{name}。")
            continue
        body = section_text(lines, heading)
        sections[name] = body
        if not has_meaningful_content(body):
            errors.append(f"必选章节为空：{name}。")
    return sections


def safe_filename_component(value: str) -> str:
    clean = re.sub(r"[\\/\x00-\x1f\x7f]+", "-", str(value or "").strip())
    return re.sub(r"\s+", "", clean).strip("-._") or "未命名"


def design_filename(identifier: str, name: str, kind: str) -> str:
    safe_name = safe_filename_component(name)
    if kind == "bug":
        return f"{identifier}-{safe_name}-设计文档.md"
    return f"{identifier}_{safe_name}_设计文档.md"


def validate_bug(
    text: str,
    lines: list[str],
    headings: list[dict[str, Any]],
    relative: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    sections = collect_sections(lines, headings, BUG_HEADINGS, errors)
    filename = Path(relative).name
    title_match = re.search(r"(?im)^#\s+(\S+)\s+(.+?)\s*$", text)
    if title_match is None:
        errors.append("Bug 文档标题必须使用“# <Bug 编号> <名称>”。")
    else:
        title_id, title_name = title_match.group(1), title_match.group(2)
        if title_id.isdigit():
            errors.append("纯数字 Bug 编号必须补 bug 前缀，例如 bug56925。")
        expected_filename = design_filename(title_id, title_name, "bug")
        if filename != expected_filename:
            errors.append(f"Bug 文件名与标题不一致；应为 {expected_filename}。")
    if len(lines) > BUG_MAX_LINES:
        errors.append(f"Bug 文档超过 {BUG_MAX_LINES} 行；请按五段式精简模板压缩。")
    for name in BUG_FORBIDDEN_HEADINGS:
        if find_heading(headings, normalize_heading(name)) is not None:
            errors.append(f"Bug 精简版不应包含需求型章节：{name}。")
    if not source_evidence_values(text) and "```" not in text:
        errors.append("Bug 原因或修复方案至少需要一个源码符号或最小代码对照。")
    risk = sections.get("风险评估", "")
    for field in ("风险等级", "极端预测", "紧急举措"):
        if field not in risk:
            errors.append(f"风险评估缺少字段：{field}。")
    if "mermaid" in text.lower():
        warnings.append("Bug 精简版默认不需要 Mermaid；确认该图确实不可由短段落替代。")


def validate_requirement(
    text: str,
    lines: list[str],
    headings: list[dict[str, Any]],
    relative: str,
    errors: list[str],
) -> None:
    sections = collect_sections(lines, headings, REQUIREMENT_HEADINGS, errors)
    filename = Path(relative).name
    if not filename.endswith("_设计文档.md"):
        errors.append("Requirement 文件名必须使用“<需求号>_<名称>_设计文档.md”格式。")
    title_match = re.search(r"(?im)^#\s+(.+_设计文档)\s*$", text)
    if title_match is None:
        errors.append("Requirement 标题必须使用“# <需求号>_<名称>_设计文档”。")
    else:
        title_value = title_match.group(1)
        identifier = title_value.split("_", 1)[0]
        if identifier.isdigit():
            errors.append("纯数字 Requirement 编号必须补 req 前缀，例如 req73822。")
        expected_filename = f"{title_value}.md"
        if filename != expected_filename:
            errors.append(f"Requirement 文件名与标题不一致；应为 {expected_filename}。")
    for label in ("江苏电信BSS项目", "文档更改记录"):
        if label not in text:
            errors.append(f"Requirement 封面缺少：{label}。")
    if re.search(r"\b\d{4}年\d{1,2}月\b", text) is None:
        errors.append("Requirement 封面缺少 YYYY年MM月 格式日期。")
    for field in ("版本", "日期", "描述", "修改人"):
        if field not in text:
            errors.append(f"文档更改记录缺少字段：{field}。")
    option_section = sections.get("设计相关选项", "")
    for field in REQUIREMENT_OPTION_FIELDS:
        if field not in option_section:
            errors.append(f"设计相关选项缺少字段：{field}。")
    scene_matches = [item for item in headings if item["normalized"] == normalize_heading("场景分析")]
    if len(scene_matches) < 2 or not any(item["level"] == 1 for item in scene_matches) or not any(item["level"] == 2 for item in scene_matches):
        errors.append("场景分析必须同时保留一级章节和二级同名章节。")
    if "紧急方案" not in sections.get("风险考虑", ""):
        errors.append("风险考虑必须包含紧急方案。")
    if not source_evidence_values(sections.get("实现方案", "")):
        errors.append("Requirement 实现方案至少需要一个真实的仓库相对路径、接口或源码符号。")
    for name in REQUIREMENT_FORBIDDEN_HEADINGS:
        if find_heading(headings, normalize_heading(name)) is not None:
            errors.append(f"Requirement 样例复刻版不应新增章节：{name}。")


def _validate_identity(
    text: str,
    relative: str,
    kind: Optional[str],
    expected_id: Optional[str],
    expected_name: Optional[str],
    errors: list[str],
) -> None:
    if not kind or not expected_id or expected_name is None:
        return
    expected_file = design_filename(expected_id, expected_name, kind)
    if Path(relative).name != expected_file:
        label = "Bug 编号" if kind == "bug" else "需求号"
        errors.append(f"设计文档文件名与 manifest {label}/名称不一致；应为 {expected_file}。")
    expected_title = f"# {expected_id} {expected_name}" if kind == "bug" else f"# {expected_id}_{expected_name}_设计文档"
    if expected_title not in text.splitlines():
        errors.append("设计文档标题与 manifest 中的编号或名称不一致。")


def validate(
    text: str,
    repo: Path,
    relative: str,
    requested_kind: str,
    *,
    expected_id: Optional[str] = None,
    expected_name: Optional[str] = None,
) -> dict[str, Any]:
    del repo
    lines = text.splitlines()
    headings = parse_headings(lines)
    errors: list[str] = []
    warnings: list[str] = []
    kind, kind_errors = infer_kind(text, headings, requested_kind)
    errors.extend(kind_errors)
    if kind == "bug":
        validate_bug(text, lines, headings, relative, errors, warnings)
    elif kind == "requirement":
        validate_requirement(text, lines, headings, relative, errors)
    _validate_identity(text, relative, kind, expected_id, expected_name, errors)
    for label, pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            errors.append(f"检测到遗留占位内容：{label}。")
    check_sensitive_content(text, errors)
    return {
        "ok": not errors,
        "kind": kind,
        "file": relative,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def requirement_scaffold(identifier: str, name: str) -> str:
    today = date.today()
    return f"""# {identifier}_{name}_设计文档

**江苏电信BSS项目**

**{name}**

**{today.year:04d}年{today.month:02d}月**

**文档更改记录**

| **版本** | **日期** | **描述** | **修改人** |
|---|---|---|---|
| 0.1 | {today.isoformat()} | 初稿脚手架 | 待确认 |

# 需求/问题概述

## 需求描述

待确认。

## 需求提出部门及联系人

待确认。

## 电信需求负责人

待确认。

## 需求适用范围

待确认。

## 需求期望完成时间

待确认。

# 设计相关选项

| 任务类型 | 需求 | 需求协调人 | 待确认 |
|---|---|---|---|
| 设计负责人 | 待确认 | 涉及中心 | 待确认 |
| 评审模式 | 待确认 | 模型变动 | 待确认 |
| 代码走查 | 待确认 | 接口变动 | 待确认 |
| 界面变动 | 待确认 | 是否联调 | 待确认 |

# 场景分析

## 场景分析

待确认。

## 风险考虑

待确认。

紧急方案：

待确认。

# 实现方案

待确认。

# 数据模型

## 5.1表结构设计

待确认。

## 5.2新增模型汇总

待确认。

## 5.3表结构描述

待确认。

## 5.4建表语句

待确认。

## 5.5表数据转储策略

待确认。

# 界面设计

待确认。
"""


def bug_scaffold(identifier: str, name: str) -> str:
    return f"""# {identifier} {name}

## 1 BUG 现象

待确认。

## 2 原因分析

待确认源码符号：`待确认`。

## 3 修复方案

### 3.1 改造思路

待确认。

### 3.2 新旧代码对照

待确认。

### 3.3 逻辑变更说明

待确认。

## 4 影响范围

待确认。

## 5 风险评估

**风险等级**：待确认

**极端预测**：待确认。

**紧急举措**：待确认。
"""


def scaffold_text(identifier: str, name: str, kind: str) -> str:
    return bug_scaffold(identifier, name) if kind == "bug" else requirement_scaffold(identifier, name)


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {payload.get('file', '-')}")
    if payload.get("kind"):
        print(f"Kind: {payload['kind']}")
    for item in payload.get("errors", []):
        print(f"ERROR: {item}")
    for item in payload.get("warnings", []):
        print(f"WARNING: {item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a source-backed development design document.")
    parser.add_argument("--file", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--kind", choices=("auto", "bug", "requirement"), default="auto")
    parser.add_argument("--expected-id")
    parser.add_argument("--expected-name")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo = resolve_repo(args.repo)
        path, relative = resolve_document(args.file, repo)
        text = path.read_text(encoding="utf-8")
    except (UsageError, OSError, UnicodeError) as exc:
        payload = {"ok": False, "kind": None, "file": str(args.file), "errors": [str(exc)], "warnings": []}
        emit(payload, args.as_json)
        return 2
    payload = validate(
        text,
        repo,
        relative,
        args.kind,
        expected_id=args.expected_id,
        expected_name=args.expected_name,
    )
    emit(payload, args.as_json)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
