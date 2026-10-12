# SPDX-License-Identifier: AGPL-3.0-only
"""Copy the central Pullfrog workflow into local checkouts, or check for drift.

Action pins (`uses: owner/repo@<sha> # vX.Y.Z`) are not drift: Dependabot moves
them independently. A copy keeps any pin newer than the template's and takes
the template's otherwise.
"""

import argparse
import re
from pathlib import Path

PIN = re.compile(
    r"^(?P<head>\s*(?:-\s+)?uses:\s*(?P<action>[\w.-]+/[\w./-]+)@)"
    + r"(?P<sha>[0-9a-f]{40}) # (?P<version>v\d+(?:\.\d+)*)$",
    re.MULTILINE,
)


class Args(argparse.Namespace):
    checkouts: list[Path] = []
    check: bool = False


def structure(text: str) -> str:
    return PIN.sub(r"\g<head>PIN", text)


def version(match: re.Match[str]) -> tuple[int, ...]:
    return tuple(int(part) for part in match["version"][1:].split("."))


def merge(template: str, target: str) -> tuple[str, list[str]]:
    """Return the template with each newer target pin kept, and the pin differences."""
    pins = {match["action"]: match for match in PIN.finditer(target)}
    differences: list[str] = []

    def pick(match: re.Match[str]) -> str:
        other = pins.get(match["action"])
        if other is None or other.group("sha", "version") == match.group("sha", "version"):
            return match[0]
        differences.append(
            f"{match['action']} {other['version']} (template {match['version']})"
        )
        newer = other if version(other) > version(match) else match
        return f"{match['head']}{newer['sha']} # {newer['version']}"

    return PIN.sub(pick, template), differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("checkouts", nargs="+", type=Path)
    _ = parser.add_argument("--check", action="store_true")
    args = parser.parse_args(namespace=Args())
    source = Path(__file__).resolve().parents[1] / "templates/pullfrog.yml"
    template = source.read_text(encoding="utf-8")
    drift = False
    for checkout in args.checkouts:
        root = Path(checkout).resolve()
        if not (root / ".git").exists():
            parser.error(f"not a Git checkout: {root}")
        target = root / ".github/workflows/pullfrog.yml"
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
            parser.error(f"workflow path contains a symlink: {target}")
        current = target.read_text(encoding="utf-8") if target.is_file() else ""
        wanted, differences = merge(template, current)
        if structure(current) != structure(template):
            drift = True
            if args.check:
                print(f"differs: {target}")
                continue
        elif current == wanted or args.check:
            pins = f": {'; '.join(differences)}" if differences else ""
            print(f"{'pins differ' if differences else 'current'}: {target}{pins}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = target.write_text(wanted, encoding="utf-8", newline="")
        print(f"copied: {target}")
    return int(args.check and drift)


if __name__ == "__main__":
    raise SystemExit(main())
