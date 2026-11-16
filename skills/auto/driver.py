# Spec: auto-loop. Behaviour changes go through it.
"""The auto loop's driver: one fresh headless session per unit of work, until no queued work
can go ahead or a stopping rule holds, then an OS notification. A build session that commits its
change is followed at once by its finish session (`/nfx:implement <feature> finish auto`), which
folds it; a run that stopped between the two starts with that finish session.

Usage: driver.py [<feature-folder>] [--budget N] [--set-asides N] [--credential-hours N]
                 [--max-sessions N] [--session-hours N]
       driver.py --recover

Run from inside a git repo. Exits 0 when the run stops by a rule, 1 when it refuses to start
(a one-line reason on stderr, no session run). Prints one line per session as it ends, then,
at the stop, the report's path when a run branch exists (`report: <path>`), and last the stop
reason, alone on the last line. `--recover` recovers a run whose driver died (a start does so
too) and exits.

The sessions do every change to the repo, bar recovering a dead run, or a timed-out session's
checkout (its uncommitted work is set aside as a patch, the checkout reset, the report told):
the driver reads git, the run report's Base line and session headings, status mode's JSON and
the sessions' stream-json output, and otherwise
writes only its own files under `<git dir>/nfx/`: its settings file, `auto-settings.json`, and
the run lock, `auto-running`, which it holds from the moment its start checks pass until it
exits by any path, bar a timed-out session's failed recovery, which keeps it. Python 3 standard library only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Iterator, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
# beside this file: the run lock, and what it shares with the driver (both are run as files)
from common import (SESSION_HEADING, Branches, DriverError, Git, is_run_branch,  # noqa: E402
                    is_side_branch, local_time, report_file, say)
from runlock import (RunInLock, RunLock, SessionInLock, dead_lock,  # noqa: E402
                     lock_file, read_lock, recover_dead_run, retrying)

SPEC_LINT = Path(__file__).resolve().parent.parent / "spec" / "scripts" / "spec_lint.py"
USAGE = ("driver.py [<feature-folder>] [--budget N] [--set-asides N] [--credential-hours N] "
         "[--max-sessions N] [--session-hours N] | driver.py --recover")
RECOVER = "--recover"
SKIPPED_LINE = re.compile(r"^spec_lint --status: skipped (.+?): (.*); lint it$")
BASE_LINE = re.compile(r"^- \*\*Base:\*\* (\S+) @ ([0-9a-fA-F]{7,64})$")
INTEGER = re.compile(r"^-?[0-9]+$")
REASON_LIMIT = 160  # characters of a no-progress session's reason line
MESSAGE_VARIABLE = "NFX_AUTO_MESSAGE"  # the notification's text, read by its command
BUILD = "/nfx:implement"
PLAN = "/nfx:spec"
AUTO = "auto"
FINISH = "finish"


# --- Options -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Knob:
    """A tunable the command line sets: its option, inclusive range and default."""

    option: str
    low: int
    high: int
    default: int

    @property
    def field_name(self) -> str:
        return self.option[2:].replace("-", "_")


BUDGET = Knob("--budget", 1, 100, 20)
SET_ASIDES = Knob("--set-asides", 1, 10, 3)
CREDENTIAL_HOURS = Knob("--credential-hours", 0, 72, 12)
MAX_SESSIONS = Knob("--max-sessions", 1, 1000, 200)
SESSION_HOURS = Knob("--session-hours", 1, 12, 3)
KNOBS = (BUDGET, SET_ASIDES, CREDENTIAL_HOURS, MAX_SESSIONS, SESSION_HOURS)
SECONDS_PER_HOUR = 3600  # tests shorten it, to time a session out in moments


@dataclass(frozen=True)
class Options:
    feature: str | None
    budget: int
    set_asides: int
    credential_hours: int
    max_sessions: int
    session_hours: int
    recover: bool = False


def parse_options(argv: list[str]) -> Options:
    """The command line's options; a bad one raises DriverError, never the parser's exit 2."""
    if RECOVER in argv:
        if len(argv) != 1:
            raise DriverError(f"{RECOVER} takes no other argument; usage: {USAGE}")
        return Options(None, *(knob.default for knob in KNOBS), recover=True)
    knobs = {knob.option: knob for knob in KNOBS}
    values: dict[str, int] = {}
    feature: str | None = None
    at = 0
    while at < len(argv):
        arg = argv[at]
        knob = knobs.get(arg)
        if knob is not None:
            if knob.field_name in values:
                raise DriverError(f"{arg} is given twice")
            if at + 1 >= len(argv):
                raise DriverError(f"{arg} needs a value ({knob.low} to {knob.high})")
            values[knob.field_name] = knob_value(knob, argv[at + 1])
            at += 2
            continue
        if arg.startswith("-"):
            raise DriverError(f"unknown option {arg}; usage: {USAGE}")
        if feature is not None:
            raise DriverError(f"give one feature folder, not '{feature}' and '{arg}'")
        feature = arg
        at += 1
    return Options(feature, **{k.field_name: values.get(k.field_name, k.default) for k in KNOBS})


def knob_value(knob: Knob, text: str) -> int:
    if not INTEGER.match(text):
        raise DriverError(f"{knob.option} takes an integer from {knob.low} to {knob.high}, "
                          f"not '{text}'")
    value = int(text)
    if not knob.low <= value <= knob.high:
        raise DriverError(f"{knob.option} must be from {knob.low} to {knob.high}, not {value}")
    return value


@dataclass(frozen=True)
class Checkout:
    """The repo the run works in: its root, its git dir and the base branch."""

    root: Path
    git_dir: Path
    base: str

    @property
    def settings(self) -> Path:
        return self.git_dir / "nfx" / "auto-settings.json"

    @property
    def lock(self) -> Path:
        return lock_file(self.git_dir)


def read_report(report: Path, branch: str) -> str:
    """The text of the run branch's report; a missing or unreadable one raises DriverError."""
    if not report.is_file():
        raise DriverError(f"{branch} is checked out but its report {report} is missing")
    try:
        return report.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise DriverError(f"{branch}'s report {report} can't be read: {error}") from error


