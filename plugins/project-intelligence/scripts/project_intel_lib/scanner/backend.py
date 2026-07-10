from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Callable

from ..core import IncrementalScanCache, file_signature


BACKEND_SUFFIXES = {".java", ".kt", ".py", ".go", ".ts", ".js"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".properties", ".xml"}


def unique_limited(items: list[Any], limit: int = 40) -> list[Any]:
    values: list[Any] = []
    seen: set[str] = set()
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if not key or key in seen:
            continue
        seen.add(key)
        values.append(item)
        if len(values) >= limit:
            break
    return values


def flatten_regex_hits(hits: list[Any]) -> list[str]:
    values: list[str] = []
    for hit in hits:
        if isinstance(hit, tuple):
            values.extend(str(part) for part in hit if part)
        elif hit:
            values.append(str(hit))
    return unique_limited(values)


def annotation_values(text: str, names: str) -> list[str]:
    values: list[str] = []
    for args in re.findall(rf"@(?:{names})\s*(?:\(([^)]*)\))?", text, re.S):
        if not args:
            values.append("")
            continue
        values.extend(re.findall(r"['\"]([^'\"]+)['\"]", args))
        values.extend(re.findall(r"\bvalue\s*=\s*([^,\n)]+)", args))
    return unique_limited([value.strip() for value in values if value is not None])


def python_ast_facts(text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"parser": "regex-fallback", "methods": [], "classes": [], "routes": []}
    methods: list[str] = []
    classes: list[str] = []
    routes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(node.name)
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not decorator.args:
                    continue
                func = decorator.func
                attr = func.attr if isinstance(func, ast.Attribute) else ""
                if attr in {"get", "post", "put", "delete", "patch", "route"}:
                    value = decorator.args[0]
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        routes.append(value.value)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {
        "parser": "python-ast",
        "methods": unique_limited(methods),
        "classes": unique_limited(classes),
        "routes": unique_limited(routes),
    }


def detect_backend_framework(path: str, text: str) -> str:
    if re.search(r"@(RestController|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|Service|Repository|Mapper|Transactional|Scheduled|MessageListener|KafkaListener|RabbitListener)\b", text):
        return "Spring"
    if re.search(r"@(Controller|Get|Post|Put|Delete|Patch|Injectable|UseGuards|MessagePattern|Cron)\b", text):
        return "NestJS"
    if re.search(r"\b(router|app|server)\.(get|post|put|delete|patch|use|route)\s*\(", text):
        return "Express/Koa/Fastify"
    if re.search(r"@(app|router|bp)\.(get|post|put|delete|patch|route)\s*\(", text):
        return "FastAPI/Flask"
    if re.search(r"\b(?:urlpatterns\s*=|path\s*\(|re_path\s*\(|APIView|ViewSet|ModelViewSet)\b", text):
        return "Django"
    if re.search(r"\b(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]", text):
        return "Go Gin"
    if path.endswith(".xml"):
        return "Mapper XML"
    return "Unknown"


def extract_backend_endpoints(text: str, ast_facts: dict[str, Any] | None = None) -> list[str]:
    endpoints: list[str] = list((ast_facts or {}).get("routes", []))
    endpoints.extend(annotation_values(text, r"RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping"))
    endpoints.extend(annotation_values(text, r"Controller"))
    endpoints.extend(re.findall(r"\b(?:router|app|server)\.(?:get|post|put|delete|patch|use|route)\s*\(\s*['\"]([^'\"]+)['\"]", text))
    endpoints.extend(re.findall(r"@(?:app|router|bp)\.(?:get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]", text))
    endpoints.extend(re.findall(r"\b(?:GET|POST|PUT|DELETE|PATCH)\s*\(\s*['\"]([^'\"]+)['\"]", text))
    endpoints.extend(re.findall(r"\b(?:HandleFunc|Handle|path|re_path)\s*\(\s*['\"]([^'\"]+)['\"]", text))
    return unique_limited([item.strip() for item in endpoints if item.strip()])


