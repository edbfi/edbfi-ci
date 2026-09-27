# SPDX-License-Identifier: AGPL-3.0-only
"""Lint templates at their deployment paths using prek's installed executables."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    tool, *filenames = sys.argv[1:]
    failed = False
    root = Path(__file__).resolve().parents[1]
    for filename in filenames:
        source = Path(filename).resolve()
        with tempfile.TemporaryDirectory(prefix="edbfi-template-") as directory:
            staging = Path(directory)
            github = staging / ".github"
            workflows = github / "workflows"
            workflows.mkdir(parents=True)
            dependabot = source.name.startswith("dependabot.")
            target = github / "dependabot.yml" if dependabot else workflows / "ci.yml"
            _ = shutil.copyfile(source, target)
            command = [tool]
            if tool == "actionlint":
                if source.name in {"ci-bun-pages.yml", "ci-content-pages.yml"}:
                    config = github / "actionlint.yaml"
                    _ = shutil.copyfile(
                        root / "templates/actionlint.pages.yaml", config
                    )
                    command += ["-config-file", str(config)]
                command.append(".github/workflows/ci.yml")
            elif tool == "zizmor":
                command += ["--offline", str(github)]
            else:
                raise ValueError(f"unsupported linter: {tool}")
            print(f"{tool}: {filename}", flush=True)
            result = subprocess.run(command, cwd=staging, check=False)
            failed |= result.returncode != 0
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
