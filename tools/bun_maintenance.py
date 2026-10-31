# SPDX-License-Identifier: AGPL-3.0-only
"""Open Bun runtime-bump and audit-fix PRs in the edbfi Bun repos.

Dependabot can't bump `packageManager` (dependabot/dependabot-core#4830) and has no
Bun security updates, so bun-maintenance.yml runs this daily:

- `target` and `plan` (unprivileged) find the latest Bun release and the Bun repos,
  run `bun audit fix` on each repo's default branch and write plan.json.
- `apply` (privileged, BUN_MAINTENANCE_TOKEN) re-derives the target and the repo set,
  computes the runtime bump itself, validates plan.json's audit patches and keeps one
  PR per repo and branch. It never moves an existing branch: a stale one is deleted
  under a lease and recreated, so the token needs no Workflows permission.

It runs on the runner's system Python (3.12), stdlib only.
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

OWNER = "edbfi"
GITHUB = "https://github.com"
RUNTIME = "chore/bun-runtime"
AUDIT = "fix/bun-audit"
PIN_FILES = ("package.json", ".bun-version")
AUDIT_PATHS = {"bun.lock", "package.json"}
DEPENDENCY_KEYS = {
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "overrides",
    "catalog",
    "catalogs",
}
BOT = "github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"
BOT_NAME, BOT_EMAIL = BOT[:-1].split(" <")
VERSION = re.compile(r"\d+\.\d+\.\d+")
RELEASE_TAG = re.compile(r"bun-v(\d+\.\d+\.\d+)")
PACKAGE_MANAGER = re.compile(r'("packageManager"\s*:\s*")bun@([^"]*)(")')
ENGINES = re.compile(r'"engines"\s*:\s*\{[^{}]*\}')
ENGINES_BUN = re.compile(r'("bun"\s*:\s*")([^"]*)(")')
DEPENDENCY_VERSION = re.compile(r"[~^]?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
SHA = re.compile(r"[0-9a-f]{40}")
PLAN_KEYS = {"repo", "base_sha", "status", "audit_patch", "fixed", "left"}


class Error(RuntimeError):
    pass


@dataclass(frozen=True)
class Repo:
    name: str
    branch: str
    sha: str
    files: tuple[tuple[str, str], ...]
    has_lock: bool
    broken: str = ""  # why its pin can't be bumped; it still gets audit PRs


@dataclass(frozen=True)
class Entry:
    repo: str
    base_sha: str
    status: str
    audit_patch: str
    fixed: tuple[str, ...]
    left: tuple[str, ...]


@dataclass(frozen=True)
class PullRequest:
    url: str
    head: str
    qualifies: bool
    conflicting: bool
    auto_merge: bool


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load(text: str) -> object:
    return cast(object, json.loads(text))


def as_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise Error("expected a JSON object")
    return cast(dict[str, object], value)


def as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise Error("expected a JSON array")
    return cast(list[object], value)


def as_str(value: object) -> str:
    if not isinstance(value, str):
        raise Error("expected a JSON string")
    return value


def version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def older(pin: str, target: str) -> bool:
    return bool(VERSION.fullmatch(pin)) and version(pin) < version(target)


# Pins


def root_pins(entries: list[object]) -> tuple[frozenset[str], bool]:
    """The regular pin files and whether a bun.lock sit at the root of a tree."""
    names = {
        as_str(entry.get("path"))
        for entry in map(as_dict, entries)
        if entry.get("type") == "blob" and entry.get("mode") == "100644"
    }
    return frozenset(name for name in PIN_FILES if name in names), "bun.lock" in names


def current_pin(files: Mapping[str, str]) -> str | None:
    """The root Bun pin: package.json's packageManager, else .bun-version."""
    text = files.get("package.json")
    if text is not None:
        manager = as_dict(load(text)).get("packageManager")
        if isinstance(manager, str) and manager.startswith("bun@"):
            return manager.removeprefix("bun@")
    text = files.get(".bun-version")
    return text.strip() if text is not None else None


