# Repository settings and ruleset (public repos)

## Contract

1. Actions MUST be enabled with SHA pinning required, the default `GITHUB_TOKEN` permission read, and "Allow GitHub Actions to create and approve pull requests" off.
2. Merging MUST be squash only, with squash title and message as in [pr-policy.md](pr-policy.md#contract), `delete_branch_on_merge` on, `allow_auto_merge` on (off in replex), and `web_commit_signoff_required: true`.
3. Security MUST have dependency graph, Dependabot alerts, security updates, grouped security updates, Secret Protection and push protection on (D7). Public repos MUST NOT run a gitleaks CI scan; private dox MUST.
4. Each repo MUST have a ruleset "main" that targets the default branch, and no classic branch protection (D21):
   1. its only rule is required checks `ci-ok` and `pr-policy` (replex: `pr-policy` only), sourced from GitHub Actions, **not strict**; no PR, force-push or deletion rule;
   2. its only bypass actor is the repository admin role in mode `always`, so the owner, and homebrew-taps' deploy key (D16), can push straight to main.

## Parameters

- A required check can be selected only after it has run within the last 7 days, so each repo's rollout PR runs `ci-ok` and `pr-policy` before the ruleset is applied.
- Current drift is recorded in [STATE.md](../STATE.md#github-state).
- Personal-account rulesets enforce both checks [V, 2026-09-27] and accept the admin-role bypass [V, 2026-10-08, playground].
- Owner direct pushes are accepted, logged as `bypass` in the rule suites, and start push CI. Dependabot PRs whose auto-merge the D5 PAT enables wait for both checks, stay open while `ci-ok` is red and merge once it is green, logged as `pass` [V, 2026-10-08, playground].
- Deploy-key pushes on a personal account are attributed to the owner, logged as `bypass`, and start push CI [V, 2026-10-09, homebrew-taps e20e421 and playground]; the playground showed the admin-role bypass suffices without a `DeployKey` actor. A read-only deploy key can clone but not push.
- The pinned `j178/prek-action` and `oven-sh/setup-bun` use Node 24 and run with SHA pinning required [V, 2026-10-08].

## Verification

- `gh api repos/{repo}` shows the merge settings above; `gh api repos/{repo}/actions/permissions` shows SHA pinning required; `…/actions/permissions/workflow` shows `read` and `can_approve_pull_request_reviews: false`.
- `gh api repos/{repo}/rulesets` lists only "main"; `…/rulesets/{id}` shows it active on `~DEFAULT_BRANCH`, its only rule the checks above from GitHub Actions (`integration_id` 15368) with `strict_required_status_checks_policy: false`, and its only bypass actor `RepositoryRole` 5 in mode `always`.
- `gh api repos/{repo}/branches/{branch}/protection` returns 404 (no classic protection).
- An owner direct push to main is accepted with "Bypassed rule violations" and starts push CI; a PR with auto-merge enabled waits for both checks.

## Open

- None.

## Why

- Auto-merge needs only the required checks: without one it merges at once ([auto-merge.md](auto-merge.md#contract) rule 12). Safe automation ([README](../README.md#principles) principle 1) needs no other rule.
- The admin bypass lets the owner push small fixes straight to main; auto-merge still waits for the checks, even when enabled as the owner.
- Every PAT ([repos.md](repos.md#contract) rule 2) and write deploy key ([Parameters](#parameters)) acts as the owner, so it could push or merge past the checks too; the ruleset is a merge gate, not a containment boundary.
