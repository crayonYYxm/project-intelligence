#!/usr/bin/env node
// Build a 0.6.1 `.project-intel` fixture set by running the baseline CLI's `init`
// against a self-contained mini project, then normalizing non-deterministic
// fields (timestamps, absolute paths, git commit) so the fixture is stable and
// committable.
//
// Usage:
//   node scripts/build-fixtures.mjs            # (re)build fixtures
//   node scripts/build-fixtures.mjs --validate # assert fixture present & normalized
//
// The baseline CLI is the immutable v0.6.1 worktree (.baseline/worktree), never
// the live workspace Python (plan 0.4 / AC-04).

import { spawnSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const BASELINE_CLI = resolve(ROOT, ".baseline/worktree/bin/project-intel.mjs");
const FIXTURE_DIR = resolve(ROOT, ".baseline/fixtures");
const validate = process.argv.includes("--validate");

if (!existsSync(BASELINE_CLI)) {
  console.error(`Baseline CLI missing: ${BASELINE_CLI}. Run plan 0.2 first.`);
  process.exit(1);
}

// A small but representative sample project: backend Python + a little frontend
// + config + docs, so init/refresh produce non-trivial knowledge + standards.
function seedSampleProject(dir) {
  const files = {
    "backend/service.py": [
      "class OrderService:",
      "    def create(self, order_id):",
      "        return {'id': order_id, 'status': 'created'}",
      "",
      "    def submit(self, order_id):",
      "        raise NotImplementedError('submit not implemented')",
      "",
    ].join("\n"),
    "backend/api.py": [
      "from flask import Blueprint",
      "",
      "bp = Blueprint('orders', __name__)",
      "",
      "@bp.route('/orders', methods=['POST'])",
      "def create_order():",
      "    return '', 201",
      "",
    ].join("\n"),
    "frontend/App.tsx": [
      "export default function App() {",
      "  return <div className=\"app\">hello</div>;",
      "}",
      "",
    ].join("\n"),
    "frontend/components/SearchForm.tsx": [
      "export function SearchForm() {",
      "  return <form><input name=\"q\" /></form>;",
      "}",
      "",
    ].join("\n"),
    "package.json": JSON.stringify(
      { name: "fixture-sample", version: "1.0.0", scripts: { lint: "eslint .", test: "jest" } },
      null,
      2
    ) + "\n",
    "README.md": "# Fixture Sample\n\nA small project used to generate the 0.6.1 .project-intel fixture.\n",
  };
  for (const [rel, content] of Object.entries(files)) {
    const full = join(dir, rel);
    mkdirSync(dirname(full), { recursive: true });
    writeFileSync(full, content);
  }
  // Make it a git repo so init can read git metadata deterministically.
  spawnSync("git", ["init", "-q"], { cwd: dir, encoding: "utf8" });
  spawnSync("git", ["add", "-A"], { cwd: dir, encoding: "utf8" });
  spawnSync("git", ["-c", "user.email=fixture@example.com", "-c", "user.name=fixture", "commit", "-q", "-m", "fixture"], {
    cwd: dir,
    encoding: "utf8",
  });
}

// Normalize non-deterministic / machine-specific fields so the fixture is stable.
function normalizeProjectIntel(projectIntelDir, sampleDir) {
  const dir = projectIntelDir;
  const now = "2026-01-01T00:00:00.000000+00:00";
  const replaceText = (rel) => {
    const f = join(dir, rel);
    if (!existsSync(f)) return;
    let t = readFileSync(f, "utf8");
    t = t.split(sampleDir).join("<SAMPLE_ROOT>");
    t = t.split(process.cwd()).join("<ROOT>");
    // normalize iso-8601 timestamps
    t = t.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})/g, now);
    // normalize sha-like git hashes (40 hex) -> placeholder
    t = t.replace(/\b[0-9a-f]{40}\b/g, "<GIT_COMMIT>");
    writeFileSync(f, t);
  };
  // JSON files: also normalize inside parsed structures for keys we know drift.
  const normalizeJson = (rel, extra = {}) => {
    const f = join(dir, rel);
    if (!existsSync(f)) return;
    const obj = JSON.parse(readFileSync(f, "utf8"));
    const merged = { generatedAt: now, lastAnalyzedAt: now, ...extra };
    for (const [k, v] of Object.entries(merged)) {
      if (k in obj) obj[k] = v;
    }
    // scrub any absolute paths + non-deterministic integer mtimes recursively
    const scrub = (node) => {
      if (typeof node === "string") {
        return node.split(sampleDir).join("<SAMPLE_ROOT>").split(process.cwd()).join("<ROOT>");
      }
      if (Array.isArray(node)) return node.map(scrub);
      if (node && typeof node === "object") {
        for (const k of Object.keys(node)) {
          // mtime is a per-file epoch-second that drifts on every rebuild.
          if (k === "mtime" && typeof node[k] === "number") node[k] = 0;
          else node[k] = scrub(node[k]);
        }
        return node;
      }
      return node;
    };
    writeFileSync(f, JSON.stringify(scrub(obj), null, 2));
  };

  normalizeJson("manifest.json", {
    git: { commit: "<GIT_COMMIT>", branch: "main", dirty: false },
  });
  normalizeJson("config.json");
  // knowledge + reports are markdown/json; normalize textually.
  for (const sub of ["knowledge", "reports", "standards", "graph"]) {
    const subDir = join(dir, sub);
    if (!existsSync(subDir)) continue;
    for (const name of readdirSafe(subDir)) {
      const rel = `${sub}/${name}`;
      if (name.endsWith(".json")) normalizeJson(rel);
      else replaceText(rel);
    }
  }
  // reports markdown
  if (existsSync(join(dir, "project-status.md"))) replaceText("project-status.md");
}

