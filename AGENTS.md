# Agent instructions

`edbfi-ci` holds the shared CI for the edbfi repos ([README](README.md)). Work on what you are asked.

## Rules

- Docs hold only what the code can't say: the policy in the README, the GitHub-side setup in [SETUP.md](SETUP.md), and short comments next to the code they explain. Most changes need no doc change. When a fact changes, search for every other statement of it and fix or delete it; never append history.
- No reports in the repo: evidence, deviations and "Owner actions" go in the PR body.
- Never write secret values. Don't change GitHub settings, secrets or other repos, or publish anything, unless the task says so.
- Conventional Commits with a DCO sign-off (`git commit -s`), on a branch, through a PR. New source files carry the `AGPL-3.0-only` SPDX line.
- Privileged workflow jobs (holding a secret, or PR-reachable with write access) follow [privileged_jobs.py](hooks/edbfi_hooks/privileged_jobs.py)'s rules; the hook checks only part of them.

## Pull requests

- After opening a PR and after each push, wait up to 30 minutes for Pullfrog's review of the head. Without one, ask once with `@pullfrog review` and wait 30 more minutes, then record `no bot review received`. Never use Pullfrog's Fix links.
- Check each finding against the source and answer it once: fixed, with the commit, or rejected, with the reason. Owner decisions beat bot suggestions. Resolve the threads you answered.
- Merge only once the review loop has ended on the current head and its required checks have passed, including the `pr-policy` run of the last title or body edit: the admin bypass lets a merge skip a pending check. Use `gh pr merge --auto --squash`, or a direct squash merge when the owner asks for one. A stacked PR merges only after its parent, retargeted to main.

## Environment

- Workspace: the `edbfi` account folder in the machine's GitHub directory (e.g. `~/github/edbfi`). The `gh` shim picks the account from the folder it runs in, so run it inside.
- Other repos: clone if missing and `git fetch --prune` before relying on a clone. A clone may hold the owner's uncommitted edits: never stash, reset or commit them; work in a `git worktree` from `origin/<default>`.
- Browser work and signed-in sites: use the `ego-browser` tool and skill.

## Hotio family

caddy, qbittorrent, qflood, sabnzbd, obzorarr-docker, otpravkarr-docker, zondarr-docker, base-image and website follow Hotio's own CI, not this repo's.

- In every clone, set `git config remote.origin.pushurl no-push-allowed` and never unset it; push deliberately with `git push git@github.com-edbfi:edbfi/<repo>.git <branch>`.
- Merging into a docker repo's channel branch publishes that channel's image, so even a pin bump is a release. PRs there come from a branch named `workflows`, the one branch `call-build` doesn't publish.
- `call-build.yml` and `call-update.yml` stay byte-identical to Hotio's except that `uses:` points at `edbfi/base-image/.github/workflows/{build,update}-on-call.yml@workflows`. These repos keep the default `GITHUB_TOKEN` permission `write`.
- base-image and website are generated from Hotio by repo-patches' `sync-hotio.yml`: change the generator, never the mirror.
