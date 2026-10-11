# Dependabot

## Contract

1. Every entry MUST follow the schedule in its stack template; replex and the fuzz project use their monthly variants.
2. Every entry MUST disable cooldown with the template exclusion and its scoped linter suppression (D2).
3. Every entry MUST use the template commit-message settings to produce Conventional Commit titles.
4. Groups MUST be, first match winning: `biome` (`@biomejs/*`); `playwright` (`playwright`, `@playwright/*`); `vitest` (`vitest`, `@vitest/*`); `slint` (EasyHDR: `slint`, `slint-build`); `compose-images` (setun); then `patch-minor` (`patterns: ["*"]`, `update-types: [minor, patch]`). The special groups may contain majors; other majors get one PR each.
5. There MUST NOT be any `ignore:` entry, pinned-back version or hold. A broken upstream release keeps its PR red until a later release fixes it.
6. Ecosystems and directories MUST follow [repos.md](repos.md#parameters). Every repo gets `github-actions` and `pre-commit`.

## Parameters

- Configs: [Bun](../templates/dependabot.bun-web.yml), [setun](../templates/dependabot.setun.yml), [Python](../templates/dependabot.python.yml), [Python + Bun](../templates/dependabot.python-bun.yml), [Rust](../templates/dependabot.rust.yml), [Zig](../templates/dependabot.zig.yml), [Homebrew](../templates/dependabot.homebrew.yml), [Shell](../templates/dependabot.shell.yml), [Content](../templates/dependabot.content.yml), [Special](../templates/dependabot.special.yml), [replex](../templates/dependabot.replex.yml).
- Copy the matching config to `.github/dependabot.yml`; adapt ecosystems and directories to [repos.md](repos.md#parameters).

- Every `bun.lock` in the Bun directories of [repos.md](repos.md#parameters) is lockfile v2 [V, 2026-10-07]. Dependabot's `bun` updater keeps it v2, with exact pins and `npm:` aliases (`@typescript/native`) intact [V, 2026-10-11, portaler#124].
- The template cooldown exclusion permits updates less than 3 days after release [V, 2026-09-30, playground].
- A security PR opened before `dependabot.yml` lands can't be rebased afterwards, and closing it doesn't make Dependabot recreate it, so a rollout turns on security updates only after its rollout PR merges [V, 2026-10-08, wtfnzb-adapter#6].

## Verification

- zizmor passes on `dependabot.yml` with only the per-entry `dependabot-cooldown` suppressions. It sometimes misses a finding on a later entry, so read every entry.
- `rg -n 'ignore:' .github/dependabot.yml` finds nothing.
- The first run after rollout opens PRs with `chore(deps…)` titles, grouped as above.

## Open

- None.

## Why

- Omitting `cooldown` gives a 3-day default, and `default-days: 0` violates the schema (minimum 1); zizmor fails all three forms without the suppression.
- `@vitest/*` packages pin `vitest` exactly, so they must move together.
- Example of a hold refused: a TypeScript 7 PR sits red until `svelte-check` and the Kit peers accept it.
