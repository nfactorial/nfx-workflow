# Spec: spec-reading. Behaviour changes go through it.
"""The one reading of a Blocked by entry: what it names, why it cannot be
read as a blocker if it cannot, and whether a change it names was ever held by its spec."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .discovery import Specs, git, norm_key
from .document import LINK_RE, Doc, change_key

# `[label](target)`, then optionally ` › ` and a change name in backticks: the only forms T-refs allows.
BLOCKER_LINK_RE = re.compile(r"^\[([^\]]*)\]\(([^)\s]+)\)\s*(?:›\s*`([^`]*)`)?$")


def git_files(root: Path, requests: list[str]) -> list[str | None]:
    """The text of each `<commit>:<path>` through one `git cat-file --batch`; None where git has none."""
    try:
        result = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"],
                                input="".join(r + "\n" for r in requests).encode("utf-8"),
                                capture_output=True)
    except OSError:
        return [None] * len(requests)
    out, data, at = [], result.stdout, 0
    for _ in requests:
        end = data.find(b"\n", at)
        if end < 0:
            out.append(None)
            continue
        fields = data[at:end].split()
        at = end + 1
        if len(fields) == 3 and fields[1] == b"blob":
            size = int(fields[2])
            out.append(data[at:at + size].decode("utf-8", errors="replace"))
            at += size + 1
        else:
            out.append(None)
    return out


@dataclass
class LinkRead:
    """One link inside a Blocked by entry, and what it points at."""
    target: str
    path: Path | None
    state: Literal["spec", "not a spec", "does not resolve", "no target"]

    @property
    def problem(self) -> Literal["not a spec", "does not resolve"] | None:
        """Why an entry opening with this link cannot be read as a blocker; None when it can."""
        if self.state == "spec":
            return None
        if self.state == "not a spec":
            return "not a spec"
        return "does not resolve"


@dataclass
class BlockerRead:
    """One Blocked by entry as `read_blocker` reads it.

    `text` is how the blocker is shown. `spec` is the document the entry names, when
    there is one, and `change` the change it names, if any. `problem` is why spec_lint cannot
    read the entry as a blocker, if it cannot. `links` are every link the entry holds, however
    it reads."""
    raw: str
    text: str
    change: str | None
    spec: Doc | None
    problem: Literal["unreadable", "not a spec", "does not resolve"] | None
    links: list[LinkRead]


@dataclass
class VersionWalk:
    """One spec's committed versions, read newest first as far as the questions asked needed.

    `requests` are the `<commit>:<path>` of every version; `next` is how many have been read and
    `held` the keys of the changes those held."""
    requests: list[str]
    held: set[str]
    next: int = 0
    batch: int = 1  # size of the next batch


class ChangeHistory:
    """Which changes a spec's committed versions held. A spec's commit list is read once per
    run and each version at most once, newest first, only as far as the question needs."""

    def __init__(self, current_version: int):
        self.current = current_version
        self.walks: dict[str, VersionWalk | None] = {}

    def _walk(self, doc: Doc) -> VersionWalk | None:
        """The spec's version walk; None when git has no history to read."""
        key = norm_key(doc.path)
        if key not in self.walks:
            log = git(doc.path.parent, "-c", "core.quotePath=false", "log", "--follow",
                      "--format=@@%H", "--name-only", "--", doc.path.name)
            walk = None
            if log and log.strip():
                requests, commit = [], None
                for line in log.splitlines():
                    if line.startswith("@@"):
                        commit = line[2:]
                    elif line.strip() and commit:
                        requests.append(f"{commit}:{line.strip()}")
                        commit = None
                walk = VersionWalk(requests, set())
            self.walks[key] = walk
        return self.walks[key]

    def _read_batch(self, doc: Doc, walk: VersionWalk) -> None:
        """Read the next batch of versions into `walk`, then double the batch size. The first two
        batches are one version each, so a change the newest versions held costs only those."""
        size = walk.batch
        batch = walk.requests[walk.next:walk.next + size]
        walk.next += len(batch)
        if walk.next > 1:
            walk.batch = size * 2
        for text in git_files(doc.path.parent, batch):
            if text is not None:  # a version git can't read adds nothing: stay conservative
                old = Doc.from_text(doc.path, text, self.current)
                walk.held |= {change_key(c.name) for c in old.changes}
                walk.held |= {change_key(e.name) for e in old.entries}

    def _ever_held(self, doc: Doc, name: str) -> bool | None:
        """Whether any committed version held the change; None when git has no history to read."""
        walk = self._walk(doc)
        if walk is None:
            return None
        key = change_key(name)
        while key not in walk.held and walk.next < len(walk.requests):
            self._read_batch(doc, walk)
        return key in walk.held

    @staticmethod
    def holds(doc: Doc, name: str) -> bool:
        key = change_key(name)
        return any(change_key(c.name) == key for c in doc.changes) or any(
            change_key(e.name) == key for e in doc.entries)

    def never_held(self, doc: Doc, name: str) -> bool:
        """The spec neither holds the change nor, where git can say, ever held it."""
        if doc.old_format or self.holds(doc, name):
            return False
        return self._ever_held(doc, name) is False

    def built(self, doc: Doc, name: str) -> bool:
        """Folded: the spec no longer holds the change and (where git can say) once did."""
        return not (doc.old_format or self.holds(doc, name) or self.never_held(doc, name))


def split_entries(text: str) -> list[str]:
    """Split a Blocked by value on commas outside brackets, parentheses and code spans (from a
    backtick to the next one; an unclosed one runs to the end)."""
    out, depth, in_code, current = [], 0, False, ""
    for char in text:
        if char == "`":
            in_code = not in_code
        elif not in_code:
            if char in "[(":
                depth += 1
            elif char in "])":
                depth = max(0, depth - 1)
        if char == "," and depth == 0 and not in_code:
            out.append(current)
            current = ""
        else:
            current += char
    out.append(current)
    return out


def read_link(specs: Specs, doc: Doc, target: str) -> LinkRead:
    path = doc.resolve(target)
    if path is None:
        return LinkRead(target, None, "no target")
    if not path.is_file():
        return LinkRead(target, path, "does not resolve")
    return LinkRead(target, path, "spec" if specs.is_spec(path) else "not a spec")


def read_blocker(specs: Specs, doc: Doc, entry: str) -> BlockerRead | None:
    """Read one Blocked by entry of `doc`; None for an empty entry or `none`. Every reader of
    an entry reads it through this, so they agree on every one."""
    raw = entry.strip().strip("*").strip().rstrip(".").strip()
    if not raw or raw.lower() == "none":
        return None
    links = [read_link(specs, doc, m.group(2)) for m in LINK_RE.finditer(raw)]
    link = BLOCKER_LINK_RE.match(raw)
    change = link.group(3).strip() if link and link.group(3) is not None else None
    if not link or change == "":
        return BlockerRead(raw, raw, None, None, "unreadable", links)
    first = links[0]  # the entry opens with this link
    label = link.group(1).strip() or link.group(2)
    return BlockerRead(raw, label if change is None else f"{label} › {change}", change,
                       specs.doc(first.path), first.problem, links)
