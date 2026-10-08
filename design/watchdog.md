# Scheduled maintenance

## Contract

### Schedule watchdog (D14 option 1)

1. `edbfi-ci` and github-stats MUST each run a watchdog, daily and on dispatch, watching each other.
2. Per in-scope public repo, it MUST check that every scheduled workflow is `active`, and that its latest successful scheduled run is within budget.
3. It MUST check that the partner watchdog ran successfully within 2 days.
4. It MUST re-enable only workflows in state `disabled_inactivity`, then dispatch each once. Every other disabled state is only reported.
5. It MUST keep exactly one tracking issue in its own repo (`issues: write`), closed when everything is green.
6. Its job is privileged ([security.md](security.md#contract)).

### Upstream watcher

7. The upstream watcher MUST run weekly and on dispatch, on main only, with `GITHUB_TOKEN` and `issues: write`. Runs MUST be serialized without cancellation.
8. Every trigger in [watch.yml](../watch.yml) MUST be checked; failed lookups or malformed responses MUST fail the run before any issue is created. Dry runs MUST perform the same reads without writes.
9. Each triggered id MUST get at most one issue, identified by its body marker across all pages of open and closed issues. Completed actions MUST remove their trigger; closing an issue MUST NOT create a replacement.
10. Version triggers MUST compare stable three-part versions numerically. PR triggers MUST require a merged PR. Manual triggers MUST require explicit confirmation by id.

### Workflow immortality (D19)

11. Every in-scope repo with a scheduled workflow, and `edbfi-ci`, MUST carry [immortality.yml](../templates/immortality.yml) as `.github/workflows/immortality.yml`. It MUST re-enable that repo's workflows monthly with the PAT in the repo secret `IMMORTALITY_TOKEN`, and MUST leave manually disabled workflows disabled.
12. Immortality MUST NOT replace the watchdog: it still checks every scheduled workflow, `immortality.yml` included (rules 2-4), so failed and late runs are still reported.

## Parameters

- Budgets: `ci.yml` 8 days; `immortality.yml` 32 days; EasyHDR audit 2 days; Miri 8 days; D8 schedulers per their cadence ([d8.md](d8.md#contract)); repo-patches `watch-hotio.yml` too (owner, 2026-10-07), its value set in S16.
- Credential: PAT `edbfi-schedule-watchdog` (Actions RW, Metadata R on every in-scope public repo plus `edbfi-ci`); the owner creates it before S16.
- Immortality credential: PAT `edbfi-workflow-immortality` (Actions RW, Metadata R, no expiry) covering every repo that carries `immortality.yml` (and, by owner decision, every other public rollout repo in advance), stored in each as the Actions secret `IMMORTALITY_TOKEN`. Coverage: [STATE.md](../STATE.md#github-state).
- By owner decision (D19), `edbfi-ci-playground` and the scheduled hotio-family repos carry it too. The hotio family is outside this design ([repos.md](repos.md#contract) rule 3), so its copies guard on its default branch instead of main.
- Upstream conditions and actions: [watch.yml](../watch.yml); schedule, permissions and dispatch inputs: [workflow](../.github/workflows/watch.yml); implementation: [watch.py](../tools/watch.py).
- Preview locally: `uv run python tools/watch.py --dry-run` (authenticated `gh` required). For a manual condition, add `--manual <id>` only after verifying it. Dispatch defaults to dry-run; unset that input to publish issues. Local publishing must not overlap a workflow run.

## Verification

- Disabling a scheduled workflow by hand is reported in the tracking issue on the next run.
- A dispatched run with everything green closes the issue.
- Each watchdog fails when its partner's latest run is older than 2 days.
- A dispatched `immortality.yml` run passes, and a workflow disabled by hand stays disabled.
- Watcher tests cover version boundaries, merge state, manual confirmation, pagination, repeat runs, dry-run writes and failed lookups. Run the local preview to verify current upstream responses.

## Open

- watchdog-A1: what counts as activity for the 60-day rule (github-stats pushes, re-enabling, issues); `immortality.yml` relies on re-enabling. Closes when a repo's `disabled_inactivity` history, or GitHub documentation, settles it; until then the design keeps both mechanisms (rules 1 and 11).

## Why

- GitHub disables scheduled workflows in public repos after 60 days without activity, with no warning.
- Two watchdogs in separate repos catch each other being disabled.
- Other disabled states are deliberate and need the owner.
- Immortality only prevents the 60-day disable; failed, late or otherwise disabled schedules still need the watchdog.
