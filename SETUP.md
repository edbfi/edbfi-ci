# Adding a repo

The GitHub-side setup, which no file in a repo records. Order matters.

1. Copy the matching `ci-*.yml`, `pr-policy.yml`, `dependabot.*.yml` and `pre-commit/<stack>/` config from `templates/`, adapted to the repo. Pages repos also take `actionlint.pages.yaml` as `.github/actionlint.yaml`, Biome repos `biome-migrate.yml`, and repos with a scheduled workflow `immortality.yml`. CI calls repo-local commands, so every check also runs locally.
2. Merge it, so `ci-ok` and `pr-policy` have run: GitHub offers only checks that ran in the last 7 days.
3. Apply the settings and ruleset below.
4. Only then add `dependabot-auto-merge.yml`.
5. Turn on Dependabot security updates last: a security PR opened before `dependabot.yml` lands can't be rebased.
6. Fix required-peer mismatches on main before enabling `check-peers`, or main starts red.

## Settings

- Actions: enabled, SHA pinning required, default `GITHUB_TOKEN` permission read, "Allow GitHub Actions to create and approve pull requests" off.
- Merging: squash only, title `PR_TITLE` and message `COMMIT_MESSAGES`, auto-merge on, delete branch on merge, web commit sign-off required.
- Security: dependency graph, Dependabot alerts, security updates, grouped security updates (UI only), secret scanning and push protection. gitleaks runs only as a local hook.
- Pages repos: source "GitHub Actions"; the `github-pages` environment allows `main` only.

## Ruleset

One ruleset, `main`, on the default branch, and no classic branch protection:

- its only rule: required checks `ci-ok` and `pr-policy` from GitHub Actions, not strict;
- its only bypass actor: the repository admin role in mode `always`, so the owner and homebrew-taps' deploy key can push straight to main.

Every PAT and write deploy key acts as the owner, so the ruleset is a merge gate, not a security boundary.

## Credentials

Fine-grained PATs, each granted the repos that use it:

| Secret | Store | PAT and permissions | Used by |
|---|---|---|---|
| `DEPENDENCY_AUTOMERGE_TOKEN` | Dependabot, never Actions | `edbfi-dependabot-auto-merge`: Contents, Pull requests, Workflows RW | auto-merge, Biome migration |
| `BIOME_MIGRATE_TOKEN` | Dependabot | `edbfi-biome-migrate`: Contents RW | Biome migration |
| `IMMORTALITY_TOKEN` | Actions | `edbfi-workflow-immortality`: Actions RW, Metadata R | `immortality.yml` |

Hotio family: repo-patches' `PERSONAL_TOKEN` is `edbfi-hotio-mirror-sync`; base-image's and the docker repos' `PERSONAL_TOKEN` is `edbfi-hotio-container-sync`. Revoke neither.

## Pullfrog

Copy `pullfrog.yml`. The Claude subscription lives at Pullfrog account scope, never in Actions secrets. Apply the review prompt with `pullfrog config set prompts.review --file templates/pullfrog-review.txt --repo <owner/repo>`, and [the settings](templates/pullfrog-settings.json) in the Pullfrog console, which has the only switches for bot PRs and base branches. `python3 tools/sync_pullfrog.py --check <checkout>…` reports drift in existing copies.
