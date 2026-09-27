# Biome (D4)

## Contract

1. Layer 1: `biome.json` `$schema` MUST be `./node_modules/@biomejs/biome/configuration_schema.json`, so patch and minor bumps change only `package.json` and `bun.lock`. Target repos' agent docs MUST NOT name a Biome version (remove the mentions in `guides/CLAUDE.md:49` and `yt-redirect/CLAUDE.md:22`).
2. Layer 2: every Biome repo MUST have the manual-stage hook `biome-migrate: bunx --no-install biome migrate --write`, `language: system`, `pass_filenames: false`. zondarr runs it from its root (`./node_modules/.bin/biome`). A needed migration modifies files, which fails prek and turns `ci-ok` red.
3. Layer 3: `biome-migrate.yml` MUST be built now in the ten Biome repos, idle until Dependabot's Bun updater returns (B1).
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

- Biome repos (ten): guides, isfuglen, portaler, yt-redirect, docrewind, obzorarr, otpravkarr, poyo-studio, setun, zondarr.
- Credential: PAT `edbfi-biome-migrate` (Contents RW), installed as the Dependabot secret `BIOME_MIGRATE_TOKEN` in the ten repos.

## Verification

- Layer 1: `rg -n '"\$schema"' biome.json*` shows the local path; `rg -in 'biome [0-9]' CLAUDE.md AGENTS.md` finds nothing in the target repo.
- Layer 2: bumping Biome across a migration makes `prek run --all-files --hook-stage manual` fail with a modified `biome.json`.
- Layer 3 (after B1 clears): a Dependabot Biome PR gains one `apply biome migrate` commit, whose parent is the Dependabot head, and auto-merges.

## Open

- biome-A1: `biome migrate --write` with a local `$schema`, and whether a promoted nursery rule fails `biome ci`. Closes on the first Biome minor bump after layer 1 lands.
- biome-A2: how `[dependabot skip]` interacts with Dependabot's "stop rebasing" behaviour. Closes with the layer 3 pilot.
- biome-A3: web-presentations uses Biome (B4) but has no `BIOME_MIGRATE_TOKEN`. Closes when S15 decides whether it gets layer 3 (the owner would then add it to the PAT).

## Why

- A plain push isn't a compare-and-swap; `--force-with-lease` against `head.sha` is.
- The two workflows race, so without job 3 a green PR could be left without auto-merge.
- A remote `$schema` URL pins a version and forces a config change on every bump.
