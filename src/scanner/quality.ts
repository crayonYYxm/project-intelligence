// Package + quality-command detection (phase 3.A.4), ported from quality.py.
//
// Per the migration requirement (P1.3): the product itself must not depend on
// Python, but scanning a Python repository must STILL recognize pytest/ruff/mypy
// as the scanned project's quality commands. The detected command strings are
// the scanned project's commands (run by that project's toolchain), not the
// product's runtime — so detecting `pytest`/`ruff`/`mypy` is correct and
// preserved. The product's own runtime never invokes these.

import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";

export const EXCLUDED_PACKAGE_PARTS = new Set([
  "node_modules",
  "dist",
  "build",
  ".git",
  ".project-intel",
  ".next",
  ".nuxt",
]);

function loadJson(path: string): Record<string, unknown> {
  try {
    const payload = JSON.parse(readFileSync(path, "utf8"));
    return payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
  } catch {
    return {};
  }
}

function isDir(path: string): boolean {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
}

function globPackageJson(dir: string): string[] {
  try {
    return readdirSync(dir)
      .map((name) => join(dir, name, "package.json"))
      .filter((p) => {
        try {
          return statSync(p).isFile();
        } catch {
          return false;
        }
      });
  } catch {
    return [];
  }
}

export function workspacePackageFiles(root: string, rootPackage: Record<string, unknown>): string[] {
  const workspacesRaw = rootPackage.workspaces;
  let patterns: string[] = [];
  if (Array.isArray(workspacesRaw)) {
    patterns = workspacesRaw.filter((s): s is string => typeof s === "string");
  } else if (workspacesRaw && typeof workspacesRaw === "object") {
    const pkg = (workspacesRaw as Record<string, unknown>).packages;
    if (Array.isArray(pkg)) {
      patterns = pkg.filter((s): s is string => typeof s === "string");
    }
  }
  const candidates = new Set<string>();
  for (const pattern of patterns) {
    const normalized = pattern.replace(/\/$/, "");
    // Support simple glob like "packages/*"
    if (normalized.includes("*")) {
      const base = normalized.split("*")[0]!.replace(/\/$/, "");
      const dir = join(root, base);
      if (isDir(dir)) {
        for (const pkg of globPackageJson(dir)) candidates.add(pkg);
      }
    } else {
      const dir = join(root, normalized);
      const pkg = join(dir, "package.json");
      if (existsSync(pkg)) candidates.add(pkg);
    }
  }
  if (!patterns.length) {
    for (const parent of ["apps", "packages", "services", "frontend", "backend"]) {
      const base = join(root, parent);
      if (isDir(base)) for (const pkg of globPackageJson(base)) candidates.add(pkg);
    }
  }
  return [...candidates]
    .filter((p) => {
      const rel = p.slice(root.length + 1).split("\\").join("/").split("/");
      return !rel.some((part) => EXCLUDED_PACKAGE_PARTS.has(part));
    })
    .sort();
}

const FRAMEWORK_MARKERS: Record<string, string[]> = {
  Vue: ["vue", "@vitejs/plugin-vue", "nuxt"],
  React: ["react", "next", "@vitejs/plugin-react"],
  Vite: ["vite"],
  NestJS: ["@nestjs/core", "@nestjs/common"],
  Express: ["express"],
  Koa: ["koa"],
  Fastify: ["fastify"],
  TypeScript: ["typescript"],
  "Element Plus": ["element-plus"],
  Pinia: ["pinia"],
  "Vue Router": ["vue-router"],
  Redux: ["redux", "@reduxjs/toolkit"],
};

export function packageFrameworks(deps: Record<string, unknown>): string[] {
  const frameworks: string[] = [];
  for (const [name, markers] of Object.entries(FRAMEWORK_MARKERS)) {
    if (markers.some((marker) => marker in deps)) frameworks.push(name);
  }
  return frameworks;
}

export function detectPackage(root: string): Record<string, unknown> {
  const rootPayload = loadJson(join(root, "package.json"));
  const rootHas = Object.keys(rootPayload).length > 0;
  const packageFiles = (rootHas ? [join(root, "package.json")] : []).concat(workspacePackageFiles(root, rootPayload));
  const packages: Record<string, unknown>[] = [];
  const frameworks = new Set<string>();
  for (const path of packageFiles) {
    const payload = path === join(root, "package.json") && rootHas ? rootPayload : loadJson(path);
    const deps: Record<string, unknown> = {};
    for (const key of ["dependencies", "devDependencies", "peerDependencies"]) {
      Object.assign(deps, (payload[key] as Record<string, unknown>) ?? {});
    }
    const detected = packageFrameworks(deps);
    detected.forEach((f) => frameworks.add(f));
    packages.push({
      path: relative(root, dirname(path)).replace(/\\/g, "/") || ".",
      name: payload.name,
      scripts: (payload.scripts as Record<string, unknown>) ?? {},
      frameworks: detected,
    });
  }
  const nonJsMarkers: Record<string, string[]> = {
    "Java/Spring": ["pom.xml", "build.gradle", "build.gradle.kts"],
    Python: ["pyproject.toml", "requirements.txt", "manage.py"],
    Go: ["go.mod"],
    Rust: ["Cargo.toml"],
  };
  for (const [name, markers] of Object.entries(nonJsMarkers)) {
    if (markers.some((m) => existsSync(join(root, m)))) frameworks.add(name);
  }
  return {
    packageName: rootPayload.name,
    scripts: (rootPayload.scripts as Record<string, unknown>) ?? {},
    frameworks: [...frameworks].sort(),
    hasPackageJson: rootHas,
    packages,
    workspace: packages.length > 1,
  };
}

