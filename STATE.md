# State

Take the first step whose status isn't `done`. "Core" means prek, `ci.yml`, `pr-policy.yml`, Dependabot, auto-merge, settings and ruleset. Blockers are in [DECISIONS.md](DECISIONS.md#blockers).

## Steps

| step | goal | status | PR |
|---|---|---|---|
| S0 | bootstrap `edbfi-ci` | done | — |
| S1 | shared hooks `privileged-jobs` + `check-peers` with tests; `.pre-commit-hooks.yaml`; tag `v0.1.0` after merge | pending | — |
| S2 | templates: `ci-<stack>.yml` per stack in [repos.md](design/repos.md), `dependabot-auto-merge.yml`, `pr-policy.yml`, `dependabot.<stack>.yml`, `pre-commit.<stack>.yaml`, `actionlint.pages.yaml`, `biome-migrate.yml`; lint- and hook-clean in this repo's CI; move code out of docs | pending | — |
| S3 | `watch.yml` and the weekly watcher ([MAINTENANCE.md](MAINTENANCE.md#watch-triggers)) | pending | — |
| S4 | dogfood: `edbfi-ci` adopts the core (owner: D5 PAT and secret, settings, ruleset); gate and auto-merge verification | pending | — |
| S5 | Phase 0 in target repos: B2 fixes, `refresh-hotio.yml` pinning, default-branch check, required-peer mismatches fixed | pending | — |
| S6 | core pilot: portaler | pending | — |
| S7 | core pilot: obzorarr | pending | — |
| S8 | core pilot: wtfnzb-adapter | pending | — |
| S9 | core pilot: edbfi | pending | — |
| S10 | core rollout: Bun web | pending | — |
| S11 | core rollout: Python | pending | — |
| S12 | core rollout: Native | pending | — |
| S13 | core rollout: Shell + Content | pending | — |
| S14 | core rollout: Special (replex manual, dox advisory, repo-patches) | pending | — |
| S15 | `biome-migrate.yml` in the ten Biome repos (idle until B1) | pending | — |
| S16 | watchdog (the owner creates its PAT first) | pending | — |
| S17 | D8: github-stats | pending | — |
| S18 | D8: EasyHDR | pending | — |
| S19 | D8: homebrew-taps (D16 checks, PR #3 reconciliation) | pending | — |
| S20 | GitHub-side cleanup: stale workflow registrations, `gh-pages` branches, wings-vpn secret and PAT access, Actions copies of `DEPENDENCY_AUTOMERGE_TOKEN` | pending | — |

## Repos

| repo | tier | step | ci | pr-policy | ruleset | auto-merge | pages | notes |
|---|---|---|---|---|---|---|---|---|
| edbfi-ci | — | S4 | — | — | — | — | — | — |
| portaler | Bun web | S6 | — | — | — | — | — | B1 |
| obzorarr | Bun web | S7 | — | — | — | — | — | B1, B4 |
| wtfnzb-adapter | Python | S8 | — | — | — | — | — | — |
| edbfi | Content | S9 | — | — | — | — | — | — |
| guides | Bun web | S10 | — | — | — | — | — | B1 |
| isfuglen | Bun web | S10 | — | — | — | — | — | B1, B2 |
| yt-redirect | Bun web | S10 | — | — | — | — | — | B1 |
| docrewind | Bun web | S10 | — | — | — | — | — | B1, B4 |
| otpravkarr | Bun web | S10 | — | — | — | — | — | B1, B4 |
| poyo-studio | Bun web | S10 | — | — | — | — | — | B1, B2, B4 |
| setun | Bun web | S10 | — | — | — | — | — | B1, B4 |
| web-presentations | Bun web | S10 | — | — | — | — | — | B1, B4 |
| zondarr | Python | S11 | — | — | — | — | — | B1, B4 |
| guide-capture | Python | S11 | — | — | — | — | — | — |
| arrsenal-of-scripts | Python | S11 | — | — | — | — | — | — |
| EasyHDR | Native | S12 | — | — | — | — | — | — |
| github-stats | Native | S12 | — | — | — | — | — | — |
| homebrew-taps | Native | S12 | — | — | — | — | — | — |
| pelican-eggs | Shell | S13 | — | — | — | — | — | — |
| mover-status | Shell | S13 | — | — | — | — | — | — |
| comradarr | Content | S13 | — | — | — | — | — | — |
| zimuarr | Content | S13 | — | — | — | — | — | — |
| agent-rules | Content | S13 | — | — | — | — | — | — |
| skills | Content | S13 | — | — | — | — | — | — |
| eksamen | Content | S13 | — | — | — | — | — | — |
| repo-patches | Special | S14 | — | — | — | — | — | — |
| replex | Special | S14 | — | — | — | — | — | — |
| dox | Special | S14 | — | — | — | — | — | B3 |

## GitHub state

From the 2026-09-26 settings snapshots; each repo's rollout step fixes its own drift.

- Default `GITHUB_TOKEN` permission is write in docrewind, eksamen, guide-capture, guides, isfuglen, portaler, replex and yt-redirect.
- "Allow GitHub Actions to create and approve pull requests" is on in those repos plus homebrew-taps.
- `web_commit_signoff_required` is off in replex, wtfnzb-adapter and dox.
- guides, isfuglen, portaler and yt-redirect serve a stale `gh-pages` branch; eksamen serves legacy `main:/docs`.
- The D5 PAT and its Dependabot secret cover 28 repos, including wings-vpn and replex but not `edbfi-ci`. Actions copies of `DEPENDENCY_AUTOMERGE_TOKEN` still exist.
