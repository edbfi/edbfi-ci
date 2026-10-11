# Scheduled maintenance

## Contract

### Upstream watcher

1. The upstream watcher MUST run weekly and on dispatch, on main only, with `GITHUB_TOKEN` and `issues: write`. Runs MUST be serialized without cancellation.
2. Every trigger in [watch.yml](../watch.yml) MUST be checked; failed lookups or malformed responses MUST fail the run before any issue is created. Dry runs MUST perform the same reads without writes.
3. Each triggered id MUST get at most one issue, identified by its body marker across all pages of open and closed issues. Completed actions MUST remove their trigger; closing an issue MUST NOT create a replacement.
4. Version triggers MUST compare stable three-part versions numerically. PR triggers MUST require a merged PR. Manual triggers MUST require explicit confirmation by id.

### Workflow immortality (D19)

5. Every in-scope repo with a scheduled workflow, and `edbfi-ci`, MUST carry [immortality.yml](../templates/immortality.yml) as `.github/workflows/immortality.yml`. It MUST re-enable that repo's workflows monthly with the PAT in the repo secret `IMMORTALITY_TOKEN`, and MUST leave manually disabled workflows disabled.

## Parameters

- Immortality credential: PAT `edbfi-workflow-immortality` (Actions RW, Metadata R, no expiry) covering every repo that carries `immortality.yml` (and, by owner decision, every other public rollout repo in advance), stored in each as the Actions secret `IMMORTALITY_TOKEN`. Coverage: [STATE.md](../STATE.md#github-state).
- By owner decision (D19), `edbfi-ci-playground` and the scheduled hotio-family repos carry it too. The hotio family is outside this design ([repos.md](repos.md#contract) rule 3), so its copies guard on its default branch instead of main.
- Upstream conditions and actions: [watch.yml](../watch.yml); schedule, permissions and dispatch inputs: [workflow](../.github/workflows/watch.yml); implementation: [watch.py](../tools/watch.py).
- Preview locally: `uv run python tools/watch.py --dry-run` (authenticated `gh` required). For a manual condition, add `--manual <id>` only after verifying it. Dispatch defaults to dry-run; unset that input to publish issues. Local publishing must not overlap a workflow run.

## Verification

- A dispatched `immortality.yml` run passes, and a workflow disabled by hand stays disabled.
- Watcher tests cover version boundaries, merge state, manual confirmation, pagination, repeat runs, dry-run writes and failed lookups. Run the local preview to verify current upstream responses.

## Open

- watchdog-A1: what counts as activity for the 60-day rule (github-stats pushes, re-enabling, issues); `immortality.yml` relies on re-enabling. Closes when a repo's `disabled_inactivity` history, or GitHub documentation, settles it.

## Why

- GitHub disables scheduled workflows in public repos after 60 days without activity, with no warning.
- Failed scheduled runs, `immortality.yml`'s included, already reach the owner as GitHub notifications, so no watchdog duplicates them (D14).
- Other disabled states are deliberate and need the owner.
