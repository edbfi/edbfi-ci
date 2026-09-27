# SPDX-License-Identifier: AGPL-3.0-only
"""Reject actions, containers and services in privileged workflow jobs."""

import re
import sys
from pathlib import Path
from typing import cast

import yaml

type Value = str | list[Value] | dict[str, Value]

EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)
TOKEN = re.compile(r"'(?:[^']|'')*'|[a-zA-Z_][\w-]*|!=|&&|\|\||[^\s]")
PR_EVENTS = {"pull_request", "pull_request_target", "issue_comment", "merge_group"}


def mapping(value: Value | None) -> dict[str, Value]:
    return value if isinstance(value, dict) else {}


def has_secret(value: Value) -> bool:
    if isinstance(value, dict):
        return any(has_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(has_secret(item) for item in value)
    for expression in EXPRESSION.finditer(value):
        tokens = [
            match.group().lower() for match in TOKEN.finditer(expression.group(1))
        ]
        for index, token in enumerate(tokens):
            if token != "secrets":
                continue
            tail = tokens[index + 1 :]
            if tail[:2] == [".", "github_token"]:
                continue
            if tail[:3] == ["[", "'github_token'", "]"]:
                continue
            return True
    return False


def excluded_events(condition: Value | None) -> set[str]:
    """Recognise only literal event exclusions in a pure, top-level AND chain."""
    if not isinstance(condition, str):
        return set()
    condition = condition.strip()
    if condition.startswith("${{") and condition.endswith("}}"):
        condition = condition[3:-2]
    tokens = [match.group().lower() for match in TOKEN.finditer(condition)]
    if "||" in tokens:
        return set()
    depth = 0
    parts: list[list[str]] = [[]]
    for token in tokens:
        if token in {"(", "["}:
            depth += 1
        elif token in {")", "]"}:
            depth -= 1
        if depth < 0:
            return set()
        if token == "&&" and depth == 0:
            parts.append([])
        else:
            parts[-1].append(token)
    if depth or any(not part for part in parts):
        return set()
    return {
        part[4][1:-1]
        for part in parts
        if len(part) == 5
        and part[:4] == ["github", ".", "event_name", "!="]
        and part[4].startswith("'")
    }


def grants_write(value: Value | None) -> bool:
    return value == "write-all" or (
        isinstance(value, dict) and "write" in value.values()
    )


def check(workflow: dict[str, Value]) -> list[str]:
    trigger = workflow.get("on", [])
    events = [trigger] if isinstance(trigger, str) else list(trigger)
    pr_events = {
        event
        for event in events
        if isinstance(event, str)
        and (event in PR_EVENTS or event.startswith("pull_request_review"))
    }
    shared_secret = has_secret(workflow.get("env", {}))
    findings: list[str] = []
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return ["expected a jobs mapping"]
    for job_id, value in jobs.items():
        if not isinstance(value, dict):
            findings.append(f"{job_id}: expected a job mapping")
            continue
        reachable = bool(pr_events - excluded_events(value.get("if")))
        secret = shared_secret or has_secret(value) or value.get("secrets") == "inherit"
        write = grants_write(value.get("permissions", workflow.get("permissions")))
        if not (secret or (reachable and write)):
            continue
        reason = (
            "non-GITHUB_TOKEN secret" if secret else "PR-reachable write permission"
        )
        for key in ("uses", "container", "services"):
            if key in value:
                findings.append(f"{job_id}: {key} forbidden with {reason}")
        steps = value.get("steps", [])
        if isinstance(steps, list):
            for index, step in enumerate(steps, 1):
                if "uses" in mapping(step):
                    findings.append(
                        f"{job_id}: step {index} uses forbidden with {reason}"
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    findings: list[str] = []
    for filename in sys.argv[1:] if argv is None else argv:
        try:
            # BaseLoader keeps GitHub's `on` key a string (YAML 1.1 calls it bool).
            workflow = cast(
                Value, yaml.load(Path(filename).read_text(), Loader=yaml.BaseLoader)
            )
            if not isinstance(workflow, dict):
                raise TypeError("expected a workflow mapping")
            findings.extend(f"{filename}: {item}" for item in check(workflow))
        except (OSError, TypeError, ValueError, yaml.YAMLError) as error:
            findings.append(f"{filename}: {error}")
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
