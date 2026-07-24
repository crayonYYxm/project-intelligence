import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  scanFrontendFile,
  scanFrontend,
  extractVueProps,
  extractEmits,
  extractApiEndpoints,
} from "../scanner/frontend.js";
import { discoverFiles, categorize, simpleMatch } from "../scanner/files.js";
import {
  detectPackage,
  detectQualityCommands,
  packageManager,
  packageFrameworks,
} from "../scanner/quality.js";
import { IncrementalScanCache, fileSignature } from "../scanner/core.js";

describe("frontend scanner", () => {
  it("extracts vue component props/emits", () => {
    const vue = [
      "<script setup lang=\"ts\">",
      "defineProps<{ title: string; count?: number }>()",
      "defineEmits(['submit', 'cancel'])",
      "</script>",
      "<template><div /></template>",
    ].join("\n");
    const f = scanFrontendFile("src/components/OrderForm.vue", vue);
    assert.equal(f.components.length, 1);
    const c = f.components[0] as Record<string, unknown>;
    assert.equal(c.kind, "vue");
    assert.deepEqual(c.props, ["count", "title"]);
    assert.deepEqual(c.emits, ["cancel", "submit"]);
  });

  it("extracts react props from interface", () => {
    const tsx = [
      "interface CardProps { title: string; onClose?: () => void }",
      "export function Card({ title, onClose }: CardProps) { return null; }",
    ].join("\n");
    const f = scanFrontendFile("src/components/Card.tsx", tsx);
    const c = f.components[0] as Record<string, unknown>;
    assert.deepEqual(c.props, ["onClose", "title"]);
  });

  it("extracts hooks by use* filename", () => {
    const ts = "export function useCounter() { return 0; }\nexport const useToggle = () => 1;";
    const f = scanFrontendFile("src/hooks/useCounter.ts", ts);
    assert.equal(f.hooks.length, 1);
    assert.deepEqual((f.hooks[0] as Record<string, unknown>).exports, ["useCounter", "useToggle"]);
  });

  it("extracts routes and redundancy candidates", () => {
    // table pattern requires >=2 of: <el-table, columns=, type:"selection"
    const tableVue = "<el-table :columns=\"cols\" />\n<el-pagination />";
    const files = [
      { path: "src/router/index.ts", text: "const r = { path: '/home' }\nexport default r" },
      { path: "src/components/A.vue", text: tableVue },
      { path: "src/components/B.vue", text: tableVue },
      { path: "src/components/C.vue", text: tableVue },
    ];
    const result = scanFrontend(files);
    assert.equal(result.routes.length, 1);
    assert.equal((result.routes[0] as Record<string, unknown>).routeCount, 1);
    // table pattern appears in >=3 files -> redundancy candidate
    assert.ok(result.redundancyCandidates.some((c) => (c as Record<string, unknown>).name === "table"));
  });

  it("extractVueProps from defineProps object form", () => {
    const props = extractVueProps("defineProps({ title: String, size: Number })");
    assert.deepEqual(props, ["size", "title"]);
  });

  it("extractEmits filters to valid names", () => {
    const emits = extractEmits("defineEmits(['submit', 'bad-name!'])");
    assert.deepEqual(emits, ["submit"]);
  });

  it("extractApiEndpoints from request/fetch calls", () => {
    const eps = extractApiEndpoints("request('/api/orders')\nfetch(`/api/list`)");
    assert.ok(eps.includes("/api/orders"));
    assert.ok(eps.includes("/api/list"));
  });
});

describe("files scanner", () => {
  it("discoverFiles walks and categorizes", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-files-"));
    mkdirSync(join(tmp, "src"), { recursive: true });
    writeFileSync(join(tmp, "src", "App.tsx"), "x");
    writeFileSync(join(tmp, "config.yml"), "x");
    writeFileSync(join(tmp, "README.md"), "x");
    writeFileSync(join(tmp, "style.css"), "x");
    const files = discoverFiles(tmp);
    assert.ok(files.some((f) => f.path === "src/App.tsx" && f.fileCategory === "code"));
    assert.ok(files.some((f) => f.path === "config.yml" && f.fileCategory === "config"));
    assert.ok(files.some((f) => f.path === "README.md" && f.fileCategory === "docs"));
    assert.ok(files.some((f) => f.path === "style.css" && f.fileCategory === "style"));
  });

  it("discoverFiles excludes node_modules/.git", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-files-"));
    mkdirSync(join(tmp, "node_modules", "pkg"), { recursive: true });
    writeFileSync(join(tmp, "node_modules", "pkg", "index.js"), "x");
    writeFileSync(join(tmp, "app.js"), "y");
    const files = discoverFiles(tmp);
    assert.ok(files.some((f) => f.path === "app.js"));
    assert.ok(!files.some((f) => f.path.includes("node_modules")));
  });

  it("uses stable code-point ordering across operating systems", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-files-order-"));
    writeFileSync(join(tmp, "Z.ts"), "z");
    writeFileSync(join(tmp, "a.ts"), "a");
    assert.deepEqual(discoverFiles(tmp).map((file) => file.path), ["Z.ts", "a.ts"]);
  });

  it("categorize and simpleMatch basics", () => {
    assert.equal(categorize(".ts", "a.ts"), "code");
    assert.equal(categorize(".md", "README.md"), "docs");
    assert.equal(categorize(".yml", ".github/workflows/ci.yml"), "infra");
    assert.ok(simpleMatch("*.ts", "a.ts"));
    assert.ok(!simpleMatch("*.ts", "a.js"));
  });
});

