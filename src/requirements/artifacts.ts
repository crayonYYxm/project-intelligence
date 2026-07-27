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

export function requirementDirectoryName(requirementId: string, requirementName: string): string {
  const id = normalizeRequirementId(requirementId);
  const availableTitleBytes = MAX_REQUIREMENT_DIRECTORY_BYTES - Buffer.byteLength(id) - 1;
  if (availableTitleBytes < 1) {
    throw new RequirementError(`需求号过长，无法生成安全目录名：${id}`);
  }
  const fallback = "untitled";
  const truncated = truncateUtf8(sanitizeTitleSegment(requirementName) || fallback, availableTitleBytes)
    .replace(/[ .-]+$/g, "");
  return `${id}-${truncated || fallback}`;
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
  return `${requirementDirectoryName(context.requirementId, context.requirementName)}-${label}.md`;
}