def bump(files: Mapping[str, str], target: str) -> dict[str, str]:
    """New text for each root pin file whose pin is older than target."""
    new: dict[str, str] = {}
    text = files.get("package.json")
    manager = current_pin({"package.json": text}) if text is not None else None
    if text is not None and manager is not None:
        matches = PACKAGE_MANAGER.findall(text)
        if len(matches) != 1:
            raise Error("package.json: packageManager is not one plain string")
        if not VERSION.fullmatch(manager):
            raise Error(f"package.json: packageManager bun@{manager} is not X.Y.Z")
        if older(manager, target):
            edited = PACKAGE_MANAGER.sub(lambda m: f"{m[1]}bun@{target}{m[3]}", text)
            engines = ENGINES.search(edited)
            if engines:
                block = ENGINES_BUN.sub(
                    lambda m: f"{m[1]}{target}{m[3]}" if m[2] == manager else m[0],
                    engines[0],
                )
                edited = edited[: engines.start()] + block + edited[engines.end() :]
            check_bump(text, edited, target)
            new["package.json"] = edited
    text = files.get(".bun-version")
    if text is not None and older(text.strip(), target):
        new[".bun-version"] = target + "\n"
    return new


def without_pins(document: dict[str, object]) -> dict[str, object]:
    rest = {key: value for key, value in document.items() if key != "packageManager"}
    engines = rest.get("engines")
    if isinstance(engines, dict):
        rest["engines"] = {
            key: value
            for key, value in cast(dict[str, object], engines).items()
            if key != "bun"
        }
    return rest


def engines_bun(document: dict[str, object]) -> object:
    engines = document.get("engines")
    return cast(dict[str, object], engines).get("bun") if isinstance(engines, dict) else None


def check_bump(old_text: str, new_text: str, target: str) -> None:
    old, new = as_dict(load(old_text)), as_dict(load(new_text))
    if new.get("packageManager") != f"bun@{target}":
        raise Error("package.json: packageManager edit failed")
    if engines_bun(new) not in (engines_bun(old), target):
        raise Error("package.json: engines.bun edit failed")
    if without_pins(old) != without_pins(new):
        raise Error("package.json: the edit changed more than the Bun pins")


def changed_leaves(
    old: object, new: object, path: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], object, object]]:
    if isinstance(old, dict) and isinstance(new, dict):
        old_map, new_map = cast(dict[str, object], old), cast(dict[str, object], new)
        if old_map.keys() != new_map.keys():
            raise Error(f"package.json: keys changed under {'.'.join(path) or 'the root'}")
        return [
            leaf
            for key in old_map
            for leaf in changed_leaves(old_map[key], new_map[key], (*path, key))
        ]
    return [] if old == new else [(path, old, new)]


def check_audit_package_json(old_text: str, new_text: str) -> None:
    """Allow only version-string changes of existing dependency entries."""
    leaves = changed_leaves(load(old_text), load(new_text))
    for path, old, new in leaves:
        name = ".".join(path)
        if len(path) < 2 or path[0] not in DEPENDENCY_KEYS:
            raise Error(f"package.json: {name} is not a dependency entry")
        if not (isinstance(old, str) and isinstance(new, str)):
            raise Error(f"package.json: {name} is not a string change")
        if not DEPENDENCY_VERSION.fullmatch(new):
            raise Error(f"package.json: {name} = {new!r} is not a version")


# Plan and trust binding


def parse_plan(text: str) -> tuple[str, list[Entry]]:
    plan = as_dict(load(text))
    if set(plan) != {"target", "repos"}:
        raise Error("plan.json: unexpected keys")
    entries: list[Entry] = []
    for item in as_list(plan["repos"]):
        raw = as_dict(item)
        if set(raw) != PLAN_KEYS:
            raise Error("plan.json: unexpected repo keys")
        entry = Entry(
            repo=as_str(raw["repo"]),
            base_sha=as_str(raw["base_sha"]),
            status=as_str(raw["status"]),
            audit_patch=as_str(raw["audit_patch"]),
            fixed=tuple(map(as_str, as_list(raw["fixed"]))),
            left=tuple(map(as_str, as_list(raw["left"]))),
        )
        if not SHA.fullmatch(entry.base_sha) or entry.status not in {"ok", "error"}:
            raise Error(f"plan.json: bad entry for {entry.repo}")
        entries.append(entry)
    return as_str(plan["target"]), entries


