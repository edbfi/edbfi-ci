# SPDX-License-Identifier: AGPL-3.0-only
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import watch
from .test_templates import items, load, mapping, run

CONFIG = Path(__file__).resolve().parents[1] / "watch.yml"


class WatchTest(unittest.TestCase):
    def test_workflow_guards_and_dispatch_arguments(self) -> None:
        workflow = load(CONFIG.parent / ".github/workflows/watch.yml")
        events = mapping(workflow["on"])
        self.assertEqual(set(events), {"schedule", "workflow_dispatch"})
        inputs = mapping(mapping(events["workflow_dispatch"])["inputs"])
        self.assertEqual(mapping(inputs["dry-run"])["default"], "true")
        self.assertEqual(workflow["permissions"], {})
        self.assertEqual(
            mapping(workflow["concurrency"])["cancel-in-progress"], "false"
        )
        job = mapping(mapping(workflow["jobs"])["watch"])
        self.assertEqual(job["if"], "github.ref == 'refs/heads/main'")
        self.assertEqual(job["permissions"], {"contents": "read", "issues": "write"})
        step = mapping(items(job["steps"])[-1])
        code = str(step["run"])
        self.assertNotIn("${{", code)
        with tempfile.TemporaryDirectory() as directory:
            uv = Path(directory) / "uv"
            _ = uv.write_text('#!/bin/bash\nprintf "%s\\n" "$@"\n')
            uv.chmod(0o755)
            for dry_run in ("true", "false"):
                manual = "$(exit 99); replex-green"
                result = run(
                    code,
                    {
                        "PATH": f"{directory}:/usr/bin:/bin",
                        "GITHUB_REPOSITORY": "edbfi/edbfi-ci",
                        "DRY_RUN": dry_run,
                        "MANUAL_TRIGGER": manual,
                    },
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                expected = [
                    "run",
                    "--no-sync",
                    "python",
                    "tools/watch.py",
                    "--repo",
                    "edbfi/edbfi-ci",
                ]
                if dry_run == "true":
                    expected.append("--dry-run")
                self.assertEqual(
                    result.stdout.splitlines(), expected + ["--manual", manual]
                )

    def test_repository_config_and_versions(self) -> None:
        self.assertEqual(len(watch.load(CONFIG)), 7)
        self.assertGreater(watch.version("v1.10.0"), watch.version("1.9.99"))
        self.assertEqual(watch.version("v2.5.14"), watch.version("2.5.14"))
        for value in ("latest", "1.2", "1.2.3-rc.1", "01.2.3", "1.2.3+meta"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _ = watch.version(value)

    def test_invalid_config_fails_before_network(self) -> None:
        original = CONFIG.read_text()
        for content in (
            "[]",
            "triggers: []",
            "triggers: [false]",
            original.replace("id: prek-toml", "id: bun-v2"),
            original.replace("kind: merged_pr", "kind: typo", 1),
            original.replace("number: 16071", "number: true"),
            original.replace("number: 16071", "number: -1"),
            original.replace("above: 2.5.14", "above: latest"),
            original.replace("kind: manual", "kind: manual\n    surprise: true"),
            original.replace("repo: rhysd/actionlint", "repo: ../bad/path"),
        ):
            with (
                self.subTest(content=content),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "watch.yml"
                _ = path.write_text(content)
                with (
                    patch.object(watch, "gh") as api,
                    self.assertRaises((TypeError, ValueError)),
                ):
                    watch.run(path, "edbfi/edbfi-ci", dry_run=True)
                api.assert_not_called()

    def test_merged_pr_requires_true_not_closed_or_missing(self) -> None:
        trigger = watch.Trigger("pr", "merged_pr", "action", "owner/repo", number=1)
        for merged in (True, False):
            with patch.object(watch, "gh", return_value={"merged": merged}):
                self.assertEqual(watch.check(trigger, "") is not None, merged)
        for data in ({"state": "closed"}, {"merged": "true"}, {"merged": None}):
            with (
                patch.object(watch, "gh", return_value=data),
                self.assertRaises(ValueError),
            ):
                _ = watch.check(trigger, "")

    def test_release_threshold_and_stability(self) -> None:
        trigger = watch.Trigger(
            "release", "github_release", "action", "owner/repo", "1.7.12"
        )
        for tag, fired in (
            ("v1.7.11", False),
            ("v1.7.12", False),
            ("v1.7.13", True),
            ("v1.10.0", True),
        ):
            data = {"tag_name": tag, "draft": False, "prerelease": False}
            with patch.object(watch, "gh", return_value=data):
                self.assertEqual(watch.check(trigger, "") is not None, fired)
        for data in (
            {"tag_name": "v1.8.0", "draft": True, "prerelease": False},
            {"tag_name": "v1.8.0-rc.1", "draft": False, "prerelease": True},
            {"tag_name": "v1.8.0"},
        ):
            with (
                patch.object(watch, "gh", return_value=data),
                self.assertRaises(ValueError),
            ):
                _ = watch.check(trigger, "")

    def test_npm_name_and_encoded_url(self) -> None:
        trigger = watch.Trigger(
            "npm", "npm_release", "action", "@biomejs/biome", "2.5.14"
        )
        for current, fired in (("2.5.13", False), ("2.5.14", False), ("2.5.15", True)):
            with patch.object(
                watch,
                "command_json",
                return_value={"name": trigger.source, "version": current},
            ) as command:
                self.assertEqual(watch.check(trigger, "") is not None, fired)
                command.assert_called_once_with(
                    [
                        "curl",
                        "--fail",
                        "--silent",
                        "--show-error",
                        "--max-time",
                        "60",
                        "https://registry.npmjs.org/%40biomejs%2Fbiome/latest",
                    ]
                )
        with (
            patch.object(
                watch,
                "command_json",
                return_value={"name": "wrong", "version": "3.0.0"},
            ),
            self.assertRaises(ValueError),
        ):
            _ = watch.check(trigger, "")

    def test_manual_requires_explicit_matching_id(self) -> None:
        trigger = watch.Trigger("manual", "manual", "action")
        with patch.object(watch, "gh") as api:
            self.assertIsNone(watch.check(trigger, ""))
            self.assertIsNone(watch.check(trigger, "other"))
            self.assertIsNotNone(watch.check(trigger, "manual"))
            api.assert_not_called()
        for manual in ("unknown", "bun-v2"):
            with self.assertRaises(ValueError):
                watch.run(CONFIG, "edbfi/edbfi-ci", dry_run=True, manual=manual)

    def test_dry_run_prints_issue_without_writing(self) -> None:
        output = io.StringIO()
        with (
            patch.object(watch, "check", return_value="Observed upstream change"),
            patch.object(watch, "gh", return_value=[[]]) as api,
            patch("tools.watch.subprocess.run") as write,
            contextlib.redirect_stdout(output),
        ):
            watch.run(CONFIG, "edbfi/edbfi-ci", dry_run=True)
        api.assert_called_once_with(
            "repos/edbfi/edbfi-ci/issues?state=all&per_page=100", paginate=True
        )
        write.assert_not_called()
        self.assertEqual(output.getvalue().count("Would create:"), 7)
        self.assertIn("<!-- edbfi-watch:bun-v2 -->", output.getvalue())

    def test_existing_open_or_closed_issue_on_later_page_prevents_duplicates(
        self,
    ) -> None:
        for state in ("open", "closed"):
            pages = [
                [{"body": "unrelated"}],
                [{"body": "<!-- edbfi-watch:bun-v2 -->\n", "state": state}],
            ]

            def check(trigger: watch.Trigger, _manual: str) -> str | None:
                return "merged" if trigger.id == "bun-v2" else None

            with (
                patch.object(watch, "check", side_effect=check),
                patch.object(watch, "gh", return_value=pages),
                patch("tools.watch.subprocess.run") as write,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                watch.run(CONFIG, "edbfi/edbfi-ci", dry_run=False)
                watch.run(CONFIG, "edbfi/edbfi-ci", dry_run=False)
            write.assert_not_called()

    def test_pull_request_marker_does_not_suppress_issue_and_body_is_stdin(
        self,
    ) -> None:
        def check(trigger: watch.Trigger, _manual: str) -> str | None:
            return "$(touch /tmp/never-run)" if trigger.id == "bun-v2" else None

        pages: list[list[dict[str, object]]] = [
            [{"body": "<!-- edbfi-watch:bun-v2 -->", "pull_request": {}}]
        ]
        with (
            patch.object(watch, "check", side_effect=check),
            patch.object(watch, "gh", return_value=pages),
            patch("tools.watch.subprocess.run") as write,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            watch.run(CONFIG, "edbfi/edbfi-ci", dry_run=False)
        trigger = watch.load(CONFIG)[0]
        write.assert_called_once_with(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                "edbfi/edbfi-ci",
                "--title",
                "chore: follow up on bun-v2",
                "--body-file",
                "-",
            ],
            input=f"<!-- edbfi-watch:bun-v2 -->\n\n$(touch /tmp/never-run)\n\n{trigger.action}\n\nRemove this entry from watch.yml in the PR that completes the action.\n",
            text=True,
            check=True,
            timeout=120,
        )

    def test_failed_late_lookup_or_issue_listing_never_writes(self) -> None:
        error = subprocess.CalledProcessError(1, ["gh", "api"])
        cases: list[tuple[list[str | Exception], object]] = [
            (["fired", "fired", error], [[]]),
            (["fired"] * 7, error),
            (["fired"] * 7, {"message": "bad response"}),
            (["fired"] * 7, [[{}]]),
            (["fired"] * 7, [[{"body": 42}]]),
        ]
        for results, pages in cases:
            with (
                patch.object(watch, "check", side_effect=results),
                patch.object(
                    watch,
                    "gh",
                    side_effect=pages if isinstance(pages, Exception) else None,
                    return_value=pages,
                ),
                patch("tools.watch.subprocess.run") as write,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                with self.assertRaises(
                    (TypeError, ValueError, subprocess.CalledProcessError)
                ):
                    watch.run(CONFIG, "edbfi/edbfi-ci", dry_run=False)
                write.assert_not_called()

    def test_cli_failure_exit_for_network_json_and_publish_errors(self) -> None:
        for error in (
            subprocess.CalledProcessError(1, ["gh"]),
            subprocess.TimeoutExpired(["gh"], 120),
            json.JSONDecodeError("bad JSON", "oops", 0),
            OSError("missing tool"),
        ):
            with (
                patch.object(watch, "run", side_effect=error),
                patch("tools.watch.sys.argv", ["watch.py", "--dry-run"]),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(watch.main(), 1)

    def test_api_pagination_and_subprocess_failure(self) -> None:
        with patch.object(watch, "command_json", return_value=[]) as command:
            self.assertEqual(watch.gh("repos/o/r/issues", paginate=True), [])
            command.assert_called_once_with(
                ["gh", "api", "repos/o/r/issues", "--paginate", "--slurp"]
            )
        with (
            patch(
                "tools.watch.subprocess.run",
                return_value=subprocess.CompletedProcess(["gh"], 0, stdout="not json"),
            ),
            self.assertRaises(ValueError),
        ):
            _ = watch.command_json(["gh"])
        with (
            patch(
                "tools.watch.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, ["gh"]),
            ),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            _ = watch.command_json(["gh"])


if __name__ == "__main__":
    _ = unittest.main()