def read_base(text: str, report: Path, branch: str) -> str:
    """The branch the report's `- **Base:** <branch> @ <commit>` line names, its first line
    after the title."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    match = BASE_LINE.match(lines[1]) if len(lines) > 1 and lines[0].startswith("# ") else None
    if match is None:
        raise DriverError(f"{branch}'s report {report} has no '- **Base:** <branch> @ <commit>' "
                          f"line after its title")
    return match.group(1)


def last_build_finish(text: str) -> Unit | None:
    """The finish of the build session whose section is the report's last, when it is a build
    session's (`/nfx:implement <target> auto`); None when the last is any other session's, an
    `interrupted` one included, since the session it records was cut short."""
    commands = [match.group(2) for match in SESSION_HEADING.finditer(text)]
    words = commands[-1].split(" ") if commands else []
    if len(words) < 3 or words[0] != BUILD or words[-1] != AUTO or words[-2] == FINISH:
        return None
    return Unit(BUILD, " ".join(words[1:-1])).finishing()


@dataclass(frozen=True)
class Pending:
    """A pending change, or an unbuilt spec (`change` None), as status mode lists it."""

    spec: str  # its spec's path, relative to the repo root
    id: str  # its spec's ID
    change: str | None

    def named_by(self, trailers: list[tuple[str, str]]) -> bool:
        """The trailers of a commit that commits it: a `Spec:` naming its spec (by ID or path)
        and a `Spec-Change:` naming the change, or the spec's ID for a new spec."""
        specs = {value for key, value in trailers if key == "Spec"}
        changes = {value.casefold() for key, value in trailers if key == "Spec-Change"}
        name = self.id if self.change is None else self.change
        return (bool(name) and bool(specs & ({self.id, self.spec} - {""}))
                and name.casefold() in changes)


def finish_due(finish: Unit, trailers: list[tuple[str, str]],
               pending: list[Pending]) -> Unit | None:
    """The finish session a run that stopped between a build session and its finish starts
    with: the last section's build's finish (`last_build_finish`), when HEAD's commit commits work
    status mode still lists as pending or unbuilt, so the build left it committed and not
    folded; otherwise None (a build that committed nothing, or work folded since)."""
    return finish if any(item.named_by(trailers) for item in pending) else None


def deny_rules(base: str) -> list[str]:
    """The settings file's `permissions.deny`: pushing, and checking out, deleting or moving
    the base, for both shell tools, each as the bare command and with anything after it. A
    best-effort guard, beside auto mode's own checks."""
    commands = ["git push", f"git switch {base}", f"git checkout {base}",
                f"git branch -d {base}", f"git branch -D {base}", f"git branch --delete {base}",
                f"git branch -f {base}", f"git update-ref refs/heads/{base}"]
    return [rule for tool in ("Bash", "PowerShell") for command in commands
            for rule in (f"{tool}({command})", f"{tool}({command} *)")]


def write_settings(checkout: Checkout) -> None:
    path = checkout.settings
    text = json.dumps({"permissions": {"deny": deny_rules(checkout.base)}}, indent=2)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    except OSError as error:
        raise DriverError(f"settings file {path} can't be written: {error}") from error


# --- Features and units ------------------------------------------------------------------------