def bind(text: str, target: str, repos: set[str]) -> dict[str, Entry]:
    """plan.json's entries, if it was made for this target and these repos."""
    planned, entries = parse_plan(text)
    if planned != target:
        raise Error(f"plan.json targets Bun {planned}, not {target}")
    bound: dict[str, Entry] = {}
    for entry in entries:
        if entry.repo not in repos:
            raise Error(f"plan.json names {entry.repo}, which is not a Bun repo")
        if entry.repo in bound:
            raise Error(f"plan.json names {entry.repo} twice")
        bound[entry.repo] = entry
    return bound


def read_artifact(directory: Path) -> str:
    """The one regular file the plan artifact may hold."""
    files = list(directory.iterdir())
    path = directory / "plan.json"
    if files != [path] or path.is_symlink() or not path.is_file():
        raise Error("the plan artifact must hold exactly one regular file, plan.json")
    return path.read_text()


# Publishing


def decide(
    desired: bool, status: str, prs: list[PullRequest], branch_sha: str | None
) -> list[tuple[str, str]]:
    """Actions for one branch: keep, arm, close, delete, create."""
    if not desired:
        if status != "ok":
            return [("keep", "")]
        actions = [("close", pr.url) for pr in prs]
        return actions + ([("delete", branch_sha)] if branch_sha else [])
    for pr in prs:
        if pr.qualifies and not pr.conflicting and pr.head == branch_sha:
            return [("keep", "")] if pr.auto_merge else [("arm", pr.url)]
    actions = [("close", pr.url) for pr in prs]
    return actions + ([("delete", branch_sha)] if branch_sha else []) + [("create", "")]


def run_actions(
    actions: list[tuple[str, str]],
    *,
    close: Callable[[str], None],
    arm: Callable[[str], None],
    delete: Callable[[str], bool],
    create: Callable[[], None],
) -> bool:
    """Run decide()'s actions; False if a lease failed and the branch was skipped."""
    for action, value in actions:
        if action == "close":
            close(value)
        elif action == "arm":
            arm(value)
        elif action == "delete" and not delete(value):
            return False
        elif action == "create":
            create()
    return True


# Subprocesses


def environment(token: str = "", **extra: str) -> dict[str, str]:
    # No tokens, and no GIT_DIR or GIT_INDEX_FILE from a calling git hook.
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"GH_TOKEN", "GITHUB_TOKEN", "BUN_MAINTENANCE_TOKEN"}
        and not key.startswith("GIT_")
    }
    env.update(GIT_TERMINAL_PROMPT="0", **extra)
    if token:
        env["GH_TOKEN"] = token
    return env


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    data: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env if env is not None else environment(),
        input=data,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        command = " ".join(arg for arg in args[:5] if not arg.startswith(("-", "core.")))
        raise Error(f"{command} failed: {result.stderr.strip()}")
    return result


def git(cwd: Path, *args: str, env: dict[str, str] | None = None, data: str | None = None) -> str:
    return run(
        ["git", "-c", "core.hooksPath=/dev/null", *args], cwd=cwd, env=env, data=data
    ).stdout.strip()


def push_env(token: str) -> dict[str, str]:
    """Credentials for one git push; never in argv, URLs or .git/config."""
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::add-mask::{basic}", flush=True)
    return environment(
        GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
        GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {basic}",
    )


def api(path: str, token: str) -> object:
    return load(run(["gh", "api", path], env=environment(token)).stdout)


def api_raw(path: str, token: str) -> str | None:
    result = run(
        ["gh", "api", "-H", "Accept: application/vnd.github.raw", path],
        env=environment(token),
        check=False,
    )
    if result.returncode and "HTTP 404" in result.stderr:
        return None
    if result.returncode:
        raise Error(f"gh api {path} failed: {result.stderr.strip()}")
    return result.stdout


def latest_bun(token: str) -> str:
    release = as_dict(api("repos/oven-sh/bun/releases/latest", token))
    match = RELEASE_TAG.fullmatch(as_str(release.get("tag_name")))
    if not match or release.get("prerelease") or release.get("draft"):
        raise Error("the latest oven-sh/bun release is not a stable bun-vX.Y.Z")
    return match[1]


