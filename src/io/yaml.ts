// Minimal YAML support (phase 2.7).
//
// The Project Intelligence data layer uses JSON + Markdown only (no PyYAML); YAML
// is limited to a few front-matter / simple config cases surfaced by scanners.
// This module provides a tiny, dependency-free reader for flat `key: value`
// mappings and flow scalars — sufficient for the configs the product emits. It
// is NOT a general YAML parser; complex YAML inputs should be converted to JSON.
//
// If a project genuinely needs full YAML later, a vendored parser is added in a
// follow-up; for now, this keeps the runtime dependency-free (AC-14).

export interface YamlScalar {
  string: string;
  int: number | null;
  bool: boolean | null;
}

/** Parse a flat YAML document into a string-keyed map of trimmed string values. */
export function parseFlatYaml(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    // strip inline comments outside quotes
    value = value.replace(/(^|[^"])#.*$/, "$1").trim();
    if (value.startsWith('"') && value.endsWith('"')) {
      value = value.slice(1, -1);
    }
    out[key] = value;
  }
  return out;
}

/** Coerce a YAML scalar string to typed scalar (best-effort). */
export function coerceScalar(raw: string): YamlScalar {
  const string = raw;
  if (/^-?\d+$/.test(raw)) return { string, int: Number(raw), bool: null };
  const lower = raw.toLowerCase();
  if (lower === "true" || lower === "false") return { string, int: null, bool: lower === "true" };
  return { string, int: null, bool: null };
}