@dataclass(frozen=True)
class Unit:
    """A skill on a feature, run as one session: a build, a plan, or a build's finish."""

    skill: str
    target: str  # relative to the repo root, `/`-separated
    finish: bool = False  # the finish session of the target's build

    @property
    def command(self) -> str:
        if self.finish:
            return f"{self.skill} {self.target} {FINISH} {AUTO}"
        return f"{self.skill} {self.target} {AUTO}"

    @property
    def builds(self) -> bool:
        """A build session's unit, which its finish session follows when it commits."""
        return self.skill == BUILD and not self.finish

    def finishing(self) -> Unit:
        """The finish session of this unit's target."""
        return Unit(BUILD, self.target, finish=True)


@dataclass(frozen=True)
class Feature:
    """A feature folder (one holding a `README.md`), or a one-file feature's spec."""

    path: str  # relative to the repo root, `/`-separated

    def units(self) -> tuple[Unit, ...]:
        return (Unit(BUILD, self.path), Unit(PLAN, self.path))


def same_path(a: Path, b: Path) -> bool:
    return os.path.normcase(str(a)) == os.path.normcase(str(b))


def within(path: Path, folder: Path) -> bool:
    """`path` is `folder` or lies under it."""
    return same_path(path, folder) or any(same_path(parent, folder) for parent in path.parents)