describe("incremental scan cache", () => {
  it("reuses unchanged frontend facts without reading the file again", () => {
    const cache = new IncrementalScanCache();
    let reads = 0;
    const file = {
      path: "src/components/Card.vue",
      signature: "stable-signature",
      readText: () => {
        reads++;
        return "<template><div /></template>";
      },
    };
    const first = scanFrontend([file], cache);
    const second = scanFrontend([file], cache);
    assert.equal(reads, 1);
    assert.deepEqual(second, first);
    assert.ok(cache.payload().entries[file.path]?.frontend);
  });

  it("uses nanosecond-compatible file signatures and invalidates changed entries", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-cache-"));
    const path = join(tmp, "source.ts");
    writeFileSync(path, "one");
    const before = fileSignature(path);
    writeFileSync(path, "content changed");
    const after = fileSignature(path);
    assert.notEqual(after, before);
  });
});

describe("quality scanner", () => {
  it("packageFrameworks detects Vue+TypeScript from deps", () => {
    const deps = { vue: "1", typescript: "5", express: "4" };
    const fw = packageFrameworks(deps);
    assert.ok(fw.includes("Vue"));
    assert.ok(fw.includes("TypeScript"));
    assert.ok(fw.includes("Express"));
  });

  it("detectPackage reads package.json scripts and frameworks", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-q-"));
    writeFileSync(
      join(tmp, "package.json"),
      JSON.stringify({ name: "demo", scripts: { lint: "eslint ." }, dependencies: { vue: "3" } })
    );
    const pkg = detectPackage(tmp);
    assert.equal(pkg.packageName, "demo");
    assert.ok((pkg.frameworks as string[]).includes("Vue"));
    assert.ok("lint" in (pkg.scripts as Record<string, unknown>));
  });

  it("packageManager detects npm/pnpm/yarn by lockfile", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-q-"));
    assert.equal(packageManager(tmp), "npm");
    writeFileSync(join(tmp, "pnpm-lock.yaml"), "");
    assert.equal(packageManager(tmp), "pnpm");
  });

  it("detectQualityCommands: Python project STILL recognizes pytest/ruff/mypy (P1.3)", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-q-"));
    writeFileSync(join(tmp, "requirements.txt"), "pytest\nruff\nmypy\nflask");
    const pkg = detectPackage(tmp);
    const cmds = detectQualityCommands(tmp, pkg);
    const kinds = cmds.map((c) => c.kind);
    assert.ok(cmds.some((c) => c.kind === "test" && (c.command as string).includes("pytest")), "pytest must be detected");
    assert.ok(cmds.some((c) => c.kind === "lint" && (c.command as string).includes("ruff")), "ruff must be detected");
    assert.ok(cmds.some((c) => c.kind === "type-check" && (c.command as string).includes("mypy")), "mypy must be detected");
    void kinds;
  });

  it("detectQualityCommands: JS project infers eslint/tsc from config presence", () => {
    const tmp = mkdtempSync(join(tmpdir(), "pi-q-"));
    writeFileSync(
      join(tmp, "package.json"),
      JSON.stringify({ name: "demo", scripts: { test: "vitest" }, dependencies: {}, devDependencies: { typescript: "5" } })
    );
    writeFileSync(join(tmp, "tsconfig.json"), "{}");
    writeFileSync(join(tmp, "eslint.config.mjs"), "export default []");
    const pkg = detectPackage(tmp);
    const cmds = detectQualityCommands(tmp, pkg);
    assert.ok(cmds.some((c) => c.kind === "lint" && (c.command as string).includes("eslint")));
    assert.ok(cmds.some((c) => c.kind === "type-check" && (c.command as string).includes("tsc")));
    assert.ok(cmds.some((c) => c.kind === "test" && (c.command as string).includes("run test")));
  });
});
