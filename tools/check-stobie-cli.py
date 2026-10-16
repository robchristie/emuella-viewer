#!/usr/bin/env python3
"""Check that every Stobie dependency names one revision and that the `stobie`
CLI (STOBIE, default `stobie`) was built from it, so its build-web loader and
packaging match the framework the viewer compiles against."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
STOBIE_GIT = "https://github.com/robchristie/stobie"


def pinned_revision(manifest: Path = ROOT / "Cargo.toml") -> str:
    dependencies = tomllib.loads(manifest.read_text())["workspace"]["dependencies"]
    stobie = {name: value for name, value in dependencies.items() if name.startswith("stobie-")}
    if not stobie:
        raise SystemExit("Cargo.toml names no Stobie dependency")
    revisions = set()
    for name, value in stobie.items():
        if not isinstance(value, dict) or value.get("git") != STOBIE_GIT:
            raise SystemExit(f"{name} must be a git dependency on {STOBIE_GIT}")
        revision = value.get("rev", "")
        if not re.fullmatch(r"[0-9a-f]{40}", revision) or {"branch", "tag"} & value.keys():
            raise SystemExit(f"{name} must pin a full 40-character rev, not a branch or tag")
        revisions.add(revision)
    if len(revisions) != 1:
        raise SystemExit(f"Stobie dependencies name several revisions: {sorted(revisions)}")
    return revisions.pop()


def cli_revision(stobie: str) -> str | None:
    output = subprocess.run([stobie, "--version"], capture_output=True, text=True, check=True).stdout
    match = re.search(r"\(commit ([0-9a-f]{40})\)", output)
    return match.group(1) if match else None


def main() -> int:
    revision = pinned_revision()
    stobie = os.environ.get("STOBIE", "stobie")
    install = f"cargo install --locked --force --git {STOBIE_GIT} --rev {revision} stobie-cli"
    try:
        built = cli_revision(stobie)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"the stobie CLI is required ({error}); run `{install}`", file=sys.stderr)
        return 1
    if built != revision:
        print(f"stobie was built from {built or 'an unknown revision'}, but Cargo.toml pins {revision}; run `{install}`", file=sys.stderr)
        return 1
    print(f"stobie and every Stobie dependency use {revision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
