import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { runInit, ensureProjectIntelGitignore, projectIntelDir } from "../commands/init.js";
import { runDoctor, doctorReport } from "../commands/doctor.js";
import { runCheck } from "../commands/check.js";
import { inferStandards } from "../standards/infer.js";
import { projectDomainCandidates } from "../standards/domains.js";
import { standardsDocs } from "../standards/docs.js";
import { evaluateHardRules, DEFAULT_HARD_RULES, type HardRuleContext } from "../rules/hard.js";

function seedProject(dir: string): void {
  mkdirSync(join(dir, "backend"), { recursive: true });
  mkdirSync(join(dir, "src/components"), { recursive: true });
  writeFileSync(join(dir, "backend/OrderService.py"), "class OrderService:\n    def create(self): pass\n");
  writeFileSync(join(dir, "backend/OrderDTO.py"), "class OrderDTO: pass\n");
  writeFileSync(join(dir, "src/components/OrderForm.vue"), "<template><div /></template>");
  writeFileSync(join(dir, "package.json"), JSON.stringify({ name: "demo", version: "1.0.0" }));
}

const noopGlobal = { project: null, jsonMode: false } as never;

describe("init command", () => {
  it("writes the .project-intel layout (manifest/config/knowledge/status)", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-init-"));
    seedProject(dir);
    const result = runInit(dir, ["--no-graph"], noopGlobal, false);
    assert.equal(result.exitCode, 0);
    const pdir = projectIntelDir(dir);
    for (const f of ["manifest.json", "config.json", "knowledge/frontend.json", "knowledge/backend.json", "knowledge/files.json", "project-status.md"]) {
      assert.ok(existsSync(join(pdir, f)), `missing ${f}`);
    }
    const manifest = JSON.parse(readFileSync(join(pdir, "manifest.json"), "utf8"));
    assert.equal(manifest.schemaVersion, 2);
    assert.equal(manifest.projectRoot, ".");
    assert.ok(typeof manifest.fileCount === "number" && manifest.fileCount > 0);
  });

  it("--dry-run does not write files", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-init-"));
    seedProject(dir);
    const result = runInit(dir, ["--dry-run", "--no-graph"], noopGlobal, false);
    assert.equal(result.exitCode, 0);
    assert.ok(!existsSync(join(projectIntelDir(dir), "manifest.json")));
  });

  it("refresh re-writes without tooling", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-init-"));
    seedProject(dir);
    runInit(dir, ["--no-graph"], noopGlobal, false);
    const result = runInit(dir, ["--no-graph"], noopGlobal, true);
    assert.equal(result.exitCode, 0);
    assert.ok(existsSync(join(projectIntelDir(dir), "manifest.json")));
  });

  it("strict + no-graph is a usage error", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-init-"));
    assert.throws(() => runInit(dir, ["--strict", "--no-graph"], noopGlobal, false));
  });

  it("ensureProjectIntelGitignore writes local-only rules", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-gi-"));
    mkdirSync(dir, { recursive: true });
    ensureProjectIntelGitignore(dir);
    const text = readFileSync(join(dir, ".gitignore"), "utf8");
    assert.ok(text.includes("cache/"));
    assert.ok(text.includes("local/"));
  });
});

describe("doctor command", () => {
  it("reports node runtime, not python", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-doc-"));
    seedProject(dir);
    const report = doctorReport(dir);
    assert.equal((report.runtime as Record<string, unknown>).name, "node");
    assert.ok(!("python" in report));
  });

  it("detects initialized state after init", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-doc-"));
    seedProject(dir);
    runInit(dir, ["--no-graph"], noopGlobal, false);
    const report = doctorReport(dir);
    assert.equal((report.project as Record<string, unknown>).initialized, true);
  });
});

describe("check command", () => {
  it("passes with no hard rules configured", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-chk-"));
    seedProject(dir);
    runInit(dir, ["--no-graph"], noopGlobal, false);
    const result = runCheck(dir, [], noopGlobal);
    assert.equal(result.exitCode, 0);
  });

  it("--dry-run does not write status", () => {
    const dir = mkdtempSync(join(tmpdir(), "pi-chk-"));
    seedProject(dir);
    runInit(dir, ["--no-graph"], noopGlobal, false);
    const statusPath = join(projectIntelDir(dir), "project-status.md");
    const before = existsSync(statusPath) ? readFileSync(statusPath, "utf8") : "";
    runCheck(dir, ["--dry-run"], noopGlobal);
    const after = readFileSync(statusPath, "utf8");
    assert.equal(after, before);
  });
});

describe("standards inference", () => {
  it("infers PascalCase naming from >=3 pascal components", () => {
    const frontend = {
      components: [{ name: "OrderForm" }, { name: "UserCard" }, { name: "NavBar" }],
    };
    const rules = inferStandards(frontend as never, {} as never);
    assert.ok(rules.some((r) => r.category === "naming" && r.rule.includes("PascalCase")));
  });

  it("infers backend Service suffix from >=2 services", () => {
    const backend = { services: [{ name: "OrderService" }, { name: "UserService" }] };
    const rules = inferStandards({} as never, backend as never);
    assert.ok(rules.some((r) => r.scope === "backend" && r.rule === "服务类使用 Service 等后缀命名"));
  });

  it("infers ui-pattern from redundancy candidates", () => {
    const frontend = { redundancyCandidates: [{ name: "table", count: 5, locations: ["a", "b"] }] };
    const rules = inferStandards(frontend as never, {} as never);
    assert.ok(rules.some((r) => r.category === "ui-pattern" && r.rule.includes("table")));
  });

  it("ports backend API, layering and operational inference categories", () => {
    const backend = {
      apis: [
        { framework: "Spring", signals: ["RestController"] },
        { framework: "Spring", signals: ["RestController"] },
      ],
      services: [{ name: "OrderService" }, { name: "UserService" }],
      dataTypes: [{ name: "OrderDTO" }, { name: "UserDTO" }],
      repositories: [{ name: "OrderRepository" }],
      configs: [{ keys: ["server.port"] }],
      permissionChecks: [{}],
      transactions: [{}],
      remoteCalls: [{}],
      messagesJobs: [{}],
      errorCodes: [{}],
      utilities: [{}],
    };
    const categories = new Set(inferStandards({}, backend).map((rule) => rule.category));
    for (const category of [
      "backend-layering", "backend-api", "config", "permission", "transaction",
      "remote-call", "message-job", "error-code", "utility",
    ]) {
      assert.ok(categories.has(category), `missing ${category}`);
    }
  });
});

