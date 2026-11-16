# Spec: spec-reading. Behaviour changes go through it.
"""The parsed model of one spec or index document, and the current body-rules version."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
LIST_ITEM_RE = re.compile(r"^-\s+")  # a list item marker straight after a header line's `>`
FIELD_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")
PART_RE = re.compile(r"^\*\*([A-Z][A-Za-z ]*?):\*\*\s?(.*)$")
POINTER_HEADING_RE = re.compile(r"^###\s+(.+?)\s+\(in\s+\[([^\]]*)\]\(([^)\s]+)\)\)\s*$")
CHANGE_HEADING_RE = re.compile(r"^###\s+(.+?)\s+\[([A-Za-z ]+)\]\s*$")
MILESTONE_HEADING_RE = re.compile(r"^###\s+Milestone\s*:(.*)$", re.IGNORECASE)


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def milestone_key(name: str) -> str:
    """A milestone name as milestone names match: backticks and asterisks removed, runs of spaces
    made one, surrounding spaces trimmed, case ignored."""
    return squash(re.sub(r"[`*]", "", name)).lower()


def milestone_slug(name: str) -> str:
    """A milestone name as branch and file names write it: `Playback and preferences` is
    `playback-and-preferences`."""
    return re.sub(r"[^a-z0-9]+", "-", milestone_key(name)).strip("-")


def find_current_version() -> int:
    template = Path(__file__).resolve().parent.parent.parent / "template.md"
    text = template.read_text(encoding="utf-8")
    match = re.search(r"\*\*Current version: v(\d+)\.\*\*", text)
    if not match:
        sys.exit(f"spec_lint: no '**Current version: vN.**' line in {template}")
    return int(match.group(1))


@dataclass(eq=False)
class Part:
    name: str
    line: int  # 1-based
    text: list[str]  # first line's remainder, then the following lines

    @property
    def content(self) -> str:
        return squash(" ".join(self.text))


@dataclass(eq=False)
class Change:
    name: str
    line: int
    status: str | None
    body: list[tuple[int, str]]  # (1-based line, text)
    parts: dict[str, Part] = field(init=False)

    def __post_init__(self) -> None:
        self.parts = parse_parts(self.body)
        self.size: int = len("\n".join(text for _, text in self.body).encode("utf-8"))


@dataclass(eq=False)
class Entry:
    name: str
    line: int
    target: str
    extra: list[tuple[int, str]]


@dataclass(eq=False)
class Milestone:
    """A `### Milestone: <name>` heading under a document's `## Not yet planned`."""
    name: str  # as the heading writes it
    line: int

    @property
    def key(self) -> str:
        return milestone_key(self.name)

    @property
    def slug(self) -> str:
        return milestone_slug(self.name)


def parse_parts(body: list[tuple[int, str]]) -> dict[str, Part]:
    parts: dict[str, Part] = {}
    current: Part | None = None
    for number, text in body:
        match = PART_RE.match(text)
        if match:
            current = Part(match.group(1).strip().lower(), number, [match.group(2)])
            parts.setdefault(current.name, current)
        elif current is not None:
            current.text.append(text)
    return parts


def split_lines(text: str) -> list[str]:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def change_key(name: str) -> str:
    return squash(name).lower()


