# SPDX-License-Identifier: AGPL-3.0-only
"""bun_maintenance.py's edits, validators, trust binding and publish decisions."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import override
from unittest import mock

from tools import bun_maintenance as bm

SHA = "a" * 40
TABS = '{\n\t"name": "x",\n\t"packageManager": "bun@1.4.2",\n\t"scripts": { "test": "bun test" }\n}\n'
POYO = (
    '{\n  "name": "poyo",\n  "packageManager": "bun@1.4.2",\n'
    '  "engines": {\n    "bun": "1.4.2",\n    "node": "1.4.2"\n  }\n}\n'
)
LOCK = '{\n  "lockfileVersion": 1,\n  "packages": {\n    "undici": ["undici@8.10.2"]\n  }\n}\n'
PACKAGE = '{\n  "name": "x",\n  "dependencies": {\n    "undici": "8.10.2"\n  }\n}\n'


def entry(repo: str = "edbfi/x", base_sha: str = SHA) -> dict[str, object]:
    return {"repo": repo, "base_sha": base_sha, "status": "ok", "audit_patch": "", "fixed": [], "left": []}


def plan(*entries: dict[str, object], target: str = "1.4.4") -> str:
    return json.dumps({"target": target, "repos": list(entries)})


def pr(*, qualifies: bool = True, head: str = SHA, auto: bool = True, conflicting: bool = False) -> bm.PullRequest:
    return bm.PullRequest("https://github.com/edbfi/x/pull/1", head, qualifies, conflicting, auto)


class PinTest(unittest.TestCase):
    def test_only_regular_root_files_count(self) -> None:
        tree: list[object] = [
            {"path": "package.json", "type": "blob", "mode": "100644"},
            {"path": "web/package.json", "type": "blob", "mode": "100644"},
            {"path": ".bun-version", "type": "blob", "mode": "120000"},
            {"path": "bun.lock", "type": "blob", "mode": "100644"},
        ]
        self.assertEqual(bm.root_pins(tree), (frozenset({"package.json"}), True))
        self.assertEqual(bm.root_pins(tree[1:2]), (frozenset(), False))

    def test_tabs_are_preserved(self) -> None:
        self.assertEqual(bm.bump({"package.json": TABS}, "1.4.4"), {"package.json": TABS.replace("1.4.2", "1.4.4")})

    def test_poyo_bumps_all_three_pins(self) -> None:
        new = bm.bump({"package.json": POYO, ".bun-version": "1.4.2\n"}, "1.4.4")
        self.assertEqual(new[".bun-version"], "1.4.4\n")
        self.assertIn('"bun": "1.4.4"', new["package.json"])
        self.assertIn('"node": "1.4.2"', new["package.json"])
        self.assertIn('"packageManager": "bun@1.4.4"', new["package.json"])

    def test_engines_range_is_left_alone(self) -> None:
        text = POYO.replace('"bun": "1.4.2"', '"bun": ">=1.4.0"')
        self.assertIn('"bun": ">=1.4.0"', bm.bump({"package.json": text}, "1.4.4")["package.json"])

    def test_bun_version_only(self) -> None:
        self.assertEqual(bm.bump({".bun-version": "1.4.3\n"}, "1.4.4"), {".bun-version": "1.4.4\n"})
        self.assertEqual(bm.current_pin({".bun-version": "1.4.3\n"}), "1.4.3")

    def test_current_and_newer_pins_are_kept(self) -> None:
        self.assertEqual(bm.bump({"package.json": TABS, ".bun-version": "1.4.2\n"}, "1.4.2"), {})
        self.assertEqual(bm.bump({"package.json": TABS, ".bun-version": "1.5.0\n"}, "1.4.1"), {})

    def test_hashed_pin_is_refused(self) -> None:
        with self.assertRaises(bm.Error):
            _ = bm.bump({"package.json": TABS.replace("bun@1.4.2", "bun@1.4.2+sha512.abc")}, "1.4.4")


class AuditPackageJsonTest(unittest.TestCase):
    def test_dependency_version_change_passes(self) -> None:
        bm.check_audit_package_json(PACKAGE, PACKAGE.replace("8.10.2", "8.12.2"))

    def test_other_changes_fail(self) -> None:
        for new in (
            PACKAGE.replace('"name": "x"', '"name": "y"'),
            PACKAGE.replace('"undici": "8.10.2"', '"undici": "8.10.2",\n    "evil": "1.0.0"'),
            PACKAGE.replace("8.10.2", "github:evil/undici"),
            PACKAGE.replace('"8.10.2"', '["8.12.2"]'),
        ):
            with self.subTest(new=new), self.assertRaises(bm.Error):
                bm.check_audit_package_json(PACKAGE, new)


class GitTest(unittest.TestCase):
    work: Path = Path()
    base: str = ""

    @override
    def setUp(self) -> None:
        self.work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        _ = bm.git(self.work, "init", "--quiet")
        _ = self.commit({"bun.lock": LOCK, "package.json": PACKAGE, "run.sh": "echo\n"})
        self.base = bm.git(self.work, "rev-parse", "HEAD")

    def commit(self, files: dict[str, str]) -> str:
        for path, text in files.items():
            _ = (self.work / path).write_text(text)
        _ = bm.git(self.work, "add", "--all")
        env = bm.environment(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        _ = bm.git(self.work, "commit", "--quiet", "--message", "m", env=env)
        return bm.git(self.work, "rev-parse", "HEAD")

    def patch(self, edit: str) -> str:
        _ = subprocess.run(["sh", "-c", edit], cwd=self.work, env=bm.environment(), check=True)
        patch = bm.run(["git", "diff", "--binary"], cwd=self.work).stdout
        _ = bm.git(self.work, "checkout", "--quiet", "--", ".")
        return patch

    def test_lockfile_and_dependency_patch_passes(self) -> None:
        patch = self.patch("sed -i s/8.10.2/8.12.2/ bun.lock package.json")
        tree = bm.patched_tree(self.work, self.base, patch)
        self.assertEqual(set(bm.changes(self.work, self.base, tree)), {"bun.lock", "package.json"})

    def test_bad_patches_fail(self) -> None:
        for edit in (
            "echo evil > run.sh",
            "chmod +x bun.lock",
            "git mv bun.lock bun.lockb",
            "echo x > new.txt && git add new.txt",
            "sed -i s/x/y/ package.json",
        ):
            patch = self.patch(edit) if "git " not in edit else self.staged(edit)
            with self.subTest(edit=edit), self.assertRaises(bm.Error):
                _ = bm.patched_tree(self.work, self.base, patch)

    def staged(self, edit: str) -> str:
        _ = subprocess.run(["sh", "-c", edit], cwd=self.work, env=bm.environment(), check=True)
        patch = bm.run(["git", "diff", "--cached", "--binary"], cwd=self.work).stdout
        _ = bm.git(self.work, "reset", "--quiet", "--hard")
        return patch

    def test_extra_commit_changes_the_pr_diff(self) -> None:
        desired = bm.changes(self.work, self.base, bm.edited_tree(self.work, self.base, {"bun.lock": "new\n"}))
        head = self.commit({"bun.lock": "new\n"})
        self.assertEqual(bm.changes(self.work, self.base, head), desired)
        extra = self.commit({"run.sh": "evil\n"})
        self.assertNotEqual(bm.changes(self.work, self.base, extra), desired)

    def test_stale_plan_skips_the_repo(self) -> None:
        origin = Path(self.enterContext(tempfile.TemporaryDirectory())) / "edbfi"
        _ = bm.git(origin.parent, "clone", "--quiet", "--bare", str(self.work), str(origin / "x.git"))
        work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        branch = bm.git(self.work, "branch", "--show-current")
        repo = bm.Repo("edbfi/x", branch, self.base, (("package.json", PACKAGE),), True)
        stale = bm.Entry("edbfi/x", "b" * 40, "ok", "", (), ())
        with mock.patch.object(bm, "GITHUB", str(origin.parent)), mock.patch.object(bm, "open_prs") as prs:
            bm.apply_repo(repo, stale, "1.4.4", "token", work)
        prs.assert_not_called()


class TrustTest(unittest.TestCase):
    def test_matching_plan_binds(self) -> None:
        self.assertEqual(set(bm.bind(plan(entry()), "1.4.4", {"edbfi/x"})), {"edbfi/x"})

    def test_mismatches_fail(self) -> None:
        for text in (
            plan(entry(), target="1.4.3"),
            plan(entry("edbfi/other")),
            plan(entry(), entry()),
            plan(entry(base_sha="main")),
            plan({**entry(), "extra": 1}),
        ):
            with self.subTest(text=text), self.assertRaises(bm.Error):
                _ = bm.bind(text, "1.4.4", {"edbfi/x"})

    def test_artifact_holds_one_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            _ = (path / "plan.json").write_text("{}")
            self.assertEqual(bm.read_artifact(path), "{}")
            _ = (path / "other").write_text("")
            with self.assertRaises(bm.Error):
                _ = bm.read_artifact(path)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            _ = (path / "real.json").write_text("{}")
            (path / "plan.json").symlink_to(path / "real.json")
            (path / "real.json").unlink()
            with self.assertRaises(bm.Error):
                _ = bm.read_artifact(path)


class DecideTest(unittest.TestCase):
    def test_table(self) -> None:
        url = pr().url
        recreate = [("close", url), ("delete", SHA), ("create", "")]
        cases: dict[str, tuple[bool, str, list[bm.PullRequest], str | None, list[tuple[str, str]]]] = {
            "qualifying PR": (True, "ok", [pr()], SHA, [("keep", "")]),
            "qualifying PR without auto-merge": (True, "ok", [pr(auto=False)], SHA, [("arm", url)]),
            "extra commit or other change": (True, "ok", [pr(qualifies=False)], SHA, recreate),
            "conflicting PR": (True, "ok", [pr(conflicting=True)], SHA, recreate),
            "branch moved past the PR head": (True, "ok", [pr(head="b" * 40)], SHA, recreate),
            "orphan branch": (True, "ok", [], SHA, [("delete", SHA), ("create", "")]),
            "new change": (True, "ok", [], None, [("create", "")]),
            "no change, ok": (False, "ok", [pr()], SHA, [("close", url), ("delete", SHA)]),
            "no change, error": (False, "error", [pr()], SHA, [("keep", "")]),
        }
        for name, (desired, status, prs, branch, expected) in cases.items():
            with self.subTest(name):
                self.assertEqual(bm.decide(desired, status, prs, branch), expected)

    def test_failed_lease_skips_create(self) -> None:
        calls: list[str] = []
        done = bm.run_actions(
            [("close", "u"), ("delete", SHA), ("create", "")],
            close=lambda _: calls.append("close"),
            arm=lambda _: calls.append("arm"),
            delete=lambda _: False,
            create=lambda: calls.append("create"),
        )
        self.assertEqual((done, calls), (False, ["close"]))


if __name__ == "__main__":
    _ = unittest.main()