describe("project domain candidates", () => {
  it("aggregates repeated non-generic parent segments in stable order", () => {
    const domains = projectDomainCandidates(
      { components: [{ path: "src/orders/components/Form.vue" }] },
      { services: [{ path: "backend/orders/OrderService.py" }] },
      { understandSummary: { domains: [] } }
    );
    assert.deepEqual(domains, [{
      name: "orders",
      count: 2,
      paths: ["src/orders/components/Form.vue", "backend/orders/OrderService.py"],
      source: "project-derived",
    }]);
  });
});

describe("standards documents", () => {
  it("renders detailed frontend and backend facts instead of count-only placeholders", () => {
    const docs = standardsDocs({
      frontend: {
        components: [{
          name: "DxDialog",
          path: "src/components/DxDialog.vue",
          scope: "public",
          props: ["visible"],
          emits: ["update:visible"],
        }],
        hooks: [],
        routes: [{ path: "src/router/order.ts", baseUrls: ["pages/order/"], routeCount: 2 }],
        apiModules: [{
          path: "src/api/order.ts",
          wrappers: ["request"],
          servicePrefixes: [{ name: "orderService", value: "/order-service" }],
          endpoints: ["/orders/create"],
          exports: ["createOrder"],
        }],
        stores: [],
        styles: [],
        redundancyCandidates: [],
        scanMode: "regex-fallback",
      },
      backend: {
        apis: [{ path: "OrderController.java", framework: "Spring", signals: ["RestController"], endpoints: ["/orders"], methods: ["list"] }],
        services: [{ name: "OrderService", path: "OrderService.java", methods: ["createOrder"] }],
        dataTypes: [{ name: "OrderDTO", path: "OrderDTO.java", kind: "DTO/VO/Model", fields: ["orderId"] }],
        repositories: [{ name: "OrderRepository", path: "OrderRepository.java", kind: "Repository/DAO", methods: ["findOrder"], sqlOps: ["SELECT"] }],
        configs: [{ path: "application.yml", kind: "yml", keys: ["order.timeout"] }],
        permissionChecks: [{ path: "OrderController.java", signals: ["PreAuthorize"], level: "candidate" }],
        transactions: [{ path: "OrderService.java", signals: ["Transactional"], level: "candidate" }],
        remoteCalls: [{ path: "OrderService.java", signals: ["RestTemplate"], level: "candidate" }],
        messagesJobs: [{ path: "OrderJob.java", signals: ["Scheduled"], level: "candidate" }],
        errorCodes: [{ path: "OrderService.java", signals: ["ORDER_FAILED"], level: "candidate" }],
        utilities: [{ name: "OrderUtils", path: "common/OrderUtils.java", exports: ["normalizeOrder"] }],
        candidateEntrypoints: [],
        testFixtures: [],
        scanModes: ["regex-fallback"],
      },
      config: { quality: { commands: [] }, rules: { inferred: [] } },
      graph: { understandSummary: { domains: [], keyModules: [], topPathPrefixes: [] } },
      files: [],
      package: { packageName: "fixture", frameworks: [], packages: [], scripts: {} },
      manifest: {},
      tooling: {},
      scanCache: { schemaVersion: 1, entries: {} },
    } as never);
    assert.match(docs["components.md"] ?? "", /DxDialog/);
    assert.match(docs["api.md"] ?? "", /\/order-service/);
    assert.match(docs["router.md"] ?? "", /pages\/order/);
    assert.match(docs["backend-services.md"] ?? "", /OrderService/);
    assert.match(docs["backend-models.md"] ?? "", /OrderDTO/);
    assert.match(docs["backend-repository.md"] ?? "", /OrderRepository/);
    assert.match(docs["backend-config.md"] ?? "", /order.timeout/);
    assert.match(docs["backend-security.md"] ?? "", /PreAuthorize/);
    assert.match(docs["backend-transactions.md"] ?? "", /Transactional/);
    assert.match(docs["backend-remote-calls.md"] ?? "", /RestTemplate/);
    assert.match(docs["backend-async.md"] ?? "", /Scheduled/);
    assert.match(docs["backend-errors.md"] ?? "", /ORDER_FAILED/);
    assert.match(docs["backend-utilities.md"] ?? "", /OrderUtils/);
  });
});

describe("hard rules engine", () => {
  it("returns no violations with the empty default set", () => {
    const ctx: HardRuleContext = { manifest: {}, config: {}, frontend: {}, backend: {} };
    assert.deepEqual(evaluateHardRules(DEFAULT_HARD_RULES, ctx), []);
  });

  it("surfaces a registered rule violation", () => {
    const rule = {
      id: "TEST-1",
      description: "always violates",
      evaluate: () => "forced violation",
    };
    const ctx: HardRuleContext = { manifest: {}, config: {}, frontend: {}, backend: {} };
    const v = evaluateHardRules([rule], ctx);
    assert.match(v[0]!, /TEST-1.*forced violation/);
  });
});