export function packageManager(root: string): string {
  if (existsSync(join(root, "pnpm-lock.yaml"))) return "pnpm";
  if (existsSync(join(root, "yarn.lock"))) return "yarn";
  return "npm";
}

export function packageScriptCommand(manager: string, directory: string, script: string): string {
  if (directory === "" || directory === ".") return `${manager} run ${script}`;
  if (manager === "pnpm") return `pnpm --dir ${directory} run ${script}`;
  if (manager === "yarn") return `yarn --cwd ${directory} run ${script}`;
  return `npm --prefix ${directory} run ${script}`;
}

function appendUnique(commands: Record<string, unknown>[], item: Record<string, unknown>): void {
  if (item.command && !commands.some((c) => c.command === item.command)) commands.push(item);
}

export function detectQualityCommands(root: string, pkg: Record<string, unknown>): Record<string, unknown>[] {
  const commands: Record<string, unknown>[] = [];
  const aliases: Record<string, string[]> = {
    lint: ["lint", "lint:eslint", "eslint"],
    "type-check": ["type-check", "typecheck", "check-types", "vue-tsc", "tsc"],
    "format-check": ["format:check", "prettier:check", "check:format"],
    "style-check": ["stylelint", "lint:style", "style:check"],
    test: ["test", "test:unit", "unit"],
  };
  const manager = packageManager(root);
  const packages = (pkg.packages as Record<string, unknown>[]) ?? (pkg.hasPackageJson ? [{ path: ".", scripts: pkg.scripts }] : []);
  for (const workspace of packages) {
    const directory = (workspace.path as string) || ".";
    const scripts = (workspace.scripts as Record<string, unknown>) ?? {};
    for (const [kind, names] of Object.entries(aliases)) {
      for (const name of names) {
        if (name in scripts) {
          appendUnique(commands, {
            kind,
            command: packageScriptCommand(manager, directory, name),
            source: directory === "." ? "package.json" : `${directory}/package.json`,
          });
          break;
        }
      }
    }
  }
  const rootKinds = new Set(commands.filter((c) => c.source === "package.json").map((c) => c.kind));
  if (!rootKinds.has("lint") && ["eslint.config.js", "eslint.config.mjs", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json"].some((n) => existsSync(join(root, n)))) {
    appendUnique(commands, { kind: "lint", command: "npx eslint .", source: "inferred" });
  }
  if (!rootKinds.has("type-check") && existsSync(join(root, "tsconfig.json"))) {
    const command = (pkg.frameworks as string[] | undefined)?.includes("Vue") ? "npx vue-tsc --noEmit" : "npx tsc --noEmit";
    appendUnique(commands, { kind: "type-check", command, source: "inferred" });
  }
  if (!rootKinds.has("style-check") && ["stylelint.config.js", "stylelint.config.cjs", ".stylelintrc", ".stylelintrc.js"].some((n) => existsSync(join(root, n)))) {
    appendUnique(commands, { kind: "style-check", command: 'npx stylelint "**/*.{css,scss,vue}"', source: "inferred" });
  }
  if (!rootKinds.has("format-check") && ["prettier.config.js", "prettier.config.cjs", ".prettierrc", ".prettierrc.js", ".prettierrc.json"].some((n) => existsSync(join(root, n)))) {
    appendUnique(commands, { kind: "format-check", command: "npx prettier --check .", source: "inferred" });
  }

  // Java
  if (existsSync(join(root, "pom.xml"))) {
    const mvn = existsSync(join(root, "mvnw")) ? "./mvnw" : "mvn";
    appendUnique(commands, { kind: "test", command: `${mvn} test`, source: "pom.xml" });
    appendUnique(commands, { kind: "verify", command: `${mvn} verify`, source: "pom.xml" });
  }
  if (existsSync(join(root, "build.gradle")) || existsSync(join(root, "build.gradle.kts"))) {
    const gradle = existsSync(join(root, "gradlew")) ? "./gradlew" : "gradle";
    appendUnique(commands, { kind: "test", command: `${gradle} test`, source: "gradle" });
    appendUnique(commands, { kind: "verify", command: `${gradle} check`, source: "gradle" });
  }
  // Python — STILL recognize pytest/ruff/mypy as the scanned project's commands (P1.3).
  if (existsSync(join(root, "pyproject.toml")) || existsSync(join(root, "requirements.txt"))) {
    let combined = "";
    try {
      if (existsSync(join(root, "pyproject.toml"))) combined += readFileSync(join(root, "pyproject.toml"), "utf8");
    } catch {
      /* ignore */
    }
    try {
      if (existsSync(join(root, "requirements.txt"))) combined += "\n" + readFileSync(join(root, "requirements.txt"), "utf8");
    } catch {
      /* ignore */
    }
    const lower = combined.toLowerCase();
    if (lower.includes("pytest") || isDir(join(root, "tests"))) {
      appendUnique(commands, { kind: "test", command: "pytest", source: "python-project" });
    }
    if (lower.includes("ruff")) {
      appendUnique(commands, { kind: "lint", command: "ruff check .", source: "python-project" });
    }
    if (lower.includes("mypy")) {
      appendUnique(commands, { kind: "type-check", command: "mypy .", source: "python-project" });
    }
  }
  if (existsSync(join(root, "go.mod"))) {
    appendUnique(commands, { kind: "test", command: "go test ./...", source: "go.mod" });
    appendUnique(commands, { kind: "verify", command: "go vet ./...", source: "go.mod" });
  }
  if (existsSync(join(root, "Cargo.toml"))) {
    appendUnique(commands, { kind: "type-check", command: "cargo check", source: "Cargo.toml" });
    appendUnique(commands, { kind: "test", command: "cargo test", source: "Cargo.toml" });
    appendUnique(commands, { kind: "format-check", command: "cargo fmt -- --check", source: "Cargo.toml" });
  }
  return commands;
}
