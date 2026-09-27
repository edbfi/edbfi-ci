# SPDX-License-Identifier: AGPL-3.0-only
import tempfile
import unittest
from pathlib import Path
from typing import override

from .check_basedpyright_config import check

CONFIG = """[tool.basedpyright]
pythonVersion = "3.14"
typeCheckingMode = "recommended"
include = ["hooks", "tools"]
"""


class BasedpyrightConfigTest(unittest.TestCase):
    root: Path = Path()

    @override
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (self.root / "hooks").mkdir()
        (self.root / "tools").mkdir()
        self.write("pyproject.toml", CONFIG)

    def write(self, name: str, text: str) -> None:
        _ = (self.root / name).write_text(text)

    def test_valid_config(self) -> None:
        self.assertEqual(check(self.root), [])

    def test_global_overrides_fail_even_if_they_enable_diagnostics(self) -> None:
        for setting in (
            "failOnWarnings = true",
            "reportAny = false",
            'exclude = ["tools"]',
            'baselineFile = "baseline.json"',
            "executionEnvironments = []",
            'extends = "other.toml"',
        ):
            with self.subTest(setting=setting):
                self.write("pyproject.toml", CONFIG + setting)
                self.assertTrue(
                    any("forbidden key" in item for item in check(self.root))
                )

    def test_required_values_and_paths(self) -> None:
        for old, new in (
            ('"3.14"', '"3.13"'),
            ('"recommended"', '"basic"'),
            ('["hooks", "tools"]', '["hooks"]'),
            ('["hooks", "tools"]', '["hooks", "tools", "../outside"]'),
            ('["hooks", "tools"]', '["hooks", "tools", 42]'),
        ):
            with self.subTest(new=new):
                self.write("pyproject.toml", CONFIG.replace(old, new))
                self.assertTrue(check(self.root))

    def test_missing_and_malformed_config(self) -> None:
        for text in ("", "[broken", "[tool]\nbasedpyright = false"):
            self.write("pyproject.toml", text)
            self.assertTrue(check(self.root))
        (self.root / "pyproject.toml").unlink()
        self.assertTrue(check(self.root))

    def test_alternate_config_and_baseline_fail(self) -> None:
        self.write("pyrightconfig.json", "{}")
        (self.root / ".basedpyright").mkdir()
        self.assertEqual(len(check(self.root)), 2)

    def test_only_justified_inline_rule_suppressions_pass(self) -> None:
        for text in (
            "# pyright: basic\nx = 1\n",
            "# basedpyright: reportAny=false\n",
            "x = 1  # pyright: reportAny=false\n",
            "# pyright: ignore[reportAny] -- untyped library\n",
            "x = 1  # pyright: ignore\n",
            "x = 1  # pyright: ignore[reportAny]\n",
        ):
            with self.subTest(text=text):
                self.write("hooks/example.py", text)
                self.assertTrue(check(self.root))
        self.write(
            "hooks/example.py",
            "x = f()  # pyright: ignore[reportAny] -- untyped library\n",
        )
        self.assertEqual(check(self.root), [])

    def test_pragma_text_in_strings_is_not_a_suppression(self) -> None:
        self.write("hooks/example.py", 'text = """\n# pyright: basic\n"""\n')
        self.assertEqual(check(self.root), [])

    def test_extra_include_directory_is_scanned(self) -> None:
        (self.root / "extra").mkdir()
        self.write("pyproject.toml", CONFIG.replace('"tools"]', '"tools", "extra"]'))
        self.write("extra/example.py", "# pyright: basic\n")
        self.assertTrue(check(self.root))


if __name__ == "__main__":
    _ = unittest.main()
