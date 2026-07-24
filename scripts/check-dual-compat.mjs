#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import {
  cpSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  compareJsonOutputs,
  normalizeForCompare,
} from "../dist/testing/dual-impl.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const BASELINE = join(ROOT, ".baseline", "worktree", "bin", "project-intel.mjs");
const CANDIDATE = join(ROOT, "dist", "cli.js");

function main() {
  const temp = mkdtempSync(join(tmpdir(), "pi-dual-compat-"));
  const baselineRoot = join(temp, "baseline", "project");
  const candidateRoot = join(temp, "candidate", "project");
  try {
    seedMixedProject(baselineRoot);
    cpSync(baselineRoot, candidateRoot, { recursive: true });
    initGit(baselineRoot);
    initGit(candidateRoot);

    const baseline = run(BASELINE, baselineRoot, ["init", "--no-graph"]);
    const candidate = run(CANDIDATE, candidateRoot, ["init", "--no-graph"]);
    if (baseline.status !== 0 || candidate.status !== 0) {
      fail(`init failed: baseline=${baseline.status}, candidate=${candidate.status}\n${baseline.stderr}\n${candidate.stderr}`);
    }

    const baselineDir = join(baselineRoot, ".project-intel");
    const candidateDir = join(candidateRoot, ".project-intel");
    const baselineFiles = walkFiles(baselineDir);
    const candidateFiles = walkFiles(candidateDir);
    const missing = baselineFiles.filter((path) => !candidateFiles.includes(path));
    const extra = candidateFiles.filter((path) => !baselineFiles.includes(path));
    if (missing.length || extra.length) {
      fail(`generated file set differs\nmissing: ${missing.join(", ")}\nextra: ${extra.join(", ")}`);
    }

    const differences = [];
    for (const path of baselineFiles.filter((item) => item.endsWith(".json"))) {
      const baselineValue = scrub(
        JSON.parse(readFileSync(join(baselineDir, path), "utf8")),
        [baselineRoot, candidateRoot]
      );
      const candidateValue = scrub(
        JSON.parse(readFileSync(join(candidateDir, path), "utf8")),
        [baselineRoot, candidateRoot]
      );
      const fileDifferences = allDifferences(baselineValue, candidateValue);
      differences.push(...fileDifferences.slice(0, 40).map((difference) => `${path}: ${difference}`));
    }
    for (const path of baselineFiles.filter((item) => !item.endsWith(".json"))) {
      const baselineText = scrubText(readFileSync(join(baselineDir, path), "utf8"), [baselineRoot, candidateRoot]);
      const candidateText = scrubText(readFileSync(join(candidateDir, path), "utf8"), [baselineRoot, candidateRoot]);
      if (baselineText !== candidateText) {
        const baselineLines = baselineText.split("\n");
        const candidateLines = candidateText.split("\n");
        const line = Math.max(0, baselineLines.findIndex((value, index) => value !== candidateLines[index]));
        differences.push(
          `${path}:${line + 1}: ${JSON.stringify(baselineLines[line] ?? "<missing>")} vs ${JSON.stringify(candidateLines[line] ?? "<missing>")}`
        );
      }
    }
    if (differences.length) fail(`generated JSON differs:\n${differences.join("\n")}`);

    console.log(`Dual implementation compatibility passed: ${baselineFiles.length} generated files.`);
  } finally {
    rmSync(temp, { recursive: true, force: true });
  }
}

function seedMixedProject(root) {
  const files = {
    "package.json": JSON.stringify({
      name: "mixed-fixture",
      dependencies: { vue: "3.5.0", react: "19.0.0" },
      scripts: { lint: "eslint .", test: "node --test" },
    }),
    "src/App.vue": '<script setup lang="ts">defineProps<{title:string}>(); defineEmits(["save"])</script><template><div>{{title}}</div></template>',
    "src/api.ts": 'export const load = () => fetch("/api/items");\n',
    "backend/api.py": 'from flask import Blueprint\nbp = Blueprint("x", __name__)\n@bp.route("/orders", methods=["POST"])\ndef create_order(): return "", 201\n',
    "backend/OrderService.py": "class OrderService:\n    def create(self): pass\n",
    "java/OrderController.java": '@RestController class OrderController { @GetMapping("/orders") public void list(){} }\n',
    "go/main.go": "package main\nfunc main() {}\n",
  };
  for (const [path, content] of Object.entries(files)) {
    const full = join(root, path);
    mkdirSync(dirname(full), { recursive: true });
    writeFileSync(full, content);
  }
}