class Doc:
    def __init__(self, path: Path, current_version: int):
        self.path = path
        self.is_index = path.name == "README.md"
        self.error: str | None = None
        try:
            raw = path.read_bytes()
            self.size: int = len(raw)
            self.lines = split_lines(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            self.size = 0
            self.lines = []
            self.error = str(exc)
        self._parse(current_version)

    @classmethod
    def from_text(cls, path: Path, text: str, current_version: int) -> Doc:
        """A document parsed from text, not read from path (for a committed version of a file)."""
        doc = cls.__new__(cls)
        doc.path = path
        doc.is_index = path.name == "README.md"
        doc.error = None
        doc.size = len(text.encode("utf-8"))
        doc.lines = split_lines(text)
        doc._parse(current_version)
        return doc

    def _parse(self, current_version: int) -> None:
        self.in_code = self._code_lines()
        self.header: dict[str, tuple[str, int]] = {}
        self.header_end = 0
        self._parse_header()
        self.version: int | None = None
        template = self.header.get("template")
        if template:
            match = re.match(r"v(\d+)\b", template[0].strip())
            if match:
                self.version = int(match.group(1))
        self.old_format = self.version is None or self.version < current_version
        self.usable = self.version == current_version  # the current version: neither old-format, above it, nor unreadable
        self.id = self.header["id"][0].strip().strip("`") if "id" in self.header else None
        self.status = self.header["status"][0].strip().strip("*").lower() if "status" in self.header else None
        self.title = self._title()
        self.sections = self._sections()
        self.pending_start = self.section_line("pending changes")
        foot = [line for line in (self.pending_start, self.section_line("not yet planned")) if line]
        self.body_end = min(foot) - 1 if foot else len(self.lines)
        self.body_size = len("\n".join(self.lines[:self.body_end]).encode("utf-8"))
        self.changes: list[Change] = []
        self.entries: list[Entry] = []
        self._parse_pending()
        self.milestones: list[Milestone] = []  # the valid headings, in order
        self.bad_milestones: list[tuple[int, str]] = []  # (line, heading text) of the others
        self._parse_milestones()

    def _code_lines(self) -> list[bool]:
        flags, inside = [], False
        for text in self.lines:
            if text.lstrip().startswith("```"):
                flags.append(True)
                inside = not inside
            else:
                flags.append(inside)
        return flags

    def _title(self) -> str:
        for text in self.lines:
            if text.startswith("# "):
                return re.sub(r"\s+—\s+Spec\s*$", "", text[2:]).strip()
        return ""

    def _parse_header(self) -> None:
        start = None
        for index, text in enumerate(self.lines[:20]):
            if text.startswith("## "):
                break
            if text.startswith(">"):
                start = index
                break
        if start is None:
            return
        index = start
        last_key = None
        while index < len(self.lines) and self.lines[index].startswith(">"):
            content = LIST_ITEM_RE.sub("", self.lines[index].lstrip(">").strip(), count=1)
            for chunk in re.split(r"\s+·\s+", content):
                match = FIELD_RE.match(chunk)
                if match:
                    key = re.sub(r"\s*\(.*\)$", "", match.group(1)).strip().lower()
                    self.header[key] = (match.group(2), index + 1)
                    last_key = key
                elif last_key:
                    value, line = self.header[last_key]
                    self.header[last_key] = (value + " · " + chunk, line)
            index += 1
        self.header_end = index

    def _sections(self) -> list[tuple[str, int]]:
        return [
            (text[3:].strip(), index + 1)
            for index, text in enumerate(self.lines)
            if text.startswith("## ") and not self.in_code[index]
        ]

    def section_line(self, name: str) -> int | None:
        for title, line in self.sections:
            if title.lower() == name:
                return line
        return None

    def section_lines(self, name: str) -> list[tuple[int, str]]:
        start = self.section_line(name)
        if start is None:
            return []
        out = []
        for index in range(start, len(self.lines)):
            text = self.lines[index]
            if text.startswith("## ") and not self.in_code[index]:
                break
            out.append((index + 1, text))
        return out

    def body_lines(self) -> list[tuple[int, str]]:
        """Lines above Pending changes, after the header, outside code fences."""
        return [
            (index + 1, self.lines[index])
            for index in range(self.header_end, self.body_end)
            if not self.in_code[index]
        ]

    def body_text(self) -> str:
        return squash(" ".join(self.lines[self.header_end:self.body_end]))

    def _parse_pending(self) -> None:
        if not self.pending_start:
            return
        blocks: list[tuple[int, str, list[tuple[int, str]]]] = []
        for index in range(self.pending_start, len(self.lines)):
            text = self.lines[index]
            if self.in_code[index]:
                if blocks:
                    blocks[-1][2].append((index + 1, text))
                continue
            if text.startswith("## "):
                break
            if text.startswith("### "):
                blocks.append((index + 1, text, []))
            elif blocks:
                blocks[-1][2].append((index + 1, text))
        for line, heading, body in blocks:
            pointer = POINTER_HEADING_RE.match(heading)
            if pointer:
                extra = [(n, t) for n, t in body if t.strip()]
                self.entries.append(Entry(pointer.group(1), line, pointer.group(3), extra))
                continue
            change = CHANGE_HEADING_RE.match(heading)
            if change:
                self.changes.append(Change(change.group(1), line, change.group(2).strip().lower(), body))
            else:
                self.changes.append(Change(heading[4:].strip(), line, None, body))

    def _parse_milestones(self) -> None:
        """The milestone headings of *Not yet planned*: a `### ` heading that starts with
        `Milestone` and has no name or slug is not one (it is recorded as bad)."""
        for number, text in self.section_lines("not yet planned"):
            if self.in_code[number - 1] or not text.startswith("### "):
                continue
            match = MILESTONE_HEADING_RE.match(text)
            if match and milestone_slug(match.group(1)):
                self.milestones.append(Milestone(match.group(1).strip(), number))
            elif text[4:].lstrip().lower().startswith("milestone"):
                self.bad_milestones.append((number, text[4:].strip()))

    def build_parts(self) -> dict[str, Part]:
        """The parts (**Milestone:**, **Delegation:**) of an unbuilt spec's `## Build` section."""
        return parse_parts(self.section_lines("build"))

    def blocked_by(self) -> str | None:
        """The header Blocked by as one comma-separated text (a line break reads as a comma)."""
        value = self.header.get("blocked by")
        return value[0].replace(" · ", ", ") if value else None

    def links(self, lines: list[tuple[int, str]]) -> list[tuple[int, str, Path | None]]:
        out = []
        for number, text in lines:
            for match in LINK_RE.finditer(text):
                out.append((number, match.group(2), self.resolve(match.group(2))))
        return out

    def resolve(self, target: str) -> Path | None:
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
            return None
        target = unquote(target.split("#", 1)[0])
        if not target:
            return None
        return Path(os.path.normpath(self.path.parent / target))

