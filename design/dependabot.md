# Dependabot

## Contract

1. Every entry MUST follow the schedule in its stack template.
2. Every entry MUST disable cooldown with the template exclusion and its scoped linter suppression (D2).
3. Every entry MUST use the template commit-message settings to produce Conventional Commit titles.
4. Groups MUST be, first match winning: `biome` (`@biomejs/*`); `playwright` (`playwright`, `@playwright/*`); `vitest` (`vitest`, `@vitest/*`); `slint` (EasyHDR: `slint`, `slint-build`); `compose-images` (setun); then `patch-minor` (`patterns: ["*"]`, `update-types: [minor, patch]`). The special groups may contain majors; other majors get one PR each.
5. There MUST NOT be any `ignore:` entry, pinned-back version or hold. A broken upstream release keeps its PR red until a later release fixes it.
6. Ecosystems and directories MUST follow [repos.md](repos.md#parameters). Every repo gets `github-actions` and `pre-commit`.
7. edbfi-ci's `github-actions` entry MUST cover `/templates` and its `pre-commit` entry `/templates/pre-commit/*`, each as well as `/`, so Dependabot moves the template pins; every pin keeps its `# vX.Y.Z` or `# frozen: vX.Y.Z` comment, which Dependabot rewrites with the SHA.

## Parameters

- Configs: [Bun](../templates/dependabot.bun-web.yml), [setun](../templates/dependabot.setun.yml), [Python](../templates/dependabot.python.yml), [Python + Bun](../templates/dependabot.python-bun.yml), [Rust](../templates/dependabot.rust.yml), [Zig](../templates/dependabot.zig.yml), [Homebrew](../templates/dependabot.homebrew.yml), [Shell](../templates/dependabot.shell.yml), [Content](../templates/dependabot.content.yml), [Special](../templates/dependabot.special.yml).
- Copy the matching config to `.github/dependabot.yml`; adapt ecosystems and directories to [repos.md](repos.md#parameters).

- Every `bun.lock` in the Bun directories of [repos.md](repos.md#parameters) is lockfile v2 [V, 2026-10-07]. Dependabot's `bun` updater keeps it v2, with exact pins and `npm:` aliases (`@typescript/native`) intact [V, 2026-10-11, portaler#124].
- The template cooldown exclusion permits updates less than 3 days after release [V, 2026-09-30, playground].
- A security PR opened before `dependabot.yml` lands can't be rebased afterwards, and closing it doesn't make Dependabot recreate it, so a rollout turns on security updates only after its rollout PR merges [V, 2026-10-08, wtfnzb-adapter#6].

## Verification

- zizmor passes on `dependabot.yml` with only the per-entry `dependabot-cooldown` suppressions. It sometimes misses a finding on a later entry, so read every entry.
- `rg -n 'ignore:' .github/dependabot.yml` finds nothing.
- The first run after rollout opens PRs with `chore(deps…)` titles, grouped as above.

## Open

- dependabot-A1: a scheduled weekly run opens version PRs. Every `github-actions` bump seen so far came from a `dependabot.yml` change, not the schedule. Closes when the 2026-10-13 run opens the pending bumps (`upload-artifact` 7.0.2, `setup-uv` 10.3.0) in repos that still lack them.

## Why

- Omitting `cooldown` gives a 3-day default, and `default-days: 0` violates the schema (minimum 1); zizmor fails all three forms without the suppression.
- `@vitest/*` packages pin `vitest` exactly, so they must move together.
- For `/` the `github-actions` updater reads only `.github/workflows` and a root `action.yml`; for any other directory it reads that directory's own `*.yml`, so `templates/` needs its own entry.
- Example of a hold refused: the TypeScript 7 PRs sit red ([B7](../DECISIONS.md#blockers)).
- Dependabot never re-locks a separate lockfile behind a path dependency (dependabot-core#11500), so EasyHDR's `fuzz/` is a root workspace member with no entry of its own.