function readdirSafe(d) {
  try {
    return readdirSync(d);
  } catch {
    return [];
  }
}function build() {
  // Deterministic temp parent + fixed sample dir name so the project name is stable.
  const tmp = mkdtempSync(join(tmpdir(), "pi-fixture-"));
  const sampleDir = join(tmp, "sample");
  mkdirSync(sampleDir, { recursive: true });
  try {
    seedSampleProject(sampleDir);
    // Run baseline init (no graph tools -> deterministic, fast).
    const run = spawnSync(
      process.execPath,
      [BASELINE_CLI, "--project", sampleDir, "init", "--no-graph"],
      { encoding: "utf8", timeout: 60_000 }
    );
    if ((run.status ?? -1) !== 0) {
      console.error("baseline init failed:\n" + (run.stderr || run.stdout));
      process.exit(1);
    }
    const src = join(sampleDir, ".project-intel");
    if (!existsSync(src)) {
      console.error("init produced no .project-intel");
      process.exit(1);
    }
    rmSync(FIXTURE_DIR, { recursive: true, force: true });
    mkdirSync(FIXTURE_DIR, { recursive: true });
    cpSync(src, join(FIXTURE_DIR, "project-intel"), {
      recursive: true,
      // Exclude machine-local cache: scan-cache signatures are mtime-based and
      // tooling.json is machine-specific; both are gitignored by .project-intel
      // itself and are NOT part of the upgrade contract.
      filter: (s) => !s.includes(`${sep}local${sep}`) && !s.endsWith(`${sep}local`),
    });
    normalizeProjectIntel(join(FIXTURE_DIR, "project-intel"), sampleDir);
    writeFileSync(
      join(FIXTURE_DIR, "README.md"),
      [
        "# 0.6.1 .project-intel fixture",
        "",
        "Generated by `node scripts/build-fixtures.mjs` from the immutable v0.6.1 worktree",
        "(`.baseline/worktree`) running `init --no-graph` against a self-contained sample",
        "project. Non-deterministic fields (timestamps, absolute paths, git hashes) are",
        "normalized so the fixture is stable and committable. Used by AC-04 upgrade tests.",
        "",
      ].join("\n")
    );
    console.log(`Wrote fixture to ${FIXTURE_DIR}/project-intel`);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

function validateFixture() {
  const dir = join(FIXTURE_DIR, "project-intel");
  const required = [
    "manifest.json",
    "config.json",
    "knowledge/backend.json",
    "knowledge/frontend.json",
    "knowledge/files.json",
  ];
  const missing = required.filter((r) => !existsSync(join(dir, r)));
  if (missing.length) {
    console.error("Fixture missing files: " + missing.join(", "));
    process.exit(1);
  }
  // Ensure normalization scrubbed absolute paths.
  const manifest = readFileSync(join(dir, "manifest.json"), "utf8");
  if (manifest.includes(process.cwd()) || /\b[0-9a-f]{40}\b/.test(manifest)) {
    console.error("Fixture not normalized (absolute path or git hash present).");
    process.exit(1);
  }
  console.log("Fixture OK.");
}

if (validate) validateFixture();
else build();
