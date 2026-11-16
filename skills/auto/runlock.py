# Spec: auto-run-lock. Behaviour changes go through it.
"""The auto run lock: the file `<git dir>/nfx/auto-running`, whether a process ID is live, and
the recovery of a dead run (its uncommitted work set aside, the run's report told, the checkout
returned to the run branch's last commit). Python 3 standard library only."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from common import (SESSION_HEADING, DriverError, Git, is_run_branch, local_time, report_file,
                    say)


# --- The run lock ------------------------------------------------------------------------------

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259
MAX_PID = 2**31 - 1  # beyond it no platform has a process; `os.kill` and `ctypes` would overflow
SHARING_RETRIES = 5  # a reader holding the lock open makes Windows refuse a rename or delete
SHARING_PAUSE = 0.05  # seconds between tries


def lock_file(git_dir: Path) -> Path:
    """The run lock: `<git dir>/nfx/auto-running`."""
    return git_dir / "nfx" / "auto-running"


def retrying(action: Callable[[], object]) -> None:
    """Runs `action`, trying again a few times when the OS refuses it with a PermissionError
    (on Windows, another process has the file open)."""
    for attempt in range(SHARING_RETRIES):
        try:
            action()
            return
        except PermissionError:
            if attempt == SHARING_RETRIES - 1:
                raise
            time.sleep(SHARING_PAUSE)


def process_is_live(pid: object) -> bool:
    """A process ID names a live process. On Windows through `ctypes` alone (`os.kill` there ends
    the process); elsewhere `os.kill(pid, 0)`. An ID reused by an unrelated process reads as
    live."""
    if isinstance(pid, bool) or not isinstance(pid, int) or not 0 < pid <= MAX_PID:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            return (bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(code)))
                    and code.value == STILL_ACTIVE)
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@dataclass(frozen=True)
class SessionInLock:
    """The session in progress, as the lock names it."""

    number: int
    command: str
    pid: int
    started: str
    log: str | None = None  # the session log's absolute path; None: the lock names no log


@dataclass(frozen=True)
class RecoveryInLock:
    """A recovery under way, as the lock names it: the interrupted section's number (None when
    there is none) and the patch holding the set-aside work (None when there is none)."""

    n: int | None
    patch: str | None


@dataclass(frozen=True)
class RunInLock:
    """The run so far, as the lock names it: the driver's start, the sessions that have ended,
    those that made progress, those that set work aside, and the last 7-day reading in percent
    (None before any)."""

    started: str
    sessions: int = 0
    progress: int = 0
    set_asides: int = 0
    reading: float | None = None


@dataclass(frozen=True)
class LockState:
    """The run lock's content: the driver's process, the base, the run branch, the session in
    progress, the recovery under way and the run so far."""

    pid: int
    base: str
    run_branch: str | None
    session: SessionInLock | None
    recovery: RecoveryInLock | None = None
    run: RunInLock | None = None

    def to_json(self) -> dict:
        data: dict = {"pid": self.pid, "base": self.base, "run_branch": self.run_branch,
                      "session": None if self.session is None else {
                          "number": self.session.number, "command": self.session.command,
                          "pid": self.session.pid, "started": self.session.started}}
        if self.session is not None and self.session.log is not None:
            data["session"]["log"] = self.session.log
        if self.recovery is not None:
            data["recovery"] = {"n": self.recovery.n, "patch": self.recovery.patch}
        if self.run is not None:
            data["run"] = {"started": self.run.started, "sessions": self.run.sessions,
                           "progress": self.run.progress, "set_asides": self.run.set_asides,
                           "reading": self.run.reading}
        return data


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_text_or_none(value: object) -> bool:
    return value is None or isinstance(value, str)


def parse_lock(data: object) -> LockState | None:
    """The lock a parsed JSON value holds; None when it is not a valid lock: an object with
    `pid` an integer, `base` a string, `run_branch` a string or null, `session` null or an
    object with all four of its fields and `log` absent or an absolute path, and `recovery`
    null, absent or an object with `n` an integer (or null: a recovery with no report section)
    and `patch` a string or null, `run`
    absent or an object with `started` a string, `sessions`, `progress` and `set_asides`
    integers and `reading` a number or null, every field present."""
    if not isinstance(data, dict) or not {"pid", "base", "run_branch", "session"} <= data.keys():
        return None
    pid, base, run_branch = data.get("pid"), data.get("base"), data.get("run_branch")
    if not (is_int(pid) and isinstance(base, str) and is_text_or_none(run_branch)):
        return None
    session: SessionInLock | None = None
    raw = data.get("session")
    if raw is not None:
        if not isinstance(raw, dict):
            return None
        number, command, session_pid, started = (raw.get(key) for key in
                                                 ("number", "command", "pid", "started"))
        log = raw.get("log")
        if not (is_int(number) and isinstance(command, str) and is_int(session_pid)
                and isinstance(started, str)
                and ("log" not in raw
                     or (isinstance(log, str) and Path(log).is_absolute()))):
            return None
        session = SessionInLock(number, command, session_pid, started, log)
    recovery: RecoveryInLock | None = None
    raw = data.get("recovery")
    if raw is not None:
        if not isinstance(raw, dict) or not {"n", "patch"} <= raw.keys():
            return None
        n, patch = raw["n"], raw["patch"]
        if not ((n is None or is_int(n)) and is_text_or_none(patch)):
            return None
        recovery = RecoveryInLock(n, patch)
    run: RunInLock | None = None
    if "run" in data:
        raw = data["run"]
        if not isinstance(raw, dict) or not (
                {"started", "sessions", "progress", "set_asides", "reading"} <= raw.keys()):
            return None
        started, reading = raw["started"], raw["reading"]
        counts = [raw.get(key) for key in ("sessions", "progress", "set_asides")]
        if not (isinstance(started, str) and all(is_int(count) for count in counts)
                and (reading is None or is_number(reading))):
            return None
        run = RunInLock(started, *counts, reading)
    return LockState(pid, base, run_branch, session, recovery, run)


def read_lock(path: Path) -> LockState | None:
    """The run lock at `path`; None when there is none; an unreadable or invalid one raises
    DriverError, for nothing is to be done to a tree whose last run can't be told."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError):
        text = ""
    try:
        state = parse_lock(json.loads(text))
    except ValueError:
        state = None
    if state is None:
        raise DriverError(f"{path}: a lock that can't be read: check the tree, then delete it")
    return state


