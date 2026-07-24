// Test-evidence secret sanitization (phase 3.E.1), ported from testing.py.
//
// Redacts credentials/PII from command output before persisting test evidence,
// so leaked secrets never reach `.project-intel/reports/test-evidence.*`. Covers:
// header values (Authorization/Cookie), key=value pairs (token/password/secret/
// api_key/aws_*/phone/id_card), raw token formats (gh_/npm_/xox/sk-/glpat/AIza/
// JWT), database URLs, URL userinfo, PRC identity numbers, mainland mobile numbers.

const SECRET_KEY_PATTERN =
  "authorization|cookie|token|access[_-]?token|refresh[_-]?token|password|secret|" +
  "api[_-]?key|aws[_-]?secret[_-]?access[_-]?key|aws[_-]?access[_-]?key[_-]?id|" +
  "party[_-]?id|phone|mobile|phone[_-]?(?:no|number)|mobile[_-]?(?:no|number)|" +
  "id[_-]?card|identity[_-]?(?:card|number)|cert(?:ificate)?[_-]?(?:no|number)";
const SECRET_VALUE_PATTERN = `(?:"[^"]*"|'[^']*'|[^\\s,;&]+)`;

const RAW_SECRET_PATTERNS: RegExp[] = [
  /\bgh[pousr]_[A-Za-z0-9]{20,}\b/g,
  /\bgithub_pat_[A-Za-z0-9_]{20,}\b/gi,
  /\bnpm_[A-Za-z0-9]{20,}\b/gi,
  /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/gi,
  /\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b/gi,
  /\bsk-ant-[A-Za-z0-9_-]{20,}\b/gi,
  /\bglpat-[A-Za-z0-9_-]{20,}\b/gi,
  /\bAIza[0-9A-Za-z_-]{20,}\b/g,
  /\b(?:rk|sk)_live_[A-Za-z0-9]{16,}\b/gi,
  /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g,
];

const DATABASE_URL_PATTERN =
  /\b((?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis):\/\/)([^:@/\s]+):([^@/\s]+)@/gi;
const URL_USERINFO_PATTERN = /\b([a-z][a-z0-9+.-]*:\/\/)([^/@\s]+)@/gi;
const MAINLAND_MOBILE_PATTERN = /(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d[-\s]?\d{4}[-\s]?\d{4}(?!\d)/g;
const PRC_IDENTITY_PATTERN =
  /(?<![0-9A-Za-z])(?:[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]|[1-9]\d{7}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3})(?![0-9A-Za-z])/g;

function findUnescaped(value: string, ch: string, start: number): number {
  let index = start;
  while (true) {
    index = value.indexOf(ch, index);
    if (index < 0) return -1;
    let backslashes = 0;
    let cursor = index - 1;
    while (cursor >= 0 && value[cursor] === "\\") {
      backslashes++;
      cursor--;
    }
    if (backslashes % 2 === 0) return index;
    index++;
  }
}

function redactHeaderValues(value: string, header: string): string {
  const pattern = new RegExp(`\\b${escapeRegex(header)}\\s*:\\s*`, "gi");
  let result = "";
  let cursor = 0;
  while (true) {
    const match = pattern.exec(value);
    if (match === null) {
      result += value.slice(cursor);
      break;
    }
    result += value.slice(cursor, match.index + match[0].length);
    const delimiter = match.index > 0 ? value[match.index - 1]! : "";
    let end: number;
    if (delimiter === "'" || delimiter === '"') {
      end = findUnescaped(value, delimiter, match.index + match[0].length);
    } else {
      const nl = [value.indexOf("\n", match.index + match[0].length), value.indexOf("\r", match.index + match[0].length)].filter((p) => p >= 0);
      end = nl.length ? Math.min(...nl) : value.length;
    }
    if (end < 0) end = value.length;
    result += "[REDACTED]";
    cursor = end;
    pattern.lastIndex = end;
  }
  return result;
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Sanitize a string by redacting secrets/PII. Mirrors testing.sanitize_text. */
export function sanitizeText(value: unknown): string {
  let text = String(value ?? "");
  text = redactHeaderValues(text, "Authorization");
  text = redactHeaderValues(text, "Cookie");
  text = text.replace(
    new RegExp(`((?:["']?)(?:${SECRET_KEY_PATTERN})(?:["']?)\\s*[:=]\\s*)(?!\\[REDACTED\\])${SECRET_VALUE_PATTERN}`, "gi"),
    "$1[REDACTED]"
  );
  text = text.replace(
    new RegExp(`(--(?:${SECRET_KEY_PATTERN})(?:=|\\s+))(?!\\[REDACTED\\])${SECRET_VALUE_PATTERN}`, "gi"),
    "$1[REDACTED]"
  );
  text = text.replace(
    new RegExp(`(\\b[A-Za-z_][A-Za-z0-9_]*(?:TOKEN|PASSWORD|SECRET|API_KEY)\\s*=\\s*)(?!\\[REDACTED\\])${SECRET_VALUE_PATTERN}`, "gi"),
    "$1[REDACTED]"
  );
  text = text.replace(
    /(AWS_(?:SECRET_ACCESS_KEY|ACCESS_KEY_ID)\s*=\s*)(?!\[REDACTED\])/gi,
    "$1[REDACTED]"
  );
  text = text.replace(DATABASE_URL_PATTERN, "$1[REDACTED]:[REDACTED]@");
  text = text.replace(URL_USERINFO_PATTERN, (_m, scheme, userinfo) => {
    if (String(userinfo).includes("[REDACTED]")) return _m;
    const replacement = String(userinfo).includes(":") ? "[REDACTED]:[REDACTED]" : "[REDACTED]";
    return `${scheme}${replacement}@`;
  });
  for (const pattern of RAW_SECRET_PATTERNS) {
    text = text.replace(pattern, "[REDACTED]");
  }
  text = text.replace(PRC_IDENTITY_PATTERN, "[REDACTED]");
  text = text.replace(MAINLAND_MOBILE_PATTERN, "[REDACTED]");
  return text;
}

export const COMMAND_ERROR_CODES = new Set([2, 3, 4, 5, 124, 126, 127]);
export const PASSING_PHASES = new Set(["green", "regression", "verify", "manual"]);
export const TEST_PHASES = ["red", "green", "regression", "verify", "manual"] as const;
export const MIN_MANUAL_EVIDENCE_LENGTH = 12;

/** Whether a manual-evidence string is specific enough (not a generic phrase). */
export function manualEvidenceValid(value: string): boolean {
  const compact = (value ?? "").toLowerCase().replace(/[^a-z0-9\u4e00-\u9fff]/g, "");
  const generic = new Set([
    "已手动验证",
    "手动验证通过",
    "验证通过",
    "测试通过",
    "manualverificationpassed",
    "testedmanually",
  ]);
  return compact.length >= MIN_MANUAL_EVIDENCE_LENGTH && !generic.has(compact);
}
