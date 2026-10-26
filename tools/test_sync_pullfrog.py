# SPDX-License-Identifier: AGPL-3.0-only
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import override

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates/pullfrog.yml").read_text()
SCRIPT = ROOT / "tools/sync_pullfrog.py"
OLD = "pullfrog/pullfrog@" + "1" * 40 + " # v0.1.9"
MAJOR = int(TEMPLATE.split("pullfrog/pullfrog@")[1].split(" # v")[1].split(".")[0])
NEW = "pullfrog/pullfrog@" + "2" * 40 + f" # v{MAJOR + 1}.0.0"


def pinned(text: str, pin: str) -> str:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if "uses: pullfrog/pullfrog@" in line:
            lines[index] = line[: line.index("pullfrog/")] + pin + "\n"
    return "".join(lines)


class SyncPullfrogTest(unittest.TestCase):
    checkout: Path = Path()

    @override
    def setUp(self) -> None:
        self.checkout = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.checkout / ".git").mkdir()

    @property
    def workflow(self) -> Path:
        return self.checkout / ".github/workflows/pullfrog.yml"

    def write(self, text: str) -> None:
        self.workflow.parent.mkdir(parents=True, exist_ok=True)
        _ = self.workflow.write_text(text)

    def sync(self, *flags: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *flags, str(self.checkout)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_template_pin_is_parsed(self) -> None:
        self.assertNotEqual(pinned(TEMPLATE, OLD), TEMPLATE)

    def test_missing_copy_is_drift_and_sync_creates_it(self) -> None:
        check = self.sync("--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn("differs:", check.stdout)
        self.assertEqual(self.sync().returncode, 0)
        self.assertEqual(self.workflow.read_text(), TEMPLATE)
        check = self.sync("--check")
        self.assertEqual((check.returncode, check.stdout[:8]), (0, "current:"))

    def test_older_pin_is_reported_not_drift_and_sync_refreshes_it(self) -> None:
        self.write(pinned(TEMPLATE, OLD))
        check = self.sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout)
        self.assertIn("pins differ:", check.stdout)
        self.assertIn("pullfrog/pullfrog v0.1.9 (template v", check.stdout)
        self.assertEqual(self.workflow.read_text(), pinned(TEMPLATE, OLD))
        self.assertIn("copied:", self.sync().stdout)
        self.assertEqual(self.workflow.read_text(), TEMPLATE)

    def test_newer_pin_is_kept(self) -> None:
        self.write(pinned(TEMPLATE, NEW))
        self.assertEqual(self.sync("--check").returncode, 0)
        result = self.sync()
        self.assertIn("pins differ:", result.stdout)
        self.assertEqual(self.workflow.read_text(), pinned(TEMPLATE, NEW))

    def test_check_reports_whatever_sync_would_rewrite(self) -> None:
        sha = TEMPLATE.split("pullfrog/pullfrog@")[1][:40]
        self.write(pinned(TEMPLATE, f"pullfrog/pullfrog@{sha} # v0.0.1"))
        self.assertIn("pins differ:", self.sync("--check").stdout)
        self.assertIn("copied:", self.sync().stdout)
        self.assertEqual(self.workflow.read_text(), TEMPLATE)

    def test_structural_drift_fails_and_sync_keeps_a_newer_pin(self) -> None:
        self.write(pinned(TEMPLATE, NEW).replace("timeout: 1h", "timeout: 2h"))
        check = self.sync("--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn("differs:", check.stdout)
        self.assertIn("copied:", self.sync().stdout)
        self.assertEqual(self.workflow.read_text(), pinned(TEMPLATE, NEW))

    def test_unpinned_or_renamed_action_is_drift(self) -> None:
        for pin in ("pullfrog/pullfrog@v0", "other/pullfrog@" + "2" * 40 + " # v9.0.0"):
            with self.subTest(pin=pin):
                self.write(pinned(TEMPLATE, pin))
                self.assertEqual(self.sync("--check").returncode, 1)
                _ = self.sync()
                self.assertEqual(self.workflow.read_text(), TEMPLATE)


if __name__ == "__main__":
    _ = unittest.main()
