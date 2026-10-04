# State

Take the first step whose status isn't `done`. "Core" means prek, `ci.yml`, `pr-policy.yml`, Dependabot, auto-merge, settings and ruleset. Blockers are in [DECISIONS.md](DECISIONS.md#blockers).

## Steps

| step | goal | status | PR |
|---|---|---|---|
| S0 | bootstrap `edbfi-ci` | done | [#1](https://github.com/edbfi/edbfi-ci/pull/1) |
| S1 | shared hooks, tests and typing gate | done | [#2](https://github.com/edbfi/edbfi-ci/pull/2) |
| S2 | validated workflow, Dependabot and hook templates | done | [#3](https://github.com/edbfi/edbfi-ci/pull/3) |
| S3 | weekly upstream watcher with deduplicated issues and dry-run | done | [#4](https://github.com/edbfi/edbfi-ci/pull/4) |
| S4 | shared Dependabot merge path verified | done | [#5](https://github.com/edbfi/edbfi-ci/pull/5), [#6](https://github.com/edbfi/edbfi-ci/pull/6), [#7](https://github.com/edbfi/edbfi-ci/pull/7), [#8](https://github.com/edbfi/edbfi-ci/pull/8) |
| S5 | Phase 0 in target repos: B2 fixes, `refresh-hotio.yml` pinning, default-branch check | in progress | [#10](https://github.com/edbfi/edbfi-ci/pull/10) |
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
| edbfi-ci | — | S4 | live; push CI and audit verified | live | active | live; credential installed | — | protocol verified in playground; edbfi-ci bot merge unobserved |
| portaler | Bun web | S6 | — | — | — | — | — | B1 |
| obzorarr | Bun web | S7 | — | — | — | — | — | B1, B4, B5 |
| wtfnzb-adapter | Python | S8 | — | — | — | — | — | — |
| edbfi | Content | S9 | — | — | — | — | — | — |
| guides | Bun web | S10 | — | — | — | — | — | B1 |
| isfuglen | Bun web | S10 | — | — | — | — | — | B1, B2 |
| yt-redirect | Bun web | S10 | — | — | — | — | — | B1 |
| docrewind | Bun web | S10 | — | — | — | — | — | B1, B4 |
| otpravkarr | Bun web | S10 | — | — | — | — | — | B1, B4, B5 |
| poyo-studio | Bun web | S10 | — | — | — | — | — | B1, B4, B5 |
| setun | Bun web | S10 | — | — | — | — | — | B1, B4 |
| web-presentations | Bun web | S10 | — | — | — | — | — | B1, B4 |
| zondarr | Python | S11 | — | — | — | — | — | B1, B4, B5 |
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

- Owner-authorized Pullfrog setup (2026-10-03): Actions enabled in all 41 active repositories (32 changed); archived repositories and individually disabled workflows unchanged. S5 and migration ship conditions unchanged.
- Claude subscription connected; Pullfrog live in all 41 active repositories with the central workflow and review presets: here via [setup #11](https://github.com/edbfi/edbfi-ci/pull/11), the playground via [pilot #8](https://github.com/edbfi/edbfi-ci-playground/pull/8), and the other 39 via the workflow PRs listed in [rollout #12](https://github.com/edbfi/edbfi-ci/pull/12), all merged. Existing migration PRs remain untouched.

- No repo has classic branch protection [V, 2026-10-04]; only `edbfi-ci` and `edbfi-ci-playground` have a ruleset.

Target-repo drift is from the 2026-09-26 snapshots; each rollout step fixes its own drift.

- Default `GITHUB_TOKEN` permission is write in docrewind, eksamen, guide-capture, guides, isfuglen, portaler, replex and yt-redirect.
- "Allow GitHub Actions to create and approve pull requests" is on in those repos plus homebrew-taps.
- `web_commit_signoff_required` is off in replex, wtfnzb-adapter and dox.
- guides, isfuglen, portaler and yt-redirect serve a stale `gh-pages` branch; eksamen serves legacy `main:/docs`.
- The D5 PAT and its Dependabot secret cover 29 repos, including `edbfi-ci`, wings-vpn and replex. Actions copies of `DEPENDENCY_AUTOMERGE_TOKEN` still exist in target repos; `edbfi-ci` has only the Dependabot secret.

- `edbfi-ci`: core merge settings, required checks, SHA pinning, Dependabot alerts/security updates, grouped security updates and secret/push protection are enabled. Main push CI, audit and watcher dry-run pass with the configured Python version.

- `edbfi-ci-playground` is active for reusable CI integration tests, with a dedicated repository-scoped PAT installed as a Dependabot secret. Retain the playground and credential for further testing; each pilot verifies its own installed credential and deployment.
