Last updated: 1791495103 (2026-10-08T21:31:43Z)

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
| S6 | core pilot: portaler | done | [portaler#119](https://github.com/edbfi/portaler/pull/119), [#25](https://github.com/edbfi/edbfi-ci/pull/25), [#26](https://github.com/edbfi/edbfi-ci/pull/26), [#27](https://github.com/edbfi/edbfi-ci/pull/27) |
| S7 | core pilot: obzorarr | done | [obzorarr#237](https://github.com/edbfi/obzorarr/pull/237), [#28](https://github.com/edbfi/edbfi-ci/pull/28) |
| S8 | core pilot: wtfnzb-adapter | done | [wtfnzb-adapter#7](https://github.com/edbfi/wtfnzb-adapter/pull/7), [wtfnzb-adapter#10](https://github.com/edbfi/wtfnzb-adapter/pull/10), [#29](https://github.com/edbfi/edbfi-ci/pull/29) |
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

Only portaler, obzorarr and wtfnzb-adapter have the core rollout [V, 2026-10-08]; no other target repo has `ci.yml`, `pr-policy.yml`, `dependabot.yml`, a ruleset or auto-merge, only icarus-bevy has a `.pre-commit-config.yaml`, and 17 still have a `prek.toml`. `—` means not rolled out.

| repo | tier | step | ci | pr-policy | ruleset | auto-merge | pages | notes |
|---|---|---|---|---|---|---|---|---|
| edbfi-ci | — | S4 | live; push CI and audit verified | live | active | live; credential installed | — | protocol verified in playground; edbfi-ci bot merge unobserved |
| portaler | Bun web | S6 | live; push CI and deploy verified | live | active | live; Dependabot merge observed ([#120](https://github.com/edbfi/portaler/pull/120)) | Actions (`gh-pages` branch kept) | B1 |
| obzorarr | Bun web | S7 | live; push CI verified | live | active | live; Dependabot merge observed ([#238](https://github.com/edbfi/obzorarr/pull/238)) | — | B1 |
| wtfnzb-adapter | Python | S8 | live; push CI and audit verified | live | active | live; Dependabot merges observed ([#8](https://github.com/edbfi/wtfnzb-adapter/pull/8), [#9](https://github.com/edbfi/wtfnzb-adapter/pull/9)) | — | — |
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
| printlab-project | Python | S11 | — | — | — | — | — | — |
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
| 3d-designs | Content | S13 | — | — | — | — | — | — |
| icarus-bevy | Content | S13 | — | — | — | — | — | — |
| repo-patches | Special | S14 | — | — | — | — | — | — |
| replex | Special | S14 | — | — | — | — | — | — |
| dox | Special | S14 | — | — | — | — | — | B3 |

## GitHub state

All [V, 2026-10-07] unless dated otherwise. Each rollout step fixes its own repos' drift.

- Actions is enabled in all 42 non-archived repositories. Pullfrog's workflow is on the default branch of all but icarus-bevy and printlab-project.
- `immortality.yml` and its `IMMORTALITY_TOKEN` are in the 14 repos with a scheduled workflow: edbfi-ci, edbfi-ci-playground, portaler, obzorarr, wtfnzb-adapter [V, 2026-10-08], repo-patches, base-image (`workflows`), caddy, qbittorrent, qflood, sabnzbd, otpravkarr-docker, obzorarr-docker, zondarr-docker. One dispatched run passed in each; the first scheduled run is on 2026-11-01. By owner decision (2026-10-08), the PAT also covers every other public rollout repo in advance (39 repos in all, 3d-designs, icarus-bevy and printlab-project included [owner, 2026-10-08]), and `IMMORTALITY_TOKEN` is set in each of them; a rollout's first dispatch proves its secret.
- Rulesets exist only in edbfi-ci, edbfi-ci-playground, portaler, obzorarr and wtfnzb-adapter, all in the D21 shape [V, 2026-10-08]; no repo has classic branch protection.
- Every target repo except portaler, obzorarr and wtfnzb-adapter: SHA pinning not required, rebase merges allowed, squash title `COMMIT_OR_PR_TITLE`, auto-merge off, Dependabot alerts and security updates off, secret scanning and push protection off (on in 3d-designs, icarus-bevy and printlab-project [V, 2026-10-08]). Merge commits are allowed in replex, which doesn't delete merged branches.
- Default `GITHUB_TOKEN` permission is write, and "Allow GitHub Actions to create and approve pull requests" is on, in docrewind, eksamen, guide-capture, guides, isfuglen, replex and yt-redirect; the latter is also on in homebrew-taps.
- `web_commit_signoff_required` is off in replex and dox.
- The `gh-pages` deploy workflows of guides, isfuglen and yt-redirect are gone; portaler deploys from `ci.yml` [V, 2026-10-08].
- Stale workflow registrations (no file on the default branch): isfuglen `ping.yml`; docrewind `opencode.yml`, `ai-review.yml`, `pr-review-ci.yml`, `pr-review-collect.yml`; github-stats `token-permission-probe.yml`; mover-status `e2e-mover-test.yml`; comradarr `integration.yaml`; replex `ci.yml`; `ci` in otpravkarr-, obzorarr- and zondarr-docker and `build-nightly` in obzorarr-docker (on no branch).
- The Dependabot secret `DEPENDENCY_AUTOMERGE_TOKEN` exists in 32 repos: every public target, edbfi-ci, edbfi-ci-playground (its own repository-scoped PAT) and wings-vpn. Actions copies exist in every public target except 3d-designs, icarus-bevy and printlab-project, and in wings-vpn. PAT `edbfi-dependabot-auto-merge` covers 31 repos [owner, 2026-10-08], wings-vpn and replex among them ([auto-merge.md](design/auto-merge.md#contract) rules 5 and 7 exclude both) [V, 2026-10-08].
- The Dependabot secret `BIOME_MIGRATE_TOKEN` exists in the ten Biome repos; github-stats has `STATS_READ_TOKEN`. EasyHDR lacks `VT_API_KEY` for S18; homebrew-taps lacks the write deploy key its S12 ruleset and S19 updater need; neither edbfi-ci nor github-stats has the S16 watchdog secret yet.
- otpravkarr-docker's and zondarr-docker's `release` builds fail at `archive/null.tar.gz` until each app publishes its first plain `X.Y.Z` release; accepted by the owner (2026-10-07).
- `edbfi-ci`: core merge settings, required checks, SHA pinning, Dependabot alerts and security updates, secret scanning and push protection are on. Main push CI, audit and the watcher pass.
- `edbfi-ci-playground` is active for reusable CI integration tests. Keep it and its credential for further testing; each pilot verifies its own installed credential and deployment.

## Open items

- obzorarr, otpravkarr, zondarr: without `ORIGIN` (no front) a SIGHUP kills the app without a drain, and a stop lingers past the drain deadline while the app awaits an upstream (11-19 s with `SHUTDOWN_TIMEOUT=2`); zondarr's `/api/[...path]` proxy call has no timeout.
- setun: a chat stream whose first event hasn't arrived by the drain deadline gets the front's 503 instead of a clean end.
- otpravkarr: the e2e runs leave `otpravkarr-e2e-*` directories in `$TMPDIR` (`playwright.config.ts` has no teardown).
- agent-rules `docs/toolchain-floors.md` still calls `sveltekit-superforms` 3 a prerelease; 3.0.0 is stable and pinned.
- qflood: nightly's `version_flood__command` (no Hotio equivalent) takes the first successful Flood run from a list GitHub sometimes serves stale, so the channel can step back for an hour.
- zondarr-docker: a VPN setup with `PUBLIC_API_URL` must expose port 8000 itself (`VPN_EXPOSE_PORTS_ON_LAN`); only the init comment says so.
- homebrew-taps PR #30 is stale (it would downgrade paicord).
- hotio/base#30: if Hotio closes it unmerged, delete the edbfi/base-image branch `fix/manifest-retry-cleanup` (a merge fires `hotio-manifest-retry-cleanup` in [watch.yml](watch.yml)).
