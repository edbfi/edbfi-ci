# Maintenance

## Cleanup gate

The last part of every step; it blocks the step.

1. `STATE.md` shows this step's outcome, and its step entry is reduced to one line: `done` plus the PR link(s).
2. Every `## Open` item this step verified is either a fact tagged `[V, YYYY-MM-DD]` in its module, or deleted. Delete open items that nothing depends on any more.
3. For every value or rule this step changed, search the repo for other statements of it (`rg`). Delete or correct any duplicate or contradiction.
4. Remove fired `watch.yml` entries whose action is done. Add an entry for every new "when X happens, do Y".
5. No leftovers: no scratch files, no commented-out experiments, no `TODO`, `TBD` or `FIXME`, no "previously" or "we used to" prose.
6. All guards (§D.3) pass. If a cap is hit, merge, trim or split content. Don't raise the cap.
7. The PR body has: what changed, the evidence (the commands run and their results), deviations from the design with reasons, and Owner actions.

Guards: `prek run --all-files --hook-stage manual` (runs [`tools/doc-guard`](tools/doc-guard/doc_guard.py) and its tests).

## Watch triggers

S3 turns this table into `watch.yml` and deletes it. The watcher runs weekly with `GITHUB_TOKEN` (`issues: write`), keeps one issue per trigger id, fails the run on a failed lookup, and has a dry-run mode.

| id | when | do |
|---|---|---|
| bun-v2 | dependabot-core#16071 merged | uncomment the Bun blocks ([dependabot.md](design/dependabot.md#contract)) and pilot `biome-migrate.yml` |
| biome-const | `@biomejs/biome` > 2.5.14 | check the seven `{@const}` repos go green, then re-check docrewind's overrides (B4) |
| actionlint-queue | actionlint > 1.7.12 | test `queue` and `ubuntu-26.04-arm` support, and drop the allowances ([prek.md](design/prek.md#contract)) |
| prek-toml | dependabot-core#15271 merged | informational |
| replex-green | manual: replex CI green | move replex to the normal auto-merge path ([auto-merge.md](design/auto-merge.md#contract)) |
