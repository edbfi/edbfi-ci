# Dependabot

## Contract

1. Every entry MUST run weekly, Monday 05:00 `Europe/Copenhagen`; replex runs monthly.
2. Every entry MUST have `cooldown: { exclude: ["*"] }` with the suppression comment `# zizmor: ignore[dependabot-cooldown] -- D2: no cooldown` (D2).
3. Every entry MUST use `commit-message: { prefix: chore, include: scope }`.
4. Groups MUST be, first match winning: `biome` (`@biomejs/*`); `playwright` (`playwright`, `@playwright/*`); `vitest` (`vitest`, `@vitest/*`); `slint` (EasyHDR: `slint`, `slint-build`); `compose-images` (setun); then `patch-minor` (`patterns: ["*"]`, `update-types: [minor, patch]`). The special groups may contain majors; other majors get one PR each.
5. There MUST NOT be any `ignore:` entry, pinned-back version or hold. A broken upstream release keeps its PR red until a later release fixes it.
6. Ecosystems and directories MUST follow [repos.md](repos.md#parameters). Every repo gets `github-actions` and `pre-commit`, except dox, whose hook revs are updated by hand.
7. Bun blocks (D3, B1) MUST be written but commented out, under a comment naming dependabot-core#16071 and #16026 that says to restore them once a pilot PR works, keeping `directory` equal to the `audit` matrix.
8. Until then, Bun MUST be updated by hand: on the first Monday of each month, and within 3 working days of a red `audit`, one PR per Bun repo titled `chore(deps): update bun dependencies`:
   1. patch and minor updates from `bun outdated`, applied with `bun add -E`;
   2. Biome in its own PR, after `biome migrate --write && biome check --write .`;
   3. advisories: `bun audit fix` first; if a dependent's range blocks it, `bun update <dependent>`, then an `overrides` entry linking the advisory; with no fix, replace the package or add a documented `--ignore=<GHSA>`;
   4. `bun.lock` MUST NOT be regenerated as a whole.

## Parameters

Template shape (Bun web):

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule: { interval: weekly, day: monday, time: "05:00", timezone: Europe/Copenhagen }
    cooldown: { exclude: ["*"] } # zizmor: ignore[dependabot-cooldown] -- D2: no cooldown
    commit-message: { prefix: chore, include: scope }
    groups:
      actions-patch-minor: { patterns: ["*"], update-types: [minor, patch] }
  - package-ecosystem: pre-commit
    directory: /
    schedule: { interval: weekly, day: monday, time: "05:00", timezone: Europe/Copenhagen }
    cooldown: { exclude: ["*"] } # zizmor: ignore[dependabot-cooldown] -- D2: no cooldown
    commit-message: { prefix: chore, include: scope }
    groups:
      hooks-patch-minor: { patterns: ["*"], update-types: [minor, patch] }
  # Bun updates are PAUSED (D3): dependabot-core#16026 / #16071 (bun.lock v2).
  # - package-ecosystem: bun   (same schedule/cooldown/commit-message; groups: biome, playwright, vitest, patch-minor)
```

- All 12 `bun.lock` files are lockfile v2; Dependabot's bun updater supports only v1.

## Verification

- zizmor passes on `dependabot.yml` with only the per-entry `dependabot-cooldown` suppressions. It sometimes misses a finding on a later entry, so read every entry.
- `rg -n 'ignore:' .github/dependabot.yml` finds nothing.
- The first run after rollout opens PRs with `chore(deps…)` titles, grouped as above.

## Open

- dependabot-A1: whether Dependabot accepts `cooldown: { exclude: ["*"] }` and offers a release under 3 days old. Closes when a rolled-out repo gets a PR for a release under 3 days old.
- dependabot-A2: whether Dependabot's `bun` support keeps `npm:` aliases (`@typescript/native`) and exact pins (poyo-studio's `foundation.test.ts`). Closes with the Bun pilot PR after dependabot-core#16071 ships.

## Why

- Omitting `cooldown` gives a 3-day default, and `default-days: 0` violates the schema (minimum 1); zizmor fails all three forms without the suppression.
- `@vitest/*` packages pin `vitest` exactly, so they must move together.
- Examples of holds refused: a TypeScript 7 PR sits red until `svelte-check` and the Kit peers accept it; the `{@const}` repos' Biome PRs stay red (B4).
- Dependabot's `pre-commit` ecosystem doesn't support private repos, hence dox's manual hook revs.
