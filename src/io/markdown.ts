// Markdown read/write helpers (phase 2.7), used for project-status.md, reports,
// requirement documents, and the adapter managed blocks. Plain UTF-8 text I/O
// with the same atomic-write guarantees as the data layer (atomic-write.ts).

import { readFileSync } from "node:fs";
import { writeText } from "../fs/atomic-write.js";

/** Read a Markdown file as UTF-8 text, returning "" when missing. */
export function readMarkdown(path: string): string {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return "";
  }
}

/** Atomic write of Markdown text (UTF-8, guaranteed trailing newline). */
export function writeMarkdown(path: string, text: string): void {
  writeText(path, text);
}

/** Find ATX headings (#-level) in a Markdown document, preserving order. */
export interface Heading {
  level: number;
  text: string;
  normalized: string;
  line: number;
}

/** Normalize a heading text for matching (trim + collapse whitespace). */
export function normalizeHeading(text: string): string {
  return text.trim().replace(/\s+/g, " ");
}

/** Extract ATX headings from Markdown lines. */
export function parseHeadings(lines: readonly string[]): Heading[] {
  const out: Heading[] = [];
  for (let i = 0; i < lines.length; i++) {
    const m = /^(#{1,6})\s+(.*?)\s*$/.exec(lines[i] ?? "");
    if (m) {
      const hashes = m[1]!;
      const text = m[2]!;
      out.push({
        level: hashes.length,
        text,
        normalized: normalizeHeading(text),
        line: i + 1,
      });
    }
  }
  return out;
}

/** Whether a heading body has meaningful (non-blank, non-placeholder) content. */
export function hasMeaningfulContent(text: string): boolean {
  const cleaned = text.replace(/<!--.*?-->/gs, "").trim();
  return cleaned.length > 0 && !/^(无|_+|待确认|待补充|n\/a)$/i.test(cleaned);
}
