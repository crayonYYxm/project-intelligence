import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { lstatSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

describe("ZCode plugin compatibility", () => {
  it("ships a root marketplace and native ZCode plugin manifest", () => {
    const packageJson = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
    const marketplace = JSON.parse(readFileSync(join(root, "marketplace.json"), "utf8"));
    const zcode = JSON.parse(readFileSync(
      join(root, "plugins/project-intelligence/.zcode-plugin/plugin.json"),
      "utf8"
    ));
    const plugin = marketplace.plugins.find((item: { name?: string }) => item.name === "project-intelligence");

    assert.equal(plugin?.source, "./plugins/project-intelligence");
    assert.equal(zcode.name, "project-intelligence");
    assert.equal(zcode.version, packageJson.version);
    assert.ok(packageJson.files.includes("marketplace.json"));
    assert.ok(packageJson.files.includes("plugins/project-intelligence/.zcode-plugin"));
  });

  it("contains no symbolic links in tracked distribution paths", () => {
    const distributionRoots = [
      "marketplace.json",
      ".claude-plugin",
      ".agents",
      "plugins/project-intelligence",
    ];
    const links: string[] = [];
    const visit = (path: string): void => {
      const stat = lstatSync(path);
      if (stat.isSymbolicLink()) {
        links.push(path);
        return;
      }
      if (!stat.isDirectory()) return;
      for (const entry of readdirSync(path)) visit(join(path, entry));
    };
    for (const path of distributionRoots) visit(join(root, path));
    assert.deepEqual(links, []);

    const tracked = spawnSync("git", ["ls-files", "-s"], { cwd: root, encoding: "utf8" });
    assert.equal(tracked.status, 0, tracked.stderr);
    const trackedLinks = tracked.stdout.split(/\r?\n/).filter((line) => line.startsWith("120000 "));
    assert.deepEqual(trackedLinks, []);
  });
});
