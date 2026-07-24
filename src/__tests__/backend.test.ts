import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { scanBackend, scanBackendFile, maskCommentsAndStrings, BACKEND_SUFFIXES } from "../scanner/backend.js";

describe("maskCommentsAndStrings", () => {
  it("masks line and block comments and string contents", () => {
    const src = "const a = 'secret'; // comment\n/* block */ let b = `tmpl`;";
    const masked = maskCommentsAndStrings(src);
    assert.ok(!masked.includes("secret"));
    assert.ok(!masked.includes("comment"));
    assert.ok(!masked.includes("block"));
    assert.ok(!masked.includes("tmpl"));
    // structure preserved (positions intact)
    assert.equal(masked.length, src.length);
  });
});

describe("scanBackendFile", () => {
  it("extracts a Spring controller endpoint and methods (.java)", () => {
    const java = [
      "@RestController",
      "@RequestMapping(\"/orders\")",
      "public class OrderController {",
      "  @GetMapping(\"/list\")",
      "  public List<Order> list() { return null; }",
      "  @PostMapping",
      "  public void create(@RequestBody Order o) {}",
      "}",
    ].join("\n");
    const f = scanBackendFile("src/main/java/OrderController.java", java);
    assert.equal(f.apis.length, 1);
    assert.equal((f.apis[0] as { framework: string }).framework, "Spring");
    const endpoints = (f.apis[0] as { endpoints: string[] }).endpoints;
    assert.ok(endpoints.includes("/orders"));
    assert.ok(endpoints.includes("/list"));
    assert.deepEqual((f.apis[0] as { signals: string[] }).signals, [
      "GetMapping",
      "PostMapping",
      "RequestMapping",
      "RestController",
    ]);
  });

  it("extracts Python def/class and Flask routes (.py)", () => {
    const py = [
      "from flask import Blueprint",
      "bp = Blueprint('orders', __name__)",
      "",
      "@bp.route('/orders', methods=['POST'])",
      "def create_order():",
      "    return '', 201",
      "",
      "class OrderService:",
      "    def submit(self, order_id):",
      "        pass",
    ].join("\n");
    const f = scanBackendFile("backend/api.py", py);
    assert.equal(f.apis.length, 1);
    const endpoints = (f.apis[0] as { endpoints: string[] }).endpoints;
    assert.ok(endpoints.includes("/orders"));
    assert.equal((f.apis[0] as { framework: string }).framework, "FastAPI/Flask");
    assert.equal((f.apis[0] as { parser: string }).parser, "python-ast");
  });

  it("classifies a service by name and extracts transaction signals", () => {
    const py = [
      "class OrderService:",
      "    def create(self):",
      "        with transaction():",
      "            pass",
    ].join("\n");
    const f = scanBackendFile("backend/OrderService.py", py);
    assert.equal(f.services.length, 1);
    assert.equal((f.services[0] as { name: string }).name, "OrderService");
    assert.ok((f.transactions[0] as { signals: string[] }).signals.length > 0);
  });

  it("extracts config keys from yaml", () => {
    const yaml = "server:\n  port: 8080\ndb:\n  url: jdbc\n";
    const f = scanBackendFile("config/app.yaml", yaml);
    assert.equal(f.configs.length, 1);
    const keys = (f.configs[0] as { keys: string[] }).keys;
    assert.ok(keys.includes("server"));
    assert.ok(keys.includes("db"));
  });

  it("classifies repository files and extracts SQL ops from xml mapper", () => {
    const xml = [
      "<mapper namespace=\"x\">",
      "  <select id=\"findById\">SELECT * FROM t</select>",
      "  <delete id=\"remove\">DELETE FROM t</delete>",
      "</mapper>",
    ].join("\n");
    const f = scanBackendFile("mapper/OrderMapper.xml", xml);
    assert.equal(f.repositories.length, 1);
    assert.equal((f.repositories[0] as { kind: string }).kind, "Mapper");
    const sqlOps = (f.repositories[0] as { sqlOps: string[] }).sqlOps;
    assert.ok(sqlOps.includes("SELECT"));
    assert.ok(sqlOps.includes("DELETE"));
  });

  it("extracts permission signals", () => {
    const java = "@PreAuthorize(\"hasRole('ADMIN')\")\npublic void secure() {}";
    const f = scanBackendFile("a.java", java);
    assert.ok(f.permissionChecks.length > 0);
  });

  it("extracts error code signals", () => {
    const py = "throw new BusinessException('ERR_001')\nNOT_FOUND_ERROR = 1";
    const f = scanBackendFile("a.py", py);
    assert.ok(f.errorCodes.length > 0);
  });

  it("requires bound framework imports and keeps Django class views", () => {
    const fake = scanBackendFile("fake.py", "@app.get('/fake')\ndef fake_route():\n    pass\n");
    assert.equal(fake.apis.length, 0);
    const django = scanBackendFile(
      "views.py",
      "from rest_framework.views import APIView\nclass HealthView(APIView):\n    def get(self, request):\n        return None\n"
    );
    assert.equal(django.apis.length, 1);
    assert.equal((django.apis[0] as { framework: string }).framework, "Django");
  });

  it("labels malformed Python without accepting route facts", () => {
    const facts = scanBackendFile(
      "broken.py",
      "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/broken')\ndef broken(\n"
    );
    assert.equal(facts.scanMode, "python-syntax-error");
    assert.equal(facts.apis.length, 0);
  });

  it("applies configured backend entrypoint rules", () => {
    const result = scanBackend(
      [{ path: "OrderController.java", text: "@RestController class OrderController {}" }],
      {
        backend: {
          entrypointRules: [{ type: "annotation", pattern: "@RestController" }],
        },
      }
    );
    assert.deepEqual((result.apis[0] as { signals: string[] }).signals, [
      "RestController",
      "config:annotation:1",
    ]);
  });
});

describe("BACKEND_SUFFIXES", () => {
  it("includes java, kt, py, go, ts, js", () => {
    for (const s of [".java", ".kt", ".py", ".go", ".ts", ".js"]) assert.ok(BACKEND_SUFFIXES.has(s));
  });
});