class SpecTree:
    """The specs under the run's scope (the feature folder given, or the specs root), read
    through status mode."""

    def __init__(self, root: Path, specs_root: Path, scope: Path):
        self.root = root  # the repo root
        self.specs_root = specs_root
        self.scope = scope
        self.pending: list[Pending] = []  # the pending and unbuilt work of the last read
        self.left = WorkLeft(0, 0, 0, 0)  # the last read's items per group

    def relative(self, path: Path) -> str:
        return Path(os.path.relpath(path, self.root)).as_posix()

    def feature_of(self, document: Path) -> Feature:
        """The nearest folder holding a `README.md` from the document up to the specs root,
        else the document itself (a one-file feature)."""
        folder = document.parent
        while within(folder, self.specs_root):
            if (folder / "README.md").is_file():
                return Feature(self.relative(folder))
            if same_path(folder, self.specs_root):
                break
            folder = folder.parent
        return Feature(self.relative(document))

    def read(self) -> tuple[list[Feature], str | None]:
        """The features of status mode's `ready`, `draft` and `not_yet_planned` items at or
        under the scope, in the order of their first item, and the reason for the first
        document status mode skipped (None when it skipped none). The pending and unbuilt work
        it lists is kept as `pending`."""
        data, skipped = self.status(self.scope)
        try:
            documents = ([item["spec"] for item in data["ready"]]
                         + [item["spec"] for item in data["draft"]]
                         + [line["file"] for line in data["not_yet_planned"]])
            self.pending = pending_of(data)
            self.left = WorkLeft(*(len(data.get(group, ())) for group in WorkLeft.GROUPS))
        except (KeyError, TypeError) as error:
            raise DriverError(f"status read failed: its JSON can't be read ({error})") from error
        features: list[Feature] = []
        for document in documents:
            feature = self.feature_of(self.root / document)
            if feature not in features and within(self.root / feature.path, self.scope):
                features.append(feature)
        return features, skipped

    def pending_everywhere(self) -> list[Pending]:
        """The pending and unbuilt work of the whole specs root, whatever the scope: the last
        read's when the scope is the root, else one more status read, of the root."""
        if same_path(self.scope, self.specs_root):
            return self.pending
        data, _ = self.status(self.specs_root)
        try:
            return pending_of(data)
        except (KeyError, TypeError) as error:
            raise DriverError(f"status read failed: its JSON can't be read ({error})") from error

    def status(self, folder: Path) -> tuple[dict, str | None]:
        """Status mode's JSON for `folder`, and the reason for the first document it skipped
        (None when it skipped none); a failed read raises DriverError."""
        command = [sys.executable, str(SPEC_LINT), "--status", self.relative(folder), "--json"]
        try:
            result = subprocess.run(command, cwd=self.root, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
        except OSError as error:
            raise DriverError(f"status read failed: {error}") from error
        skipped = None
        for line in result.stderr.splitlines():
            match = SKIPPED_LINE.match(line.strip())
            if match is not None:
                skipped = f"{match.group(1)} skipped: {match.group(2)}; lint it"
                break
        if result.returncode != 0:
            lines = result.stderr.strip().splitlines() or [f"exit {result.returncode}"]
            raise DriverError(f"status read failed: {lines[-1]}")
        try:
            data = json.loads(result.stdout)
        except ValueError as error:
            raise DriverError(f"status read failed: its JSON can't be read ({error})") from error
        if not isinstance(data, dict):
            raise DriverError("status read failed: its JSON can't be read (not an object)")
        return data, skipped


@dataclass(frozen=True)
class WorkLeft:
    """How many items status mode lists in each group that holds queued work."""

    GROUPS = ("ready", "blocked", "draft", "convert")  # the order of the fields

    ready: int
    blocked: int
    draft: int
    convert: int

    def stop_reason(self) -> str:
        """The stop reason of a run with every unit idle."""
        parts = [f"{count} {label}" for count, label in
                 ((self.ready, "ready"), (self.blocked, "blocked"), (self.draft, "draft"),
                  (self.convert, "to convert")) if count]
        if not parts:
            return "all queued work is done"
        return "work is left, but none can go ahead: " + ", ".join(parts)


def pending_of(data: dict) -> list[Pending]:
    """The pending changes and unbuilt specs status mode's JSON lists, in any group."""
    return [Pending(item["spec"], item.get("id") or "", item.get("change"))
            for group in ("ready", "blocked", "draft", "convert") for item in data.get(group, [])]


# --- Sessions ----------------------------------------------------------------------------------

@dataclass(frozen=True)
class StreamFacts:
    """What a session's stream-json output said: whether it sent a `result` event, its last
    7-day reading (percent), and its last `result` event's credential expiry and `result`
    text ("" when it has none)."""

    saw_result: bool = False
    reading: float | None = None
    credential_expires: datetime | None = None
    result_text: str = ""


def parse_expiry(value: object) -> datetime | None:
    """`credential_expires_at` as an aware datetime: epoch seconds (or milliseconds) or an ISO
    8601 string; None when it is neither."""
    if isinstance(value, str) and INTEGER.match(value.strip()):
        value = int(value.strip())
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = value / 1000 if value > 1e11 else value
        try:
            return datetime.fromtimestamp(seconds, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            when = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
        return when if when.tzinfo else when.replace(tzinfo=timezone.utc)
    return None


def seven_day_reading(event: dict) -> float | None:
    info = event.get("rate_limit_info")
    windows = info.get("unifiedWindows") if isinstance(info, dict) else None
    window = windows.get("seven_day") if isinstance(windows, dict) else None
    utilization = window.get("utilization") if isinstance(window, dict) else None
    if isinstance(utilization, (int, float)) and not isinstance(utilization, bool):
        return round(utilization * 100, 6)
    return None


def read_stream(lines: Iterable[str]) -> StreamFacts:
    """The facts of a session's stdout, read line by line; lines that don't parse as a JSON
    object are skipped."""
    saw_result = False
    reading = None
    expires = None
    text = ""
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "rate_limit_event":
            seen = seven_day_reading(event)
            reading = seen if seen is not None else reading
        elif event.get("type") == "result":
            saw_result = True
            expires = parse_expiry(event.get("credential_expires_at"))
            said = event.get("result")
            text = said if isinstance(said, str) else ""
    return StreamFacts(saw_result, reading, expires, text)


def reason_line(text: str) -> str | None:
    """The last non-blank line of a session's `result` text, its whitespace runs made one space
    and cut to REASON_LIMIT characters ending in `…`; None when the text has no such line."""
    for line in reversed(text.splitlines()):
        words = " ".join(line.split())
        if words:
            return words if len(words) <= REASON_LIMIT else words[:REASON_LIMIT - 1] + "…"
    return None


@dataclass(frozen=True)
class SessionEnd:
    exit_code: int
    facts: StreamFacts
    timed_out: bool = False  # the session was killed for running past its hours

    @property
    def failure(self) -> str | None:
        """What failed the session ("exit 1", "no result event", or both, comma-separated);
        None when it exited 0 and sent a `result` event."""
        parts = ([f"exit {self.exit_code}"] if self.exit_code != 0 else []) + (
            [] if self.facts.saw_result else ["no result event"])
        return ", ".join(parts) or None


LOG_FOLDER = "auto-logs"


def session_log_file(git_dir: Path, started: str, number: int) -> Path:
    """`<git dir>/nfx/auto-logs/<started>-<driver pid>-<number>.log`, `<started>` with each `:`
    made `-`; the driver's process ID keeps two drivers' logs apart."""
    return (git_dir / "nfx" / LOG_FOLDER
            / f"{started.replace(':', '-')}-{os.getpid()}-{number}.log")


def clear_old_logs(git_dir: Path, keep: Path | None) -> None:
    """Deletes every file in the logs folder but `keep`: a log serves only the run it belongs
    to. A log that can't be deleted is printed and left for the next start to try again."""
    folder = git_dir / "nfx" / LOG_FOLDER
    try:
        if not folder.is_dir():
            return
        paths = [path for path in folder.iterdir()
                 if path.is_file() and not (keep is not None and same_path(path, keep))]
    except OSError as error:
        say(f"the old session logs in {folder} can't be listed: {error}")
        return
    for path in paths:
        try:
            path.unlink()
        except OSError as error:
            say(f"the old session log {path} can't be deleted: {error}")


def logged(lines: Iterable[str], log: TextIO, path: Path) -> Iterator[str]:
    """The lines as they come, each first appended to the log (ending in a newline) and
    flushed."""
    for line in lines:
        try:
            log.write(line if line.endswith("\n") else line + "\n")
            log.flush()
        except OSError as error:
            raise DriverError(f"the session log {path} can't be written: {error}") from error
        yield line


def kill_tree(process: subprocess.Popen) -> None:
    """Kills the process and every process it started: on Windows `taskkill /T /F`, elsewhere
    the process group it was started in (`run_session` starts it in its own)."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                       capture_output=True, stdin=subprocess.DEVNULL)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
    process.kill()


def run_session(claude: list[str], unit: Unit, checkout: Checkout, log_path: Path,
                started: Callable[[int], None], seconds: float) -> SessionEnd:
    """One fresh `claude -p` process from the repo root, stdin closed, its stream read as it
    comes and appended to the session log `log_path`, created before the process starts.
    `started` is called with the process's ID once it has started; when it or the log raises,
    the process is killed. A process still running `seconds` after it started is killed with
    its whole process tree, and the end says so."""
    command = [*claude, "-p", unit.command, "--permission-mode", "auto", "--output-format",
               "stream-json", "--verbose", "--settings", str(checkout.settings)]
    environment = dict(os.environ, CLAUDE_CODE_RETRY_WATCHDOG="1")
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = log_path.open("a", encoding="utf-8", newline="\n")
    except OSError as error:
        raise DriverError(f"the session log {log_path} can't be created: {error}") from error
    with log:
        try:
            process = subprocess.Popen(command, cwd=checkout.root, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, env=environment, text=True,
                                       encoding="utf-8", errors="replace",
                                       start_new_session=sys.platform != "win32")
        except OSError as error:
            raise DriverError(f"session {unit.command} could not be started: {error}") from error
        timed_out = threading.Event()

        def time_out() -> None:
            if process.poll() is None:
                timed_out.set()
                kill_tree(process)

        timer = threading.Timer(seconds, time_out)
        with process:
            assert process.stdout is not None
            try:
                started(process.pid)
                timer.start()
                facts = read_stream(logged(process.stdout, log, log_path))
            except BaseException:
                kill_tree(process)
                raise
            finally:
                timer.cancel()
                if timer.is_alive():
                    timer.join()
    return SessionEnd(process.wait(), facts, timed_out.is_set())


def find_claude() -> list[str]:
    found = shutil.which("claude")
    if found is None:
        raise DriverError("claude is not on PATH")
    return [found]


# --- Notification ------------------------------------------------------------------------------

TOAST_SCRIPT = """
$name = 'Windows.UI.Notifications.ToastNotificationManager'
$null = [Type]::GetType($name + ', Windows.UI.Notifications, ContentType = WindowsRuntime')
$manager = [Windows.UI.Notifications.ToastNotificationManager]
$kind = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
$template = $manager::GetTemplateContent($kind)
$texts = $template.GetElementsByTagName('text')
$texts.Item(0).AppendChild($template.CreateTextNode('nfx:auto')) > $null
$texts.Item(1).AppendChild($template.CreateTextNode($env:NFX_AUTO_MESSAGE)) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'
$manager::CreateToastNotifier($app).Show($toast)
"""


class Notifier(ABC):
    """An OS notification, raised by a command that is given the message (and reads it from
    the `NFX_AUTO_MESSAGE` environment variable where quoting it would be fragile)."""

    @abstractmethod
    def command(self, message: str) -> list[str]:
        """The command that raises the notification."""

    def notify(self, message: str) -> str | None:
        """Raises the notification; returns why it failed, or None."""
        environment = dict(os.environ, **{MESSAGE_VARIABLE: message})
        try:
            result = subprocess.run(self.command(message), capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", env=environment,
                                    stdin=subprocess.DEVNULL, timeout=60)
        except (OSError, subprocess.SubprocessError) as error:
            return str(error)
        if result.returncode != 0:
            lines = result.stderr.strip().splitlines()
            return f"exit {result.returncode}" + (f": {lines[-1]}" if lines else "")
        return None


class ToastNotifier(Notifier):
    """Windows: a toast through `powershell.exe`'s `Windows.UI.Notifications`."""

    def command(self, message: str) -> list[str]:
        return ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", TOAST_SCRIPT]


class OsascriptNotifier(Notifier):
    """macOS: `osascript`'s `display notification`."""

    def command(self, message: str) -> list[str]:
        return ["osascript", "-e",
                f'display notification (system attribute "{MESSAGE_VARIABLE}") '
                'with title "nfx:auto"']


class NotifySendNotifier(Notifier):
    """Elsewhere: `notify-send`."""

    def command(self, message: str) -> list[str]:
        return ["notify-send", "nfx:auto", message]


def platform_notifier() -> Notifier | None:
    """This OS's notifier; None where there is none (no `notify-send` outside Windows and macOS)."""
    if sys.platform == "win32":
        return ToastNotifier()
    if sys.platform == "darwin":
        return OsascriptNotifier()
    return NotifySendNotifier() if shutil.which("notify-send") else None


# --- The run -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Outcome:
    """What a session did: whether it made progress, what failed it (None: nothing) and its log."""

    progress: bool
    failure: str | None
    log: Path


NO_READING = "no 7-day usage reading yet: the budget can't stop this run until one arrives"


@dataclass(frozen=True)
class Host:
    """What the driver runs beyond git and status mode: the `claude` command (None: `claude`
    on PATH) and the notifier (None: no notification). Tests pass stand-ins."""

    claude: tuple[str, ...] | None
    notifier: Notifier | None


def format_percent(value: float) -> str:
    return f"{round(value, 2):g}%"


class Run:
    """The loop: the next unit, its session, what it did, and the stopping rules."""

    def __init__(self, options: Options, checkout: Checkout, tree: SpecTree, claude: list[str],
                 features: list[Feature], lock: RunLock, branches: Branches,
                 resume: Unit | None = None):
        self.options = options
        self.checkout = checkout
        self.tree = tree
        self.claude = claude
        self.git = Git(checkout.root)
        self.features = features
        self.lock = lock
        self.branches = branches  # the git read at start, then after each session: no other
        self.sessions = 0
        self.counted = 0  # sessions as max-sessions counts them: a build and its finish are one
        self.resume = resume  # the finish session a run stopped between the two starts with
        self.idle: set[Unit] = set()  # units whose last session made no progress
        self.set_asides = 0  # sessions in a row that set work aside and made no progress
        self.baseline: float | None = None  # the run's first 7-day reading
        self.last_reading: float | None = None
        self.credential_expires: datetime | None = None  # from the last `result` event

    def next_unit(self) -> Unit | None:
        for feature in self.features:
            for unit in feature.units():
                if unit not in self.idle:
                    return unit
        return None

    def before_session(self) -> str | None:
        """The stop reason the budget or the credential gives before a session after the
        first, or None."""
        if self.sessions == 0:
            return None
        if (self.baseline is not None and self.last_reading is not None
                and self.last_reading >= self.baseline + self.options.budget):
            return (f"budget used: {format_percent(self.baseline)} → "
                    f"{format_percent(self.last_reading)}")
        if self.credential_expires is not None:
            left = self.credential_expires - datetime.now(timezone.utc)
            if left <= timedelta(hours=self.options.credential_hours):
                when = self.credential_expires.astimezone().isoformat(timespec="minutes")
                return f"sign-in expires {when}: run `claude setup-token` for unattended runs"
        return None

    @property
    def run_branch(self) -> str | None:
        """The run branch checked out at the last read, for the lock; none when a side branch
        or nothing is."""
        branch = self.branches.checked_out
        return branch if branch is not None and is_run_branch(branch) else None

    def read_after_failed_session(self) -> None:
        """A session that failed may have created the run branch: reads the branches again so the
        stop's report path is right; a read that fails leaves the last one."""
        try:
            self.branches = self.git.read_branches()
        except DriverError:
            pass

    def session(self, unit: Unit) -> Outcome:
        """Runs the unit's session and records what it did. A session killed for running past
        the session hours is recovered, then raises DriverError with the stop reason (or with
        the recovery's error, the lock kept)."""
        before = self.branches
        sides_before = {name for name in before.heads if is_side_branch(name)}
        number = self.sessions + 1
        started = local_time()

        log = session_log_file(self.checkout.git_dir, started, number)

        def process_started(pid: int) -> None:
            self.lock.write(self.run_branch,
                            SessionInLock(number, unit.command, pid, started, str(log)))

        try:
            end = run_session(self.claude, unit, self.checkout, log, process_started,
                              self.options.session_hours * SECONDS_PER_HOUR)
            if end.timed_out:
                self.recover_timed_out(number)
        except DriverError:
            self.read_after_failed_session()
            raise
        if end.timed_out:
            self.read_after_failed_session()
            hours = self.options.session_hours
            noun = "hour" if hours == 1 else "hours"
            raise DriverError(f"session {number} ran past {hours} {noun}: killed; log {log}")
        self.sessions += 1
        self.branches = self.git.read_branches()
        branch, heads = self.branches.checked_out, self.branches.heads
        # progress: the run branch checked out after has a commit other than its own before;
        # a branch new in the session is compared with the commit HEAD was at (none: a detached
        # HEAD, whose commit the held read doesn't have)
        progress = (branch is not None and is_run_branch(branch) and heads.get(branch)
                    != before.heads.get(branch, before.heads.get(before.checked_out)))
        set_aside = any(is_side_branch(name) and name not in sides_before for name in heads)
        self.set_asides = self.set_asides + 1 if set_aside and not progress else 0
        if end.facts.reading is not None:
            self.last_reading = end.facts.reading
            if self.baseline is None:
                self.baseline = end.facts.reading
        run = self.lock.run
        self.lock.run = RunInLock(
            run.started, self.sessions, run.progress + progress, run.set_asides + set_aside,
            None if self.last_reading is None else round(self.last_reading, 2))
        self.lock.write(self.run_branch, None)
        if end.facts.saw_result:
            self.credential_expires = end.facts.credential_expires
        parts = ["progress" if progress else "no progress"]
        if set_aside:
            parts.append("set work aside")
        if end.failure:
            parts.append(end.failure)
        parts.append("7-day " + (format_percent(self.last_reading)
                                 if self.last_reading is not None else "not read yet"))
        print(f"session {self.sessions}: {unit.command}: {', '.join(parts)}", flush=True)
        reason = None if progress else reason_line(end.facts.result_text)
        if reason:
            print(f"  {reason}", flush=True)
        return Outcome(progress, end.failure, log)

    def recover_timed_out(self, number: int) -> None:
        """Recovers the checkout of the session just killed, from the run's own lock; when that
        fails the lock is kept, so the next start finds a dead run and finishes the recovery."""
        try:
            state = read_lock(self.checkout.lock)
            if state is None:
                raise DriverError(f"the run lock {self.checkout.lock} is gone: session {number} "
                                  f"can't be recovered")
            recover_dead_run(self.checkout.root, self.checkout.git_dir, state)
        except DriverError:
            self.lock.keep()
            raise

    def loop(self) -> str:
        """Runs sessions until a stopping rule holds; returns the stop reason."""
        try:
            while True:
                unit, self.resume = self.resume or self.next_unit(), None
                if unit is None:
                    return self.tree.left.stop_reason()
                reason = self.before_session()
                if reason is not None:
                    return reason
                if self.sessions == 0:
                    write_settings(self.checkout)
                first = self.sessions == 0
                outcome = self.session(unit)
                progress = outcome.progress
                if first:
                    if outcome.failure is not None:
                        return (f"the first session failed ({outcome.failure}): check that "
                                f"`claude -p` runs here with the permissions auto mode needs; "
                                f"log {outcome.log}")
                    if self.last_reading is None:
                        print(NO_READING, flush=True)
                if progress and unit.builds:
                    # the build committed its change: its finish session folds it, before the
                    # next pick and with no stopping rule between the two
                    self.session(unit.finishing())
                self.counted += 1
                if self.set_asides >= self.options.set_asides:
                    noun = "set-aside" if self.set_asides == 1 else "set-asides"
                    return f"{self.set_asides} {noun} in a row: check the environment"
                if self.counted >= self.options.max_sessions:
                    noun = "session" if self.counted == 1 else "sessions"
                    return f"{self.counted} {noun}: max-sessions reached"
                if progress:
                    self.idle.clear()
                    self.features, skipped = self.tree.read()
                    if skipped is not None:
                        return skipped
                else:
                    self.idle.add(unit)
        except DriverError as error:
            return str(error)

    def report_path(self) -> Path | None:
        """The report of the run branch checked out, else of the first run branch, if any."""
        branch = self.branches.checked_out
        if branch is None or not is_run_branch(branch):
            branch = next((name for name in self.branches.heads if is_run_branch(name)), None)
        return report_file(self.checkout.git_dir, branch) if branch is not None else None


def open_repo(cwd: Path) -> tuple[Path, Path]:
    """The repo root and git dir `cwd` is in; a refusal raises DriverError."""
    try:
        root, git_dir = Git(cwd).out("rev-parse", "--show-toplevel",
                                     "--absolute-git-dir").splitlines()
    except DriverError as error:
        raise DriverError(f"{cwd} is not in a git repo ({error})") from error
    return Path(root).resolve(), Path(git_dir).resolve()


def start(options: Options, cwd: Path, host: Host) -> Run:
    """Checks the run can start, recovers a dead run if the lock names one, checks the branch
    and reads the features; a refusal raises DriverError. The lock's validity and a live
    driver's refusal come first, then the checks that read no branch (so a mistyped command
    changes nothing), then the recovery, then the branch checks."""
    root, git_dir = open_repo(cwd)
    dead = dead_lock(git_dir)
    specs_root, scope = find_scope(options, cwd, root)
    claude = list(host.claude) if host.claude is not None else find_claude()
    lock = RunLock(lock_file(git_dir), dead.base if dead else "")
    if dead is not None:  # this run's lock from now on; a refusal below removes it
        lock.write(recover_dead_run(root, git_dir, dead), None)
        say("the lock is written as this run's: going on with the start checks")
    try:
        run = begin(options, root, git_dir, lock, claude, specs_root, scope)
        keep = Path(dead.session.log) if dead and dead.session and dead.session.log else None
        clear_old_logs(git_dir, keep)
    except BaseException:
        lock.remove()
        raise
    return run


def find_scope(options: Options, cwd: Path, root: Path) -> tuple[Path, Path]:
    """The specs root and the scope of the run (the feature folder given, or the root)."""
    specs_root = next((root / name for name in ("documents/specs", "docs/specs")
                       if (root / name).is_dir()), None)
    if specs_root is None:
        raise DriverError(f"no specs root: neither documents/specs nor docs/specs is under {root}")
    scope = specs_root
    if options.feature is not None:
        # read as a path under the specs root first, then from the working directory
        scope = (specs_root / options.feature).resolve()
        if not scope.is_dir():
            scope = (cwd / options.feature).resolve()
        if not scope.is_dir() or not within(scope, specs_root):
            raise DriverError(f"{options.feature} is not a folder under {specs_root}")
    return specs_root, scope


def begin(options: Options, root: Path, git_dir: Path, lock: RunLock, claude: list[str],
          specs_root: Path, scope: Path) -> Run:
    """The branch checks after any recovery, then the status read, the lock and the run."""
    git = Git(root)
    branches = git.read_branches()
    branch = branches.checked_out
    if branch is None:
        raise DriverError("HEAD is detached: check out the branch the run is to start from")
    if is_side_branch(branch) or branch.startswith("milestone/"):
        raise DriverError(f"{branch} is checked out: a run can't start on a side branch or a "
                          f"milestone branch; check out the branch the run is to start from")
    finish = None
    if is_run_branch(branch):
        report = report_file(git_dir, branch)
        text = read_report(report, branch)
        base = read_base(text, report, branch)
        finish = last_build_finish(text)
        if base not in branches.heads:
            raise DriverError(f"{branch}'s report names base {base}, which is not a local branch")
    else:
        others = [name for name in branches.heads if is_run_branch(name)]
        if others:
            raise DriverError(f"run branch {others[0]} exists: answer and merge it "
                              f"(/nfx:auto answer), or delete it, before a new run")
        base = branch
    checkout = Checkout(root, git_dir, base)
    tree = SpecTree(root, specs_root, scope)
    features, skipped = tree.read()
    if skipped is not None:
        raise DriverError(skipped)
    # HEAD's trailers, and the specs root's status beyond the scope, are read only when the
    # last section is a build session's
    resume = (finish_due(finish, git.head_trailers(), tree.pending_everywhere())
              if finish is not None else None)
    lock.base = base
    run = Run(options, checkout, tree, claude, features, lock, branches, resume)
    lock.write(run.run_branch, None)
    return run


def finish(run: Run, reason: str, notifier: Notifier | None) -> None:
    """At a stop: the notification, the report's path when a run branch exists, and last the
    stop reason, alone on the last line."""
    report = run.report_path()
    if notifier is not None:
        failure = notifier.notify(reason if report is None else f"{reason}\n{report}")
        if failure is not None:
            print(f"notification failed: {failure}", flush=True)
    if report is not None:
        print(f"report: {report}", flush=True)
    print(reason, flush=True)


def recover_only(cwd: Path) -> int:
    """`--recover`: recovers a dead run and exits; no lock is `no dead run`."""
    try:
        root, git_dir = open_repo(cwd)
        state = dead_lock(git_dir)
        if state is None:
            say("no dead run")
            return 0
        recover_dead_run(root, git_dir, state)
        retrying(lock_file(git_dir).unlink)
    except (DriverError, OSError) as error:
        print(f"nfx:auto: {error}", file=sys.stderr, flush=True)
        return 1
    say("the lock is removed")
    return 0


def main(argv: list[str], cwd: Path | None = None, host: Host | None = None) -> int:
    host = host if host is not None else Host(None, platform_notifier())
    try:
        options = parse_options(argv)
        if options.recover:
            return recover_only((cwd or Path.cwd()).resolve())
        run = start(options, (cwd or Path.cwd()).resolve(), host)
    except DriverError as error:
        print(f"nfx:auto: {error}", file=sys.stderr, flush=True)
        return 1
    try:
        reason = run.loop()
        run.lock.remove()
        finish(run, reason, host.notifier)
    finally:
        run.lock.remove()
    return 0


if __name__ == "__main__":
    # UTF-8 whatever the console's code page, so a stop reason (`→`) or path always prints
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
