# Decisions

All resolved. The rules they produce live in [design/](design/); this file only names them.

| ID | Decision | Enforced by |
|---|---|---|
| D1 | Scope as in [repos.md](design/repos.md#contract); replex has advisory CI with accepted failures; repo-patches is in for its tooling only. | per-repo table in [STATE.md](STATE.md) |
| D2 | Every Dependabot PR auto-merges once CI passes, majors included, with no cooldown. | `dependabot-auto-merge.yml`; `cooldown` exclusion ([dependabot.md](design/dependabot.md#contract)) |
| D3 | Bun Dependabot is paused until lockfile v2 is supported; manual updates plus audits until then. | commented-out Bun blocks; `audit` job; `bun-v2` watch trigger |
| D4 | Automatic Biome migration with `BIOME_MIGRATE_TOKEN`, built now. | `biome-migrate` hook and `biome-migrate.yml` ([biome.md](design/biome.md#contract)) |
| D5 | A dedicated auto-merge PAT. | `DEPENDENCY_AUTOMERGE_TOKEN` Dependabot secret ([auto-merge.md](design/auto-merge.md#parameters)) |
| D6 | prek hooks update automatically: `.pre-commit-config.yaml` plus Dependabot's `pre-commit` ecosystem. | `pre-commit` entry in every `dependabot.yml` ([prek.md](design/prek.md#contract)) |
| D7 | Local gitleaks plus GitHub secret scanning and push protection; a gitleaks CI scan only in dox. | gitleaks hook; repo security settings ([settings.md](design/settings.md#contract)) |
| D8 | Restore the github-stats generator, homebrew direct updates, EasyHDR release/audit/Miri/profiling; defer docrewind releases. | D8 workflows ([d8.md](design/d8.md#contract)) |
| D9 | Conventional Commits titles plus DCO. | required check `pr-policy` ([pr-policy.md](design/pr-policy.md#contract)) |
| D10 | Archive wings-vpn; EasyHDR `/fuzz` updates monthly. | S20 cleanup; EasyHDR `dependabot.yml` |
| D11 | eksamen publishes through the gated deploy. | `deploy` job ([ci.md](design/ci.md#contract)) |
| D12 | `-latest` runner labels, keeping required architectures. | [ci.md](design/ci.md#contract) rule 10; actionlint |
| D13 | poyo-studio macOS media-tools job; homebrew Linux x86_64/ARM64 formula builds. | jobs required in `ci-ok` ([d8.md](design/d8.md#contract)) |
| D14 | Watchdog option 1: a PAT with Actions RW re-enables disabled schedules automatically. | watchdog workflows ([watchdog.md](design/watchdog.md#contract)) |
| D15 | Superseded by D6; no dox token. | — |
| D16 | homebrew-taps' only bypass actor is a deploy key. | homebrew-taps ruleset ([settings.md](design/settings.md#contract)) |
| D17 | The shared hooks and the watchdog live in `edbfi-ci`. | `.pre-commit-hooks.yaml`; watchdog here |

## Blockers

| ID | Blocker | Enforced by |
|---|---|---|
| B1 | Dependabot's bun updater supports only `bun.lock` v1 (D3). | `bun-v2` watch trigger ([MAINTENANCE.md](MAINTENANCE.md#watch-triggers)) |
| B2 | isfuglen preview-fit and poyo-studio gallery/browser whitespace fixes must land before `ci-ok` becomes required. | S5; required-check rollout |
| B3 | dox is private on the Free plan: no rulesets, no auto-merge. | manual merges |
| B4 | Not blocking: the seven `{@const}` repos (docrewind, obzorarr, otpravkarr, poyo-studio, setun, zondarr, web-presentations) stay red on Biome 2.5.14 until biomejs/biome#11837 ships; then re-check docrewind's formatter-off overrides (`biome.json:62-96`). | `biome-const` watch trigger |
| B5 | Required peer ranges exclude TypeScript 6: `svelte-adapter-bun@1.0.1` requires `^5` in obzorarr, otpravkarr, poyo-studio and zondarr; `openapi-typescript@7.13.0` requires `^5.x` in zondarr. These are the latest releases. | `check-peers` stays off in each affected repo until it passes ([prek.md](design/prek.md#contract) rule 12) |
