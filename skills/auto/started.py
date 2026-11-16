# Spec: auto-loop. Behaviour changes go through it.
"""Says whether an auto run is going before a start, and whether a just-started driver has taken
the run lock. `python started.py check`, run from inside the repo: exit 0 with no output when no
live run holds the lock, else exit 1 naming the driver's process. `python started.py wait`: waits
up to WAIT_SECONDS for the lock to name a live process, printing `running` and exiting 0, else
printing `not running` and exiting 1. Python 3 standard library only."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runlock  # noqa: E402  (beside this file: the lock reading must agree with the driver's)
from common import DriverError, Git  # noqa: E402  (beside this file)

WAIT_SECONDS = 30
POLL_SECONDS = 1


def live_driver(lock: Path, strict: bool = False) -> int | None:
    """The process ID the lock at `lock` names when it is a live process; else None. A lock that
    is absent names no one; one that can't be read (a driver mid-write) names no one too, unless
    `strict`, which raises DriverError."""
    try:
        state = runlock.read_lock(lock)
    except DriverError:
        if strict:
            raise
        return None
    return state.pid if state is not None and runlock.process_is_live(state.pid) else None


def lock_path(cwd: Path) -> Path:
    try:
        common = Git(cwd).out("rev-parse", "--git-common-dir")
    except DriverError as error:
        raise DriverError(f"{cwd} is not in a git repo ({error})") from error
    return runlock.lock_file((cwd / common).resolve())


def wait_for_lock(lock: Path) -> bool:
    """Waits up to WAIT_SECONDS, looking every POLL_SECONDS, for a live driver in the lock."""
    deadline = time.monotonic() + WAIT_SECONDS
    while True:
        if live_driver(lock) is not None:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(POLL_SECONDS)


def main(argv: list[str], cwd: Path | None = None) -> int:
    try:
        if len(argv) != 1 or argv[0] not in ("check", "wait"):
            raise DriverError(f"started takes `check` or `wait`, not {' '.join(argv) or 'nothing'}")
        lock = lock_path((cwd or Path.cwd()).resolve())
        if argv[0] == "wait":
            started = wait_for_lock(lock)
            print("running" if started else "not running", flush=True)
            return 0 if started else 1
        # `check` reads strictly: a lock that can't be read is the driver's refusal to make
        pid = live_driver(lock, strict=True)
    except DriverError as error:
        print(f"nfx:auto: {error}", file=sys.stderr, flush=True)
        return 1
    if pid is not None:
        print(f"nfx:auto: a run is going (pid {pid}); /nfx:auto status shows it", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
