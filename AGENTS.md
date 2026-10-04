# Agent instructions

`edbfi-ci` is the single source of truth for CI across the edbfi repos: design, state, shared code and runbook. The work happens here, one step at a time.

**Start:** read this file, then [STATE.md](STATE.md), and take the first step whose status isn't `done`.

## Working model

1. **One step per session, one PR per step.** A step may also open PRs in the target repos it touches. Its `edbfi-ci` PR records the outcome.
2. **Every step ends with the [cleanup gate](MAINTENANCE.md#cleanup-gate), which blocks the step.** A step isn't done until the gate passes, and the gate's changes are part of the same PR.
3. **Docs describe only two things:** the target design ([design/](design/)) and the current state ([STATE.md](STATE.md), [DECISIONS.md](DECISIONS.md)). Anything finished is removed from plans and reduced to state. Anything superseded is deleted, not marked as old.
4. **Each fact lives in one place.**
   - Code and concrete values (pins, schedules, labels, commands) live in `templates/` or `hooks/`. Docs link to the file instead of copying it.
   - Rules live in exactly one `design/*.md`.
   - Progress lives only in `STATE.md`.
5. **No reports in the repo.** Session summaries, logs, test evidence, migration checklists and "what I did" go in the **PR body**, never in a file. `git log` and the PR history are the history.
6. **Be precise, not complete.** Leave out anything that doesn't change what someone would do. A one-line reason is enough; drop reasons that restate the rule. Don't add a new doc file unless an existing module truly can't hold the content.
7. **Automated guards back these rules** ([`tools/doc_guard`](tools/doc_guard/doc_guard.py)). Never weaken a guard or raise a cap to get past it. Trim the content instead.
8. **Never write secret values.** Secret names are fine. Don't change GitHub settings, secrets or other repos, except where the current step says so. Anything that needs the owner goes under "Owner actions" in the PR body.

## Design modules

Each `design/*.md` has exactly the sections Contract · Parameters · Verification · Open · Why.

- **Contract:** numbered MUST and MUST NOT rules.
- **Parameters:** only values that no template holds yet; once a template exists, a link to it.
- **Verification:** concrete checks; each rollout step runs the checks for its modules.
- **Open:** unverified assumptions as IDs (`ci-A1`), each saying what would close it.
- **Why:** at most 5 one-line bullets.

## Environment

- **Working copy:** `~/Documents/GitHub/edbfi/edbfi-ci` (`git@github.com-edbfi:edbfi/edbfi-ci.git`), public, default branch `main`.
- **License:** AGPL-3.0-only. Keep `LICENSE`; use this SPDX identifier in package metadata and new source files.
- **Target repos:** clone into `~/Documents/GitHub/edbfi/ci-refactor/<repo>` if missing, and `git fetch` before relying on a clone.
- **`gh`:** a shim refuses to run outside `~/Documents/GitHub/edbfi/…`, so run it from inside that tree.
- **Archive:** `~/Documents/GitHub/edbfi/ci-refactor-notes` (local-only, no remote) is frozen background: the old plan, its revision reasoning and settings snapshots from 2026-09-26. Read it only when this repo doesn't answer a question; this repo wins. Never copy text from it or edit it.
- **Rules:** read every `.agents/rules/*.md` in the repo you work in, if the directory exists; project rules override these instructions.
- **Commits:** Conventional Commits with a DCO sign-off (`git commit -s`). Work on a branch and open a PR; merging is automated, except in replex and dox ([auto-merge.md](design/auto-merge.md#contract) rules 10-12).
- **Tool choice:** Prefer `gh`, `git` and other purpose-built CLIs for repository operations. For browser or frontend interaction, and website access using a signed-in session, use the `ego-browser` tool and skill instead of built-in browser tools.
- **Tools:** verified versions are in [design/prek.md](design/prek.md#parameters); check for newer ones at the start of each step.
