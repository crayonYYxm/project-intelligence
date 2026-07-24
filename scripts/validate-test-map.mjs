#!/usr/bin/env node
// Test-map strict gate (AC-10).
//
// Validates that every current Python test method in
// plugins/project-intelligence/tests is listed in .baseline/test-map.json with
// status "done" and a concrete Node-equivalent test artifact.
//
// Usage: node scripts/validate-test-map.mjs [--strict]

import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { resolve, dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TEST_MAP_PATH = join(ROOT, ".baseline", "test-map.json");
const TESTS_DIR = join(ROOT, "src", "__tests__");
const PYTHON_TESTS_DIR = join(ROOT, "plugins", "project-intelligence", "tests");
const strict = process.argv.includes("--strict");

const testMap = JSON.parse(readFileSync(TEST_MAP_PATH, "utf8"));

// Build a set of all existing test files under src/__tests__/
const existingTests = new Set();
function walkTests(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walkTests(full);
    else if (name.endsWith(".test.ts")) existingTests.add(relative(TESTS_DIR, full));
  }
}
walkTests(TESTS_DIR);

function walkFiles(dir, predicate, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) walkFiles(full, predicate, out);
    else if (predicate(name, full)) out.push(full);
  }
  return out;
}

function enumeratePythonTests() {
  const tests = [];
  for (const file of walkFiles(PYTHON_TESTS_DIR, (name) => name.startsWith("test_") && name.endsWith(".py"))) {
    const rel = relative(PYTHON_TESTS_DIR, file).replaceAll("\\", "/");
    const lines = readFileSync(file, "utf8").split(/\r?\n/);
    let currentClass = null;
    for (const line of lines) {
      const classMatch = /^class\s+([A-Za-z_][\w]*)\b/.exec(line);
      if (classMatch) currentClass = classMatch[1];
      const methodMatch = /^\s+def\s+(test_[A-Za-z_]\w*)\s*\(/.exec(line);
      if (methodMatch && currentClass) tests.push(`${rel}#${currentClass}.${methodMatch[1]}`);
    }
  }
  return tests.sort();
}

let errors = 0;
let done = 0;
let pending = 0;
let skipped = 0;
const seenSources = new Set();

for (const mapping of testMap.mappings) {
  if (seenSources.has(mapping.source)) {
    console.error(`  ❌ duplicate source mapping: ${mapping.source}`);
    errors++;
  }
  seenSources.add(mapping.source);
  if (mapping.status === "done") {
    done++;
    // In strict mode, verify the actualNodeFile exists on disk.
    if (strict) {
      const actual = mapping.actualNodeFile ?? mapping.nodeTarget;
      const basename = actual.split("/").pop();
      let found;
      if (actual.endsWith(".mjs")) {
        found = existsSync(join(ROOT, "plugins/project-intelligence/skills/project-design/scripts", basename));
      } else {
        found = existingTests.has(basename) ||
          [...existingTests].some((t) => t.endsWith(basename));
      }
      if (!found) {
        console.error(`  ❌ ${mapping.source} → ${actual} (status=done but file not found)`);
        errors++;
      }
    }
  } else if (mapping.status === "pending") {
    pending++;
  } else if (mapping.status === "skipped") {
    skipped++;
  }
}

console.log(`Test map: ${testMap.mappings.length} mappings (${done} done, ${pending} pending, ${skipped} skipped)`);

if (strict && pending > 0) {
  console.error(`❌ --strict requires all mappings to be done; ${pending} still pending`);
  errors++;
}

if (strict) {
  const currentPythonTests = enumeratePythonTests();
  if (currentPythonTests.length > 0) {
    for (const source of currentPythonTests) {
      if (!seenSources.has(source)) {
        console.error(`  ❌ missing Python test mapping: ${source}`);
        errors++;
      }
    }
    const currentSet = new Set(currentPythonTests);
    for (const source of seenSources) {
      if (!currentSet.has(source)) {
        console.error(`  ❌ stale Python test mapping: ${source}`);
        errors++;
      }
    }
    console.log(`Python tests: ${currentPythonTests.length} current methods`);
  } else {
    const expected = Number(testMap.baselineTestCount ?? 0);
    if (expected <= 0 || testMap.mappings.length !== expected) {
      console.error(`  ❌ Python source tests are archived; test-map baselineTestCount=${expected} must equal mappings=${testMap.mappings.length}`);
      errors++;
    }
    console.log(`Python tests: source directory archived; validating ${testMap.mappings.length} baseline method mappings`);
  }
}

if (errors > 0) {
  console.error(`❌ ${errors} validation error(s)`);
  process.exit(1);
}

console.log("✅ Test map validation passed.");