def store_lock(path: Path, state: LockState) -> None:
    """Writes the lock whole, through a temporary file beside it."""
    temporary = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(json.dumps(state.to_json(), indent=2) + "\n", encoding="utf-8")
        retrying(lambda: os.replace(temporary, path))
    except OSError as error:
        raise DriverError(f"the run lock {path} can't be written: {error}") from error


class RunLock:
    """`<git dir>/nfx/auto-running`: the driver's process, the base, the run branch and the
    session in progress and the run so far, so a run's other readers tell a run still going from
    one that ended. Each write replaces the whole file through a temporary file beside it."""

    def __init__(self, path: Path, base: str):
        self.path = path
        self.base = base
        self.held = False
        self.run = RunInLock(local_time())  # this driver's, whatever run it recovered

    def write(self, run_branch: str | None, session: SessionInLock | None) -> None:
        store_lock(self.path, LockState(os.getpid(), self.base, run_branch, session,
                                        run=self.run))
        self.held = True

    def keep(self) -> None:
        """Leaves the lock in place at every later `remove`: a recovery that failed is finished
        by the next start, which finds a dead run."""
        self.held = False

    def remove(self) -> None:
        """Removes the lock this driver wrote; does nothing when it holds none. A lock that
        can't be removed is reported on stderr, never raised, so the stop's output still comes."""
        if self.held:
            self.held = False
            try:
                retrying(lambda: self.path.unlink(missing_ok=True))
            except OSError as error:
                print(f"nfx:auto: the run lock {self.path} can't be removed: {error}",
                      file=sys.stderr, flush=True)


