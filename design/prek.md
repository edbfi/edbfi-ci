# prek hooks and the shared hooks

## Contract

1. The prek config MUST be `.pre-commit-config.yaml`, converted mechanically from the repo's `prek.toml` (prek has only `yaml-to-toml`), with comments carried over by hand. `prek.toml` MUST then be deleted, because prek prefers it when both exist.
2. Every config MUST set `default_stages: [pre-commit, manual]`, so the manual stage is the CI set.
3. CI MUST run exactly one prek command, `prek run --all-files --hook-stage manual`. Other CI jobs cover only what isn't a hook: builds, smoke, e2e, other operating systems.
4. Every config MUST be normalised the same way:
   1. `no-commit-to-branch` gets `stages: [pre-commit]`;
   2. hooks that run only at `pre-push` also get `manual`;
   3. actionlint (`rhysd/actionlint`) and zizmor (`zizmorcore/zizmor-pre-commit`) are added; zizmor also audits `dependabot.yml`;
   4. remote revs are frozen with `prek update --freeze` (`rev: <sha>  # frozen: vX.Y.Z`);
   5. this repo's shared hooks are added by frozen rev;
   6. gitleaks stays a local-only hook (`stages: [pre-commit]`): it runs `--staged`, so it does nothing under `--all-files`.
5. Coverage-gap hooks MUST be added: lock freshness (`uv lock --check`); drizzle drift (obzorarr, setun); `biome-migrate` ([biome.md](biome.md#contract)); wtfnzb-adapter pytest; skills docendo tests and `node --check`; pelican-eggs `check-eggs.py` and `check-pair.py` (restored from `27fff0b^`); docrewind's Biome hook `files` widened to `.svelte`; isfuglen `build:assets` before `bun test`.
6. Repos without a prek config MUST get the edbfi baseline plus local hooks.
7. Linter allowances MUST be exactly: Pages repos' `.github/actionlint.yaml` ignoring `queue`; the zizmor suppression `bot-conditions` in the Dependabot workflows; `dependabot-cooldown` on each `cooldown:` line.

### Shared hooks (`.pre-commit-hooks.yaml` in this repo)

8. A `vX.Y.Z` tag MUST be cut only when `hooks/` or `.pre-commit-hooks.yaml` change. Consumers pin the tag's frozen SHA; Dependabot updates it.
9. `privileged-jobs` (`language: python`) MUST fail when a privileged job ([security.md](security.md#contract)) has a step or job-level `uses:`, `container:` or `services:`. PyYAML MUST be declared in the hook package's [pyproject.toml](../pyproject.toml) and covered by Dependabot.
10. `check-peers` (Bun) MUST check, for each direct dependency, every non-optional peer, resolved from the dependent's own directory, and MUST fail if a peer is missing or unsatisfied (`Bun.semver.satisfies`). It MUST NOT have an allowlist. It runs once per `audit` matrix directory.
11. `check-peers` MUST use the consumer's installed Bun and dependencies. Consumers MUST pass each audit directory through hook arguments (default: repo root); filenames are disabled in the [manifest](../.pre-commit-hooks.yaml).
12. A repo's required-peer mismatches on main MUST be fixed before `check-peers` is enabled there, or main starts red.
13. Python in `edbfi-ci` MUST pass the latest basedpyright with zero errors and warnings. The [config guard](../tools/check_basedpyright_config.py) MUST reject global overrides, baselines and file-wide suppressions; only justified inline rule-specific suppressions at untyped third-party boundaries are allowed.

## Parameters

- Tools [V, 2026-10-08]: prek 0.5.5, actionlint 1.7.12, zizmor 1.30.1.
- A second CI run of the same config restores the prek cache and passes the Go actionlint hook [V, 2026-09-27]; gitleaks stays local-only.
- Dependabot's `pre-commit` updater accepts `repo: builtin` and checks the remote hooks successfully [V, 2026-09-27].
- Hook entries and filters: [manifest](../.pre-commit-hooks.yaml); implementations and tests: [hooks/](../hooks/). Both remote language modes pass against setun [V, 2026-09-27]; `script` avoids installing a second Bun environment.
- Baseline: [Content](../templates/pre-commit.content.yaml). Stack additions: [Bun](../templates/pre-commit.bun-web.yaml), [Python](../templates/pre-commit.python.yaml), [Python + Bun](../templates/pre-commit.python-bun.yaml), [Rust](../templates/pre-commit.rust.yaml) (also replex), [Zig](../templates/pre-commit.zig.yaml), [Homebrew](../templates/pre-commit.homebrew.yaml), [Shell](../templates/pre-commit.shell.yaml), [Special](../templates/pre-commit.special.yaml), [dox](../templates/pre-commit.dox.yaml). Preserve existing project hooks and apply [repos.md](repos.md#parameters).
- Pages allowance: [actionlint.pages.yaml](../templates/actionlint.pages.yaml).
- The existing `prek.toml` configs convert 1:1 [V, 2026-09-27]: identical data, `prek validate-config` passes, `prek list` identical, `glob` excludes behave the same.

## Verification

- `prek validate-config` passes; `prek list` matches the pre-conversion output.
- `prek run --all-files --hook-stage manual` passes locally and in CI, and `prek.toml` is gone.
- `privileged-jobs` tests:
  - the `ci.yml` template (Pages `deploy` included) and the auto-merge template pass;
  - a PR job with `dependabot/fetch-metadata` next to the PAT fails; a deploy job guarded by `github.event_name != 'pull_request' || …` fails;
  - a scheduled job with `actions/checkout` next to `secrets.STATS_READ_TOKEN` fails; the same secret set through workflow-level `env:` fails; the Pages `deploy` job passes.
- `check-peers` tests: `vitest@5.0.0` with `@vitest/browser-playwright@5.0.1` fails from both sides; the matched pair passes; setun's optional `vite` → `esbuild` peer is ignored.
- `prek validate-manifest .pre-commit-hooks.yaml` passes, and a consumer runs both hooks by frozen rev.

## Open

- prek-A2: zizmor accepting `queue`, and the actionlint ignore text, on each linter bump. Closes per bump, through the actionlint watch trigger ([MAINTENANCE.md](../MAINTENANCE.md#watch-triggers)).

## Why

- Dependabot's `pre-commit` ecosystem reads only `.pre-commit-config.yaml`/`.yml`; `prek.toml` support is stalled (dependabot-core#14624 unanswered, PRs #15239 and #15271 unreviewed since June 2026).
- A frozen SHA with its `# frozen:` comment lets Dependabot rewrite both together.
- Bun only warns about unmet peers and `bun ci` exits 0, so without `check-peers` a mismatched update would auto-merge once Dependabot's Bun updater returns.
- Tagging only on hook changes keeps documentation commits from causing bump PRs elsewhere.
