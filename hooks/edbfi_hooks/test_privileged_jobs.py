# SPDX-License-Identifier: AGPL-3.0-only
import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path
from typing import cast

import yaml

from .privileged_jobs import Value, check, main


def workflow(text: str) -> dict[str, Value]:
    return cast(dict[str, Value], yaml.load(text, Loader=yaml.BaseLoader))


class PrivilegedJobsTest(unittest.TestCase):
    def job(
        self,
        job: str,
        top: str = "on: pull_request\npermissions: {}\n",
    ) -> list[str]:
        return check(
            workflow(
                top
                + "jobs:\n  test:\n"
                + "\n".join("    " + line for line in job.splitlines())
            )
        )

    def test_reference_templates(self) -> None:
        root = Path(__file__).resolve().parents[2]
        # S2 moves these templates; read their canonical location in either form.
        templates = list((root / "templates").glob("*.yml"))
        texts = [path.read_text() for path in templates]
        for path in (root / "design").glob("*.md"):
            texts.extend(
                re.findall(r"```yaml\n(.*?)\n```", path.read_text(), re.DOTALL)
            )
        tested = 0
        for text in texts:
            value = workflow(text)
            if "jobs" in value:
                tested += 1
                self.assertEqual(check(value), [])
        self.assertGreaterEqual(tested, 2)

    def test_secret_action_in_any_event(self) -> None:
        for event in ("pull_request", "push", "workflow_dispatch", "[schedule]"):
            for secret in (
                "${{ secrets.STATS_READ_TOKEN }}",
                "${{ secrets['STATS_READ_TOKEN'] }}",
                "${{ secrets[inputs.name] }}",
                "${{ toJSON(secrets) }}",
                "${{ SECRETS.STATS_READ_TOKEN }}",
                "${{ format('}}{0}', secrets.PAT) }}",
            ):
                with self.subTest(event=event, secret=secret):
                    result = self.job(
                        f'env:\n  TOKEN: "{secret}"\nsteps:\n  - uses: actions/checkout@sha',
                        f"on: {event}\n",
                    )
                    self.assertEqual(len(result), 1)

    def test_metadata_next_to_pat(self) -> None:
        self.assertEqual(
            len(
                self.job(
                    "steps:\n  - uses: dependabot/fetch-metadata@sha\n"
                    + "  - run: gh pr merge\n    env:\n      GH_TOKEN: ${{ secrets.PAT }}"
                )
            ),
            1,
        )

    def test_workflow_env_secret(self) -> None:
        self.assertEqual(
            len(
                self.job(
                    "steps:\n  - uses: actions/checkout@sha",
                    "on: {schedule: [{cron: '1 2 * * *'}]}\nenv:\n  TOKEN: ${{ secrets.PAT }}\n",
                )
            ),
            1,
        )

    def test_github_token_and_literal_are_not_custom_secrets(self) -> None:
        for value in (
            "${{ secrets.GITHUB_TOKEN }}",
            "${{ secrets['GITHUB_TOKEN'] }}",
            "${{ github.token }}",
            "secrets.PAT",
            "${{ 'secrets.PAT' }}",
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    self.job(
                        f'env:\n  TOKEN: "{value}"\nsteps:\n  - uses: actions/checkout@sha'
                    ),
                    [],
                )

    def test_permissions_and_overrides(self) -> None:
        action = "steps:\n  - uses: actions/checkout@sha"
        for permissions in ("write-all", "{contents: write}", "{id-token: write}"):
            with self.subTest(permissions=permissions):
                top = f"on: [push, pull_request]\npermissions: {permissions}\n"
                self.assertEqual(len(self.job(action, top)), 1)
                self.assertEqual(self.job("permissions: {}\n" + action, top), [])
                self.assertEqual(
                    self.job("permissions: {contents: read}\n" + action, top), []
                )
                self.assertEqual(
                    len(self.job(f"permissions: {permissions}\n" + action)), 1
                )
        self.assertEqual(
            self.job("permissions: write-all\n" + action, "on: push\n"), []
        )

    def test_all_pr_event_forms(self) -> None:
        job = "permissions: write-all\nsteps:\n  - uses: actions/checkout@sha"
        for event in (
            "pull_request",
            "pull_request_target",
            "pull_request_review",
            "pull_request_review_comment",
            "issue_comment",
            "merge_group",
        ):
            for on in (event, f"[{event}, push]", f"{{{event}: {{types: [opened]}}}}"):
                with self.subTest(on=on):
                    self.assertEqual(len(self.job(job, f"on: {on}\n")), 1)

    def test_only_top_level_and_guard_excludes_prs(self) -> None:
        job = "permissions: {pages: write}\nsteps:\n  - uses: actions/deploy-pages@sha"
        safe = (
            "github.event_name != 'pull_request'",
            "always() && github.event_name != 'pull_request' && github.ref == 'refs/heads/main'",
            "${{ github.event_name != 'pull_request' && success() }}",
        )
        unsafe = (
            "github.event_name != 'pull_request' || success()",
            "(github.event_name != 'pull_request' && success()) || failure()",
            "contains('github.event_name != ''pull_request''', 'x')",
            "${{ !(github.event_name != 'pull_request') }}",
            "github.event_name != 'pull_request' == false",
            "success() && (github.event_name != 'pull_request' || failure())",
        )
        for condition in safe + unsafe:
            with self.subTest(condition=condition):
                self.assertEqual(
                    bool(self.job(f"if: {condition}\n{job}")), condition in unsafe
                )
        self.assertEqual(
            len(
                self.job(f"if: {safe[0]}\n{job}", "on: [pull_request, issue_comment]\n")
            ),
            1,
        )
        self.assertEqual(
            self.job(
                f"if: {safe[0]} && github.event_name != 'issue_comment'\n{job}",
                "on: [pull_request, issue_comment]\n",
            ),
            [],
        )

    def test_guard_cannot_exempt_custom_secret(self) -> None:
        self.assertEqual(
            len(
                self.job(
                    "if: github.event_name != 'pull_request'\n"
                    + "env: {TOKEN: '${{ secrets.PAT }}'}\nsteps:\n  - uses: actions/checkout@sha"
                )
            ),
            1,
        )

    def test_forbidden_job_features_and_shell_only_job(self) -> None:
        for feature in (
            "uses: owner/repo/.github/workflows/reusable.yml@sha",
            "container: ubuntu:latest",
            "services: {db: {image: postgres}}",
        ):
            self.assertEqual(len(self.job("permissions: write-all\n" + feature)), 1)
        self.assertEqual(
            self.job(
                "env: {TOKEN: '${{ secrets.PAT }}'}\nsteps:\n  - run: gh pr merge"
            ),
            [],
        )

    def test_reusable_workflow_inherits_secrets(self) -> None:
        self.assertEqual(
            len(
                self.job(
                    "uses: owner/repo/.github/workflows/reusable.yml@sha\nsecrets: inherit",
                    "on: push\n",
                )
            ),
            1,
        )

    def test_cli_diagnostics_and_invalid_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ci.yml"
            for text in ("[", "[]", "jobs: []", "jobs: {bad: text}"):
                _ = path.write_text(text)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main([str(path)]), 1)
                self.assertIn(str(path), output.getvalue())
            _ = path.write_text("on: push\njobs: {ok: {steps: [{run: echo ok}]}}")
            self.assertEqual(main([str(path)]), 0)


if __name__ == "__main__":
    _ = unittest.main()
