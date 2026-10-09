# CI workflow (`ci.yml`) and Pages

## Contract

1. `ci.yml` MUST trigger on `pull_request`, `push` to main, `workflow_dispatch` and a weekly `schedule` (audit, main revalidation and redeploy). It MUST NOT have a workflow-level `paths:` filter.
2. PR runs MUST use the concurrency group `ci-pr-<PR number>-<event head SHA>` with cancel-in-progress. Push, schedule and dispatch MUST use `ci-<sha>` without cancelling.
3. `ci-ok` MUST be `if: always()`, MUST `needs:` every PR-relevant job, and MUST pass only through the inline `jq` gate over `toJSON(needs)`: each need is `success`, or `skipped` and listed in `ALLOWED_SKIPS`. An empty `needs` fails.
4. A job-level `if:` MUST appear only on a job listed in `ALLOWED_SKIPS` whose own `needs` are also direct needs of `ci-ok`. Otherwise use step-level early exits.
5. Jobs that never run on PRs (`audit`, `deploy`) MUST stay out of `ci-ok`.
6. Every workflow MUST start with `permissions: {}`. Every job MUST have minimal grants and `timeout-minutes`; every checkout MUST set `persist-credentials: false`.
7. Every action MUST be pinned to a full SHA with a `# vX.Y.Z` comment, which Dependabot updates together. `pull_request_target` MUST NOT be used anywhere.
8. Toolchains MUST come from repo files: `setup-bun` with `bun-version-file: package.json`, `setup-uv` with `.python-version`, `rust-toolchain.toml`, `setup-zig` reading `build.zig.zon`, and for a SvelteKit 3 app `setup-node` with `node-version-file` pointing at the `.node-version` in the app's directory, before the install (Kit 3 needs Node ≥22.17 for `svelte-kit sync`, `svelte-check`, `drizzle-kit`, Vitest and Playwright).
9. Installs MUST be frozen: `bun ci`, or `bun ci --ignore-scripts` with required project preparation run explicitly, omitting lifecycle steps that only install Git hooks; `uv sync --locked`; `cargo … --locked`.
10. Runners MUST use `-latest` labels (D12). Linux ARM64 has none, so it uses the `ubuntu-<gen>-arm` label of `ubuntu-latest`'s generation.
11. CI MUST call repo-local commands (`scripts/smoke.*`, package scripts), so every check also runs locally.
12. Deploys MUST use a successful non-PR run of a commit on main (`push`, scheduled revalidation or dispatch), never a PR run. A PR run tests a synthetic merge ref, not the final squash commit.
13. `audit` MUST run only outside PRs, with one matrix entry per independent lockfile: `bun audit --audit-level=high` per Bun directory, and `uvx pip-audit` (unpinned; no secrets) over `uv export --locked` per uv project. The directories are the bun and uv entries of the Dependabot column in [repos.md](repos.md#parameters).
14. A uv `audit` entry MUST stay until ci-A1 closes for that project.

### Pages (guides, isfuglen, portaler, yt-redirect, eksamen)

15. `deploy` MUST run only after `ci-ok` passes, in the same non-PR run on main, and MUST publish the artifact that commit's smoke job built.
16. `deploy` MUST be serialised by `pages-deploy` with `queue: max`, and MUST check that its commit is still main's tip while holding the slot.
17. The `github-pages` environment MUST allow deployments from main only, and the Pages source MUST be "GitHub Actions". `CNAME` and `.nojekyll` stay.
18. `withastro/action` MUST NOT be used.
19. eksamen has no build step: its smoke job uploads `docs/`.
20. A repo's `gh-pages` branch MUST NOT be deleted before its first successful Actions deploy.

### Pullfrog reviews

21. Pullfrog MUST use a separate default-branch-only dispatch workflow from the [template](../templates/pullfrog.yml), with its Claude subscription stored at account scope in Pullfrog, never in GitHub Actions secrets. It MUST stay outside `ci-ok` and the required checks. New repositories MUST receive the workflow, settings and review instructions before activation.
22. Reviews MUST cover all base branches, new commits, drafts and bot PRs, with critical, high, medium, low and nitpick findings included. Review instructions MUST respect repository rules and owner decisions. External contributors MUST require a collaborator's review request.
23. Pullfrog MUST NOT push code, approve or auto-merge PRs, auto-address reviews, fix CI or enrich issues. Shell isolation MUST stay restricted. Changing Pullfrog MUST preserve existing publishing workflow states and MUST NOT advance the core CI rollout.

## Parameters

Copy a workflow as `.github/workflows/ci.yml`, then apply the repo's row in [repos.md](repos.md#parameters). Templates use repo-local smoke/check entry points: the rollout must supply or adapt them, allocate a distinct schedule minute, and include every added PR job in the gate.

| Stack | Templates |
|---|---|
| Bun web | [Bun](../templates/ci-bun-web.yml), [Bun + Pages](../templates/ci-bun-pages.yml) |
| Python | [uv](../templates/ci-python.yml), [Python + Bun](../templates/ci-python-bun.yml); stdlib-only repos start from [Special](../templates/ci-special.yml) and add their smoke/runner |
| Native | [Rust/Windows](../templates/ci-rust.yml), [Zig](../templates/ci-zig.yml), [Homebrew](../templates/ci-homebrew.yml) |
| Shell | [Shell](../templates/ci-shell.yml) |
| Content | [Content](../templates/ci-content.yml), [static Pages](../templates/ci-content-pages.yml) |
| Special | [repo-patches](../templates/ci-special.yml), [replex](../templates/ci-replex.yml), [dox](../templates/ci-dox.yml) |

- The uv `audit` invocation fails on a locked advisory and passes once it is fixed [V, 2026-10-08, wtfnzb-adapter#7, #10].
- Pins, schedules, runners and commands live in those templates. Runner architectures were verified [V, 2026-09-27]; re-check at rollout (ci-A2).
- Pages linter allowance: [actionlint.pages.yaml](../templates/actionlint.pages.yaml), copied to `.github/actionlint.yaml`.
- Pullfrog: [setup](https://docs.pullfrog.com/getting-started), [account-scoped Claude auth](https://docs.pullfrog.com/claude-auth), [review configuration](https://docs.pullfrog.com/pr-reviews), and [CLI settings](https://docs.pullfrog.com/cli-configuration). A SHA pins its action bootstrap; its npm runtime still follows the upstream major ([versioning](https://docs.pullfrog.com/versioning)).
- Maintain Pullfrog in its template; `python3 tools/sync_pullfrog.py <checkout>…` copies it locally, and `--check` detects drift. Commit copies through per-repository PRs. The command never pushes, merges or changes settings.
- Console values: [settings](../templates/pullfrog-settings.json); the Review mode's instructions: [prompt](../templates/pullfrog-review.txt). Apply the prompt through `pullfrog config set prompts.review --file templates/pullfrog-review.txt --repo <owner/repo>`; settings use the console because bot inclusion and base-branch scope have no CLI keys.

## Verification

- actionlint and `zizmor --offline` pass on every workflow.
- The `ci-ok` gate fails on sample `needs` JSON with a failed, cancelled or unlisted skipped job, and on `{}`.
- Two quick pushes to main each finish their own run; a newer PR head never cancels another head's run.
- Pages: a push to main deploys; a run that finishes behind a newer commit skips `deploy-pages`.
- The repo's cron minute differs from every rolled-out repo's.
- Pullfrog's workflow passes both linters and `privileged-jobs`; a run uses the Claude subscription and posts a review on its exact PR head. `pullfrog config list` confirms the review contract; the workflow has no PR trigger or secret reference.

## Open

- ci-A1: whether the dependency graph covers uv transitive packages. Closes when a project's SBOM export (`gh api repos/{repo}/dependency-graph/sbom`) lists its locked transitive packages at their locked versions; then drop that `audit` entry.
- ci-A2: `macos-latest` staying arm64, and `ubuntu-latest`'s generation for the ARM64 label. Closes per change: re-check the runner-images README at S19 and at the 26.04 move. `ubuntu-latest` moves to 26.04 between 2026-10-19 and 2026-11-19, and the ARM64 label must follow [V, 2026-10-09].

## Why

- A skipped workflow leaves required checks pending, so no `paths:` filter.
- Queue order isn't guaranteed and a re-run keeps its SHA, so a per-PR group could cancel the current head; one main group would drop the middle of three fast merges.
- Declared dependencies in the graph do not establish coverage of every locked transitive package.
- The tip check stops an older run overwriting a newer site; `withastro/action` installs Bun `latest` unfrozen.
- GitHub blocks `pull_request_target` on public repos from 2026-11-02.
