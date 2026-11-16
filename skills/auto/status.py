# Spec: auto-status. Behaviour changes go through it.
"""Says what the auto run in this repo is doing now: `python status.py`, run from inside the
repo with no arguments. It reads the run lock, the running session's log, the run branch and
the run's report, prints them on stdout and exits 0; outside a git repo, or with an argument,
it prints `nfx:auto: <reason>` on stderr and exits 1. It changes nothing. Python 3 standard
library only."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import driver  # noqa: E402  (beside this file)
import runlock  # noqa: E402  (beside this file: the lock reading must agree with the driver's)

STEP_COUNT = 5
SUMMARY_LIMIT = 100
SAID_LIMIT = 160
SUMMARY_FIELDS = ("command", "file_path", "pattern", "description", "prompt")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


@dataclass(frozen=True)
class Steps:
    """What a session log shows: its latest tool uses as `(name, summary)`, oldest first, and
    the last line the assistant said (None: it said nothing)."""

    tools: list[tuple[str, str]]
    said: str | None


def cut(text: str, limit: int) -> str:
    """`text` with runs of whitespace made one space, cut to one less than `limit` and ended
    in `…` when it is longer than `limit`."""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def summarise(tool_input: object) -> str:
    """A tool use's input in one short line: its first present string field among
    SUMMARY_FIELDS, else the input as compact JSON."""
    if isinstance(tool_input, dict):
        for field in SUMMARY_FIELDS:
            if isinstance(tool_input.get(field), str):
                return cut(tool_input[field], SUMMARY_LIMIT)
    return cut(json.dumps(tool_input, separators=(",", ":"), ensure_ascii=False), SUMMARY_LIMIT)


def assistant_blocks(line: str) -> list[object]:
    """The content blocks of the log line, when it is an `assistant` event; else none."""
    try:
        event = json.loads(line)
    except ValueError:
        return []
    if not isinstance(event, dict) or event.get("type") != "assistant":
        return []
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return content if isinstance(content, list) else []


def read_steps(lines: list[str]) -> Steps:
    """The latest steps of the stream-json `lines`; a line that is not a JSON object is
    skipped."""
    tools: list[tuple[str, str]] = []
    said: str | None = None
    for line in lines:
        for block in assistant_blocks(line):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                name = block.get("name")
                tools.append((name if isinstance(name, str) else "?",
                              summarise(block.get("input"))))
            elif block.get("type") == "text" and isinstance(block.get("text"), str):
                spoken = [text for text in block["text"].splitlines() if text.strip()]
                said = cut(spoken[-1], SAID_LIMIT) if spoken else None
    return Steps(tools[-STEP_COUNT:], said)


def step_lines(log: str | None) -> list[str]:
    """The lines that show the session whose log is at `log`."""
    if log is None:
        return ["log: none recorded"]
    try:
        text = Path(log).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [f"log: {log} can't be read"]
    steps = read_steps(text.split("\n"))
    lines = [f"- {name}: {summary}" for name, summary in steps.tools]
    if steps.said is not None:
        lines.append(f"last said: {steps.said}")
    return lines


def your_turn(report: Path) -> list[str] | None:
    """The report's *Your turn* section, from its heading to the next heading of the same or a
    higher level (a `#` line inside a code fence is no heading); None when the report can't be
    read or has no such heading."""
    try:
        lines = report.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    start = level = None
    in_fence = False
    for number, line in enumerate(lines):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        match = None if in_fence else HEADING.match(line)
        if match is None:
            continue
        if start is None:
            if "your turn" in match.group(2).lower():
                start, level = number, len(match.group(1))
        elif len(match.group(1)) <= level:
            return lines[start:number]
    return None if start is None else lines[start:]


def run_line(run: runlock.RunInLock | None) -> str:
    if run is None:
        return "run: not recorded"
    reading = "none" if run.reading is None else driver.format_percent(run.reading)
    return (f"run: started {run.started}, {run.sessions} sessions, {run.progress} with "
            f"progress, {run.set_asides} set work aside, 7-day reading {reading}")


def branch_line(git: driver.Git, state: runlock.LockState) -> str:
    if state.run_branch is None:
        return f"branch: none yet, base {state.base}"
    try:
        count = git.out("rev-list", "--count", f"{state.base}..{state.run_branch}")
    except driver.DriverError:
        return f"branch: {state.run_branch}, base {state.base}"
    return f"branch: {state.run_branch}, base {state.base}, {count} commits since the base"


def live_run_lines(git: driver.Git, git_dir: Path, state: runlock.LockState) -> list[str]:
    lines = [run_line(state.run), branch_line(git, state)]
    if state.session is None:
        lines.append("between sessions")
    else:
        lines.append(f"session {state.session.number}: {state.session.command}, "
                     f"started {state.session.started}")
        lines.extend(step_lines(state.session.log))
    section = None
    if state.run_branch is not None:
        section = your_turn(driver.report_file(git_dir, state.run_branch))
    lines.extend(section if section is not None else ["report: none yet"])
    return lines


def status_lines(cwd: Path) -> list[str]:
    """The lines that say what the run in the repo `cwd` is in is doing."""
    git = driver.Git(cwd)
    try:
        common = git.out("rev-parse", "--git-common-dir")
    except driver.DriverError as error:
        raise driver.DriverError(f"{cwd} is not in a git repo ({error})") from error
    git_dir = (cwd / common).resolve()
    lock = runlock.lock_file(git_dir)
    try:
        state = runlock.read_lock(lock)
    except driver.DriverError:
        return [f"{lock}: a lock that can't be read"]
    if state is None:
        lines = ["no run is going"]
        runs = [name for name in git.branches() if driver.is_run_branch(name)]
        if runs:
            last = max(runs)
            lines.append(f"last run: {last}, report {driver.report_file(git_dir, last)}")
        return lines
    if not runlock.process_is_live(state.pid):
        return [f"the run's driver died (process {state.pid}): /nfx:auto, or /nfx:auto answer, "
                f"recovers it"]
    return live_run_lines(git, git_dir, state)


def main(argv: list[str], cwd: Path | None = None) -> int:
    try:
        if argv:
            raise driver.DriverError(f"status takes no arguments, not {' '.join(argv)}")
        lines = status_lines((cwd or Path.cwd()).resolve())
    except driver.DriverError as error:
        print(f"nfx:auto: {error}", file=sys.stderr, flush=True)
        return 1
    print("\n".join(lines), flush=True)
    return 0


if __name__ == "__main__":
    # UTF-8 whatever the console's code page, so `…` and paths always print
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
