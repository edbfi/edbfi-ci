# Maintenance

## Cleanup gate

The last part of every step; it blocks the step.

1. `STATE.md` shows this step's outcome, and its step entry is reduced to one line: `done` plus the PR link(s). Every PR that touches `STATE.md` sets its freshness line to the time the PR is finalized.
2. Every `## Open` item this step verified is either a fact tagged `[V, YYYY-MM-DD]` in its module, or deleted. Delete open items that nothing depends on any more.
3. For every value or rule this step changed, search the repo for other statements of it (`rg`). Delete or correct any duplicate or contradiction.
4. Remove fired `watch.yml` entries whose action is done. Add an entry for every new "when X happens, do Y".
5. No leftovers: no scratch files, no commented-out experiments, no `TODO`, `TBD` or `FIXME`, no "previously" or "we used to" prose.
6. All guards pass. If a cap is hit, merge, trim or split content. Don't raise the cap.
7. The PR body has: what changed, the evidence (the commands run and their results), deviations from the design with reasons, and Owner actions.

Guards: `prek run --all-files --hook-stage manual` (runs [`tools/doc_guard`](tools/doc_guard/doc_guard.py) and its tests).

## Watch triggers

Conditions and actions live in [watch.yml](watch.yml). Operation and verification are in [scheduled maintenance](design/watchdog.md#parameters).
