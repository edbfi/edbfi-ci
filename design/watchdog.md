# Schedule watchdog (D14 option 1)

## Contract

1. `edbfi-ci` and github-stats MUST each run a watchdog, daily and on dispatch, watching each other.
2. Per in-scope public repo, it MUST check that every scheduled workflow is `active`, and that its latest successful scheduled run is within budget.
3. It MUST check that the partner watchdog ran successfully within 2 days.
4. It MUST re-enable only workflows in state `disabled_inactivity`, then dispatch each once. Every other disabled state is only reported.
5. It MUST keep exactly one tracking issue in its own repo (`issues: write`), closed when everything is green.
6. Its job is privileged ([security.md](security.md#contract)).

## Parameters

- Budgets: `ci.yml` 8 days; EasyHDR audit 2 days; Miri 8 days; D8 schedulers per their cadence ([d8.md](d8.md#contract)).
- Credential: PAT `edbfi-schedule-watchdog` (Actions RW, Metadata R on every in-scope public repo plus `edbfi-ci`). It doesn't exist yet; the owner creates it before S16.

## Verification

- Disabling a scheduled workflow by hand is reported in the tracking issue on the next run.
- A dispatched run with everything green closes the issue.
- Each watchdog fails when its partner's latest run is older than 2 days.

## Open

- watchdog-A1: what counts as activity for the 60-day rule (github-stats pushes, re-enabling, issues). Closes when a repo's `disabled_inactivity` history, or GitHub documentation, settles it; until then both watchdogs run.

## Why

- GitHub disables scheduled workflows in public repos after 60 days without activity, with no warning.
- Two watchdogs in separate repos catch each other being disabled.
- Other disabled states are deliberate and need the owner.
