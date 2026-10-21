# edbfi-ci

Shared CI for the edbfi repos: workflow, Dependabot and prek templates, two shared prek hooks and the Pullfrog review workflow. Each repo carries its own copy of the templates, and its Dependabot PRs, majors included, merge on their own once CI passes. Changing a template here doesn't update the copies.

## Principles

1. **No human in the loop** where automation can do it safely.
2. **No holds:** no Dependabot `ignore:` entries or pinned-back versions; a broken upstream release keeps its PR red until a later release fixes it. An unavoidable exception is named at the pin, with its upstream issue.
3. **Upstream mechanisms over custom code:** Dependabot, GitHub and prek first; custom code only for what none of them does, in one copy, here.

## Scope

Every public edbfi repo with a `ci.yml` and `pr-policy.yml`; repo-patches only for its tooling. Out of scope: the [Hotio family](AGENTS.md#hotio-family), which keeps Hotio's CI, the private dox notes and archived repos.

## Layout

- `templates/`: each file's header says where to copy it; [SETUP.md](SETUP.md) covers a new repo.
- `hooks/` and [`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml): `privileged-jobs` and `check-peers`. Cut a `vX.Y.Z` tag only when these change; consumers pin the tag's frozen SHA and Dependabot moves it.
- `tools/`: template lints and tests, and `sync_pullfrog.py`.

## Local checks

```sh
uv sync --locked
prek run --all-files --hook-stage manual
```

## License

[AGPL-3.0-only](LICENSE).
