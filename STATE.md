Last updated: 1791595779 (2026-10-10T01:29:39Z)

# State

Take the first step whose status isn't `done` or `blocked`; a blocked step names what it waits for. "Core" means prek, `ci.yml`, `pr-policy.yml`, Dependabot, auto-merge, settings and ruleset. Blockers are in [DECISIONS.md](DECISIONS.md#blockers).

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
| S9 | core pilot: edbfi | done | [edbfi#35](https://github.com/edbfi/edbfi/pull/35), [#30](https://github.com/edbfi/edbfi-ci/pull/30), [#31](https://github.com/edbfi/edbfi-ci/pull/31) |
| S10 | core rollout: Bun web | done | [guides#83](https://github.com/edbfi/guides/pull/83), [#85](https://github.com/edbfi/guides/pull/85); [isfuglen#70](https://github.com/edbfi/isfuglen/pull/70), [#72](https://github.com/edbfi/isfuglen/pull/72); [yt-redirect#88](https://github.com/edbfi/yt-redirect/pull/88), [#90](https://github.com/edbfi/yt-redirect/pull/90); [docrewind#178](https://github.com/edbfi/docrewind/pull/178), [#180](https://github.com/edbfi/docrewind/pull/180); [otpravkarr#156](https://github.com/edbfi/otpravkarr/pull/156), [#158](https://github.com/edbfi/otpravkarr/pull/158); [poyo-studio#95](https://github.com/edbfi/poyo-studio/pull/95), [#97](https://github.com/edbfi/poyo-studio/pull/97); [setun#112](https://github.com/edbfi/setun/pull/112), [#116](https://github.com/edbfi/setun/pull/116); [#32](https://github.com/edbfi/edbfi-ci/pull/32) |
| S11 | core rollout: Python | done | [zondarr#276](https://github.com/edbfi/zondarr/pull/276), [#282](https://github.com/edbfi/zondarr/pull/282); [guide-capture#38](https://github.com/edbfi/guide-capture/pull/38); [arrsenal-of-scripts#39](https://github.com/edbfi/arrsenal-of-scripts/pull/39); [printlab-project#2](https://github.com/edbfi/printlab-project/pull/2), [#3](https://github.com/edbfi/printlab-project/pull/3); [#34](https://github.com/edbfi/edbfi-ci/pull/34) |
| S12 | core rollout: Native | done | [EasyHDR#175](https://github.com/edbfi/EasyHDR/pull/175); [github-stats#31](https://github.com/edbfi/github-stats/pull/31); [homebrew-taps#40](https://github.com/edbfi/homebrew-taps/pull/40), [#42](https://github.com/edbfi/homebrew-taps/pull/42); [#36](https://github.com/edbfi/edbfi-ci/pull/36), [#37](https://github.com/edbfi/edbfi-ci/pull/37), [#38](https://github.com/edbfi/edbfi-ci/pull/38) |
| S12a | homebrew-taps: rebuild [homebrew-taps#28](https://github.com/edbfi/homebrew-taps/pull/28) (qBittorrent cask) on core CI | done | [homebrew-taps#43](https://github.com/edbfi/homebrew-taps/pull/43); [#39](https://github.com/edbfi/edbfi-ci/pull/39) |
| S13 | core rollout: Shell + Content | done | [pelican-eggs#36](https://github.com/edbfi/pelican-eggs/pull/36), [mover-status#59](https://github.com/edbfi/mover-status/pull/59), [comradarr#158](https://github.com/edbfi/comradarr/pull/158), [zimuarr#32](https://github.com/edbfi/zimuarr/pull/32), [agent-rules#43](https://github.com/edbfi/agent-rules/pull/43), [skills#34](https://github.com/edbfi/skills/pull/34), [eksamen#39](https://github.com/edbfi/eksamen/pull/39), [3d-designs#4](https://github.com/edbfi/3d-designs/pull/4), [icarus-bevy#1](https://github.com/edbfi/icarus-bevy/pull/1), [icarus-bevy#2](https://github.com/edbfi/icarus-bevy/pull/2); [#33](https://github.com/edbfi/edbfi-ci/pull/33) |
| S14 | core rollout: Special (replex advisory, dox manual, repo-patches) | blocked: B7 (dox), B8 (repo-patches); replex done | [replex#2](https://github.com/edbfi/replex/pull/2); [#35](https://github.com/edbfi/edbfi-ci/pull/35) |
| S15 | `biome-migrate.yml` in the ten Biome repos (idle until B1) | blocked: held by the owner (2026-10-08) | — |
| S16 | watchdog (owner PAT and secrets in both watchdog repos first) | blocked: the watchdog secret ([GitHub state](#github-state)) | — |
| S17 | D8: github-stats | done | [github-stats#33](https://github.com/edbfi/github-stats/pull/33); [#43](https://github.com/edbfi/edbfi-ci/pull/43) |
| S18 | D8: EasyHDR | blocked: `VT_API_KEY` ([GitHub state](#github-state)) | — |
| S19 | D8: homebrew-taps (D16 checks, [homebrew-taps#3](https://github.com/edbfi/homebrew-taps/pull/3) reconciliation) | done | [homebrew-taps#45](https://github.com/edbfi/homebrew-taps/pull/45), [#46](https://github.com/edbfi/homebrew-taps/pull/46); [#40](https://github.com/edbfi/edbfi-ci/pull/40) |
| S20 | GitHub-side cleanup: stale workflow registrations, `gh-pages` branches, wings-vpn archive and secret/PAT cleanup, Actions copies of `DEPENDENCY_AUTOMERGE_TOKEN` | blocked: the owner removes wings-vpn and replex from PAT `edbfi-dependabot-auto-merge`; everything else done | [#44](https://github.com/edbfi/edbfi-ci/pull/44) |
| S21 | agent-rules: record `sveltekit-superforms` 3.0.0 as stable in `docs/toolchain-floors.md` (docs only) | done | [agent-rules#45](https://github.com/edbfi/agent-rules/pull/45); [#45](https://github.com/edbfi/edbfi-ci/pull/45) |
| S22 | otpravkarr: each e2e Playwright run owns and removes its temporary database directory | done | [otpravkarr#159](https://github.com/edbfi/otpravkarr/pull/159); [#46](https://github.com/edbfi/edbfi-ci/pull/46) |

## Repos

Each repo's core rollout state is in the table below [V, 2026-10-09]; `—` means not rolled out. Of the target repos, only dox still has a `prek.toml`.

| repo | tier | step | ci | pr-policy | ruleset | auto-merge | pages | notes |
|---|---|---|---|---|---|---|---|---|
| edbfi-ci | — | S4 | live; push CI and audit verified | live | active | live; credential installed | — | protocol verified in playground; edbfi-ci bot merge unobserved |
| portaler | Bun web | S6 | live; push CI and deploy verified | live | active | live; Dependabot merge observed ([#120](https://github.com/edbfi/portaler/pull/120)) | Actions | B1 |
| obzorarr | Bun web | S7 | live; push CI verified | live | active | live; Dependabot merge observed ([#238](https://github.com/edbfi/obzorarr/pull/238)) | — | B1 |
| wtfnzb-adapter | Python | S8 | live; push CI and audit verified | live | active | live; Dependabot merges observed ([#8](https://github.com/edbfi/wtfnzb-adapter/pull/8), [#9](https://github.com/edbfi/wtfnzb-adapter/pull/9)) | — | — |
| edbfi | Content | S9 | live; push CI verified | live | active | live; Dependabot merge observed ([#36](https://github.com/edbfi/edbfi/pull/36)) | — | — |
| guides | Bun web | S10 | live; push CI and deploy verified | live | active | live; Dependabot merge observed ([#84](https://github.com/edbfi/guides/pull/84)) | Actions | B1 |
| isfuglen | Bun web | S10 | live; push CI and deploy verified | live | active | live; Dependabot merge observed ([#71](https://github.com/edbfi/isfuglen/pull/71)) | Actions | B1 |
| yt-redirect | Bun web | S10 | live; push CI and deploy verified | live | active | live; Dependabot merge observed ([#89](https://github.com/edbfi/yt-redirect/pull/89)) | Actions | B1 |
| docrewind | Bun web | S10 | live; push CI verified; `audit` red ([Open items](#open-items)) | live | active | live; Dependabot merge observed ([#179](https://github.com/edbfi/docrewind/pull/179)) | — | B1 |
| otpravkarr | Bun web | S10 | live; push CI verified | live | active | live; Dependabot merge observed ([#157](https://github.com/edbfi/otpravkarr/pull/157)) | — | B1 |
| poyo-studio | Bun web | S10 | live; push CI verified (macOS media-tools included) | live | active | live; Dependabot merge observed ([#96](https://github.com/edbfi/poyo-studio/pull/96)) | — | B1 |
| setun | Bun web | S10 | live; push CI verified | live | active | live; Dependabot merges observed ([#113](https://github.com/edbfi/setun/pull/113), [#114](https://github.com/edbfi/setun/pull/114), [#115](https://github.com/edbfi/setun/pull/115)) | — | B1 |
| zondarr | Python | S11 | live; push CI and audit verified | live | active | live; Dependabot merges observed ([#277](https://github.com/edbfi/zondarr/pull/277), [#278](https://github.com/edbfi/zondarr/pull/278)) | — | B1, B6 |
| guide-capture | Python | S11 | live; push CI verified (macOS included) | live | active | live; Dependabot merge observed ([#39](https://github.com/edbfi/guide-capture/pull/39)) | — | — |
| arrsenal-of-scripts | Python | S11 | live; push CI verified | live | active | live; Dependabot merge observed ([#40](https://github.com/edbfi/arrsenal-of-scripts/pull/40)) | — | — |
| printlab-project | Python | S11 | live; push CI verified | live | active | live; no Dependabot PR yet (nothing outdated) | — | — |
| EasyHDR | Native | S12 | live; push CI verified (Windows tests, smoke, cargo-deny, `fuzz/` check) | live | active | live; Dependabot merges observed ([#177](https://github.com/edbfi/EasyHDR/pull/177), [#178](https://github.com/edbfi/EasyHDR/pull/178)) | — | — |
| github-stats | Native | S12, S17 | live on `master`; push CI verified; daily stats generator live | live | active | live; Dependabot merge observed ([#32](https://github.com/edbfi/github-stats/pull/32)) | — | — |
| homebrew-taps | Native | S12, S19 | live; push CI verified (formulae on x86_64 and ARM64, macOS casks); cask updater live | live | active (admin role only; the deploy key passes it, D16) | live; Dependabot merge observed ([#41](https://github.com/edbfi/homebrew-taps/pull/41)) | — | — |
| pelican-eggs | Shell | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#37](https://github.com/edbfi/pelican-eggs/pull/37)) | — | — |
| mover-status | Shell | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#60](https://github.com/edbfi/mover-status/pull/60)) | — | — |
| comradarr | Content | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#159](https://github.com/edbfi/comradarr/pull/159)) | — | — |
| zimuarr | Content | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#33](https://github.com/edbfi/zimuarr/pull/33)) | — | — |
| agent-rules | Content | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#44](https://github.com/edbfi/agent-rules/pull/44)) | — | — |
| skills | Content | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#35](https://github.com/edbfi/skills/pull/35)) | — | — |
| eksamen | Content | S13 | live; push CI and deploy verified | live | active | live; Dependabot merge observed ([#40](https://github.com/edbfi/eksamen/pull/40)) | Actions | — |
| 3d-designs | Content | S13 | live; push CI verified | live | active | live; Dependabot merge observed ([#5](https://github.com/edbfi/3d-designs/pull/5)) | — | — |
| icarus-bevy | Content | S13 | live; push CI verified | live | active | live; no Dependabot PR yet (nothing outdated) | — | — |
| repo-patches | Special | S14 | — | — | — | — | — | B8 |
| replex | Special | S14 | live, advisory ([repos.md](design/repos.md#contract) rule 4): push `checks` red (rustfmt, clippy, cargo-test), smoke green | live | active (`pr-policy` only) | none ([auto-merge.md](design/auto-merge.md#contract) rule 7) | — | — |
| dox | Special | S14 | — | — | — | — | — | B3, B7 |

## GitHub state

All [V, 2026-10-07] unless dated otherwise. Each rollout step fixes its own repos' drift.

- Actions is enabled in all 41 non-archived repositories (wings-vpn is archived, D10) [V, 2026-10-10]. Pullfrog's workflow is on the default branch of all of them [V, 2026-10-09].
- `immortality.yml` and its `IMMORTALITY_TOKEN` are in every repo with a scheduled workflow: edbfi-ci, edbfi-ci-playground, the rolled-out target repos [V, 2026-10-09], repo-patches, base-image (`workflows`), caddy, qbittorrent, qflood, sabnzbd, otpravkarr-docker, obzorarr-docker, zondarr-docker. One dispatched run passed in each; the first scheduled run is on 2026-11-01. By owner decision (2026-10-08), the PAT also covers every other public rollout repo in advance (39 repos in all, 3d-designs, icarus-bevy and printlab-project included [owner, 2026-10-08]), and `IMMORTALITY_TOKEN` is set in each of them; a rollout's first dispatch proves its secret.
- Rulesets exist only in edbfi-ci, edbfi-ci-playground and the rolled-out target repos, all in the D21 shape [V, 2026-10-09]; no repo has classic branch protection.
- Every target repo not yet rolled out: SHA pinning not required, rebase merges allowed, squash title `COMMIT_OR_PR_TITLE`, auto-merge off, Dependabot alerts and security updates off, secret scanning and push protection off.
- `web_commit_signoff_required` is off in dox.
- Grouped security updates ([settings.md](design/settings.md#contract) rule 3) have no API, so they wait for the owner in every rolled-out repo.
- guides, isfuglen, portaler, yt-redirect and eksamen deploy Pages from `ci.yml`; their `github-pages` environments allow `main` only [V, 2026-10-09].
- The Dependabot secret `DEPENDENCY_AUTOMERGE_TOKEN` exists in 30 repos: every public target except replex, edbfi-ci, and edbfi-ci-playground (its own repository-scoped PAT); no Actions copies remain [V, 2026-10-10]. PAT `edbfi-dependabot-auto-merge` still covers replex and the archived wings-vpn until the owner removes them (S20), and repo-patches holds the secret and PAT access ahead of its own rollout (S14, B8).
- The Dependabot secret `BIOME_MIGRATE_TOKEN` exists in the ten Biome repos; github-stats has `STATS_READ_TOKEN`. EasyHDR lacks `VT_API_KEY` for S18; homebrew-taps has `UPDATER_DEPLOY_KEY`, the private half of its write deploy key [V, 2026-10-09]; neither edbfi-ci nor github-stats has the S16 watchdog secret yet.
- otpravkarr-docker's and zondarr-docker's `release` builds fail at `archive/null.tar.gz` until each app publishes its first plain `X.Y.Z` release; accepted by the owner (2026-10-07).
- `edbfi-ci`: core merge settings, required checks, SHA pinning, Dependabot alerts and security updates, secret scanning and push protection are on. Main push CI, audit and the watcher pass.
- `edbfi-ci-playground` is active for reusable CI integration tests. Keep it and its credential for further testing; each pilot verifies its own installed credential and deployment.

## Open items

- dox: its rollout adds a weekly schedule ([`ci-dox.yml`](templates/ci-dox.yml)), but dox has no `IMMORTALITY_TOKEN`, and [watchdog.md](design/watchdog.md#contract) rule 11 has no exception for private repos. Owner decision before the rollout: the secret, or a rule-11 exception.
- replex: Dependabot security PRs [#3](https://github.com/edbfi/replex/pull/3) to [#6](https://github.com/edbfi/replex/pull/6) (openssl, rustls-webpki, serde_with, xxhash-rust) wait for the owner's hand merge; the advisory CI's red tests can't vouch for them.
- docrewind: `audit` is red for braces (GHSA-vfj7-8cjw-p6xm) and node-forge (GHSA-86w9-cpqp-85rv), which have no fixed release; owner decision: a documented `--ignore` ([dependabot.md](design/dependabot.md#contract) rule 8.3) or waiting (`braces-fix`, `node-forge-fix` in [watch.yml](watch.yml)).
- setun: Docker and Compose Dependabot updates auto-merge on host-only checks, which never build or run an image (#113 took CLIProxyAPI v7 → v8 and Caddy 2.11); owner decision: widen setun's row in [repos.md](design/repos.md#parameters) with a container check, or accept the risk ([auto-merge.md](design/auto-merge.md#contract) rule 1).
- obzorarr, otpravkarr, zondarr: without `ORIGIN` (no front) a SIGHUP kills the app without a drain, and a stop lingers past the drain deadline while the app awaits an upstream (11-19 s with `SHUTDOWN_TIMEOUT=2`); zondarr's `/api/[...path]` proxy call has no timeout.
- setun: a chat stream whose first event hasn't arrived by the drain deadline gets the front's 503 instead of a clean end.
- qflood: nightly's `version_flood__command` (no Hotio equivalent) takes the first successful Flood run from a list GitHub sometimes serves stale, so the channel can step back for an hour.
- zondarr-docker: a VPN setup with `PUBLIC_API_URL` must expose port 8000 itself (`VPN_EXPOSE_PORTS_ON_LAN`); only the init comment says so.
- homebrew-taps: the `DeployKey` bypass actor was removed (2026-10-09); the next updater push must show `bypass` and start push CI (`homebrew-push-admin-only` in [watch.yml](watch.yml)), as the playground did.
- hotio/base#30: if Hotio closes it unmerged, delete the edbfi/base-image branch `fix/manifest-retry-cleanup` (a merge fires `hotio-manifest-retry-cleanup` in [watch.yml](watch.yml)).
