# Biome (D4)

## Contract

1. Layer 1: `biome.json` `$schema` MUST be `./node_modules/@biomejs/biome/configuration_schema.json`, so schema-version changes alone don't rewrite `biome.json`; migrations may still change its configuration. Target repos' agent docs, where they exist, MUST NOT name a Biome version.
2. Layer 2: every Biome repo MUST have the manual-stage hook `biome-migrate: bunx --bun --no-install biome migrate --write`, `language: system`, `pass_filenames: false`. A needed migration modifies files, which fails prek and turns `ci-ok` red.
3. Layer 3: every Biome repo ([Parameters](#parameters)) MUST carry `biome-migrate.yml`.
4. It MUST trigger on `pull_request` `[opened, synchronize, reopened]`, filtered by the three auto-merge conditions ([auto-merge.md](auto-merge.md#contract), with the same zizmor suppression) and by a diff touching `@biomejs/biome`.
5. Concurrency MUST be `biome-migrate-<PR>-<head.sha>` with cancel-in-progress.
6. Job 1 (unprivileged) MUST check out `head.sha`, run `bun ci --ignore-scripts` and `biome migrate --write`, and upload `git diff` if there is one.
7. Job 2 (privileged, with the artifact intake of [security.md](security.md#contract)) MUST:
   1. reject a patch touching anything but `biome.json`/`biome.jsonc`;
   2. exit early if the API head is no longer `head.sha`;
   3. fetch that SHA per command and apply the patch;
   4. commit as `github-actions[bot]` with `chore(deps): apply biome migrate [dependabot skip]`, without sign-off;
   5. assert `HEAD^` == `head.sha`;
   6. push with `git push --force-with-lease=refs/heads/<ref>:<head.sha> origin HEAD:refs/heads/<ref>`;
   7. output the new SHA.
8. Job 3 (privileged) MUST run the auto-merge enable script with `HEAD_SHA` set to the new SHA, using `DEPENDENCY_AUTOMERGE_TOKEN`.

## Parameters

- Workflow: [biome-migrate.yml](../templates/biome-migrate.yml); migration hook: [Bun config](../templates/pre-commit/bun-web/.pre-commit-config.yaml). The publisher applies patches to the index without checking out PR files.
- Biome repos: guides, isfuglen, portaler, yt-redirect, docrewind, poyo-studio, setun; the five rewrite apps join with their `package.json` ([repos.md](repos.md#contract) rule 12): obzorarr, otpravkarr and zondarr with their app skeleton, comradarr and zimuarr with their tooling-only manifest.
- Credential: PAT `edbfi-biome-migrate` (Contents RW), installed as the Dependabot secret `BIOME_MIGRATE_TOKEN` in every Biome repo ([coverage](../STATE.md#github-state)).

## Verification

- Layer 1: `rg -n '"\$schema"' biome.json*` shows the local path; `rg -in -g 'CLAUDE.md' -g 'AGENTS.md' 'biome [0-9]'` finds no match in the target repo.
- Layer 2: bumping Biome across a migration makes `prek run --all-files --hook-stage manual` fail with a modified `biome.json`.
- Layer 3: a Dependabot Biome PR gains one `apply biome migrate` commit, whose parent is the Dependabot head, and auto-merges; its unmigrated head stays red until then, and the bot's own commit doesn't re-trigger the workflow [V, 2026-10-11, edbfi-ci-playground#15, Biome 1.9.4 → 2.5.15 with a local `$schema`].

## Open

- biome-A1: whether a promoted nursery rule fails `biome ci`. Closes on the first Biome minor bump in a Biome repo.
- biome-A2: how `[dependabot skip]` interacts with Dependabot's "stop rebasing" behaviour; the pilot merged before any rebase. Closes when a migrated Biome PR needs a rebase.

## Why

- A plain push isn't a compare-and-swap; `--force-with-lease` against `head.sha` is.
- The two workflows race, so without job 3 a green PR could be left without auto-merge.
- A remote `$schema` URL pins a version and forces a config change on every bump.