def discover(token: str, only: str, target: str) -> list[Repo]:
    """Public, unarchived edbfi repos with pr-policy.yml and a root Bun pin."""
    pages = as_list(
        load(
            run(
                ["gh", "api", "--paginate", "--slurp", f"users/{OWNER}/repos?type=owner&per_page=100"],
                env=environment(token),
            ).stdout
        )
    )
    repos: list[Repo] = []
    for item in sorted(
        (as_dict(item) for page in pages for item in as_list(page)),
        key=lambda item: as_str(item["full_name"]),
    ):
        if item.get("private") or item.get("archived"):
            continue
        name, branch = as_str(item["full_name"]), as_str(item["default_branch"])
        sha = as_str(as_dict(as_dict(api(f"repos/{name}/git/ref/heads/{branch}", token))["object"])["sha"])
        if api_raw(f"repos/{name}/contents/.github/workflows/pr-policy.yml?ref={sha}", token) is None:
            continue
        pins, has_lock = root_pins(as_list(as_dict(api(f"repos/{name}/git/trees/{sha}", token))["tree"]))
        files = {path: api_raw(f"repos/{name}/contents/{path}?ref={sha}", token) or "" for path in pins}
        try:
            if current_pin(files) is None:
                continue
            _ = bump(files, target)
            broken = ""
        except (Error, ValueError) as error:
            broken = str(error)
        repos.append(Repo(name, branch, sha, tuple(sorted(files.items())), has_lock, broken))
    wanted = {f"{OWNER}/{part.strip()}" for part in only.split(",") if part.strip()}
    if unknown := wanted - {repo.name for repo in repos}:
        raise Error(f"not Bun repos: {', '.join(sorted(unknown))}")
    return [repo for repo in repos if not wanted or repo.name in wanted]


def open_prs(repo: str, branch: str, token: str) -> list[dict[str, object]]:
    fields = "url,headRefOid,headRepository,headRepositoryOwner,baseRefName,mergeable,autoMergeRequest"
    result = run(
        ["gh", "pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", fields],
        env=environment(token),
    )
    owner, name = repo.split("/")
    return [
        pr
        for pr in map(as_dict, as_list(load(result.stdout)))
        if as_dict(pr.get("headRepositoryOwner") or {}).get("login") == owner
        and as_dict(pr.get("headRepository") or {}).get("name") == name
    ]


def write_output(**values: str) -> None:
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a") as output:
            for key, value in values.items():
                _ = output.write(f"{key}={value}\n")


def summarize(line: str) -> None:
    print(line, flush=True)
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(path, "a") as summary:
            _ = summary.write(line + "\n")


# plan


def advisories(text: str) -> set[str]:
    """The high and critical advisories in `bun audit --json` output."""
    found: set[str] = set()
    for package, items in as_dict(load(text)).items():
        for advisory in map(as_dict, as_list(items)):
            if advisory.get("severity") in {"high", "critical"}:
                found.add(f"{as_str(advisory.get('url')).rsplit('/', 1)[-1]} ({package})")
    return found


