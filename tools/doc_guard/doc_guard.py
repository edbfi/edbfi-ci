#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Documentation guards for edbfi-ci (AGENTS.md rule 7).

Checks every ``*.md`` file outside dot-directories under the repo root:
line caps, relative links, fenced-block length (Mermaid diagrams exempt),
no work markers, the fixed section list of ``design/*.md``, and the
freshness line that starts ``STATE.md``.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import override

LINE_CAPS: dict[str, int] = {
    "README.md": 80,
    "AGENTS.md": 80,
    "CLAUDE.md": 1,
    "MAINTENANCE.md": 40,
    "STATE.md": 150,
    "DECISIONS.md": 40,
}
DESIGN_CAP = 150
DESIGN_SECTIONS = ("Contract", "Parameters", "Verification", "Open", "Why")
MAX_BLOCK_LINES = 12
UNCAPPED_BLOCK_LANGUAGES = frozenset({"mermaid"})

LONG_BLOCK_EXEMPTIONS: frozenset[tuple[str, str]] = frozenset()

MARKER = re.compile(r"\b(TODO|TBD|FIXME)\b")
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+\1")
LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FRESHNESS = re.compile(
    r"^Last updated: (\d+) \((\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\)$"
)
FRESHNESS_FORMAT = "Last updated: <unix seconds> (<YYYY-MM-DDTHH:MM:SSZ>)"


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class Block:
    start: int
    first_line: str
    length: int
    language: str = ""


@dataclass(frozen=True)
class Parsed:
    prose: list[tuple[int, str]]
    blocks: list[Block]
    unclosed: int | None


def parse(lines: list[str]) -> Parsed:
    """Split lines into prose (1-based numbers) and fenced blocks."""
    prose: list[tuple[int, str]] = []
    blocks: list[Block] = []
    fence = ""
    language = ""
    start = 0
    body: list[str] = []
    for number, line in enumerate(lines, 1):
        match = FENCE.match(line)
        if not fence:
            if match:
                fence, start, body = match.group(1), number, []
                info = line[match.end() :].split()
                language = info[0].lower() if info else ""
            else:
                prose.append((number, line))
        elif (
            match
            and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= len(fence)
        ):
            if line.strip() == match.group(1):
                first = body[0].strip() if body else ""
                blocks.append(Block(start, first, len(body), language))
                fence = ""
            else:
                body.append(line)
        else:
            body.append(line)
    return Parsed(prose, blocks, start if fence else None)


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def line_cap(rel: str) -> int | None:
    if rel in LINE_CAPS:
        return LINE_CAPS[rel]
    if rel.startswith("design/") and rel.count("/") == 1:
        return DESIGN_CAP
    return None


def check_file(
    root: Path,
    path: Path,
    exemptions: frozenset[tuple[str, str]],
    used: set[tuple[str, str]],
) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").splitlines()
    parsed = parse(lines)
    findings: list[Finding] = []

    cap = line_cap(rel)
    if cap is not None and len(lines) > cap:
        findings.append(
            Finding(rel, cap + 1, f"{len(lines)} lines exceed the cap of {cap}")
        )

    if parsed.unclosed is not None:
        findings.append(Finding(rel, parsed.unclosed, "unclosed fenced code block"))

    for block in parsed.blocks:
        key = (rel, block.first_line)
        if key in exemptions:
            used.add(key)
        elif (
            block.length > MAX_BLOCK_LINES
            and block.language not in UNCAPPED_BLOCK_LANGUAGES
        ):
            findings.append(
                Finding(
                    rel,
                    block.start,
                    f"code block has {block.length} lines (max {MAX_BLOCK_LINES})",
                )
            )

    for number, line in parsed.prose:
        text = INLINE_CODE.sub("", line)
        if marker := MARKER.search(text):
            findings.append(Finding(rel, number, f"work marker {marker.group(1)}"))
        for link in LINK.finditer(text):
            findings.extend(check_link(root, path, rel, number, link.group(1)))
    for block in parsed.blocks:
        for offset, line in enumerate(
            lines[block.start : block.start + block.length], 1
        ):
            if marker := MARKER.search(line):
                findings.append(
                    Finding(rel, block.start + offset, f"work marker {marker.group(1)}")
                )

    if rel.startswith("design/") and rel.count("/") == 1:
        findings.extend(check_sections(rel, parsed))
    if rel == "STATE.md":
        findings.extend(check_freshness(rel, lines))
    return findings


def check_freshness(rel: str, lines: list[str]) -> list[Finding]:
    """The first line is ``Last updated: <unix> (<ISO UTC>)``, both the same time."""
    match = FRESHNESS.match(lines[0]) if lines else None
    if not match:
        return [Finding(rel, 1, f"first line must be '{FRESHNESS_FORMAT}'")]
    try:
        stamp = datetime.strptime(match.group(2), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return [Finding(rel, 1, f"invalid timestamp: {match.group(2)}")]
    if int(stamp.replace(tzinfo=UTC).timestamp()) != int(match.group(1)):
        return [
            Finding(rel, 1, f"{match.group(1)} is not {match.group(2)} in unix seconds")
        ]
    return []


def check_link(
    root: Path, path: Path, rel: str, number: int, target: str
) -> list[Finding]:
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith(
        "#"
    ):
        return []
    file_part = target.split("#", 1)[0]
    resolved = (
        (root / file_part.lstrip("/"))
        if file_part.startswith("/")
        else (path.parent / file_part)
    )
    resolved = resolved.resolve()
    if not resolved.is_relative_to(root.resolve()):
        return [Finding(rel, number, f"link leaves the repo: {target}")]
    if not resolved.exists():
        return [Finding(rel, number, f"broken link: {target}")]
    return []


def check_sections(rel: str, parsed: Parsed) -> list[Finding]:
    found: list[tuple[int, str]] = []
    for number, line in parsed.prose:
        match = HEADING.match(line)
        if match and len(match.group(1)) == 2:
            found.append((number, match.group(2)))
    names = tuple(name for _, name in found)
    if names == DESIGN_SECTIONS:
        return []
    line = found[0][0] if found else 1
    return [
        Finding(
            rel, line, f"sections are {list(names)}, expected {list(DESIGN_SECTIONS)}"
        )
    ]


def check(
    root: Path, exemptions: frozenset[tuple[str, str]] = LONG_BLOCK_EXEMPTIONS
) -> list[Finding]:
    root = root.resolve()
    used: set[tuple[str, str]] = set()
    findings: list[Finding] = []
    for path in markdown_files(root):
        findings.extend(check_file(root, path, exemptions, used))
    for rel, first in sorted(exemptions - used):
        findings.append(Finding(rel, 1, f"stale code block exemption: {first!r}"))
    return sorted(findings)


class Args(argparse.Namespace):
    root: Path = Path()


def main(
    argv: list[str] | None = None,
    exemptions: frozenset[tuple[str, str]] = LONG_BLOCK_EXEMPTIONS,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--root", type=Path, default=Path.cwd(), help="repo root")
    args = parser.parse_args(argv, namespace=Args())
    findings = check(args.root, exemptions)
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
