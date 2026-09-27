# CI workflow (`ci.yml`) and Pages

## Contract

1. `ci.yml` MUST trigger on `pull_request`, `push` to main, `workflow_dispatch` and a weekly `schedule` (audit, main revalidation and redeploy). It MUST NOT have a workflow-level `paths:` filter.
2. PR runs MUST use the concurrency group `ci-pr-<PR number>-<event head SHA>` with cancel-in-progress. Push, schedule and dispatch MUST use `ci-<sha>` without cancelling.
3. `ci-ok` MUST be `if: always()`, MUST `needs:` every PR-relevant job, and MUST pass only through the inline `jq` gate over `toJSON(needs)`: each need is `success`, or `skipped` and listed in `ALLOWED_SKIPS`. An empty `needs` fails.
4. A job-level `if:` MUST appear only on a job listed in `ALLOWED_SKIPS` whose own `needs` are also direct needs of `ci-ok`. Otherwise use step-level early exits.
5. Jobs that never run on PRs (`audit`, `deploy`) MUST stay out of `ci-ok`.
6. Every workflow MUST start with `permissions: {}`. Every job MUST have minimal grants and `timeout-minutes`; every checkout MUST set `persist-credentials: false`.
7. Every action MUST be pinned to a full SHA with a `# vX.Y.Z` comment, which Dependabot updates together. `pull_request_target` MUST NOT be used anywhere.
8. Toolchains MUST come from repo files: `setup-bun` with `bun-version-file: package.json`, `setup-uv` with `.python-version`, `rust-toolchain.toml`, `setup-zig` reading `build.zig.zon`.
9. Installs MUST be frozen: `bun ci`, or `bun ci --ignore-scripts` plus an explicit `bun run prepare` where install scripts run `prek install` (obzorarr's postinstall, zondarr's root prepare); `uv sync --locked`; `cargo … --locked`.
10. Runners MUST use `-latest` labels (D12). Linux ARM64 has none, so it uses the `ubuntu-<gen>-arm` label of `ubuntu-latest`'s generation.
11. CI MUST call repo-local commands (`scripts/smoke.*`, package scripts), so every check also runs locally.
12. Deploys MUST depend only on the `push` run of the squash commit on main. A PR run tests `refs/pull/N/merge` against the base at that moment, not that commit.
13. `audit` MUST run only outside PRs, with one matrix entry per independent lockfile: `bun audit --audit-level=high` per Bun directory, and `uvx pip-audit` (unpinned; no secrets) over `uv export --locked` per uv project. The directories are the bun and uv entries of the Dependabot column in [repos.md](repos.md#parameters).
14. A uv `audit` entry MUST stay until ci-A1 closes for that project.

### Pages (guides, isfuglen, portaler, yt-redirect, eksamen)

15. `deploy` MUST run only after `ci-ok` passes, in the same non-PR run on main, and MUST publish the artifact that commit's smoke job built.
16. `deploy` MUST be serialised by `pages-deploy` with `queue: max`, and MUST check that its commit is still main's tip while holding the slot.
17. The `github-pages` environment MUST allow deployments from main only, and the Pages source MUST be "GitHub Actions". `CNAME` and `.nojekyll` stay.
18. `withastro/action` MUST NOT be used.
19. eksamen has no build step: its smoke job uploads `docs/`.
20. A repo's `gh-pages` branch MUST NOT be deleted before its first successful Actions deploy.

## Parameters

- Weekly cron: Sunday about 02:00 UTC, a distinct minute per repo that is never `:00`, clear of Dependabot's Monday slot.
- Runner labels: `ubuntu-latest` is 24.04, so the ARM64 label is `ubuntu-24.04-arm`; `macos-latest` is arm64 [V, 2026-09-27]. Per-repo runners are in [repos.md](repos.md#parameters). actionlint 1.7.12 knows `ubuntu-24.04-arm` but would need a `self-hosted-runner.labels` allowance for `ubuntu-26.04-arm`.
- Reference template (Bun, with Pages); S2 re-resolves every SHA when writing templates. It passes actionlint 1.7.12 with the Pages allowance ([prek.md](prek.md#contract)) and zizmor 1.30.1 `--offline`:

```yaml
name: CI
on:
  pull_request:
  push: { branches: [main] }
  workflow_dispatch:
  schedule: [{ cron: "17 2 * * 0" }]   # weekly audit + main revalidation/redeploy; minute unique per repo
permissions: {}
concurrency:
  group: ${{ github.event_name == 'pull_request' && format('ci-pr-{0}-{1}', github.event.pull_request.number, github.event.pull_request.head.sha) || format('ci-{0}', github.sha) }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
jobs:
  checks:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }
      - uses: oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6 # v2.2.0
        with: { bun-version-file: package.json }
      - run: bun ci
      - uses: j178/prek-action@4e14d07f9231acabce116ccfca13b13dd9755ece # v3.0.0
        with: { extra-args: "--all-files --hook-stage manual" }   # no prek-version: defaults to latest
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }
      - uses: oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6 # v2.2.0
        with: { bun-version-file: package.json }
      - run: bun ci
      - run: bun run build
      - run: bun run smoke
      - if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'   # Pages repos only
        uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with: { path: dist }
  ci-ok:
    if: always()
    needs: [checks, smoke]
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions: {}
    steps:
      - env:
          NEEDS: ${{ toJSON(needs) }}
          ALLOWED_SKIPS: ""
        run: |
          jq -e --arg skips "$ALLOWED_SKIPS" '
            ($skips | split(",") | map(select(. != ""))) as $allowed
            | length > 0 and all(to_entries[]; .value.result == "success"
                or (.value.result == "skipped" and (.key | IN($allowed[]))))
          ' <<<"$NEEDS" >/dev/null || { echo "::error::ci-ok failed: $(jq -c 'map_values(.result)' <<<"$NEEDS")"; exit 1; }
  audit:
    if: github.event_name != 'pull_request'
    strategy: { fail-fast: false, matrix: { dir: ["."] } }
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions: { contents: read }
    defaults: { run: { working-directory: "${{ matrix.dir }}" } }
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with: { persist-credentials: false }
      - uses: oven-sh/setup-bun@0c5077e51419868618aeaa5fe8019c62421857d6 # v2.2.0
        with: { bun-version-file: "${{ matrix.dir }}/package.json" }
      - run: bun audit --audit-level=high
  deploy:                                # Pages repos only
    needs: [ci-ok]
    if: always() && needs.ci-ok.result == 'success' && github.event_name != 'pull_request' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions: { contents: read, pages: write, id-token: write }
    environment: { name: github-pages, url: "${{ steps.deploy.outputs.page_url }}" }
    concurrency: { group: pages-deploy, cancel-in-progress: false, queue: max }
    steps:
      - id: tip
        run: |
          tip="$(gh api "repos/${GITHUB_REPOSITORY}/commits/main" --jq .sha)"
          echo "current=$([ "$tip" = "$GITHUB_SHA" ] && echo true || echo false)" >> "$GITHUB_OUTPUT"
        env: { GH_TOKEN: "${{ github.token }}" }
      - id: deploy
        if: steps.tip.outputs.current == 'true'
        uses: actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1
```

- Other pins [V, 2026-09-27]: `astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0`, `mlugg/setup-zig@d1434d08867e3ee9daa34448df10607b98908d29 # v2.2.1`, `Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2`.

## Verification

- actionlint and `zizmor --offline` pass on every workflow.
- The `ci-ok` gate fails on sample `needs` JSON with a failed, cancelled or unlisted skipped job, and on `{}`.
- Two quick pushes to main each finish their own run; a newer PR head never cancels another head's run.
- Pages: a push to main deploys; a run that finishes behind a newer commit skips `deploy-pages`.
- The repo's cron minute differs from every rolled-out repo's.

## Open

- ci-A1: whether the dependency graph covers uv transitive packages. Closes when a project's SBOM export (`gh api repos/{repo}/dependency-graph/sbom`) lists its locked transitive packages at their locked versions; then drop that `audit` entry.
- ci-A2: `macos-latest` staying arm64, and `ubuntu-latest`'s generation for the ARM64 label. Closes per change: re-check the runner-images README when homebrew-taps rolls out (S12, S19).
- ci-A3: the exact `uv export` / `pip-audit` invocation. Closes with a green `audit` run in the wtfnzb-adapter pilot (S8).

## Why

- A skipped workflow leaves required checks pending, so no `paths:` filter.
- Queue order isn't guaranteed and a re-run keeps its SHA, so a per-PR group could cancel the current head; one main group would drop the middle of three fast merges.
- GitHub's dependency graph lists neither `bun.lock` nor `uv.lock`, so `audit` covers them.
- The tip check stops an older run overwriting a newer site; `withastro/action` installs Bun `latest` unfrozen.
- GitHub blocks `pull_request_target` on public repos from 2026-11-02.