def audit_repo(repo: Repo, work: Path) -> Entry:
    """Run `bun audit fix` on a fresh copy of the repo's default branch."""
    entry = Entry(repo.name, repo.sha, "ok", "", (), ())
    if not repo.has_lock:
        return entry
    _ = git(work, "init", "--quiet")
    _ = git(work, "fetch", "--quiet", "--depth=1", "--no-tags", f"{GITHUB}/{repo.name}.git", repo.sha)
    _ = git(work, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    try:
        before = advisories(run(["bun", "audit", "--json"], cwd=work, check=False).stdout)
        if not before:
            return entry
        fix = run(
            ["bun", "audit", "fix", "--audit-level=high", "--lockfile-only", "--ignore-scripts", "--json"],
            cwd=work,
            check=False,
        )
        report = as_dict(load(fix.stdout))
        if report.get("manifestUnavailable") or report.get("unaudited"):
            raise Error("bun audit fix could not read every package")
        after = advisories(run(["bun", "audit", "--json"], cwd=work, check=False).stdout)
    except (ValueError, Error) as error:
        log(f"{repo.name}: bun audit failed: {error}")
        return Entry(repo.name, repo.sha, "error", "", (), ())
    patch = run(["git", "diff", "--binary"], cwd=work).stdout
    return Entry(repo.name, repo.sha, "ok", patch, tuple(sorted(before - after)), tuple(sorted(after)))


def plan(only: str, out: Path) -> int:
    token = os.environ.get("GH_TOKEN", "")
    target = latest_bun(token)
    repos = discover(token, only, target)
    if run(["bun", "--version"]).stdout.strip() != target:
        raise Error(f"plan must run on Bun {target}")
    entries: list[Entry] = []
    has_work = False
    summarize(f"Target: Bun {target}\n\n| Repo | Pin | Audit | Left |\n|---|---|---|---|")
    for repo in repos:
        files = dict(repo.files)
        with tempfile.TemporaryDirectory() as work:
            entry = audit_repo(repo, Path(work))
        entries.append(entry)
        pending = any(open_prs(repo.name, branch, token) for branch in (RUNTIME, AUDIT))
        # A broken pin still sends the run to apply, which reports it and fails.
        runtime = bool(repo.broken) or bool(bump(files, target))
        has_work |= runtime or bool(entry.audit_patch) or pending
        audit = "error" if entry.status == "error" else "fix" if entry.audit_patch else "clean"
        pin = "broken" if repo.broken else current_pin(files)
        summarize(f"| {repo.name} | {pin} | {audit} | {', '.join(entry.left)} |")
        if repo.broken:
            print(f"::error::{repo.name}: {repo.broken}", flush=True)
        if entry.status == "error":
            print(f"::warning::{repo.name}: bun audit failed, no audit change this run", flush=True)
        if entry.left:
            print(f"::warning::{repo.name}: no in-range fix for {', '.join(entry.left)}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    _ = (out / "plan.json").write_text(
        json.dumps(
            {
                "target": target,
                "repos": [
                    {
                        "repo": entry.repo,
                        "base_sha": entry.base_sha,
                        "status": entry.status,
                        "audit_patch": entry.audit_patch,
                        "fixed": list(entry.fixed),
                        "left": list(entry.left),
                    }
                    for entry in entries
                ],
            },
            indent=2,
        )
    )
    write_output(has_work=str(has_work).lower())
    return 0


# apply


def changes(work: Path, old: str, new: str) -> dict[str, str]:
    """Path -> new blob between two trees; only in-place edits of regular files."""
    found: dict[str, str] = {}
    fields = git(work, "diff-tree", "-r", "-z", "--no-renames", "--raw", old, new).split("\0")
    for meta, path in zip(fields[0::2], fields[1::2]):
        old_mode, new_mode, _, blob, status = meta.lstrip(":").split(" ")
        if status != "M" or old_mode != "100644" or new_mode != "100644":
            raise Error(f"{path}: not an in-place edit of a regular file")
        found[path] = blob
    return found


def edited_tree(work: Path, base: str, files: Mapping[str, str]) -> str:
    """base's tree with files replaced, built in a private index."""
    env = environment(GIT_INDEX_FILE=str(work / ".git" / "maintenance.index"))
    _ = git(work, "read-tree", base, env=env)
    for path, text in files.items():
        blob = git(work, "hash-object", "-w", "--stdin", data=text)
        _ = git(work, "update-index", "--cacheinfo", f"100644,{blob},{path}", env=env)
    return git(work, "write-tree", env=env)


def patched_tree(work: Path, base: str, patch: str) -> str:
    """base's tree with plan.json's audit patch, checked the way biome-migrate does."""
    env = environment(GIT_INDEX_FILE=str(work / ".git" / "maintenance.index"))
    _ = git(work, "read-tree", base, env=env)
    if git(work, "apply", "--summary", env=env, data=patch):
        raise Error("audit patch creates, deletes, renames or changes modes")
    _ = git(work, "apply", "--cached", "--check", env=env, data=patch)
    _ = git(work, "apply", "--cached", env=env, data=patch)
    tree = git(work, "write-tree", env=env)
    paths = set(changes(work, base, tree))
    if not paths or not paths <= AUDIT_PATHS:
        raise Error(f"audit patch touches {', '.join(sorted(paths)) or 'nothing'}")
    if "package.json" in paths:
        check_audit_package_json(
            git(work, "show", f"{base}:package.json"), git(work, "show", f"{tree}:package.json")
        )
    return tree


@dataclass
class Target:
    repo: Repo
    work: Path
    main: str
    token: str
    run_url: str

    def branch_sha(self, branch: str) -> str | None:
        line = git(self.work, "ls-remote", "origin", f"refs/heads/{branch}")
        return line.split("\t")[0] if line else None

    def pull_requests(self, branch: str, desired: dict[str, str]) -> list[PullRequest]:
        found: list[PullRequest] = []
        for raw in open_prs(self.repo.name, branch, self.token):
            head = as_str(raw["headRefOid"])
            qualifies = False
            if raw.get("baseRefName") == self.repo.branch:
                _ = git(self.work, "fetch", "--quiet", "--filter=blob:none", "origin", head)
                base = git(self.work, "merge-base", self.main, head)
                try:
                    qualifies = changes(self.work, base, head) == desired
                except Error:
                    qualifies = False
            found.append(
                PullRequest(
                    url=as_str(raw["url"]),
                    head=head,
                    qualifies=qualifies,
                    conflicting=raw.get("mergeable") == "CONFLICTING",
                    auto_merge=raw.get("autoMergeRequest") is not None,
                )
            )
        return found

    def close(self, url: str) -> None:
        log(f"{self.repo.name}: closing {url}")
        comment = f"Superseded or no longer needed, per {self.run_url}."
        _ = run(["gh", "pr", "close", url, "--comment", comment], env=environment(self.token))

    def arm(self, url: str, sha: str) -> None:
        args = ["gh", "pr", "merge", "--auto", "--squash", "--match-head-commit", sha, url]
        for attempt in range(1, 6):
            result = run(args, env=environment(self.token), check=False)
            if not result.returncode:
                return
            if "unstable status" not in result.stderr or attempt == 5:
                raise Error(f"auto-merge failed for {url}: {result.stderr.strip()}")
            log("Merge state is still settling; retrying in 5 seconds")
            time.sleep(5)

    def delete(self, branch: str, sha: str) -> bool:
        lease = f"--force-with-lease=refs/heads/{branch}:{sha}"
        result = run(
            ["git", "-c", "core.hooksPath=/dev/null", "push", "--quiet", lease, "origin", f":refs/heads/{branch}"],
            cwd=self.work,
            env=push_env(self.token),
            check=False,
        )
        if result.returncode:
            print(f"::warning::{self.repo.name}: {branch} moved; skipped until the next run", flush=True)
        return result.returncode == 0

    def create(self, branch: str, tree: str, title: str, body: str) -> None:
        env = environment(
            GIT_AUTHOR_NAME=BOT_NAME,
            GIT_AUTHOR_EMAIL=BOT_EMAIL,
            GIT_COMMITTER_NAME=BOT_NAME,
            GIT_COMMITTER_EMAIL=BOT_EMAIL,
        )
        message = f"{title}\n\nSigned-off-by: {BOT}\n"
        commit = git(self.work, "commit-tree", tree, "-p", self.main, env=env, data=message)
        _ = run(
            [
                "git", "-c", "core.hooksPath=/dev/null", "push", "--quiet",
                f"--force-with-lease=refs/heads/{branch}:", "origin", f"{commit}:refs/heads/{branch}",
            ],
            cwd=self.work,
            env=push_env(self.token),
        )
        url = run(
            [
                "gh", "pr", "create", "--repo", self.repo.name, "--base", self.repo.branch,
                "--head", branch, "--title", title, "--body", body,
            ],
            env=environment(self.token),
        ).stdout.strip()
        log(f"{self.repo.name}: opened {url}")
        self.arm(url, commit)

    def publish(self, branch: str, tree: str | None, status: str, title: str, body: str) -> bool:
        desired = changes(self.work, self.main, tree) if tree else {}
        prs = self.pull_requests(branch, desired)
        heads = {pr.url: pr.head for pr in prs}
        actions = decide(bool(desired), status, prs, self.branch_sha(branch))
        return run_actions(
            actions,
            close=self.close,
            arm=lambda url: self.arm(url, heads[url]),
            delete=lambda sha: self.delete(branch, sha),
            create=lambda: self.create(branch, cast(str, tree), title, body),
        )


def apply_repo(repo: Repo, entry: Entry | None, target: str, token: str, work: Path) -> None:
    _ = git(work, "init", "--quiet")
    _ = git(work, "remote", "add", "origin", f"{GITHUB}/{repo.name}.git")
    _ = git(work, "fetch", "--quiet", "--filter=blob:none", "--no-tags", "origin", f"refs/heads/{repo.branch}")
    main = git(work, "rev-parse", "FETCH_HEAD")
    if entry is not None and entry.base_sha != main:
        log(f"{repo.name}: {repo.branch} moved since plan; the next run re-plans it")
        return
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_url = f"{server}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    repo_target = Target(repo, work, main, token, run_url)
    # Read at the fetched head, not discovery's API snapshot.
    files = {path: run(["git", "show", f"{main}:{path}"], cwd=work).stdout for path, _ in repo.files}
    footer = f"Opened by [bun-maintenance]({run_url}) in edbfi-ci."
    try:
        new = bump(files, target)
        broken = None
    except (Error, ValueError) as error:
        new, broken = {}, error
    if broken is None:
        old = min((current_pin({path: files[path]}) or target for path in new), key=version, default=target)
        _ = repo_target.publish(
            RUNTIME,
            edited_tree(work, main, new) if new else None,
            "ok",
            f"chore(deps): bump Bun from {old} to {target}",
            f"Bumps the Bun pin to [{target}](https://github.com/oven-sh/bun/releases/tag/bun-v{target}).\n\n{footer}",
        )
    status = entry.status if entry is not None else "error"
    patch = entry.audit_patch if entry is not None else ""
    fixed = "".join(f"- {item}\n" for item in entry.fixed) if entry is not None else ""
    left = "".join(f"- {item}\n" for item in entry.left) if entry is not None else ""
    body = "`bun audit fix --audit-level=high --lockfile-only` resolves:\n\n" + fixed
    if left:
        body += "\nStill open, no in-range fix:\n\n" + left
    _ = repo_target.publish(
        AUDIT,
        patched_tree(work, main, patch) if patch else None,
        status,
        "fix(deps): refresh vulnerable lockfile entries",
        f"{body}\n{footer}",
    )
    if broken is not None:
        raise broken


def apply(only: str, plan_dir: Path) -> int:
    token = os.environ.get("BUN_MAINTENANCE_TOKEN", "")
    if not token:
        raise Error("BUN_MAINTENANCE_TOKEN is not set (see SETUP.md)")
    text = read_artifact(plan_dir)
    target = latest_bun(token)
    repos = discover(token, only, target)
    entries = bind(text, target, {repo.name for repo in repos})
    failed: list[str] = []
    for repo in repos:
        try:
            with tempfile.TemporaryDirectory() as work:
                apply_repo(repo, entries.get(repo.name), target, token, Path(work))
        except (Error, ValueError) as error:
            print(f"::error::{repo.name}: {error}", flush=True)
            failed.append(repo.name)
    if failed:
        log(f"failed: {', '.join(failed)}")
    return int(bool(failed))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    _ = commands.add_parser("target")
    plan_parser = commands.add_parser("plan")
    _ = plan_parser.add_argument("--repos", default="")
    _ = plan_parser.add_argument("--out", type=Path, required=True)
    apply_parser = commands.add_parser("apply")
    _ = apply_parser.add_argument("--repos", default="")
    _ = apply_parser.add_argument("--plan-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    command = cast(str, args.command)
    try:
        if command == "target":
            target = latest_bun(os.environ.get("GH_TOKEN", ""))
            write_output(target=target)
            print(target)
            return 0
        if command == "plan":
            return plan(cast(str, args.repos), cast(Path, args.out))
        return apply(cast(str, args.repos), cast(Path, args.plan_dir))
    except (Error, ValueError) as error:
        print(f"::error::{error}", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
