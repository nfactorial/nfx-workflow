#!/usr/bin/env python3
# Spec: spec-lint. Behaviour changes go through it.
"""Lint specs and their indexes against the spec rules in ../template.md.

Usage: spec_lint.py <path> [<path> ...]
       spec_lint.py --status <path> [<path> ...] [--json]
       spec_lint.py --status <path> --milestone <name> [--json]
       spec_lint.py --status <path> --milestone <name> --refusals
       spec_lint.py --status <path> --waiting <spec or 'spec › change'> [...]

Each path is a spec file, an index (README.md in a spec folder) or a folder, whose every .md is
linted. Prints one line per finding, `ERROR|WARN <rule-id> <file>:<line> <message>`, then a
summary line. Exits 1 when any ERROR was found, else 0. Python 3 standard library only.

An ERROR is a rule the document breaks. A WARN is a likely problem the script can't confirm:
read it and decide.

With --status, every argument is handed to status mode (speclint/status.py, spec: status-mode),
which lints nothing and whose exit code is this script's.
"""

from __future__ import annotations

import sys
from pathlib import Path

from speclint.lint import Linter
from speclint.status import main as status_mode


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not argv:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    if "--status" in argv:
        return status_mode(argv)
    for option in ("--json", "--milestone"):
        if option in argv:
            print(f"spec_lint: {option} needs --status", file=sys.stderr)
            return 2
    paths = [Path(a.replace("\\", "/")) for a in argv]
    return Linter(paths, Path.cwd().resolve()).run()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
