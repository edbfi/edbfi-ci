# SPDX-License-Identifier: AGPL-3.0-only
"""Copy the central Pullfrog workflow into local checkouts, or check for drift."""

import argparse
from pathlib import Path


class Args(argparse.Namespace):
    checkouts: list[Path] = []
    check: bool = False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("checkouts", nargs="+", type=Path)
    _ = parser.add_argument("--check", action="store_true")
    args = parser.parse_args(namespace=Args())
    source = Path(__file__).resolve().parents[1] / "templates/pullfrog.yml"
    content = source.read_bytes()
    drift = False
    for checkout in args.checkouts:
        root = Path(checkout).resolve()
        if not (root / ".git").exists():
            parser.error(f"not a Git checkout: {root}")
        target = root / ".github/workflows/pullfrog.yml"
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
            parser.error(f"workflow path contains a symlink: {target}")
        if target.is_file() and target.read_bytes() == content:
            print(f"current: {target}")
            continue
        drift = True
        if args.check:
            print(f"differs: {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            _ = target.write_bytes(content)
            print(f"copied: {target}")
    return int(args.check and drift)


if __name__ == "__main__":
    raise SystemExit(main())
