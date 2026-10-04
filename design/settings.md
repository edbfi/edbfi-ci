# Repository settings and ruleset (public repos)

## Contract

1. Actions MUST be enabled with SHA pinning required, the default `GITHUB_TOKEN` permission read, and "Allow GitHub Actions to create and approve pull requests" off.
2. Merging MUST be squash only, with squash title and message as in [pr-policy.md](pr-policy.md#contract), `delete_branch_on_merge` on, `allow_auto_merge` on (off in replex), and `web_commit_signoff_required: true`.
3. Security MUST have dependency graph, Dependabot alerts, security updates, grouped security updates, Secret Protection and push protection on (D7). Public repos MUST NOT run a gitleaks CI scan; private dox MUST.
4. Each repo MUST have a ruleset "main" that targets the default branch, and no classic branch protection:
   1. a PR is required, with 0 approvals and no required conversation resolution;
   2. required checks `ci-ok` and `pr-policy` (replex: `pr-policy` only), sourced from GitHub Actions, **not strict**;
   3. force-pushes and deletion are blocked;
   4. no bypass actor, except homebrew-taps, whose only bypass actor is its write-enabled deploy key (D16).

## Parameters

- A required check can be selected only after it has run within the last 7 days, so each repo's rollout PR runs `ci-ok` and `pr-policy` before the ruleset is applied.
- Current drift is recorded in [STATE.md](../STATE.md#github-state).
- Personal-account rulesets accept an empty bypass list and enforce both checks [V, 2026-09-27]; the matching playground ruleset rejects direct pushes [V, 2026-09-30].
- The pinned `j178/prek-action` and `oven-sh/setup-bun` use Node 24 and run with SHA pinning required [V, 2026-09-27].

## Verification

- `gh api repos/{repo}` shows the merge settings above; `gh api repos/{repo}/actions/permissions` shows SHA pinning required; `…/actions/permissions/workflow` shows `read` and `can_approve_pull_request_reviews: false`.
- `gh api repos/{repo}/rulesets` shows one active ruleset "main" with the checks above, `strict_required_status_checks_policy: false`, `required_review_thread_resolution: false`, and an empty bypass list (homebrew-taps: the deploy key only).
- `gh api repos/{repo}/branches/{branch}/protection` returns 404 (no classic protection).
- A direct push to main is rejected.

## Open

- settings-A1: a deploy-key bypass actor and deploy-key pushes starting CI on a personal account. Closes when S19 pushes with homebrew-taps' deploy key.

## Why

- A leaked D5 PAT can still land code through a PR it opens itself. No bypass keeps the gate honest; it isn't a containment boundary.
- The admin can still edit the ruleset, so no bypass actor is needed.
- Pullfrog stays advisory ([ci.md](ci.md#contract) rule 21) and reviews Dependabot PRs too, so required conversation resolution would let its open threads block merges that only CI gates.
