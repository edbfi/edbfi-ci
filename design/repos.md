# Repos: scope and per-repo adaptations

## Contract

1. In the tiers below, "main" means the repo's default branch: `main` everywhere except github-stats, whose default branch is `master`. Substitute `master` there in every branch filter, ref guard and API path.
2. "PAT" means a fine-grained personal access token; every PAT here acts as the owner.
3. The in-scope repos are the tiers below (D1). Out of scope: website, base-image, obzorarr-docker, otpravkarr-docker, zondarr-docker, caddy, qbittorrent, qflood, sabnzbd (the hotio family keeps its upstream CI), and wings-vpn (to be archived, D10).
4. replex is in scope with advisory CI whose failures are accepted; repo-patches only for its tooling (D1).
5. Each repo MUST own `ci.yml` (required check `ci-ok`), `pr-policy.yml` (required check `pr-policy`), `dependabot.yml` and `.pre-commit-config.yaml`; where they apply, `dependabot-auto-merge.yml`, `.github/actionlint.yaml` (Pages) and `scripts/smoke.*`; with its first scheduled workflow, `immortality.yml` ([watchdog.md](watchdog.md#contract)); and, in later steps, `biome-migrate.yml` ([biome.md](biome.md#parameters) repos), the D8 workflows ([d8.md](d8.md#contract) repos) and the watchdog ([watchdog.md](watchdog.md#contract) repos).
6. Each repo MUST get the adaptations in its row below. Each rollout PR MUST also fix the repo's stale CI references (below) and keep `process.env.CI`, `scripts/serve-dist.ts` and poyo-studio's `*:ci` scripts.
7. The hotio-family docker repos (caddy, qbittorrent, qflood, sabnzbd, otpravkarr-docker, obzorarr-docker, zondarr-docker; D20) MUST carry Hotio's `call-build.yml` and `call-update.yml` on every channel branch, byte-identical to the matching hotio repo (schedules included) except that `uses:` points at `edbfi/base-image/.github/workflows/{build,update}-on-call.yml@workflows`. These repos and base-image MUST keep the default `GITHUB_TOKEN` permission `write`, which their reusable workflows need. Any other difference in these two caller workflows needs an owner decision.
8. A PR into a hotio-family channel branch MUST use the branch name `workflows`, the one branch `call-build` doesn't build and publish. Merging it publishes that channel's image.
9. base-image and website MUST stay generated mirrors of hotio/base and hotio/website (D20): repo-patches' `watch-hotio.yml` and `sync-hotio.yml` reset each mirrored branch to Hotio and apply edbfi's edits (base-image's `immortality.yml` included). Never change them by hand or PR.
10. A shared agent rule changes in agent-rules first. Consumers then copy the canonical bytes from agent-rules `main` into `.agents/rules/` in a PR that changes nothing else, and agent-rules lists the earlier hash under `[accepted]` in `manifest.toml`. Copies are never edited in place. comradarr keeps its accepted older `svelte5-sveltekit-app` copy until a re-copy includes it.
11. Each SvelteKit app (obzorarr, otpravkarr, poyo-studio, setun, zondarr/frontend) owns its front ([svelte5-sveltekit-app](https://github.com/edbfi/agent-rules/blob/main/rules/svelte5-sveltekit-app.md)). A fix found in one front MUST be ported to the others where it applies; the `IDLE_TIMEOUT` alias stays only in otpravkarr, obzorarr and zondarr.

## Parameters

Tiers: 26 public in-scope repos plus private dox; `edbfi-ci` itself is outside the tiers. GitHub default branches match rule 1 [V, 2026-09-30].

| Tier | Repos | Stack |
|---|---|---|
| Bun web | guides, isfuglen, portaler, yt-redirect (Astro 7 + Svelte 5, Pages); docrewind (WXT MV3 extension); obzorarr, otpravkarr, poyo-studio, setun (SvelteKit 3 with `@sveltejs/adapter-bun` + SQLite; setun also has a `scripts/` uv project, Dockerfile, compose) | Bun 1.4.2 (`packageManager` required by agent rules), Biome 2.5 |
| Python | zondarr (Litestar `backend/` uv, SvelteKit 3 `frontend/` bun with `@sveltejs/adapter-bun`, root bun for Biome/prek); wtfnzb-adapter (Litestar, uv); guide-capture (bash + stdlib Python + Node, needs macOS arm64); arrsenal-of-scripts (shell/zsh/Python) | uv |
| Native | EasyHDR (Rust 1.98.1, Windows-only Slint GUI, `fuzz/` crate, cargo-deny); github-stats (Zig 0.16, default branch `master`); homebrew-taps (casks + Linux formulae + bash/python pipeline) | |
| Shell | pelican-eggs, mover-status | |
| Content | edbfi, comradarr, zimuarr (docs only); agent-rules; skills; eksamen (static site in `docs/`, Pages) | |
| Special | repo-patches (stdlib Python tooling; scheduled `watch-hotio.yml` and dispatched `sync-hotio.yml` generate the base-image and website mirrors of Hotio); replex (Rust fork; its advisory CI's failures are accepted); dox (private, Free plan) | |

Hotio-family credentials (revoke neither PAT): repo-patches' `PERSONAL_TOKEN` is PAT `edbfi-hotio-mirror-sync` (Contents and Workflows RW on base-image and website); base-image's and the docker repos' `PERSONAL_TOKEN` is PAT `edbfi-hotio-container-sync`, used by their updaters; `DISCORD_WEBHOOK` feeds Hotio's `notify` job in base-image and the docker repos.

Adaptations (Dependabot directories double as the `audit` matrix, [ci.md](ci.md#contract)):

| Repo | Beyond prek | Smoke | Runner(s) | Dependabot |
|---|---|---|---|---|
| guides | build | restore `scripts/smoke.sh`: serve `dist/`; `/`, `/google-drev/`, `/meebook/`, one GitBook redirect, `/pagefind/pagefind.js`; assert `<title>` | ubuntu | bun `/`, gha |
| isfuglen | `check-bundle.ts`; Playwright chromium/firefox/webkit (`--with-deps`, `CI=true`) | curl 8 routes + CSP meta; e2e. B2: fix `tests/e2e/layout.spec.ts:146` first | ubuntu | bun `/`, gha |
| portaler | add tests to prek; build | `PORT=4321 bun run scripts/serve-dist.ts`; `/ /other /grade/3 /fag/matematik` | ubuntu | bun `/`, gha |
| yt-redirect | tests + build | Playwright chromium (24 tests, `e2e/`) | ubuntu | bun `/`, gha |
| docrewind | guard scripts (~190 s), `test:logic`, `test:coverage`, build, zip, `zip:firefox`, `verify-manifest.sh`, `lint:firefox` | Playwright extension smoke; `verify-reproducible-build.sh` | ubuntu | bun `/`, gha |
| obzorarr | drizzle drift (`drizzle-kit check`/`generate`, clean `git status`); build | `bun run smoke:production` with `DATABASE_PATH=$RUNNER_TEMP/smoke.db` | ubuntu | bun `/`, gha |
| otpravkarr | Vitest (Node), build | new `scripts/smoke.ts`: empty DB, start `scripts/serve.ts`, `/api/health` ok/degraded, `/`→`/setup`; `test:e2e` | ubuntu | bun `/`, gha |
| poyo-studio | prek runs tests+build; `test:browser:ci` | `test:production-smoke`; never `test:live`, its live-approval switches or bare `bun test` | ubuntu + macOS media-tools | bun `/`, gha |
| setun | `test:component`, Playwright (4 servers), `check:python`, `uv lock --check --project scripts`, drizzle drift, build; stub model gateway only (no real CLIProxyAPI, provider login or MCP credential) | dummy env with a synthetic `ORIGIN` (without one setun exits at startup), `/`→`/setup` title+banner, SIGTERM exits 0 | ubuntu | bun `/`, uv `/scripts`, docker `/`, docker-compose `/` + `/scripts` (grouped) |
| zondarr | `uv sync --locked` (backend), `bun ci --ignore-scripts` at root + `frontend/`, frontend build, `uv build`, API-types drift (restore `check-api.ts`, 7038c47) | restore `smoke.py`: alembic upgrade, both servers (frontend through `scripts/serve.ts`), `/health/ready`, `/api/auth/methods` via proxy | ubuntu | uv `/backend`, bun `/`, bun `/frontend`, gha |
| wtfnzb-adapter | pytest hook, `uv build`, `prek validate-config` | Litestar `/health` + `caps` with dummy config | ubuntu | uv `/`, gha |
| guide-capture | `check-sensitive-files --all`, `/bin/bash -n` | `bin/guide-capture validate specs/…android.json` | macos-latest (arm64) | gha |
| arrsenal-of-scripts | `bash -n`, `shellcheck -S error`, `zsh -n`, unittest (63), basedpyright via `uvx` | `claude-diag.py --self-test` (age ≥1.3, zsh, GNU tar) | ubuntu | gha |
| EasyHDR | Windows: integration tests `--test-threads=1`, doctests; Ubuntu: `cargo deny --locked check` | restore `smoke-windows.ps1` (release build, temp `%APPDATA%`, window + log line) | windows-latest + ubuntu | cargo `/`, cargo `/fuzz` (monthly), rust-toolchain, gha |
| github-stats | `zig fmt --check`, `zig build test` | restore `smoke.py` (replay `tests/fixtures/stats.json`) | ubuntu | gha (Zig pin manual) |
| homebrew-taps | `bash -n` + shellcheck, 2 unittest trees; macOS: `brew readall`, `brew style`, `brew audit --cask` | changed formulae on Linux x64 + ARM64 ([d8.md](d8.md#contract)) | ubuntu-latest + `ubuntu-<gen>-arm` + macos-latest | gha |
| pelican-eggs | restored `check-eggs.py`, `check-pair.py` | unittest (5), `bash -n` + shellcheck on `ini-merge.sh` | ubuntu | gha |
| mover-status | `bash -n`, shellcheck | `python3 tests/runtime.py` (timing-sensitive; Linux only) | ubuntu | gha |
| edbfi, comradarr, zimuarr | — | — | ubuntu | gha |
| agent-rules | rule-shape check (frontmatter, title, filename, TOML) | — | ubuntu | gha (pins inside `rules/*.md` stay manual) |
| skills | docendo tests, `node --check scripts/*.mjs` | `scripts/check-content.py` | ubuntu | gha |
| eksamen | Pages deploy of `docs/` | restore `smoke.sh` (`1e37642^`): serve `docs/`, `/index.html`, `/optagelsesprover.html` | ubuntu | gha |
| dox (private) | + gitleaks CI scan | — | ubuntu | gha (no pre-commit); advisory CI, manual merges |
| repo-patches | `python3 -m unittest discover -s tools -p 'test_*.py'` | — | ubuntu | gha |
| replex | fmt, clippy, test, build (red is accepted) | `REPLEX_HOST=http://127.0.0.1:9`, `/ping` → `pong!` | ubuntu | cargo (security-only, `open-pull-requests-limit: 0`, monthly), docker `/docker`, gha |

Stale CI references, fixed in each repo's rollout PR:

- isfuglen `astro.config.mjs:11-12`; yt-redirect `e2e/converter.spec.ts:6-9`, `playwright.config.ts:9,19-21`
- homebrew-taps `Casks/*/*.rb:1`, `scripts/lib/common.sh:6`, `scripts/discover.sh:2-4`, `.gitignore:4`
- github-stats `README.md:3-6`

## Verification

- Each rolled-out repo's `ci.yml` has the row's checks and smoke, on the row's runners, and its `dependabot.yml` has exactly the row's ecosystems and directories.
- `rg -n` of each stale reference above finds no CI claim that contradicts the repo's workflows.
- github-stats workflows filter on `master`, never `main`.
- Before S20 retires a workflow registration: its file is absent from every branch, its runs are inspected, only that workflow's runs are deleted, and the registrations are re-queried.

## Open

- None.

## Why

- Pinned line numbers age; re-find each stale reference by content before editing it.
- One row per repo keeps rollout PRs mechanical.
