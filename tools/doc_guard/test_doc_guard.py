# SPDX-License-Identifier: AGPL-3.0-only
"""Each documentation guard failing and passing."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import override

from . import doc_guard

FENCE = "```"
DESIGN_OK = (
    "# M\n\n## Contract\n\n## Parameters\n\n## Verification\n\n## Open\n\n## Why\n"
)
NO_EXEMPTIONS: frozenset[tuple[str, str]] = frozenset()


def block(lines: int, first: str = "x", info: str = "yaml") -> str:
    return "\n".join([FENCE + info, first, *(["x"] * (lines - 1)), FENCE]) + "\n"


class GuardTest(unittest.TestCase):
    root: Path = Path()

    @override
    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(text, encoding="utf-8")

    def messages(
        self, exemptions: frozenset[tuple[str, str]] = NO_EXEMPTIONS
    ) -> list[str]:
        return [str(f) for f in doc_guard.check(self.root, exemptions)]

    def test_line_cap(self) -> None:
        self.write("CLAUDE.md", "@AGENTS.md\n")
        self.write("README.md", "x\n" * 80)
        self.write("design/a.md", DESIGN_OK + "x\n" * (150 - DESIGN_OK.count("\n")))
        self.assertEqual(self.messages(), [])
        self.write("CLAUDE.md", "@AGENTS.md\nmore\n")
        self.write("README.md", "x\n" * 81)
        self.write("design/a.md", DESIGN_OK + "x\n" * 150)
        self.assertEqual(
            self.messages(),
            [
                "CLAUDE.md:2: 2 lines exceed the cap of 1",
                "README.md:81: 81 lines exceed the cap of 80",
                "design/a.md:151: 161 lines exceed the cap of 150",
            ],
        )

    def test_relative_links(self) -> None:
        self.write("design/b.md", DESIGN_OK)
        self.write(
            "README.md",
            "[b](design/b.md#why) [web](https://example.com) [top](#x) `[no](nope.md)`\n",
        )
        self.assertEqual(self.messages(), [])
        self.write("README.md", "[gone](design/gone.md) [out](../outside.md)\n")
        self.assertEqual(
            self.messages(),
            [
                "README.md:1: broken link: design/gone.md",
                "README.md:1: link leaves the repo: ../outside.md",
            ],
        )

    def test_links_inside_code_blocks_are_ignored(self) -> None:
        self.write("notes.md", FENCE + "\n[gone](gone.md)\n" + FENCE + "\n")
        self.assertEqual(self.messages(), [])

    def test_code_block_length(self) -> None:
        self.write("notes.md", block(12))
        self.assertEqual(self.messages(), [])
        self.write("notes.md", block(13))
        self.assertEqual(
            self.messages(), ["notes.md:1: code block has 13 lines (max 12)"]
        )

    def test_mermaid_blocks_are_uncapped(self) -> None:
        self.write("notes.md", block(40, "flowchart LR", "mermaid"))
        self.write("other.md", block(40, "graph TD", "Mermaid title"))
        self.assertEqual(self.messages(), [])
        self.write("other.md", block(13, "flowchart LR", "mermaidx"))
        self.write("third.md", block(13, "mermaid"))
        self.assertEqual(
            self.messages(),
            [
                "other.md:1: code block has 13 lines (max 12)",
                "third.md:1: code block has 13 lines (max 12)",
            ],
        )

    def test_mermaid_fence_variants(self) -> None:
        body = "\n".join(["flowchart LR", *(["x"] * 19)])
        self.write("tilde.md", f"~~~mermaid\n{body}\n~~~\n")
        self.write("indent.md", f"   ```Mermaid {{init}}\n{body}\n   ```\n")
        self.write("long.md", f"````mermaid\n{body}\n```\n````\n")
        self.assertEqual(self.messages(), [])
        self.write("short.md", f"````mermaid\n{body}\n```\n")
        self.assertEqual(self.messages(), ["short.md:1: unclosed fenced code block"])

    def test_mermaid_blocks_keep_other_checks(self) -> None:
        self.write("notes.md", block(20, "flowchart LR", "mermaid") + FENCE + "mermaid\n")
        self.assertEqual(self.messages(), ["notes.md:23: unclosed fenced code block"])
        self.write("notes.md", block(20, "%% TODO", "mermaid"))
        self.assertEqual(self.messages(), ["notes.md:2: work marker TODO"])

    def test_freshness_line(self) -> None:
        self.write("STATE.md", "Last updated: 1791384000 (2026-10-07T14:40:00Z)\n# State\n")
        self.assertEqual(self.messages(), [])
        expected = "first line must be 'Last updated: <unix seconds> (<YYYY-MM-DDTHH:MM:SSZ>)'"
        for text in (
            "# State\n",
            "",
            "Last updated: 1791384000\n",
            "Last updated: 1791384000 (2026-10-07 14:40:00Z)\n",
            "last updated: 1791384000 (2026-10-07T14:40:00Z)\n",
        ):
            self.write("STATE.md", text)
            self.assertEqual(self.messages(), [f"STATE.md:1: {expected}"], text)
        self.write("STATE.md", "Last updated: 1791384001 (2026-10-07T14:40:00Z)\n")
        self.assertEqual(
            self.messages(),
            ["STATE.md:1: 1791384001 is not 2026-10-07T14:40:00Z in unix seconds"],
        )
        self.write("STATE.md", "Last updated: 1791384000 (2026-02-30T14:40:00Z)\n")
        self.assertEqual(
            self.messages(), ["STATE.md:1: invalid timestamp: 2026-02-30T14:40:00Z"]
        )
        self.write("STATE.md", "Last updated: 1791384000 (2026-10-07T24:40:00Z)\n")
        self.assertEqual(
            self.messages(), ["STATE.md:1: invalid timestamp: 2026-10-07T24:40:00Z"]
        )
        self.write(
            "STATE.md", "# State\nLast updated: 1791384000 (2026-10-07T14:40:00Z)\n"
        )
        self.assertEqual(self.messages(), [f"STATE.md:1: {expected}"])
        self.write("design/STATE.md", "no freshness line here\n" + DESIGN_OK)
        self.write("STATE.md", "Last updated: 1791384000 (2026-10-07T14:40:00Z)\n")
        self.assertEqual(self.messages(), [])

    def test_code_block_exemption(self) -> None:
        exempt = frozenset({("notes.md", "name: CI")})
        self.write("notes.md", block(40, "name: CI"))
        self.assertEqual(self.messages(exempt), [])
        self.write("notes.md", "moved to templates/\n")
        self.assertEqual(
            self.messages(exempt),
            ["notes.md:1: stale code block exemption: 'name: CI'"],
        )

    def test_unclosed_block(self) -> None:
        self.write("notes.md", "text\n" + FENCE + "\nx\n")
        self.assertEqual(self.messages(), ["notes.md:2: unclosed fenced code block"])

    def test_work_markers(self) -> None:
        self.write(
            "notes.md", "No `TODO`, `TBD` or `FIXME` markers; TODOS is a word.\n"
        )
        self.assertEqual(self.messages(), [])
        self.write(
            "notes.md", "TODO: x\nmaybe TBD\n" + FENCE + "\n# FIXME\n" + FENCE + "\n"
        )
        self.assertEqual(
            self.messages(),
            [
                "notes.md:1: work marker TODO",
                "notes.md:2: work marker TBD",
                "notes.md:4: work marker FIXME",
            ],
        )

    def test_design_sections(self) -> None:
        self.write(
            "design/c.md",
            DESIGN_OK.replace(
                "## Why", FENCE + "\n## Not a heading\n" + FENCE + "\n## Why"
            ),
        )
        self.assertEqual(self.messages(), [])
        self.write(
            "design/c.md",
            DESIGN_OK.replace("## Open\n\n", "").replace(
                "## Why", "## Why\n\n### Detail"
            ),
        )
        self.assertEqual(
            self.messages(),
            [
                "design/c.md:3: sections are ['Contract', 'Parameters', 'Verification', 'Why'], "
                + "expected ['Contract', 'Parameters', 'Verification', 'Open', 'Why']"
            ],
        )
        self.write("design/c.md", DESIGN_OK + "\n## Extra\n")
        self.assertEqual(len(self.messages()), 1)

    def test_dot_directories_are_skipped(self) -> None:
        self.write(".github/notes.md", "TODO\n")
        self.assertEqual(self.messages(), [])

    def test_main_exit_code(self) -> None:
        argv = ["--root", str(self.root)]
        self.write("notes.md", "fine\n")
        self.assertEqual(doc_guard.main(argv, NO_EXEMPTIONS), 0)
        self.write("notes.md", "TODO\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(doc_guard.main(argv, NO_EXEMPTIONS), 1)
        self.assertEqual(out.getvalue(), "notes.md:1: work marker TODO\n")


if __name__ == "__main__":
    _ = unittest.main()
