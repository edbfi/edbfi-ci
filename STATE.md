Last updated: 1791473293 (2026-10-08T15:28:13Z)

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
| S5 | Phase 0 in target repos: B2 fixes, Hotio workflow pinning, default-branch check | done | [#10](https://github.com/edbfi/edbfi-ci/pull/10), [#14](https://github.com/edbfi/edbfi-ci/pull/14), [#20](https://github.com/edbfi/edbfi-ci/pull/20), [#23](https://github.com/edbfi/edbfi-ci/pull/23) |
| S6 | core pilot: portaler | in progress (D21 ruleset decided; next: portaler ruleset) | [portaler#119](https://github.com/edbfi/portaler/pull/119), [#25](https://github.com/edbfi/edbfi-ci/pull/25) |
| S7 | core pilot: obzorarr | pending | — |
| S8 | core pilot: wtfnzb-adapter | pending | — |
| S9 | core pilot: edbfi | pending | — |
| S10 | core rollout: Bun web | pending | — |
| S11 | core rollout: Python | pending | — |
| S12 | core rollout: Native | pending | — |
| S13 | core rollout: Shell + Content | pending | — |
| S14 | core rollout: Special (replex advisory, dox manual, repo-patches) | pending | — |
| S15 | `biome-migrate.yml` in the ten Biome repos (idle until B1) | pending | — |
| S16 | watchdog (owner PAT and secrets in both watchdog repos first) | pending | — |
| S17 | D8: github-stats | pending | — |
| S18 | D8: EasyHDR | pending | — |
| S19 | D8: homebrew-taps (D16 checks, PR #3 reconciliation) | pending | — |
| S20 | GitHub-side cleanup: stale workflow registrations, `gh-pages` branches, wings-vpn archive and secret/PAT cleanup, Actions copies of `DEPENDENCY_AUTOMERGE_TOKEN` | pending | — |

## Repos

No target repo has the core rollout yet [V, 2026-10-07]: none has `ci.yml`, `pr-policy.yml`, `dependabot.yml`, `.pre-commit-config.yaml`, a ruleset or auto-merge; 19 still have a `prek.toml`. `—` means not rolled out.

| repo | tier | step | ci | pr-policy | ruleset | auto-merge | pages | notes |
|---|---|---|---|---|---|---|---|---|
| edbfi-ci | — | S4 | live; push CI and audit verified | live | active | live; credential installed | — | protocol verified in playground; edbfi-ci bot merge unobserved |
| portaler | Bun web | S6 | — | — | — | — | `gh-pages` branch | B1 |
| obzorarr | Bun web | S7 | — | — | — | — | — | B1 |
| wtfnzb-adapter | Python | S8 | — | — | — | — | — | — |
| edbfi | Content | S9 | — | — | — | — | — | — |
| guides | Bun web | S10 | — | — | — | — | `gh-pages` branch | B1 |
| isfuglen | Bun web | S10 | — | — | — | — | `gh-pages` branch | B1 |
| yt-redirect | Bun web | S10 | — | — | — | — | `gh-pages` branch | B1 |
| docrewind | Bun web | S10 | — | — | — | — | — | B1 |
| otpravkarr | Bun web | S10 | — | — | — | — | — | B1 |
| poyo-studio | Bun web | S10 | — | — | — | — | — | B1 |
| setun | Bun web | S10 | — | — | — | — | — | B1 |
| zondarr | Python | S11 | — | — | — | — | — | B1, B6 |
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
| eksamen | Content | S13 | — | — | — | — | legacy `main:/docs` | — |
| repo-patches | Special | S14 | — | — | — | — | — | — |
| replex | Special | S14 | — | — | — | — | — | — |
| dox | Special | S14 | — | — | — | — | — | B3 |

## GitHub state

All [V, 2026-10-07] unless dated otherwise. Each rollout step fixes its own repos' drift.

- Actions is enabled in all 42 non-archived repositories. Pullfrog's workflow is on the default branch of all but icarus-bevy and printlab-project.
- `immortality.yml` and its `IMMORTALITY_TOKEN` are in the 11 repos with a scheduled workflow: edbfi-ci, edbfi-ci-playground, repo-patches, base-image (`workflows`), caddy, qbittorrent, qflood, sabnzbd, otpravkarr-docker, obzorarr-docker, zondarr-docker. One dispatched run passed in each; the first scheduled run is on 2026-11-01.
- Rulesets exist only in edbfi-ci and edbfi-ci-playground, both in the D21 shape [V, 2026-10-08]; no repo has classic branch protection.
- Every target repo: SHA pinning not required, rebase merges allowed, squash title `COMMIT_OR_PR_TITLE`, auto-merge off, Dependabot alerts and security updates off. Secret scanning and push protection are on only in wtfnzb-adapter. Merge commits are allowed in wtfnzb-adapter and replex; replex doesn't delete merged branches.
- Default `GITHUB_TOKEN` permission is write, and "Allow GitHub Actions to create and approve pull requests" is on, in docrewind, eksamen, guide-capture, guides, isfuglen, portaler, replex and yt-redirect; the latter is also on in homebrew-taps.
- `web_commit_signoff_required` is off in replex, wtfnzb-adapter and dox.
- The four `gh-pages` sites' deploy workflows are gone.
- Stale workflow registrations (no file on the default branch): isfuglen `ping.yml`; docrewind `opencode.yml`, `ai-review.yml`, `pr-review-ci.yml`, `pr-review-collect.yml`; github-stats `token-permission-probe.yml`; mover-status `e2e-mover-test.yml`; comradarr `integration.yaml`; replex `ci.yml`; `ci` in otpravkarr-, obzorarr- and zondarr-docker and `build-nightly` in obzorarr-docker (on no branch).
- The Dependabot secret `DEPENDENCY_AUTOMERGE_TOKEN` exists in 29 repos: every public target, edbfi-ci, edbfi-ci-playground (its own repository-scoped PAT) and wings-vpn. Actions copies exist in every public target and wings-vpn.
- The Dependabot secret `BIOME_MIGRATE_TOKEN` exists in the ten Biome repos; github-stats has `STATS_READ_TOKEN`. EasyHDR lacks `VT_API_KEY` for S18; homebrew-taps lacks the write deploy key its S12 ruleset and S19 updater need; neither edbfi-ci nor github-stats has the S16 watchdog secret yet.
- otpravkarr-docker's and zondarr-docker's `release` builds fail at `archive/null.tar.gz` until each app publishes its first plain `X.Y.Z` release; accepted by the owner (2026-10-07).
- `edbfi-ci`: core merge settings, required checks, SHA pinning, Dependabot alerts and security updates, secret scanning and push protection are on. Main push CI, audit and the watcher pass.
- `edbfi-ci-playground` is active for reusable CI integration tests. Keep it and its credential for further testing; each pilot verifies its own installed credential and deployment.

## Open items

- Owner decision: should 3d-designs, icarus-bevy or printlab-project join the rollout tiers? Until then they stay outside scope ([repos.md](design/repos.md#contract) rule 3).
- obzorarr, otpravkarr, zondarr: without `ORIGIN` (no front) a SIGHUP kills the app without a drain, and a stop lingers past the drain deadline while the app awaits an upstream (11-19 s with `SHUTDOWN_TIMEOUT=2`); zondarr's `/api/[...path]` proxy call has no timeout.
- setun: a chat stream whose first event hasn't arrived by the drain deadline gets the front's 503 instead of a clean end.
- otpravkarr: the e2e runs leave `otpravkarr-e2e-*` directories in `$TMPDIR` (`playwright.config.ts` has no teardown).
- agent-rules `docs/toolchain-floors.md` still calls `sveltekit-superforms` 3 a prerelease; 3.0.0 is stable and pinned.
- qflood: nightly's `version_flood__command` (no Hotio equivalent) takes the first successful Flood run from a list GitHub sometimes serves stale, so the channel can step back for an hour.
- zondarr-docker: a VPN setup with `PUBLIC_API_URL` must expose port 8000 itself (`VPN_EXPOSE_PORTS_ON_LAN`); only the init comment says so.
- homebrew-taps PR #30 is stale (it would downgrade paicord).
- hotio/base#30: if Hotio closes it unmerged, delete the edbfi/base-image branch `fix/manifest-retry-cleanup` (a merge fires `hotio-manifest-retry-cleanup` in [watch.yml](watch.yml)).
