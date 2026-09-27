# PR policy (`pr-policy.yml`, D9)

## Contract

1. `pr-policy.yml` MUST trigger on `pull_request` `[opened, edited, reopened, synchronize]` and provide the required check `pr-policy`.
2. It MUST have `permissions: {}`, with only `pull-requests: read` on the job. It MUST NOT check out or run PR code.
3. Concurrency MUST be `pr-policy-<PR>-<event head SHA>` with cancel-in-progress, separate from `ci.yml`, so title edits never cancel CI.
4. The first step MUST be one API read, `gh api repos/{repo}/pulls/{n}`, for `title`, `head.sha` and `commits`, and MUST fail unless all are non-empty. Later checks MUST use these values, never the event payload.
5. The title MUST match the Conventional Commits header `type(scope)!: description`: scope and `!` optional, case-insensitive, no type allowlist, no length limit. The title MUST reach the script through `env:`, never inline.
6. If any commit uses `!` or a `BREAKING CHANGE:`/`BREAKING-CHANGE:` footer, the title MUST contain `!`.
7. Commits MUST be read with `gh api …/pulls/{n}/commits --paginate`. The check MUST fail closed if their count differs from `commits` or the last SHA isn't `head.sha`.
8. Every non-merge commit MUST carry a `Signed-off-by:` matching its author's name and email, except when **both** hold: the author is `dependabot[bot]` or `github-actions[bot]`, and the PR is Dependabot-authored with a same-repo head. Human commits on such PRs still need a sign-off.
9. Repos MUST set `squash_merge_commit_title=PR_TITLE` and `squash_merge_commit_message=COMMIT_MESSAGES`; auto-merge passes no `--subject`/`--body` ([auto-merge.md](auto-merge.md#contract)).

## Parameters

- Workflow and inline validation: [pr-policy.yml](../templates/pr-policy.yml).
- The commits endpoint returns at most 250 commits; a PR with more fails closed by rule 7.
- Title failure then correction on one SHA blocks then restores mergeability [V, 2026-09-27]. Re-running an older run uses the current title, but if it cancels a newer edit run, re-run that newer run too.

## Verification

- Titles `feat: x`, `Fix(scope)!: y` and `chore(deps): z` pass; `update stuff` fails.
- A `feat!:` commit under a title without `!` fails.
- An unsigned human commit fails; a Dependabot PR with only bot commits passes; a human commit pushed to it without sign-off fails.
- Editing the title re-runs `pr-policy` without cancelling `ci.yml`.
- Re-running an old run after a title fix uses the current title.

## Open

- prpolicy-A1: that auto-merge enabled without `--subject` uses the title at merge time. Closes by retitling a PR after enabling auto-merge and reading the squash commit (S4).
- prpolicy-A3: whether Dependabot commits carry a sign-off, and that they pass the exemption as designed. Closes with the first Dependabot PR on `edbfi-ci` (S4).

## Why

- Re-runs replay old payloads, so the API read is the source of truth.
- Inline `${{ }}` titles are a script-injection vector.
- The squash commit takes the PR title, so the title is what lands on main.
