# SPDX-License-Identifier: AGPL-3.0-only
"""Check upstream triggers; publish one issue per id unless --dry-run is set."""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import quote

import yaml


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("expected an object")
    items = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in items):
        raise ValueError("expected string keys")
    return cast(dict[str, object], items)


def sequence(value: object) -> list[object]:
    if not isinstance(value, list):
        raise TypeError("expected an array")
    return cast(list[object], value)


def string(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected a non-empty string")
    return value


def version(value: str) -> tuple[int, ...]:
    if not re.fullmatch(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value):
        raise ValueError(f"expected a stable three-part version: {value}")
    return tuple(int(part) for part in value.removeprefix("v").split("."))


def repository(value: object) -> str:
    name = string(value)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name):
        raise ValueError("expected owner/repository")
    return name


@dataclass(frozen=True)
class Trigger:
    id: str
    kind: str
    action: str
    source: str = ""
    above: str = ""
    number: int = 0


def load(path: Path) -> list[Trigger]:
    config = mapping(cast(object, yaml.safe_load(path.read_text())))
    if set(config) != {"triggers"}:
        raise ValueError("watch.yml must contain only triggers")
    triggers: list[Trigger] = []
    ids: set[str] = set()
    for value in sequence(config["triggers"]):
        item = mapping(value)
        name = string(item.get("id"))
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name) or name in ids:
            raise ValueError(f"invalid or duplicate trigger id: {name}")
        ids.add(name)
        kind = string(item.get("kind"))
        action = string(item.get("action"))
        fields = {"id", "kind", "action"}
        source, above, number = "", "", 0
        if kind == "merged_pr":
            fields |= {"repo", "number"}
            source = repository(item.get("repo"))
            raw_number = item.get("number")
            if type(raw_number) is not int or raw_number <= 0:
                raise ValueError("PR number must be a positive integer")
            number = raw_number
        elif kind in {"github_release", "npm_release"}:
            key = "repo" if kind == "github_release" else "package"
            fields |= {key, "above"}
            source = (
                repository(item.get(key)) if key == "repo" else string(item.get(key))
            )
            above = string(item.get("above"))
            _ = version(above)
        elif kind != "manual":
            raise ValueError(f"unknown trigger kind: {kind}")
        if set(item) != fields:
            raise ValueError(f"unexpected fields for {name}")
        triggers.append(Trigger(name, kind, action, source, above, number))
    if not triggers:
        raise ValueError("at least one trigger is required")
    return triggers


def command_json(args: list[str]) -> object:
    result = subprocess.run(
        args, check=True, capture_output=True, text=True, timeout=120
    )
    return cast(object, json.loads(result.stdout))


def gh(endpoint: str, *, paginate: bool = False) -> object:
    args = ["gh", "api", endpoint]
    if paginate:
        args += ["--paginate", "--slurp"]
    return command_json(args)


def check(trigger: Trigger, manual: str) -> str | None:
    if trigger.kind == "manual":
        return (
            "Manually confirmed by workflow dispatch or CLI."
            if manual == trigger.id
            else None
        )
    if trigger.kind == "merged_pr":
        data = mapping(gh(f"repos/{trigger.source}/pulls/{trigger.number}"))
        merged = data.get("merged")
        if not isinstance(merged, bool):
            raise ValueError(f"missing merged state for {trigger.id}")
        return (
            f"https://github.com/{trigger.source}/pull/{trigger.number} merged."
            if merged
            else None
        )
    if trigger.kind == "github_release":
        data = mapping(gh(f"repos/{trigger.source}/releases/latest"))
        if data.get("draft") is not False or data.get("prerelease") is not False:
            raise ValueError(f"expected a published stable release for {trigger.id}")
        latest = string(data.get("tag_name"))
        source = (
            f"https://github.com/{trigger.source}/releases/tag/{quote(latest, safe='')}"
        )
    else:
        data = mapping(
            command_json(
                [
                    "curl",
                    "--fail",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    "60",
                    f"https://registry.npmjs.org/{quote(trigger.source, safe='')}/latest",
                ]
            )
        )
        if data.get("name") != trigger.source:
            raise ValueError(f"unexpected npm package for {trigger.id}")
        latest = string(data.get("version"))
        source = f"https://www.npmjs.com/package/{trigger.source}/v/{latest}"
    return (
        f"{source} is newer than {trigger.above}."
        if version(latest) > version(trigger.above)
        else None
    )


def run(path: Path, repo: str, *, dry_run: bool, manual: str = "") -> None:
    repo = repository(repo)
    triggers = load(path)
    if manual and not any(t.id == manual and t.kind == "manual" for t in triggers):
        raise ValueError(f"unknown manual trigger: {manual}")
    # Complete all lookups before writing: a partial API failure must not look green.
    fired: list[tuple[Trigger, str]] = []
    for trigger in triggers:
        evidence = check(trigger, manual)
        print(f"{trigger.id}: {'triggered' if evidence else 'waiting'}", flush=True)
        if evidence:
            fired.append((trigger, evidence))
    pages = sequence(gh(f"repos/{repo}/issues?state=all&per_page=100", paginate=True))
    bodies: list[str] = []
    for page in pages:
        for value in sequence(page):
            issue = mapping(value)
            if "pull_request" not in issue:
                if "body" not in issue:
                    raise ValueError("missing issue body")
                body = issue.get("body")
                if body is not None and not isinstance(body, str):
                    raise ValueError("expected an issue body string or null")
                bodies.append(body or "")
    for trigger, evidence in fired:
        marker = f"<!-- edbfi-watch:{trigger.id} -->"
        if any(marker in body.splitlines() for body in bodies):
            print(f"{trigger.id}: issue already exists (open or closed)")
            continue
        body = f"{marker}\n\n{evidence}\n\n{trigger.action}\n\nRemove this entry from watch.yml in the PR that completes the action.\n"
        title = f"chore: follow up on {trigger.id}"
        if dry_run:
            print(f"Would create: {title}\n{body}")
        else:
            _ = subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--repo",
                    repo,
                    "--title",
                    title,
                    "--body-file",
                    "-",
                ],
                input=body,
                text=True,
                check=True,
                timeout=120,
            )


class Arguments(argparse.Namespace):
    config: Path = Path("watch.yml")
    repo: str = "edbfi/edbfi-ci"
    dry_run: bool = False
    manual: str = ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--config", type=Path, default=Path("watch.yml"))
    _ = parser.add_argument("--repo", default="edbfi/edbfi-ci")
    _ = parser.add_argument("--dry-run", action="store_true")
    _ = parser.add_argument(
        "--manual", default="", help="Confirm one manual trigger id"
    )
    args = parser.parse_args(namespace=Arguments())
    try:
        run(args.config, args.repo, dry_run=args.dry_run, manual=args.manual)
    except (
        OSError,
        TypeError,
        ValueError,
        yaml.YAMLError,
        subprocess.SubprocessError,
    ) as error:
        print(f"watch failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
