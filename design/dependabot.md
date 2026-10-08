# Dependabot

## Contract

1. Every entry MUST follow the schedule in its stack template; replex and the fuzz project use their monthly variants.
2. Every entry MUST disable cooldown with the template exclusion and its scoped linter suppression (D2).
3. Every entry MUST use the template commit-message settings to produce Conventional Commit titles.
4. Groups MUST be, first match winning: `biome` (`@biomejs/*`); `playwright` (`playwright`, `@playwright/*`); `vitest` (`vitest`, `@vitest/*`); `slint` (EasyHDR: `slint`, `slint-build`); `compose-images` (setun); then `patch-minor` (`patterns: ["*"]`, `update-types: [minor, patch]`). The special groups may contain majors; other majors get one PR each.
5. There MUST NOT be any `ignore:` entry, pinned-back version or hold. A broken upstream release keeps its PR red until a later release fixes it.
6. Ecosystems and directories MUST follow [repos.md](repos.md#parameters). Every repo gets `github-actions` and `pre-commit`, except dox, whose hook revs are updated by hand.
7. Bun blocks (D3, B1) MUST be written but commented out, under a comment naming dependabot-core#16071 that says to restore them once a pilot PR works, keeping `directory` equal to the `audit` matrix.
8. Until then, Bun MUST be updated by hand: on the first Monday of each month, and within 3 working days of a red `audit`, one PR per Bun repo titled `chore(deps): update bun dependencies`:
   1. patch and minor updates from `bun outdated`, applied with `bun add -E`;
   2. Biome in its own PR, after `biome migrate --write && biome check --write .`;
   3. advisories: `bun audit fix` first; if a dependent's range blocks it, `bun update <dependent>`, then an `overrides` entry linking the advisory; with no fix, replace the package or add a documented `--ignore=<GHSA>`;
   4. `bun.lock` MUST NOT be regenerated as a whole.

## Parameters

- Configs: [Bun](../templates/dependabot.bun-web.yml), [setun](../templates/dependabot.setun.yml), [Python](../templates/dependabot.python.yml), [Python + Bun](../templates/dependabot.python-bun.yml), [Rust](../templates/dependabot.rust.yml), [Zig](../templates/dependabot.zig.yml), [Homebrew](../templates/dependabot.homebrew.yml), [Shell](../templates/dependabot.shell.yml), [Content](../templates/dependabot.content.yml), [Special](../templates/dependabot.special.yml), [replex](../templates/dependabot.replex.yml), [dox](../templates/dependabot.dox.yml).
- Copy the matching config to `.github/dependabot.yml`; adapt ecosystems and directories to [repos.md](repos.md#parameters).

- Every `bun.lock` in the Bun directories of [repos.md](repos.md#parameters) is lockfile v2 [V, 2026-10-07].
- The template cooldown exclusion permits updates less than 3 days after release [V, 2026-09-30, playground].
- A security PR opened before `dependabot.yml` lands can't be rebased afterwards, and closing it doesn't make Dependabot recreate it, so a rollout turns on security updates only after its rollout PR merges [V, 2026-10-08, wtfnzb-adapter#6].

## Verification

- zizmor passes on `dependabot.yml` with only the per-entry `dependabot-cooldown` suppressions. It sometimes misses a finding on a later entry, so read every entry.
- `rg -n 'ignore:' .github/dependabot.yml` finds nothing.
- The first run after rollout opens PRs with `chore(deps…)` titles, grouped as above.

## Open

- dependabot-A2: whether Dependabot's `bun` support keeps `npm:` aliases (`@typescript/native`) and exact pins (poyo-studio's `foundation.test.ts`). Closes with the Bun pilot PR after dependabot-core#16071 ships.

## Why

- Omitting `cooldown` gives a 3-day default, and `default-days: 0` violates the schema (minimum 1); zizmor fails all three forms without the suppression.
- `@vitest/*` packages pin `vitest` exactly, so they must move together.
- Example of a hold refused: a TypeScript 7 PR sits red until `svelte-check` and the Kit peers accept it.
- Dependabot's `pre-commit` ecosystem doesn't support private repos, hence dox's manual hook revs.
