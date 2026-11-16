# Spec: auto-loop. Behaviour changes go through it.
"""What the auto driver and the run lock share: its error, the git commands it runs, the run
branch and report names, the local time and the one-line printer. Python 3 standard library
only."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class DriverError(Exception):
    """Why the driver can't go on: a refusal to start before the first session, a stop after."""


# --- Git ---------------------------------------------------------------------------------------

def is_run_branch(name: str) -> bool:
    """`L-auto-branch`: an `auto/…` branch whose name holds no `--`."""
    return name.startswith("auto/") and "--" not in name


def is_side_branch(name: str) -> bool:
    """An `auto/…--…` branch, kept for set-aside work."""
    return name.startswith("auto/") and "--" in name


@dataclass(frozen=True)
class Branches:
    """One read of the local branches: each one's commit, in git's order, and the one checked
    out (None: a detached HEAD)."""

    heads: dict[str, str]
    checked_out: str | None


class Git:
    """Git commands run in one folder; a failure raises DriverError."""

    def __init__(self, cwd: Path):
        self.cwd = cwd

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(["git", *args], cwd=self.cwd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        except OSError as error:
            raise DriverError(f"git could not be run: {error}") from error

    def out(self, *args: str) -> str:
        result = self._run(*args)
        if result.returncode != 0:
            lines = result.stderr.strip().splitlines() or [f"exit {result.returncode}"]
            raise DriverError(f"git {' '.join(args)} failed: {lines[-1]}")
        return result.stdout.strip()

    def ok(self, *args: str) -> bool:
        return self._run(*args).returncode == 0

    def current_branch(self) -> str | None:
        """The branch checked out, or None when HEAD is detached."""
        result = self._run("symbolic-ref", "-q", "HEAD")
        ref = result.stdout.strip()
        return ref[len("refs/heads/"):] if result.returncode == 0 and ref.startswith(
            "refs/heads/") else None

    def _read_refs(self) -> Branches:
        """One `git for-each-ref`; `checked_out` is the branch it marks, else None."""
        heads: dict[str, str] = {}
        checked_out = None
        for line in self.out("for-each-ref", "--format=%(objectname) %(refname) %(HEAD)",
                             "refs/heads/").splitlines():
            commit, ref, *marker = line.split(" ")
            if ref.startswith("refs/heads/"):
                name = ref[len("refs/heads/"):]
                heads[name] = commit
                if marker == ["*"]:
                    checked_out = name
        return Branches(heads, checked_out)

    def read_branches(self) -> Branches:
        """The branches, their commits and the branch checked out. No branch marked: one more
        read tells a detached HEAD from a branch with no commits yet, taken as checked out."""
        read = self._read_refs()
        if read.checked_out is None:
            return Branches(read.heads, self.current_branch())
        return read

    def branches(self) -> list[str]:
        return list(self._read_refs().heads)

    def has_branch(self, name: str) -> bool:
        return self.ok("show-ref", "--verify", "--quiet", f"refs/heads/{name}")

    def head_trailers(self) -> list[tuple[str, str]]:
        """HEAD's `Spec:` and `Spec-Change:` lines, as (key, value) pairs in order, from its whole
        message: they sit above an attribution paragraph, which git's trailer parsing alone would
        read."""
        message = self.out("show", "-s", "--format=%B", "HEAD")
        return [(match.group(1), match.group(2).strip())
                for match in SPEC_TRAILER.finditer(message)]

    def staged_changes(self) -> bool:
        """The index differs from HEAD."""
        result = self._run("diff", "--cached", "--quiet", "HEAD")
        if result.returncode not in (0, 1):
            lines = result.stderr.strip().splitlines() or [f"exit {result.returncode}"]
            raise DriverError(f"git diff --cached --quiet HEAD failed: {lines[-1]}")
        return result.returncode == 1


# `L-trailers`: a commit's `Spec:` and `Spec-Change:` lines.
SPEC_TRAILER = re.compile(r"^(Spec|Spec-Change):[ \t]*(.+)$", re.M)

# `L-auto-report`: a session's section heading, `## Session <n>: <command>`; the recovery writes
# `interrupted` as the command of a session it found cut short.
SESSION_HEADING = re.compile(r"^## Session (\d+):[ \t]*(.*?)[ \t]*$", re.M)


def report_file(git_dir: Path, run_branch: str) -> Path:
    """`L-auto-report`: `<git dir>/nfx/auto-<date>.md`, its date from the run branch's name."""
    return git_dir / "nfx" / f"auto-{run_branch[len('auto/'):]}.md"


def local_time() -> str:
    """Now as local ISO time to the second, with its offset."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def say(text: str) -> None:
    print(text, flush=True)
