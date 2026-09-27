# Privileged-job rule

## Contract

1. A job is **privileged** if (case 1) it references any non-`GITHUB_TOKEN` secret, in any workflow, workflow-level `env:` included; or (case 2) it is PR-reachable and grants any `write` permission, `write-all` and workflow defaults included.
2. A job is **PR-reachable** if its workflow has a PR-event trigger (`pull_request`, `pull_request_target`, `pull_request_review*`, `issue_comment`, `merge_group`), unless the job's `if:` is a pure `&&` chain with `github.event_name != 'pull_request'` as a top-level conjunct.
3. A privileged job MUST NOT have `uses:`, `container:` or `services:`, MUST NOT check out PR code, and MUST NOT restore caches. It uses only inline shell and preinstalled tools (`git`, `gh`, `jq`, `curl`), plus toolchains installed inline from a pinned URL whose SHA-256 is checked.
4. A privileged job MUST validate PR-derived data as data and never execute it.
5. A privileged job consuming an artifact MUST:
   1. download it with `gh run download … -D "$(mktemp -d)"` (needs `actions: read`);
   2. require exactly one regular, non-symlink file with the expected name;
   3. for patches, build the repo in a separate fresh `mktemp -d` with `git init` and apply the patch by absolute path;
   4. require `git apply --summary` to show no create, delete, rename or mode change;
   5. run every `git` command with `-c core.hooksPath=/dev/null`.
6. Work needing third-party actions MUST be split: an unprivileged job builds, and a shell-only privileged job publishes.
7. A dispatchable job holding a write credential MUST add `github.ref == 'refs/heads/main'` to its `if:`.
8. A privileged job fetching its own repo MUST pass `git -c http.extraheader="AUTHORIZATION: basic <base64 of x-access-token:$GITHUB_TOKEN>" fetch …` per command and MUST NOT write it to `.git/config`.
9. If collaborators are ever given write access, secrets MUST move into environments with branch or tag policies.

## Parameters

- Enforced by the `privileged-jobs` shared hook ([prek.md](prek.md#contract)).
- Only the owner has write access today.

## Verification

- `privileged-jobs` passes on every workflow in the repo.
- Every privileged job's toolchain download has a SHA-256 check next to it.

## Open

- None.

## Why

- Dependabot bumps actions with no cooldown, so a compromised action release (as with `tj-actions/changed-files`, March 2025) would run next to a secret within hours.
- Trusted-ref guards catch mistakes; they aren't a boundary against someone with write access.
- The per-command extra header works in private repos too and leaves no credential on disk.
