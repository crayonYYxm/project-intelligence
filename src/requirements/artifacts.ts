import { RequirementError } from "../errors.js";

export const LEGACY_ARTIFACT_FILES: Record<string, string> = {
  requirement: "requirement.md",
  design: "design.md",
  "requirement-design": "design.md",
  plan: "plan.md",
  test: "test-report.md",
  "test-report": "test-report.md",
  "unit-test": "test-report.md",
  "service-test": "test-report.md",
  "manual-test": "test-report.md",
  closure: "closure-summary.md",
};

export const ARTIFACT_FILES = LEGACY_ARTIFACT_FILES;

const ARTIFACT_LABELS: Record<string, string> = {
  requirement: "需求文档",
  design: "设计文档",
  plan: "实施计划",
  test: "测试文档",
  closure: "收口文档",
};

const MAX_REQUIREMENT_DIRECTORY_BYTES = 240;

export interface ArtifactContext {
  requirementId: string;
  requirementName: string;
  ticketKind?: string;
  versionDate?: string;
}

function truncateUtf8(value: string, maxBytes: number): string {
  let result = "";
  let bytes = 0;
  for (const character of value) {
    const size = Buffer.byteLength(character);
    if (bytes + size > maxBytes) break;
    result += character;
    bytes += size;
  }
  return result;
}

export function normalizeRequirementId(id: string): string {
  return (id ?? "").trim().replace(/[^A-Za-z0-9._-]/g, "-");
}

export function sanitizeTitleSegment(value: string): string {
  return String(value ?? "")
    .normalize("NFKC")
    .replace(/[\u0000-\u001f\u007f-\u009f<>:\x22/\\|?*]/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^[ .-]+|[ .-]+$/g, "");
}

export function normalizeVersionDate(value: string, referenceDate = new Date()): string {
  const raw = String(value ?? "").trim().replace(/\s*版本\s*$/u, "");
  const normalized = raw
    .replace(/年|月/gu, "-")
    .replace(/日/gu, "")
    .replace(/[./]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
  const parts = normalized.split("-");
  if (parts.length !== 2 && parts.length !== 3) {
    throw new RequirementError(`版本日期格式无效：${value}`);
  }
  const [yearValue, monthValue, dayValue] = parts.length === 3
    ? parts
    : [String(referenceDate.getFullYear()), parts[0], parts[1]];
  if (!/^\d{4}$/.test(yearValue!) || !/^\d{1,2}$/.test(monthValue!) || !/^\d{1,2}$/.test(dayValue!)) {
    throw new RequirementError(`版本日期格式无效：${value}`);
  }
  const year = Number(yearValue);
  const month = Number(monthValue);
  const day = Number(dayValue);
  const candidate = new Date(year, month - 1, day);
  if (
    year < 1000
    || year > 9999
    || candidate.getFullYear() !== year
    || candidate.getMonth() !== month - 1
    || candidate.getDate() !== day
  ) {
    throw new RequirementError(`版本日期不是有效日历日期：${value}`);
  }
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function requirementArtifactStem(requirementId: string, requirementName: string, maxBytes: number): string {
  const id = normalizeRequirementId(requirementId);
  const availableTitleBytes = maxBytes - Buffer.byteLength(id) - 1;
  if (availableTitleBytes < 1) {
    throw new RequirementError(`需求号过长，无法生成安全目录名：${id}`);
  }
  const fallback = "untitled";
  const truncated = truncateUtf8(sanitizeTitleSegment(requirementName) || fallback, availableTitleBytes)
    .replace(/[ .-]+$/g, "");
  return `${id}-${truncated || fallback}`;
}

export function requirementDirectoryName(
  requirementId: string,
  requirementName: string,
  versionDate?: string
): string {
  const datePrefix = versionDate ? `${normalizeVersionDate(versionDate)}-` : "";
  return `${datePrefix}${requirementArtifactStem(
    requirementId,
    requirementName,
    MAX_REQUIREMENT_DIRECTORY_BYTES - Buffer.byteLength(datePrefix)
  )}`;
}

export function normalizeArtifactType(type: string): string {
  if (type === "requirement-design") return "design";
  if (["test-report", "unit-test", "service-test", "manual-test"].includes(type)) return "test";
  return type;
}

/** Resolve the canonical filename for an artifact type. */
export function artifactFilename(type: string, context?: ArtifactContext): string {
  const normalized = normalizeArtifactType(type);
  if (!context) return LEGACY_ARTIFACT_FILES[type] ?? LEGACY_ARTIFACT_FILES[normalized] ?? `${type}.md`;
  const label = normalized === "requirement" && context.ticketKind === "bug"
    ? "Bug文档"
    : ARTIFACT_LABELS[normalized];
  if (!label) return `${sanitizeTitleSegment(type) || "artifact"}.md`;
  return `${requirementArtifactStem(
    context.requirementId,
    context.requirementName,
    MAX_REQUIREMENT_DIRECTORY_BYTES
  )}-${label}.md`;
}
