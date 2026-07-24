#!/usr/bin/env node
// Scan the Node.js production core for runtime Python dependencies.
//
// Per the migration requirement (P1.4): detect ACTUAL runtime dependencies, not
// bare ".py" strings (the scanner legitimately recognizes .py suffixes). This
// flags:
//   - child_process spawn/exec of python/python3/py
//   - dynamic import / require of Python-bridge libraries (python-shell etc.)
//   - production-entry reads of .py files at runtime
//
// Scans dist/ (the shipped core) + bin/. Returns non-zero if any runtime Python
// reference is found. Used by the phase 4 gate (AC-09 / AC-14).

import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SCAN_DIRS = [
  join(ROOT, "dist"),
  join(ROOT, "bin"),
];
// Patterns that indicate an ACTUAL runtime Python invocation (not a string literal).
const RUNTIME_PYTHON_PATTERNS = [
  // spawn/exec of a python interpreter as a command argument.
  /(?:spawn|spawnSync|exec|execSync|fork)\s*\(\s*['"`](?:python|python3|py)['"`]/,
  // argv-form command lists whose first element is a python interpreter.
  /\[\s*['"`](?:python|python3|py)['"`]\s*[,)]/,
  // dynamic import / require of a Python-bridge package.
  /(?:import|require)\s*\(?['"`](?:python-shell|child_process-python|pythonia)['"`]/,
  // runtime read of a .py file (the production entry resolving a python source).
  /readText\s*\(\s*[^)]*\.py['"`]/,
  /readFileSync\s*\(\s*[^)]*\.py['"`]/,
];

function walk(dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walk(full, out);
    else if (/\.(js|mjs)$/.test(name)) out.push(full);
  }
  return out;
}

function main() {
  const findings = [];
  for (const dir of SCAN_DIRS) {
    for (const file of walk(dir)) {
      const rel = relative(ROOT, file);
      const text = readFileSync(file, "utf8");
      for (const pattern of RUNTIME_PYTHON_PATTERNS) {
        const match = pattern.exec(text);
        if (match) {
          findings.push({ file: rel, match: match[0], line: lineOf(text, match.index) });
        }
      }
    }
  }

  if (findings.length) {
    console.error("Runtime Python references found in production core:");
    for (const f of findings) {
      console.error(`  ${f.file}:${f.line}  ${f.match.trim()}`);
    }
    process.exit(1);
  }
  console.log("No runtime Python references in dist/ + bin/. ✅");
}

function lineOf(text, index) {
  return text.slice(0, index).split("\n").length;
}

function relative(from, to) {
  return to.slice(from.length + 1).split("\\").join("/");
}

main();
