#!/usr/bin/env bun
// SPDX-License-Identifier: AGPL-3.0-only
import { existsSync, readFileSync, realpathSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

type Manifest = {
  version?: string;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  optionalDependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  peerDependenciesMeta?: Record<string, { optional?: boolean }>;
};

function readManifest(path: string): Manifest {
  return JSON.parse(readFileSync(path, "utf8"));
}

// Walk node_modules from the dependent's real location, including Bun's isolated
// symlink layout. Read manifests directly: package exports may hide package.json.
function resolveManifest(name: string, from: string): string {
  for (let dir = realpathSync(from); ; dir = dirname(dir)) {
    const candidate = join(dir, "node_modules", name, "package.json");
    if (existsSync(candidate)) return realpathSync(candidate);
    if (dirname(dir) === dir) throw new Error(`missing installed package ${name}`);
  }
}

export function checkPeers(directory: string): string[] {
  const root = resolve(directory);
  const manifest = readManifest(join(root, "package.json"));
  const dependencies = {
    ...manifest.dependencies,
    ...manifest.devDependencies,
    ...manifest.optionalDependencies,
  };
  const findings: string[] = [];
  for (const name of Object.keys(dependencies).sort()) {
    let path: string;
    try {
      path = resolveManifest(name, root);
    } catch (error) {
      // An optional direct package may be absent on this platform.
      if (name in (manifest.optionalDependencies ?? {})) continue;
      findings.push(`${name}: ${String(error)}`);
      continue;
    }
    try {
      const dependent = readManifest(path);
      for (const [peer, range] of Object.entries(dependent.peerDependencies ?? {})) {
        if (dependent.peerDependenciesMeta?.[peer]?.optional === true) continue;
        try {
          const installed = readManifest(resolveManifest(peer, dirname(path)));
          if (!installed.version || !Bun.semver.satisfies(installed.version, range)) {
            findings.push(`${name}: requires ${peer}@${range}, found ${installed.version ?? "no version"}`);
          }
        } catch (error) {
          findings.push(`${name}: requires ${peer}@${range}: ${String(error)}`);
        }
      }
    } catch (error) {
      findings.push(`${name}: ${String(error)}`);
    }
  }
  return findings;
}

if (import.meta.main) {
  const directories = process.argv.slice(2);
  for (const directory of directories.length ? directories : ["."]) {
    try {
      const findings = checkPeers(directory);
      for (const finding of findings) console.error(`${directory}: ${finding}`);
      if (findings.length) process.exitCode = 1;
    } catch (error) {
      console.error(`${directory}: ${String(error)}`);
      process.exitCode = 1;
    }
  }
}
