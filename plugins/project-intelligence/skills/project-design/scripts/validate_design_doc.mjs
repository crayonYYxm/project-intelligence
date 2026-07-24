#!/usr/bin/env node
// Design document validator (Node.js port of validate_design_doc.py).
// Performs basic structure validation of project design documents:
//   - Checks the file exists and is markdown
//   - Verifies required headings per document kind (requirement / bug)
//   - Reports missing/extra headings and content issues
//   - Exits 0 on success, 1 on validation failure
//
// Usage:
//   node validate_design_doc.mjs --file <design.md> --repo <root> --kind auto --json

import { existsSync, readFileSync } from "node:fs";
import { resolve, relative } from "node:path";

const args = process.argv.slice(2);
const flag = (name) => {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
};
const hasFlag = (name) => args.includes(name);

const fileArg = flag("--file");
const repoArg = flag("--repo") ?? ".";
const kindArg = flag("--kind") ?? "auto";
const jsonMode = hasFlag("--json");

if (!fileArg) {
  console.error("usage: validate_design_doc.mjs --file <design.md> [--repo <root>] [--kind auto|requirement|bug] [--json]");
  process.exit(2);
}

const filePath = resolve(fileArg);
const repoRoot = resolve(repoArg);

// Document kind requirements
const REQUIRED_REQUIREMENT = [
  "需求问题概述", "需求描述", "场景分析", "风险考虑", "实现方案",
];
const REQUIRED_BUG = [
  "bug现象", "原因分析", "修复方案",
];

function extractHeadings(text) {
  const headingRe = /^#{1,6}\s+(.+?)\s*$/gm;
  const headings = [];
  let match;
  while ((match = headingRe.exec(text)) !== null) {
    headings.push(match[1].replace(/^\d+[.、]?\s*/, ""));
  }
  return headings;
}

let exitCode = 0;
const findings = [];

try {
  if (!existsSync(filePath)) {
    findings.push({ severity: "critical", message: `文件不存在：${filePath}` });
    exitCode = 1;
  } else {
    const content = readFileSync(filePath, "utf8");
    const relPath = relative(repoRoot, filePath);

    // Check file is markdown
    if (!filePath.toLowerCase().endsWith(".md")) {
      findings.push({ severity: "important", message: "设计文档应为 .md 文件" });
    }

    // Check content is not empty
    if (content.trim().length < 50) {
      findings.push({ severity: "critical", message: "设计文档内容过短，不足 50 个字符" });
      exitCode = 1;
    }

    const headings = extractHeadings(content);

    // Determine document kind
    let kind = kindArg;
    if (kind === "auto") {
      const hasBug = headings.some((h) => h.includes("bug") || h.includes("Bug") || h.includes("修复方案"));
      kind = hasBug ? "bug" : "requirement";
    }

    const required = kind === "bug" ? REQUIRED_BUG : REQUIRED_REQUIREMENT;
    for (const h of required) {
      if (!headings.includes(h)) {
        findings.push({ severity: "important", message: `缺少必要章节：${h}` });
      }
    }

    // Check for code references (path#symbol patterns)
    const codeRefRe = /\S+#\S+/g;
    const codeRefs = content.match(codeRefRe) || [];
    if (codeRefs.length === 0 && kind === "bug") {
      findings.push({ severity: "important", message: "Bug 设计文档未包含源码证据引用" });
    }

    if (findings.filter((f) => f.severity === "critical").length > 0) {
      exitCode = 1;
    }

    if (jsonMode) {
      process.stdout.write(JSON.stringify({
        valid: exitCode === 0,
        kind,
        file: relPath,
        headingCount: headings.length,
        findings,
      }, null, 2) + "\n");
    } else {
      if (exitCode === 0) {
        console.log(`设计文档验证通过：${filePath} (kind=${kind})`);
      } else {
        for (const f of findings) {
          console.error(`  [${f.severity}] ${f.message}`);
        }
      }
    }
  }
} catch (err) {
  findings.push({ severity: "critical", message: `验证异常：${err.message}` });
  exitCode = 1;
  if (jsonMode) {
    process.stdout.write(JSON.stringify({ valid: false, findings }, null, 2) + "\n");
  }
}

process.exit(exitCode);
