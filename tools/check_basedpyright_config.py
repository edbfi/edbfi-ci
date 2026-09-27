# SPDX-License-Identifier: AGPL-3.0-only
"""Keep the repository's typing gate strict; fix code instead of weakening it."""

import io
import re
import sys
import tokenize
import tomllib
from pathlib import Path
from typing import cast

ALLOWED_KEYS = {"pythonVersion", "typeCheckingMode", "include"}
REQUIRED_ROOTS = {"hooks", "tools"}
PRAGMA = re.compile(r"#\s*(?:based)?pyright:\s*(.*)")
INLINE_IGNORE = re.compile(r"ignore\[report\w+(?:\s*,\s*report\w+)*\]\s*(.+)")


def check_source(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            pragma = PRAGMA.fullmatch(token.string)
            if pragma is None:
                continue
            inline = bool(token.line[: token.start[1]].strip())
            ignore = INLINE_IGNORE.fullmatch(pragma.group(1))
            justified = ignore is not None and bool(ignore.group(1).strip(" #-"))
            if not (inline and justified):
                problems.append(
                    f"{path}:{token.start[0]}: only justified inline "
                    + "pyright: ignore[ruleName] is allowed"
                )
    except (OSError, SyntaxError, tokenize.TokenError) as error:
        problems.append(f"{path}: {error}")
    return problems


def check(root: Path) -> list[str]:
    try:
        data = cast(
            dict[str, object], tomllib.loads((root / "pyproject.toml").read_text())
        )
    except (OSError, ValueError) as error:
        return [f"pyproject.toml: {error}"]
    tool = data.get("tool")
    raw = (
        cast(dict[str, object], tool).get("basedpyright")
        if isinstance(tool, dict)
        else None
    )
    table = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
    problems = [
        f"[tool.basedpyright]: forbidden key {key}"
        for key in sorted(table.keys() - ALLOWED_KEYS)
    ]
    for key, expected in (
        ("pythonVersion", "3.14"),
        ("typeCheckingMode", "recommended"),
    ):
        if table.get(key) != expected:
            problems.append(f"[tool.basedpyright]: {key} must be {expected!r}")
    include = table.get("include")
    roots: set[str] = set()
    if isinstance(include, list):
        for item in cast(list[object], include):
            if (
                isinstance(item, str)
                and (root / item).resolve().is_relative_to(root.resolve())
                and (root / item).is_dir()
            ):
                roots.add(item)
            else:
                problems.append(
                    "[tool.basedpyright]: include entries must be repository directories"
                )
    for missing in sorted(REQUIRED_ROOTS - roots):
        problems.append(f"[tool.basedpyright]: include must cover {missing!r}")
    for name in ("pyrightconfig.json", ".basedpyright"):
        if (root / name).exists():
            problems.append(f"{name}: alternate configs and baselines are forbidden")
    paths = {
        path for name in roots | REQUIRED_ROOTS for path in (root / name).rglob("*.py")
    }
    for path in sorted(paths):
        problems.extend(check_source(path))
    return problems


def main() -> int:
    problems = check(Path(__file__).resolve().parents[1])
    for problem in problems:
        print(problem, file=sys.stderr)
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