def extract_backend_methods(text: str, suffix: str, ast_facts: dict[str, Any] | None = None) -> list[str]:
    if suffix == ".py" and ast_facts and ast_facts.get("methods"):
        return unique_limited(ast_facts["methods"])
    names: list[str] = []
    if suffix in {".java", ".kt"}:
        names.extend(re.findall(r"\b(?:public|private|protected)\s+(?:static\s+)?(?:[\w<>\[\], ?]+\s+)+([A-Za-z_$][\w$]*)\s*\(", text))
    if suffix in {".ts", ".js"}:
        names.extend(re.findall(r"\b(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*[{:]?", text))
    if suffix == ".py":
        names.extend(re.findall(r"\bdef\s+([A-Za-z_][\w]*)\s*\(", text))
    if suffix == ".go":
        names.extend(re.findall(r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_][\w]*)\s*\(", text))
    return unique_limited([name for name in names if name not in {"if", "for", "while", "switch", "catch"}])


def extract_backend_fields(text: str, suffix: str) -> list[str]:
    fields: list[str] = []
    if suffix in {".java", ".kt"}:
        fields.extend(re.findall(r"\b(?:private|protected|public)\s+(?:final\s+)?[\w<>\[\], ?]+\s+([A-Za-z_$][\w$]*)\s*[;=]", text))
    if suffix in {".ts", ".js"}:
        fields.extend(re.findall(r"\b([A-Za-z_$][\w$]*)\??\s*:\s*(?:string|number|boolean|Date|Array|Record|[A-Z][\w<>]*)", text))
    if suffix == ".py":
        fields.extend(re.findall(r"^\s*([A-Za-z_][\w]*)\s*:\s*[\w\[\].\"']+", text, re.M))
    if suffix == ".go":
        fields.extend(re.findall(r"^\s*([A-Z][A-Za-z0-9_]*)\s+[\w\[\]*.]+", text, re.M))
    return unique_limited(fields)


def extract_repository_methods(text: str, suffix: str, ast_facts: dict[str, Any] | None = None) -> list[str]:
    names = extract_backend_methods(text, suffix, ast_facts)
    if suffix == ".xml":
        names.extend(re.findall(r"\b(?:select|insert|update|delete)\b[^>]*\bid\s*=\s*['\"]([^'\"]+)['\"]", text, re.I))
    names.extend(re.findall(r"\b(?:find|query|get|select|insert|update|delete|save|remove)[A-Z][A-Za-z0-9_]*\b", text))
    return unique_limited(names, 50)


def extract_sql_ops(text: str) -> list[str]:
    return unique_limited([op.upper() for op in re.findall(r"\b(SELECT|INSERT|UPDATE|DELETE|MERGE)\b", text, re.I)], 10)


def extract_config_keys(text: str, suffix: str) -> list[str]:
    keys: list[str] = []
    if suffix == ".properties":
        keys.extend(re.findall(r"^\s*([A-Za-z0-9_.-]+)\s*=", text, re.M))
    elif suffix in {".yaml", ".yml"}:
        keys.extend(re.findall(r"^\s*([A-Za-z0-9_.-]+)\s*:", text, re.M))
    elif suffix == ".xml":
        keys.extend(re.findall(r"\b(?:id|name|key)\s*=\s*['\"]([^'\"]+)['\"]", text))
    keys.extend(re.findall(r"@Value\s*\(\s*['\"]\$\{([^}:]+)", text))
    keys.extend(re.findall(r"@ConfigurationProperties\s*\(\s*(?:prefix\s*=\s*)?['\"]([^'\"]+)['\"]", text))
    keys.extend(re.findall(r"process\.env\.([A-Z0-9_]+)", text))
    return unique_limited(keys, 60)


def extract_signals(text: str, patterns: list[str], limit: int = 30) -> list[str]:
    values: list[str] = []
    for pattern in patterns:
        values.extend(flatten_regex_hits(re.findall(pattern, text)))
    return unique_limited([value.strip() for value in values if value], limit)


def extract_permission_signals(text: str) -> list[str]:
    return extract_signals(text, [
        r"@(?:PreAuthorize|PostAuthorize|Secured|RolesAllowed|RequiresPermissions|SaCheckPermission|PermitAll|UseGuards)\b[^\n\r{;]*",
        r"\b(?:hasPermission|checkPermission|checkAuth|authorize|isAuthorized)\s*\(",
        r"\b(?:jwt|token|session|principal|SecurityContext|AuthGuard|CanActivate)\b",
    ])


def extract_transaction_signals(text: str) -> list[str]:
    return extract_signals(text, [
        r"@Transactional\b(?:\([^)]*\))?",
        r"\b(?:TransactionTemplate|DataSourceTransactionManager|EntityManager|UnitOfWork)\b",
        r"\b(?:transaction|withTransaction|db\.transaction|sequelize\.transaction)\s*\(",
    ])


def extract_remote_call_signals(text: str) -> list[str]:
    return extract_signals(text, [
        r"@FeignClient\b(?:\([^)]*\))?",
        r"@(?:DubboReference|Reference|GrpcClient)\b(?:\([^)]*\))?",
        r"\b(?:RestTemplate|WebClient|Feign|HttpClient|OkHttpClient|ServiceMeshAdapter|grpc|requests\.|axios|fetch)\b",
        r"\b(?:call|invoke|proxy|exchange|getForObject|postForObject)\s*\(",
    ])


def extract_message_job_signals(text: str) -> list[str]:
    return extract_signals(text, [
        r"@(?:Scheduled|KafkaListener|RabbitListener|JmsListener|MessageListener|SqsListener|EventListener|Cron|MessagePattern)\b(?:\([^)]*\))?",
        r"\b(?:Queue|Topic|Consumer|Producer|BullMQ|agenda|cron|schedule)\b",
    ])


def extract_error_code_signals(text: str) -> list[str]:
    values: list[str] = []
    values.extend(re.findall(r"\b(?:ErrorCode|ErrCode|ResultCode|ResponseCode)\.([A-Z0-9_]+)", text))
    values.extend(re.findall(r"\b([A-Z][A-Z0-9_]*(?:_ERROR|_FAILED|_FAIL|_INVALID|_NOT_FOUND|_DENIED))\b", text))
    values.extend(re.findall(r"['\"]([A-Z]\d{3,}|[BE]\d{3,}|ERR[_-][A-Z0-9_-]+)['\"]", text))
    values.extend(re.findall(r"\bthrow\s+new\s+([A-Za-z_$][\w$]*(?:Exception|Error))\b", text))
    values.extend(re.findall(r"@ResponseStatus\s*\(([^)]*)\)", text))
    return unique_limited([value.strip() for value in values if value], 40)


def extract_exported_functions(text: str) -> list[str]:
    names = re.findall(r"\bexport\s+const\s+([A-Za-z_$][\w$]*)\s*=", text)
    names += re.findall(r"\bexport\s+function\s+([A-Za-z_$][\w$]*)\s*\(", text)
    return unique_limited(names, 80)


def scan_backend_file(
    path: Path,
    rel_path: str,
    text: str,
    configured_entrypoints: list[str],
) -> dict[str, Any]:
    suffix = path.suffix.lower()
    lower = rel_path.lower()
    facts = {key: [] for key in (
        "apis", "services", "dataTypes", "repositories", "configs", "permissionChecks",
        "transactions", "remoteCalls", "messagesJobs", "errorCodes", "utilities", "candidateEntrypoints",
    )}
    ast_facts = python_ast_facts(text) if suffix == ".py" else {"parser": "regex-fallback", "methods": [], "routes": []}
    mapper_xml = suffix == ".xml" and ("<mapper" in text.lower() or "/mapper" in lower)
    route_pattern = r"@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|MessageListener|Scheduled)|\b(router|app|server)\.(get|post|put|delete|patch|use|route)\s*\(|@(app|router|bp)\.(get|post|put|delete|patch|route)\s*\("
    route_signals = re.findall(route_pattern, text)
    decorators = re.findall(r"@(Controller|Get|Post|Put|Delete|Patch|Injectable|MessagePattern|Cron)\b", text)
    django_route = suffix == ".py" and bool(re.search(r"\b(?:urlpatterns\s*=|path\s*\(|re_path\s*\(|APIView|ViewSet|ModelViewSet)\b", text))
    framework = detect_backend_framework(rel_path, text)
    if route_signals or decorators or configured_entrypoints or django_route or ast_facts.get("routes"):
        facts["apis"].append({
            "path": rel_path,
            "framework": framework,
            "parser": ast_facts.get("parser"),
            "signals": sorted(set(flatten_regex_hits(route_signals + decorators) + configured_entrypoints))[:20],
            "endpoints": extract_backend_endpoints(text, ast_facts),
            "methods": extract_backend_methods(text, suffix, ast_facts)[:20],
        })
    service_name = bool(re.search(r"(?:Service|Manager|UseCase|Facade)\.(?:java|kt|ts|js|py)$|(?:^|/)[^/]+[._-](?:service|manager|usecase|facade)\.(?:ts|js|py)$", rel_path, re.I))
    if service_name or "@Service" in text or "@Injectable" in text:
        facts["services"].append({
            "name": path.stem,
            "path": rel_path,
            "framework": framework,
            "parser": ast_facts.get("parser"),
            "methods": extract_backend_methods(text, suffix, ast_facts)[:30],
            "transactions": extract_transaction_signals(text),
            "remoteCalls": extract_remote_call_signals(text),
            "permissionSignals": extract_permission_signals(text),
        })
    if re.search(r"(?:DTO|Dto|VO|Entity|Model|Schema)\.(?:java|kt|ts|js|py)$", rel_path) or re.search(r"@(Entity|Table|Column)\b", text):
        facts["dataTypes"].append({
            "name": path.stem,
            "path": rel_path,
            "kind": "Entity" if re.search(r"@(Entity|Table)\b", text) or path.stem.endswith("Entity") else "DTO/VO/Model",
            "fields": extract_backend_fields(text, suffix)[:40],
            "annotations": sorted(set(re.findall(r"@(Entity|Table|Column|NotNull|NotBlank|Size|Schema|JsonProperty)\b", text)))[:20],
        })
    if re.search(r"(?:Repository|Mapper|Dao|DAO)\.(?:java|kt|ts|js|py)$", rel_path) or re.search(r"@(Repository|Mapper)\b", text) or mapper_xml:
        facts["repositories"].append({
            "name": path.stem,
            "path": rel_path,
            "kind": "Mapper" if re.search(r"Mapper\.(?:java|kt|ts|js|py|xml)$", rel_path) or "@Mapper" in text or mapper_xml else "Repository/DAO",
            "methods": extract_repository_methods(text, suffix, ast_facts)[:50],
            "sqlOps": extract_sql_ops(text),
        })
    if suffix in {".yaml", ".yml", ".properties"} or (suffix == ".xml" and not mapper_xml) or "/config" in lower:
        facts["configs"].append({"path": rel_path, "keys": extract_config_keys(text, suffix), "kind": suffix.removeprefix(".") or "config"})
    signals = {
        "permissionChecks": extract_permission_signals(text),
        "transactions": extract_transaction_signals(text),
        "remoteCalls": extract_remote_call_signals(text),
        "messagesJobs": extract_message_job_signals(text),
        "errorCodes": extract_error_code_signals(text),
    }
    for key, values in signals.items():
        if values:
            facts[key].append({"path": rel_path, "signals": values, "level": "candidate"})
    if re.search(r"(^|/)(utils?|common|helpers?|support)/", lower) and suffix in BACKEND_SUFFIXES:
        facts["utilities"].append({"name": path.stem, "path": rel_path, "exports": extract_exported_functions(text) or extract_backend_methods(text, suffix, ast_facts)[:30]})
    if not (route_signals or decorators or configured_entrypoints or django_route or ast_facts.get("routes")) and re.search(r"(?:handler|endpoint|facade|adapter|action)", lower):
        facts["candidateEntrypoints"].append({"path": rel_path, "reason": "路径/名称暗示非标准入口点", "level": "candidate"})
    facts["scanMode"] = ast_facts.get("parser")
    return facts


def scan_backend(
    root: Path,
    files: list[Path],
    config: dict[str, Any] | None,
    *,
    read_text: Callable[[Path], str],
    rel: Callable[[Path, Path], str],
    path_matches_pattern: Callable[[str, str], bool],
    cache: IncrementalScanCache | None = None,
) -> dict[str, Any]:
    cache = cache or IncrementalScanCache()
    groups = {key: [] for key in (
        "apis", "services", "dataTypes", "repositories", "configs", "permissionChecks",
        "transactions", "remoteCalls", "messagesJobs", "errorCodes", "utilities", "candidateEntrypoints",
    )}
    parser_modes: set[str] = set()
    rules = (config or {}).get("backend", {}).get("entrypointRules", [])
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in BACKEND_SUFFIXES | CONFIG_SUFFIXES:
            continue
        rel_path = rel(root, path)
        signature = file_signature(path)
        facts = cache.get(rel_path, "backend", signature)
        if facts is None:
            text = read_text(path)
            configured: list[str] = []
            for idx, rule in enumerate(rules):
                rule_type = rule.get("type")
                pattern = rule.get("pattern", "")
                matched = path_matches_pattern(rel_path, pattern) if rule_type == "path" else bool(re.search(pattern, text))
                if matched:
                    configured.append(f"config:{rule_type}:{idx + 1}")
            facts = scan_backend_file(path, rel_path, text, configured)
            cache.put(rel_path, "backend", signature, facts)
        for key in groups:
            groups[key].extend(facts.get(key, []))
        parser_modes.add(str(facts.get("scanMode") or "regex-fallback"))
    groups["scanModes"] = sorted(parser_modes)
    return groups
