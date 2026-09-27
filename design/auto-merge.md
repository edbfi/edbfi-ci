# Dependabot auto-merge (D2, D5)

## Contract

1. Every Dependabot PR, majors included, MUST be eligible, and MUST merge once `ci-ok` and `pr-policy` pass on its current head. CI is the only gate, so gaps in smoke depth are merge risks.
2. `dependabot-auto-merge.yml` MUST exist in every public repo except replex, and only after the repo's ruleset exists ([settings.md](settings.md#contract)).
3. Authorisation MUST be the PR author `dependabot[bot]` plus a same-repository head. The `github.actor` term only filters later pushes; the author check MUST NOT be removed.
4. The `if:` MUST stay a single-line plain scalar.
5. The workflow MUST use the PAT `edbfi-dependabot-auto-merge` through the Dependabot secret `DEPENDENCY_AUTOMERGE_TOKEN`, never `GITHUB_TOKEN`. The PAT and the secret MUST cover exactly the repos running the workflow; the secret MUST NOT exist as an Actions secret.
6. The enable step MUST NOT pass `--subject` or `--body`, so the squash commit takes the PR title ([pr-policy.md](pr-policy.md#contract)).
7. replex has no auto-merge workflow and no PAT (its settings: [settings.md](settings.md#contract)). It is merged by hand after reading the advisory `ci-ok`, and moves to the normal path once its CI is green and enforced.
8. dox has no auto-merge or rulesets; it is merged by hand.

## Parameters

- PAT `edbfi-dependabot-auto-merge`: no expiry; Contents, Pull requests and Workflows RW (`github-actions` PRs modify workflow files).
- Current coverage and leftover Actions copies: [STATE.md](../STATE.md#github-state).
- Template (actionlint 1.7.12 and zizmor 1.30.1 pass):

```yaml
name: Dependabot auto-merge
on:
  pull_request:
    types: [opened, reopened, synchronize]
permissions: {}
jobs:
  enable:
    if: github.event.pull_request.user.login == 'dependabot[bot]' && github.event.pull_request.head.repo.full_name == github.repository && github.actor == 'dependabot[bot]' # zizmor: ignore[bot-conditions] -- PR author is checked; actor only filters later pushes
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions: {}
    steps:
      - run: |
          if gh pr merge --auto --squash --match-head-commit "$HEAD_SHA" "$PR_URL"; then exit 0; fi
          current="$(gh pr view "$PR_URL" --json headRefOid --jq .headRefOid)" || { echo "::error::enable failed and head lookup failed"; exit 1; }
          if [ -n "$current" ] && [ "$current" != "$HEAD_SHA" ]; then echo "head moved to $current; its writer enables auto-merge"; exit 0; fi
          echo "::error::enable failed for the current head"; exit 1
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          GH_TOKEN: ${{ secrets.DEPENDENCY_AUTOMERGE_TOKEN }}
```

## Verification

- actionlint, zizmor and `privileged-jobs` pass on the workflow.
- A Dependabot PR merges on its own once both checks pass, and its merge starts a `push` run of `ci.yml` (automerge-A1).
- A PR by any other author, or from a fork, skips `enable`.

## Open

- automerge-A1: that PAT merges start `push` runs and Pages deploys, for deferred and immediate auto-merge, including workflow-modifying PRs. Closes with observed runs in S4 and the portaler pilot (S6).
- automerge-A2: that GitHub rejects an `--auto --match-head-commit` enable for a stale head. Closes by enabling against an outdated SHA on a test PR (S4).

## Why

- `gh pr merge --auto` merges immediately when no required check blocks it, hence ruleset first.
- PAT merges trigger `push` CI, which `GITHUB_TOKEN` merges would not; that justifies non-strict required checks.
- Accepted residual risk (D2): a bumped action runs in its own PR and can make its own job pass. The inline `jq` gate and the privileged-job rule limit it.