function initGit(root) {
  for (const args of [
    ["init", "-q"],
    ["config", "user.email", "dual@example.com"],
    ["config", "user.name", "Dual Compatibility"],
    ["add", "."],
    ["commit", "-qm", "fixture"],
  ]) {
    const result = spawnSync("git", args, { cwd: root, encoding: "utf8" });
    if (result.status !== 0) fail(`git ${args.join(" ")} failed: ${result.stderr}`);
  }
}

function run(cli, cwd, args) {
  return spawnSync(process.execPath, [cli, "--project", cwd, ...args], {
    cwd,
    encoding: "utf8",
    timeout: 60_000,
  });
}

function walkFiles(root) {
  const out = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      const stat = statSync(full);
      if (stat.isDirectory()) walk(full);
      else {
        const path = relative(root, full).replaceAll("\\", "/");
        out.push(path);
      }
    }
  };
  walk(root);
  return out.sort();
}

function scrubText(value, roots) {
  return String(normalizeForCompare(value, roots))
    .replaceAll("0.6.1", "<VERSION>")
    .replaceAll("0.7.0", "<VERSION>");
}

function scrub(value, roots) {
  const normalized = normalizeForCompare(value, roots);
  const walk = (node) => {
    if (!node || typeof node !== "object") return;
    if ("toolVersion" in node) node.toolVersion = "<VERSION>";
    if ("generatedAt" in node) node.generatedAt = "<TIME>";
    if ("mtime" in node) node.mtime = "<MTIME>";
    if ("signature" in node && /^[0-9a-f]{20}$/.test(String(node.signature))) {
      node.signature = "<SIGNATURE>";
    }
    if (Array.isArray(node.required)) {
      node.required = node.required.map((item) => (
        /python|node/i.test(String(item.name ?? ""))
          ? { ...item, name: "runtime" }
          : item
      ));
    }
    for (const child of Object.values(node)) walk(child);
  };
  walk(normalized);
  return normalized;
}

function allDifferences(baseline, candidate, path = "") {
  if (typeof baseline !== typeof candidate) {
    return [`${path || "<root>"}: type ${typeof baseline} vs ${typeof candidate}`];
  }
  if (baseline === null || typeof baseline !== "object") {
    return baseline === candidate ? [] : [`${path || "<root>"}: ${JSON.stringify(baseline)} vs ${JSON.stringify(candidate)}`];
  }
  if (Array.isArray(baseline)) {
    if (!Array.isArray(candidate)) return [`${path || "<root>"}: array vs non-array`];
    const differences = [];
    const length = Math.max(baseline.length, candidate.length);
    for (let index = 0; index < length; index++) {
      const child = `${path}[${index}]`;
      if (index >= baseline.length) differences.push(`${child}: missing in baseline`);
      else if (index >= candidate.length) differences.push(`${child}: missing in candidate`);
      else differences.push(...allDifferences(baseline[index], candidate[index], child));
    }
    return differences;
  }
  const differences = [];
  for (const key of new Set([...Object.keys(baseline), ...Object.keys(candidate)])) {
    const child = path ? `${path}.${key}` : key;
    if (!(key in baseline)) differences.push(`${child}: missing in baseline`);
    else if (!(key in candidate)) differences.push(`${child}: missing in candidate`);
    else differences.push(...allDifferences(baseline[key], candidate[key], child));
  }
  return differences;
}

function fail(message) {
  console.error(`Dual implementation compatibility failed: ${message}`);
  process.exitCode = 1;
  throw new Error(message);
}

main();
