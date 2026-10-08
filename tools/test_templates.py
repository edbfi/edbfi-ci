# SPDX-License-Identifier: AGPL-3.0-only
"""Exercise the shipped workflow scripts and their security boundaries locally."""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import cast, override

import yaml

type Value = str | list[Value] | dict[str, Value]
ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
GIT = shutil.which("git") or "git"


def mapping(value: Value) -> dict[str, Value]:
    assert isinstance(value, dict)
    return value


def items(value: Value) -> list[Value]:
    assert isinstance(value, list)
    return value


def load(path: Path) -> dict[str, Value]:
    return mapping(cast(Value, yaml.load(path.read_text(), Loader=yaml.BaseLoader)))


def steps(template: str, job: str) -> list[dict[str, Value]]:
    jobs = mapping(load(TEMPLATES / template)["jobs"])
    return [mapping(step) for step in items(mapping(jobs[job])["steps"])]


def script(template: str, job: str, index: int = 0) -> str:
    return str([step["run"] for step in steps(template, job) if "run" in step][index])


def run(
    code: str, env: dict[str, str], cwd: Path = ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-euo", "pipefail", "-c", code],
        cwd=cwd,
        env=os.environ | env,
        capture_output=True,
        text=True,
        check=False,
    )


class TemplateContractTest(unittest.TestCase):
    def test_python_selection(self) -> None:
        paths = [*TEMPLATES.glob("ci-*.yml"), *ROOT.glob(".github/workflows/*.yml")]
        for path in paths:
            for name, value in mapping(load(path)["jobs"]).items():
                job = mapping(value)
                actions = [mapping(step) for step in items(job["steps"])]
                for index, action in enumerate(actions):
                    if not str(action.get("uses", "")).startswith(
                        "astral-sh/setup-uv@"
                    ):
                        continue
                    with self.subTest(path=path.name, job=name):
                        inputs = mapping(action["with"])
                        self.assertNotIn("python-version-file", inputs)
                        reader = actions[index - 1]
                        self.assertEqual(
                            inputs["python-version"],
                            "${{ steps." + str(reader["id"]) + ".outputs.version }}",
                        )
                        defaults = mapping(
                            mapping(job.get("defaults", {})).get("run", {})
                        )
                        directory = str(
                            reader.get(
                                "working-directory", defaults.get("working-directory", ".")
                            )
                        )
                        directory = directory.replace("${{ matrix.dir }}", "backend")
                        with tempfile.TemporaryDirectory() as tmp:
                            root = Path(tmp)
                            cwd = root / directory
                            cwd.mkdir(parents=True, exist_ok=True)
                            output = root / "output"
                            version = cwd / ".python-version"
                            for content in (None, "", "3.14\n"):
                                if content is not None:
                                    _ = version.write_text(content)
                                result = run(
                                    str(reader["run"]),
                                    {"GITHUB_OUTPUT": str(output)},
                                    cwd,
                                )
                                self.assertEqual(
                                    result.returncode == 0,
                                    content == "3.14\n",
                                    result.stderr,
                                )
                            self.assertEqual(output.read_text(), "version=3.14\n")

    def test_ci_contracts(self) -> None:
        templates = sorted(TEMPLATES.glob("ci-*.yml"))
        self.assertGreaterEqual(len(templates), 10)
        for path in templates:
            with self.subTest(path=path.name):
                workflow = load(path)
                self.assertEqual(workflow["permissions"], {})
                events = mapping(workflow["on"])
                self.assertEqual(
                    set(events),
                    {"push", "pull_request", "schedule", "workflow_dispatch"},
                )
                self.assertNotIn("paths", mapping(events["push"]))
                jobs = mapping(workflow["jobs"])
                gate = mapping(jobs["ci-ok"])
                self.assertEqual(gate["if"], "always()")
                expected = {
                    name
                    for name in jobs
                    if name != "ci-ok"
                    and not name.startswith("audit")
                    and name != "deploy"
                }
                self.assertEqual(set(cast(list[str], gate["needs"])), expected)
                for name, value in jobs.items():
                    job = mapping(value)
                    self.assertIn("timeout-minutes", job)
                    self.assertIn("permissions", job)
                    if name.startswith("audit"):
                        self.assertEqual(
                            job["if"], "github.event_name != 'pull_request'"
                        )
                    elif name not in {"ci-ok", "deploy"}:
                        self.assertNotIn("if", job)
                    for step in items(job["steps"]):
                        action = mapping(step)
                        if "uses" in action:
                            self.assertRegex(str(action["uses"]), r"@[0-9a-f]{40}$")
                        if str(action.get("uses", "")).startswith("actions/checkout@"):
                            self.assertEqual(
                                mapping(action["with"])["persist-credentials"], "false"
                            )
                if "deploy" in jobs:
                    deploy = mapping(jobs["deploy"])
                    self.assertEqual(deploy["needs"], ["ci-ok"])
                    self.assertIn("needs.ci-ok.result == 'success'", str(deploy["if"]))
                    self.assertEqual(mapping(deploy["concurrency"])["queue"], "max")

    def test_pr_policy_never_cancels(self) -> None:
        for path in (
            TEMPLATES / "pr-policy.yml",
            ROOT / ".github/workflows/pr-policy.yml",
        ):
            with self.subTest(path=path.name):
                workflow = load(path)
                self.assertNotIn("concurrency", workflow)
                for job in mapping(workflow["jobs"]).values():
                    self.assertNotIn("concurrency", mapping(job))

    def test_ci_gate_results(self) -> None:
        for path in TEMPLATES.glob("ci-*.yml"):
            gate = script(path.name, "ci-ok")
            for result in ("success", "failure", "cancelled", "skipped"):
                for allowed in ("", "checks"):
                    with self.subTest(path=path.name, result=result, allowed=allowed):
                        actual = run(
                            gate,
                            {
                                "NEEDS": json.dumps({"checks": {"result": result}}),
                                "ALLOWED_SKIPS": allowed,
                            },
                        )
                        self.assertEqual(
                            actual.returncode == 0,
                            result == "success"
                            or (result == "skipped" and allowed == "checks"),
                            actual.stderr,
                        )
            self.assertNotEqual(
                run(gate, {"NEEDS": "{}", "ALLOWED_SKIPS": ""}).returncode, 0
            )

    def test_dependabot_and_hook_configs(self) -> None:
        for path in TEMPLATES.glob("dependabot.*.yml"):
            with self.subTest(path=path.name):
                updates = [mapping(item) for item in items(load(path)["updates"])]
                ecosystems = {str(item["package-ecosystem"]) for item in updates}
                self.assertIn("github-actions", ecosystems)
                self.assertEqual(
                    "pre-commit" in ecosystems, path.name != "dependabot.dox.yml"
                )
                self.assertNotIn("bun", ecosystems)
                for update in updates:
                    self.assertNotIn("ignore", update)
                    self.assertEqual(update["cooldown"], {"exclude": ["*"]})
                    self.assertEqual(
                        update["commit-message"],
                        {"prefix": "chore", "include": "scope"},
                    )
                # Parse the idle Bun blocks too: they must be complete update entries.
                restored = re.sub(r"(?m)^  # (?= |-)", "  ", path.read_text())
                parsed = mapping(
                    cast(Value, yaml.load(restored, Loader=yaml.BaseLoader))
                )
                for update in items(parsed["updates"]):
                    entry = mapping(update)
                    if entry.get("package-ecosystem") == "bun":
                        self.assertEqual(
                            list(mapping(entry["groups"])),
                            ["biome", "playwright", "vitest", "patch-minor"],
                        )
        for path in TEMPLATES.glob("pre-commit.*.yaml"):
            config = load(path)
            self.assertEqual(config["default_stages"], ["pre-commit", "manual"])
            repos = [mapping(repo) for repo in items(config["repos"])]
            for repo in repos:
                if str(repo["repo"]).startswith("https:"):
                    self.assertRegex(str(repo["rev"]), r"^[0-9a-f]{40}$")
            shared = [
                repo
                for repo in repos
                if repo["repo"] == "https://github.com/edbfi/edbfi-ci"
            ]
            self.assertEqual(len(shared), 1)
            self.assertEqual(
                shared[0]["rev"], "d07ccc13141d4aee4fa28546f4328f4e48d5363b"
            )


