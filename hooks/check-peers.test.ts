// SPDX-License-Identifier: AGPL-3.0-only
import { afterEach, beforeEach, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { checkPeers } from "./check-peers";

let root: string;
function manifest(path: string, value: object) {
  const filename = join(root, path, "package.json");
  mkdirSync(dirname(filename), { recursive: true });
  writeFileSync(filename, JSON.stringify(value));
}

beforeEach(() => {
  root = mkdtempSync(join(tmpdir(), "edbfi-peers-"));
});
afterEach(() => rmSync(root, { recursive: true, force: true }));

function vitestPair(core: string, browser: string) {
  manifest("", { devDependencies: { vitest: core, "@vitest/browser-playwright": browser } });
  manifest("node_modules/vitest", { version: core });
  manifest("node_modules/@vitest/browser-playwright", {
    version: browser, peerDependencies: { vitest: browser },
  });
}

test("Vitest updates fail from either side until the pair matches", () => {
  vitestPair("5.0.0", "5.0.1");
  expect(checkPeers(root)).toEqual([
    "@vitest/browser-playwright: requires vitest@5.0.1, found 5.0.0",
  ]);
  vitestPair("5.0.1", "5.0.0");
  expect(checkPeers(root)).toEqual([
    "@vitest/browser-playwright: requires vitest@5.0.0, found 5.0.1",
  ]);
  vitestPair("5.0.1", "5.0.1");
  expect(checkPeers(root)).toEqual([]);
});

test("missing required peers fail; absent or incompatible optional peers are ignored", () => {
  manifest("", { dependencies: { vite: "8.3.0" } });
  manifest("node_modules/vite", {
    version: "8.3.0", peerDependencies: { esbuild: "^0.27.0", typescript: ">=6" },
    peerDependenciesMeta: { esbuild: { optional: true } },
  });
  expect(checkPeers(root)).toHaveLength(1);
  expect(checkPeers(root)[0]).toContain("requires typescript@>=6");
  manifest("node_modules/typescript", { version: "6.0.3" });
  manifest("node_modules/esbuild", { version: "0.28.2" });
  expect(checkPeers(root)).toEqual([]);
});

test("resolves peers next to the dependent, not the root", () => {
  manifest("", { dependencies: { plugin: "1.0.0" } });
  manifest("node_modules/plugin", { peerDependencies: { host: "^2" } });
  manifest("node_modules/host", { version: "1.0.0" });
  manifest("node_modules/plugin/node_modules/host", { version: "2.1.0" });
  expect(checkPeers(root)).toEqual([]);
  manifest("node_modules/host", { version: "2.1.0" });
  manifest("node_modules/plugin/node_modules/host", { version: "1.0.0" });
  expect(checkPeers(root)).toEqual(["plugin: requires host@^2, found 1.0.0"]);
});

test("Bun isolated symlinks and hidden package exports resolve without executing code", () => {
  manifest("", { dependencies: { plugin: "1.0.0" } });
  const store = "node_modules/.bun/plugin@1.0.0/node_modules";
  manifest(`${store}/plugin`, {
    version: "1.0.0", peerDependencies: { host: "^2" }, exports: "./throw.js",
  });
  writeFileSync(join(root, store, "plugin/throw.js"), "throw new Error('must not execute')");
  manifest(`${store}/host`, { version: "2.0.0", exports: { ".": "./index.js" } });
  symlinkSync(join(root, store, "plugin"), join(root, "node_modules/plugin"), "dir");
  manifest("node_modules/host", { version: "1.0.0" });
  expect(checkPeers(root)).toEqual([]);
});

test("checks production, development and installed optional direct dependencies", () => {
  manifest("", {
    dependencies: { prod: "1" }, devDependencies: { dev: "1" },
    optionalDependencies: { optional: "1", absent: "1" },
  });
  for (const name of ["prod", "dev", "optional"]) {
    manifest(`node_modules/${name}`, { peerDependencies: { missing: "*" } });
  }
  expect(checkPeers(root)).toHaveLength(3);
});

test("missing direct packages and malformed installed manifests fail", () => {
  manifest("", { dependencies: { missing: "1" } });
  expect(checkPeers(root)[0]).toContain("missing installed package missing");
  manifest("node_modules/missing", { peerDependencies: { peer: "^1" } });
  manifest("node_modules/peer", {});
  expect(checkPeers(root)[0]).toContain("found no version");
  writeFileSync(join(root, "node_modules/missing/package.json"), "{");
  expect(checkPeers(root)).toHaveLength(1);
});

test("supports separate matrix directories and fails the CLI on missing installs", () => {
  manifest("frontend", { dependencies: { missing: "1" } });
  manifest("", {});
  const command = Bun.spawnSync([
    process.execPath, join(import.meta.dir, "check-peers.ts"), ".", "frontend",
  ], { cwd: root });
  expect(command.exitCode).toBe(1);
  expect(command.stderr.toString()).toContain("frontend: missing:");
});