def refuse_live_driver(state: LockState) -> None:
    """Raises when the lock's driver is a live process."""
    if process_is_live(state.pid):
        raise DriverError(f"a run is going (driver process {state.pid}): wait for it, or end it")


# --- Recovering a dead run ---------------------------------------------------------------------

class Recovery:
    """Recovers a run whose driver died: sets the checkout's uncommitted work aside as a patch,
    tells the report, and returns the checkout to the run branch's last commit. Each step is
    printed. The patch, the lock's `recovery` and the report's section are all written before
    the reset, so a recovery cut short leaves the work in the tree or in a patch the lock names."""

    def __init__(self, git: Git, git_dir: Path, lock: Path):
        self.git = git
        self.git_dir = git_dir
        self.lock = lock

    def recover(self, state: LockState) -> str | None:
        """Steps 1 to 8; returns the run branch checked out at the end, None when the base is."""
        session = state.session
        if session is not None and process_is_live(session.pid):
            raise DriverError(f"a session of a dead run is still going (process {session.pid}): "
                              f"wait for it, or end it")
        say(f"recovering a dead run: driver process {state.pid} is gone")
        branch = self.run_branch_of(state)
        if state.recovery is not None:
            number, patch = state.recovery.n, state.recovery.patch
            say("an earlier recovery was cut short: going on from its number and patch")
            self.say_branch(branch, number)
        else:
            if session is None and self.git.out("status", "--porcelain"):
                raise DriverError("the driver died between sessions and the tree has changes, "
                                  "which may be yours: commit or remove them")
            number = self.next_number(branch)
            self.say_branch(branch, number)
            patch = self.set_work_aside(session, branch, number)
            store_lock(self.lock, LockState(state.pid, state.base, state.run_branch, session,
                                            RecoveryInLock(number, patch), state.run))
            say(f"recorded the recovery in the lock (section {number or 'none'}, patch "
                f"{patch or 'none'})")
        self.tell_report(session, branch, number, patch)
        return self.reset(state, branch)

    @staticmethod
    def say_branch(branch: str | None, number: int | None) -> None:
        say(f"run branch: {branch or 'none'}; interrupted section number: {number or 'none'}")

    def run_branch_of(self, state: LockState) -> str | None:
        """The lock's run branch when it exists, else the only run branch that exists."""
        if state.run_branch is not None and self.git.has_branch(state.run_branch):
            return state.run_branch
        runs = [name for name in self.git.branches() if is_run_branch(name)]
        return runs[0] if len(runs) == 1 else None

    def report_of(self, branch: str | None) -> Path | None:
        """The report of the run branch, when there is both."""
        if branch is None:
            return None
        report = report_file(self.git_dir, branch)
        return report if report.is_file() else None

    @staticmethod
    def read_report(report: Path) -> str:
        try:
            return report.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise DriverError(f"the report {report} can't be read: {error}") from error

    def next_number(self, branch: str | None) -> int | None:
        """The last `## Session <m>:` heading's `<m>` plus one (1 with none); None when the run
        branch or its report is missing."""
        report = self.report_of(branch)
        if report is None:
            return None
        numbers = [match.group(1) for match in SESSION_HEADING.finditer(self.read_report(report))]
        return int(numbers[-1]) + 1 if numbers else 1

    def set_work_aside(self, session: SessionInLock | None, branch: str | None,
                       number: int | None) -> str | None:
        """Saves the uncommitted work as a binary patch (`git add -A`, then `git diff --cached
        --binary HEAD`); returns its path, None when there is no work. A failure restores the
        index and refuses."""
        nfx = self.git_dir / "nfx"
        target: Path | None = None
        if number is not None and branch is not None:
            target = nfx / f"auto-{branch[len('auto/'):]}" / f"interrupted-{number}.patch"
        elif session is not None:
            target = nfx / f"interrupted-{session.started.replace(':', '-')}.patch"
        try:
            self.git.out("add", "-A")
            if not self.git.staged_changes():
                say("the checkout has no uncommitted work to set aside")
                return None
            if target is None:
                raise DriverError("the tree has changes but the lock names no session")
            target.parent.mkdir(parents=True, exist_ok=True)
            self.git.out("diff", "--cached", "--binary", f"--output={target}", "HEAD")
            if not target.is_file() or target.stat().st_size == 0:
                raise DriverError(f"{target} is empty")
        except (DriverError, OSError) as error:
            self.git.ok("reset", "-q")
            raise DriverError(f"the uncommitted work can't be set aside: {error}") from error
        say(f"set the uncommitted work aside: {target}")
        return str(target)

    def tell_report(self, session: SessionInLock | None, branch: str | None, number: int | None,
                    patch: str | None) -> None:
        """Appends `## Session <n>: interrupted` to the run's report, once. With no `<n>` the
        patch path is only printed; with no session (the driver died between sessions) nothing
        was interrupted, and no section is written."""
        report = self.report_of(branch)
        if number is None or report is None or session is None:
            say("no interrupted section is written: " + (
                "the run has no number" if number is None or report is None
                else "the driver died between sessions") + (f"; patch: {patch}" if patch else ""))
            return
        heading = f"## Session {number}: interrupted"
        text = self.read_report(report)
        session_log = session.log is not None and Path(session.log).is_file()
        if re.search(rf"^{re.escape(heading)}[ \t]*$", text, re.M):
            say(f"the report already holds '{heading}'")
            return
        lines = [heading, "",
                 f"The driver died during its session {session.number} (`{session.command}`), "
                 f"started {session.started}, with {self.git.current_branch() or 'no branch'} "
                 f"checked out. " + ("The session's uncommitted work is set aside and its "
                                     "commits" if patch is not None else
                                     "The session had no uncommitted work, and its commits")
                 + " stay on the run branch; the next sessions' pick decides what is done "
                 "with its work." + (f" Its log: {session.log}" if session_log else "")]
        if patch is not None:
            lines += ["", f"- **{number}.W1** uncommitted work of the interrupted session: "
                          f"{patch}"]
        gap = "\n" * max(0, 2 - (len(text) - len(text.rstrip("\n")))) if text else ""
        try:
            with report.open("a", encoding="utf-8", newline="\n") as out:
                out.write(gap + "\n".join(lines) + "\n")
        except OSError as error:
            raise DriverError(f"the report {report} can't be written: {error}") from error
        say(f"added '{heading}' to {report}")

    def reset(self, state: LockState, branch: str | None) -> str | None:
        """Resets the checkout (`git reset --hard`, `git clean -fd`) and switches to the run
        branch, or the base when there is none; a side branch is left as it is. Returns the
        run branch, None when the base is checked out."""
        died_on = self.git.current_branch()
        target = branch if branch is not None else state.base
        self.git.out("reset", "--hard", "-q")
        self.git.out("clean", "-fdq")
        if target == died_on:
            say(f"reset the checkout; {target} is checked out")
        else:
            if not self.git.has_branch(target):
                raise DriverError(f"{target} is not a local branch: check out the branch the "
                                  f"run is to start from")
            self.git.out("switch", "-q", target)
            say(f"reset the checkout; {died_on or 'a detached HEAD'} was checked out at the "
                f"death: switched to {target}")
        return branch


def dead_lock(git_dir: Path) -> LockState | None:
    """The lock of a dead run, None when there is no lock. An invalid lock, or a live driver's,
    raises DriverError and nothing is touched."""
    state = read_lock(lock_file(git_dir))
    if state is not None:
        refuse_live_driver(state)
    return state


def recover_dead_run(root: Path, git_dir: Path, state: LockState) -> str | None:
    """Recovers the dead run `state` names; returns the run branch left checked out (None: the
    base)."""
    return Recovery(Git(root), git_dir, lock_file(git_dir)).recover(state)