class ScriptTest(unittest.TestCase):
    root: Path = Path()

    @override
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.env: dict[str, str] = {}

    @override
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.root / "bin").mkdir()
        self.env = {
            "PATH": str(self.root / "bin") + os.pathsep + os.environ["PATH"],
            "RUNNER_TEMP": str(self.root),
            "GITHUB_OUTPUT": str(self.root / "output"),
            "GITHUB_REPOSITORY": "owner/repo",
            "PR_NUMBER": "2",
            "GH_TOKEN": "fixture",
        }

    def executable(self, name: str, source: str) -> None:
        path = self.root / "bin" / name
        _ = path.write_text(source)
        path.chmod(0o755)

    def execute(self, code: str) -> subprocess.CompletedProcess[str]:
        return run(code, self.env, self.root)


class PRPolicyTest(ScriptTest):
    def check_policy(
        self,
        title: str,
        messages: list[str],
        *,
        trusted: bool = False,
        authors: list[str] | None = None,
        stale: bool = False,
        count: int | None = None,
        fork: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        commit_authors = authors or ["human"] * len(messages)
        pr = {
            "title": title,
            "commits": len(messages) if count is None else count,
            "head": {
                "sha": "stale" if stale else str(len(messages)),
                "repo": {"full_name": "fork/repo" if fork else "owner/repo"},
            },
            "user": {"login": "dependabot[bot]" if trusted else "human"},
        }
        commits = [
            {
                "sha": str(i + 1),
                "parents": [{"sha": "parent"}],
                "author": {"login": author},
                "commit": {
                    "message": message,
                    "author": {"name": "Human", "email": "human@example.invalid"},
                },
            }
            for i, (message, author) in enumerate(
                zip(messages, commit_authors, strict=True)
            )
        ]
        _ = (self.root / "pr.json").write_text(json.dumps(pr))
        _ = (self.root / "commits.json").write_text(json.dumps([commits]))
        self.executable(
            "gh",
            '#!/bin/sh\ncase "$*" in *commits*) cat "$RUNNER_TEMP/commits.json" ;; *) cat "$RUNNER_TEMP/pr.json" ;; esac\n',
        )
        first = self.execute(script("pr-policy.yml", "pr-policy", 0))
        return (
            first
            if first.returncode
            else self.execute(script("pr-policy.yml", "pr-policy", 1))
        )

    def test_titles_and_dco(self) -> None:
        signed = "feat: x\n\nSigned-off-by: Human <human@example.invalid>"
        for title in (
            "feat: x",
            "Fix(scope)!: y",
            "chore(deps): z",
            "custom-type: x",
            "feat: $(touch injected)",
        ):
            result = self.check_policy(title, [signed])
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "injected").exists())
        for title, message in (
            ("update stuff", signed),
            ("feat: x", "unsigned"),
            ("feat: x", signed.replace("Human <", "Other <")),
        ):
            self.assertNotEqual(self.check_policy(title, [message]).returncode, 0)

    def test_breaking_changes(self) -> None:
        for message in (
            "feat!: x",
            "feat: x\n\nBREAKING CHANGE: x",
            "feat: x\n\nBREAKING-CHANGE: x",
        ):
            signed = message + "\n\nSigned-off-by: Human <human@example.invalid>"
            self.assertNotEqual(self.check_policy("feat: x", [signed]).returncode, 0)
            self.assertEqual(self.check_policy("feat!: x", [signed]).returncode, 0)

    def test_bot_exemption_requires_author_and_same_repository(self) -> None:
        bots = ["dependabot[bot]", "github-actions[bot]"]
        result = self.check_policy(
            "chore(deps): x", ["update", "migration"], trusted=True, authors=bots
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for trusted, authors, fork in (
            (False, bots, False),
            (True, bots, True),
            (True, ["dependabot[bot]", "human"], False),
        ):
            self.assertNotEqual(
                self.check_policy(
                    "chore(deps): x",
                    ["update", "unsigned"],
                    trusted=trusted,
                    authors=authors,
                    fork=fork,
                ).returncode,
                0,
            )

    def test_snapshot_and_pagination_must_match(self) -> None:
        signed = "feat: x\n\nSigned-off-by: Human <human@example.invalid>"
        self.assertNotEqual(
            self.check_policy("feat: x", [signed], stale=True).returncode, 0
        )
        for count in (0, 2, 251):
            self.assertNotEqual(
                self.check_policy("feat: x", [signed], count=count).returncode, 0
            )


class AutoMergeTest(ScriptTest):
    def test_transient_merge_state_retry_is_bounded_and_head_safe(self) -> None:
        live = mapping(
            load(ROOT / ".github/workflows/dependabot-auto-merge.yml")["jobs"]
        )
        live_steps = items(mapping(live["enable"])["steps"])
        code = script("dependabot-auto-merge.yml", "enable")
        self.assertEqual(mapping(live_steps[0])["run"], code)
        self.env.update(
            {"HEAD_SHA": "old", "PR_URL": "https://github.com/owner/repo/pull/2"}
        )
        self.executable(
            "sleep", '#!/bin/sh\nprintf "%s\\n" "$*" >> "$RUNNER_TEMP/sleeps"\n'
        )
        self.executable(
            "gh",
            """#!/bin/sh
case "$2" in
  merge)
    count=0
    if [ -f "$RUNNER_TEMP/count" ]; then count="$(cat "$RUNNER_TEMP/count")"; fi
    count=$((count + 1))
    echo "$count" > "$RUNNER_TEMP/count"
    printf '%s\\n' "$*" >> "$RUNNER_TEMP/calls"
    if [ "$count" -le "$MERGE_FAILURES" ]; then echo "$MERGE_ERROR" >&2; exit 1; fi
    exit 0 ;;
  view) echo "$CURRENT_SHA"; exit "$LOOKUP_EXIT" ;;
esac
""",
        )
        unstable = "GraphQL: Pull request Pull request is in unstable status (enablePullRequestAutoMerge)"
        for failures, error, current, lookup_exit, expected, attempts in (
            (0, unstable, "old", 1, 0, 1),
            (2, unstable, "old", 0, 0, 3),
            (5, unstable, "old", 0, 1, 5),
            (2, unstable, "new", 0, 0, 1),
            (2, unstable, "", 0, 1, 1),
            (2, unstable, "old", 1, 1, 1),
            (
                2,
                "GraphQL: Resource not accessible by personal access token",
                "old",
                0,
                1,
                1,
            ),
        ):
            with self.subTest(
                failures=failures, error=error, current=current, lookup=lookup_exit
            ):
                for filename in ("count", "calls", "sleeps"):
                    (self.root / filename).unlink(missing_ok=True)
                self.env.update(
                    {
                        "MERGE_FAILURES": str(failures),
                        "MERGE_ERROR": error,
                        "CURRENT_SHA": current,
                        "LOOKUP_EXIT": str(lookup_exit),
                    }
                )
                result = self.execute(code)
                self.assertEqual(result.returncode, expected, result.stderr)
                calls = (self.root / "calls").read_text().splitlines()
                self.assertEqual(len(calls), attempts)
                self.assertTrue(
                    all("--match-head-commit old" in call for call in calls)
                )
                sleeps = self.root / "sleeps"
                self.assertEqual(
                    sleeps.read_text().splitlines() if sleeps.exists() else [],
                    ["5"] * (attempts - 1),
                )

    def test_failed_enable_is_ignored_only_if_the_head_moved(self) -> None:
        self.env.update(
            {
                "HEAD_SHA": "old",
                "PR_URL": "https://github.com/owner/repo/pull/2",
            }
        )
        for merge_exit, lookup_exit, current, expected in (
            (0, 0, "old", 0),
            (1, 0, "new", 0),
            (1, 0, "old", 1),
            (1, 1, "", 1),
            (1, 0, "", 1),
        ):
            self.executable(
                "gh",
                f'#!/bin/sh\ncase "$2" in merge) exit {merge_exit} ;; view) echo "{current}"; exit {lookup_exit} ;; esac\n',
            )
            for template in ("dependabot-auto-merge.yml", "biome-migrate.yml"):
                result = self.execute(script(template, "enable"))
                self.assertEqual(result.returncode, expected, result.stderr)


class PagesAndBiomeDetectionTest(ScriptTest):
    def test_pages_tip_check(self) -> None:
        self.env["GITHUB_SHA"] = "current"
        for tip, status, expected in (
            ("current", 0, "true"),
            ("newer", 0, "false"),
            ("", 1, ""),
        ):
            self.executable("gh", f'#!/bin/sh\nprintf "%s\\n" "{tip}"\nexit {status}\n')
            for name in ("ci-bun-pages.yml", "ci-content-pages.yml"):
                output = self.root / "output"
                output.unlink(missing_ok=True)
                result = self.execute(script(name, "deploy"))
                self.assertEqual(result.returncode, status)
                if status == 0:
                    self.assertEqual(output.read_text().strip(), "current=" + expected)
                else:
                    self.assertFalse(output.exists())

    def test_only_biome_manifest_changes_trigger_migration(self) -> None:
        self.executable("gh", '#!/bin/sh\ncat "$RUNNER_TEMP/changes.json"\n')
        for filename, patch, expected in (
            ("package.json", '+  "@biomejs/biome": "3.0.0"', True),
            ("frontend/package.json", '+"@biomejs/biome":"3.0.0"', True),
            ("package.json", '+  "other": "3.0.0"', False),
            ("bun.lock", '+  "@biomejs/biome": "3.0.0"', False),
            ("package.json", '   "@biomejs/biome": "3.0.0"', False),
        ):
            output = self.root / "output"
            output.unlink(missing_ok=True)
            _ = (self.root / "changes.json").write_text(
                json.dumps([[{"filename": filename, "patch": patch}]])
            )
            result = self.execute(script("biome-migrate.yml", "migrate"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.exists(), expected)


class BiomePatchTest(ScriptTest):
    source: Path = Path()
    origin: Path = Path()
    head: str = ""

    def git(self, *args: str, cwd: Path | None = None) -> str:
        return subprocess.check_output(
            [GIT, *args], cwd=cwd or self.source, text=True, stderr=subprocess.PIPE
        ).strip()

    @override
    def setUp(self) -> None:
        super().setUp()
        self.source = self.root / "source"
        self.origin = self.root / "origin.git"
        self.source.mkdir()
        (self.root / "artifact").mkdir()
        _ = self.git("init", "-q")
        _ = self.git("config", "user.name", "Fixture")
        _ = self.git("config", "user.email", "fixture@example.invalid")
        _ = (self.source / "biome.json").write_text('{"version": 1}\n')
        _ = (self.source / "other.txt").write_text("protected\n")
        _ = self.git("add", ".")
        _ = self.git(
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qs",
            "-m",
            "test: initial fixture",
        )
        self.head = self.git("rev-parse", "HEAD")
        _ = self.git("init", "-q", "--bare", str(self.origin))
        _ = self.git("push", str(self.origin), "HEAD:refs/heads/dependabot/biome")
        self.env.update(
            {
                "HEAD_SHA": self.head,
                "HEAD_REF": "dependabot/biome",
                "CURRENT_SHA": self.head,
                "PUSH_TOKEN": "fixture",
                "GITHUB_RUN_ID": "123",
                "FIXTURE_ORIGIN": str(self.origin),
                "REAL_GIT": GIT,
                "GIT_LOG": str(self.root / "git.log"),
                "RACE_SHA": "",
            }
        )
        self.executable(
            "gh",
            """#!/bin/sh
case "$1" in
  api) printf '%s\n' "$CURRENT_SHA" ;;
  run) for destination; do :; done; cp -R "$RUNNER_TEMP/artifact/." "$destination/" ;;
  *) exit 1 ;;
esac
""",
        )
        self.executable(
            "git",
            """#!/usr/bin/env python3
import json, os, subprocess, sys
args = sys.argv[1:]
with open(os.environ["GIT_LOG"], "a") as stream:
    stream.write(json.dumps(args) + "\\n")
if "remote" in args and "add" in args:
    args[-1] = os.environ["FIXTURE_ORIGIN"]
if "push" in args and os.environ["RACE_SHA"]:
    subprocess.run([os.environ["REAL_GIT"], "--git-dir=" + os.environ["FIXTURE_ORIGIN"],
        "update-ref", "refs/heads/dependabot/biome", os.environ["RACE_SHA"]], check=True)
raise SystemExit(subprocess.call([os.environ["REAL_GIT"], *args]))
""",
        )

    def patch(self) -> None:
        _ = self.git("add", "--all")
        patch = subprocess.check_output(
            [GIT, "diff", "--cached", "--binary"], cwd=self.source
        )
        _ = (self.root / "artifact/biome.patch").write_bytes(patch)

    def apply(self) -> subprocess.CompletedProcess[str]:
        return self.execute(script("biome-migrate.yml", "apply"))

    def published(self) -> str:
        return self.git(
            "--git-dir=" + str(self.origin), "rev-parse", "refs/heads/dependabot/biome"
        )

    def test_valid_patch_commits_one_parent_without_checkout_or_saved_credentials(
        self,
    ) -> None:
        _ = (self.source / "biome.json").write_text('{"version": 2}\n')
        self.patch()
        result = self.apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        published = self.published()
        self.assertNotEqual(published, self.head)
        self.assertEqual(
            self.git("--git-dir=" + str(self.origin), "rev-parse", published + "^"),
            self.head,
        )
        self.assertEqual(
            self.git(
                "--git-dir=" + str(self.origin), "show", published + ":biome.json"
            ),
            '{"version": 2}',
        )
        self.assertIn("sha=" + published, (self.root / "output").read_text())
        for line in (self.root / "git.log").read_text().splitlines():
            args = cast(list[str], json.loads(line))
            self.assertEqual(args[:2], ["-c", "core.hooksPath=/dev/null"])
            self.assertNotIn("checkout", args)
            self.assertNotIn("config", args)

    def test_stale_head_skips_without_pushing(self) -> None:
        _ = (self.source / "biome.json").write_text('{"version": 2}\n')
        self.patch()
        self.env["CURRENT_SHA"] = "0" * 40
        result = self.apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.published(), self.head)
        self.assertFalse((self.root / "output").exists())

    def test_forbidden_paths_and_file_operations_are_rejected(self) -> None:
        for operation in ("other", "create", "delete", "rename", "mode", "symlink"):
            with self.subTest(operation=operation):
                _ = self.git("reset", "--hard", self.head)
                _ = self.git("clean", "-fd")
                config = self.source / "biome.json"
                if operation == "other":
                    _ = (self.source / "other.txt").write_text("changed\n")
                elif operation == "create":
                    _ = (self.source / "biome.jsonc").write_text("{}\n")
                elif operation == "delete":
                    config.unlink()
                elif operation == "rename":
                    _ = config.rename(self.source / "biome.jsonc")
                elif operation == "mode":
                    config.chmod(0o755)
                else:
                    config.unlink()
                    config.symlink_to("other.txt")
                self.patch()
                self.assertNotEqual(self.apply().returncode, 0)
                self.assertEqual(self.published(), self.head)

    def test_extra_or_symlink_artifact_is_rejected(self) -> None:
        _ = (self.source / "biome.json").write_text('{"version": 2}\n')
        self.patch()
        extra = self.root / "artifact/extra"
        _ = extra.write_text("unexpected")
        self.assertNotEqual(self.apply().returncode, 0)
        extra.unlink()
        patch = self.root / "artifact/biome.patch"
        _ = patch.rename(self.root / "outside.patch")
        patch.symlink_to(self.root / "outside.patch")
        self.assertNotEqual(self.apply().returncode, 0)
        self.assertEqual(self.published(), self.head)

    def test_concurrent_head_change_fails_the_lease(self) -> None:
        _ = self.git(
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--allow-empty",
            "-qs",
            "-m",
            "test: concurrent fixture",
        )
        newer = self.git("rev-parse", "HEAD")
        _ = self.git("push", str(self.origin), "HEAD:refs/heads/other")
        _ = (self.source / "biome.json").write_text('{"version": 2}\n')
        self.patch()
        self.env["RACE_SHA"] = newer
        result = self.apply()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stale info", result.stderr)
        self.assertEqual(self.published(), newer)


if __name__ == "__main__":
    _ = unittest.main()
