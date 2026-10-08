# Auto-merge (D2, D5)

## Contract

1. Every Dependabot PR, majors included, MUST be eligible, and MUST merge once `ci-ok` and `pr-policy` pass on its current head. CI is the only gate, so gaps in smoke depth are merge risks.
2. `dependabot-auto-merge.yml` MUST exist in every public repo except replex, and only after the repo's ruleset exists ([settings.md](settings.md#contract)).
3. Authorisation MUST be the PR author `dependabot[bot]` plus a same-repository head. The `github.actor` term only filters later pushes; the author check MUST NOT be removed.
4. The `if:` MUST stay a single-line plain scalar.
5. The workflow MUST use the PAT `edbfi-dependabot-auto-merge` through the Dependabot secret `DEPENDENCY_AUTOMERGE_TOKEN`, never `GITHUB_TOKEN`. The PAT and the secret MUST cover exactly the repos running the workflow; the secret MUST NOT exist as an Actions secret.
6. The enable step MUST NOT pass `--subject` or `--body`, so the squash commit takes the PR title ([pr-policy.md](pr-policy.md#contract)).
7. replex has no auto-merge workflow and no PAT (its settings: [settings.md](settings.md#contract)). It is merged by hand after reading the advisory `ci-ok`, and moves to the normal path once its CI is green and enforced.
8. dox has no auto-merge or rulesets; it is merged by hand.
9. The Dependabot auto-merge workflow MUST retry transient GitHub merge-state instability within a bounded limit, keep the head guard on every attempt, and fail on other errors unless the head moved.

### Every other PR

10. Outside replex and dox (rules 7 and 8), every PR MUST merge, squashed, with no manual merge step, once its required checks pass on its current head and every review finding on that head has a reply: fixed in a commit, or rejected with a reason. It MUST NOT merge earlier. The ruleset's required checks gate the merge ([settings.md](settings.md#contract) rule 4); the author enforces the replies through rule 11 and resolves each thread it answered. Pullfrog stays advisory ([ci.md](ci.md#contract) rule 21); Dependabot PRs have no author to answer findings, so rule 1 alone gates them.
11. The author, an agent included, MUST enable auto-merge on its PR (`gh pr merge --auto --squash`) only once its review loop has ended on the current head. A stacked PR MUST get it only after its parent has merged and the PR targets main: auto-merge doesn't wait for a parent.
12. Before a repo's rollout, as an exception to rules 10-11: no required check exists, so auto-merge merges at once; where `allow_auto_merge` is still off, the author merges with `gh pr merge --squash --match-head-commit <head>` once rule 10 holds. The agent MUST first run the repo's gates and record them in the PR body; they stand in for the required checks.
13. Review loop: after opening a PR and after every push, the author waits up to 30 minutes for Pullfrog's review of the current head (a progress comment is not a review). Without one, it requests one once with `@pullfrog review` and waits up to 30 more minutes, then ends the loop on the checks and records `no bot review received`. Pullfrog's Fix links MUST NOT be used.
14. Every finding is checked against the source, then answered once per revision of its comment: APPROVED (fixed as suggested), REVISED (fixed differently, saying how) or REJECTED (with the reason or the owner decision it conflicts with); owner decisions win over bot suggestions. The author tracks answered items by ID and body revision, so edited comments are re-read and nothing is answered twice; a failed or partial read is never an empty result. A thread a person reopens is answered once; reopened again, it stays open for the owner.
15. The author pushes only a head whose gates ran, rewrites pushed history only when the step requires it (`--force-with-lease` on the expected remote head), and on a parent change moves only the PR's own commits.
16. A PR is closed unmerged only when an owner decision supersedes it, with a comment naming the decision and the replacement; never to get around review, failing checks or unfinished work.

## Parameters

- PAT `edbfi-dependabot-auto-merge`: no expiry; Contents, Pull requests and Workflows RW (`github-actions` PRs modify workflow files).
- Current coverage and leftover Actions copies: [STATE.md](../STATE.md#github-state).
- Workflow: [dependabot-auto-merge.yml](../templates/dependabot-auto-merge.yml).
- GitHub rejects `--auto --match-head-commit` with an outdated SHA [V, 2026-09-30].
- A repository-scoped fine-grained PAT merges both immediately and after required checks recover, including workflow updates, and starts push CI on the squash SHA [V, 2026-09-30, playground].

## Verification

- actionlint, zizmor and `privileged-jobs` pass on the workflow.
- In each rolled-out repo, a Dependabot PR merges on its own once both checks pass, and its merge starts a `push` run of `ci.yml`.
- The [script tests](../tools/test_templates.py) verify transient recovery, exhausted retries, head changes and permanent failures.
- A PR by any other author, or from a fork, skips `enable`.
- An agent enables auto-merge only after its review loop ends on the current head, and on a stacked PR only after the parent merged and the PR targets main.
- Each PR body records its review outcome (findings with verdicts, or `no bot review received`) and the final head's checks.

## Open

- automerge-A1: that PAT merges trigger the gated Pages deployment. Closes with an observed deployment in the portaler pilot (S6).

## Why

- `gh pr merge --auto` merges immediately when no required check blocks it, hence ruleset first.
- Once checks pass and findings are answered, a person adds no safety ([README](../README.md#principles) principle 1); auto-merge is the upstream mechanism (principle 4).
- PAT merges trigger `push` CI, which `GITHUB_TOKEN` merges would not; that justifies non-strict required checks.
- Accepted residual risk (D2): a bumped action runs in its own PR and can make its own job pass. The inline `jq` gate and the privileged-job rule limit it.
