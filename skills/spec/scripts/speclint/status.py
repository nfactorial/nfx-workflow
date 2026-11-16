# Spec: status-mode. Behaviour changes go through it.
"""Status mode: the walk of the paths given (or, for one milestone, every known document searched
for its items), each spec's and change's place in the five groups, and their report as text or
JSON."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .blockers import ChangeHistory, read_blocker, split_entries
from .discovery import Specs, has_index, indexed_subfolder, is_link, norm_key
from .document import (LINK_RE, Change, Doc, Milestone, Part, change_key, milestone_key,
                       squash)


Node = tuple[str, str | None]  # a spec's `norm_key` and, for one of its changes, its `change_key`


@dataclass
class Pick:
    """A spec, whether the spec itself is an item, and which of its changes are."""
    doc: Doc
    spec_item: bool
    changes: list[Change]


@dataclass
class Blocker:
    text: str
    target: str | None  # the path of the document the entry names, as the output writes paths
    built: bool
    in_milestone: bool = False


@dataclass
class Item:
    spec: str
    id: str | None
    change: str | None
    status: str | None
    delegation: str | None
    blockers: list[Blocker]


@dataclass
class Convert:
    spec: str
    id: str | None


@dataclass
class Planned:
    file: str
    line: int
    text: str
    milestone: str | None  # the name of the milestone heading the line sits under, if it is one


@dataclass
class Skipped:
    """A document status mode could not read: its path as the output writes it, and why."""
    file: str
    reason: str


@dataclass
class Refusal:
    """One reason a milestone run refuses to start: `reason` is `not ready` (`detail` the item's
    status, none when missing), `old-format` (the spec is in *Needs conversion*), `blocked`
    (`detail` the text of a blocker that is not built and not in the milestone), `not yet
    planned` (`spec` the file, `detail` the line's text) or `skipped` (`spec` the document,
    `detail` why it was skipped)."""
    reason: str
    spec: str
    change: str | None
    detail: str | None


@dataclass
class Waiting:
    """A spec or change that waits, through some chain of *Blocked by*, on the changes given."""
    spec: str
    change: str | None


@dataclass
class Report:
    """The groups of a status run, the milestone reported (if any) and the documents skipped."""
    ready: list[Item]
    blocked: list[Item]
    draft: list[Item]
    convert: list[Convert]
    not_yet_planned: list[Planned]
    milestone: Milestone | None
    skipped: list[Skipped]


class Scope:
    """One milestone of a feature: its document, and the specs and changes found to be its items
    (recorded by `pick`)."""

    def __init__(self, doc: Doc, milestone: Milestone):
        self.doc = doc
        self.milestone = milestone
        self._specs: set[str] = set()
        self._changes: set[tuple[str, str]] = set()

    def _links(self, doc: Doc, text: str) -> bool:
        """Whether the text, in `doc`, links this milestone's document under its name."""
        for match in LINK_RE.finditer(text):
            target = doc.resolve(match.group(2))
            if (target and milestone_key(match.group(1)) == self.milestone.key
                    and norm_key(target.resolve()) == norm_key(self.doc.path)):
                return True
        return False

    def _names(self, doc: Doc, part: Part | None) -> bool:
        """Whether a **Milestone:** part of `doc` links this milestone's document under its name."""
        return part is not None and self._links(doc, " ".join(part.text))

    def mentions(self, doc: Doc) -> bool:
        """Whether any line of `doc` links this milestone's document under its name: how an
        old-format spec, whose parts are not read, is found to hold milestone work."""
        return any(self._links(doc, text) for text in doc.lines)

    def pick(self, doc: Doc) -> Pick:
        """The items of this milestone in a current-format spec, recorded as its items."""
        build = doc.build_parts().get("milestone")
        spec_item = doc.status != "built" and self._names(doc, build)
        changes = [c for c in doc.changes if self._names(doc, c.parts.get("milestone"))]
        if spec_item:
            self._specs.add(norm_key(doc.path))
        self._changes.update((norm_key(doc.path), change_key(c.name)) for c in changes)
        return Pick(doc, spec_item, changes)

    def has(self, doc: Doc, change: str | None = None) -> bool:
        """Whether the spec, or its change when one is named, is an item picked so far."""
        if change is None:
            return norm_key(doc.path) in self._specs
        return (norm_key(doc.path), change_key(change)) in self._changes

    def lines(self) -> list[tuple[int, str]]:
        """The lines under the first heading of this milestone in the document's *Not yet
        planned*, up to the next `### ` heading (a later heading of the same name starts no
        second run)."""
        out: list[tuple[int, str]] = []
        inside = False
        for number, text in self.doc.section_lines("not yet planned"):
            if self.doc.in_code[number - 1]:
                continue
            if text.startswith("### "):
                inside = number == self.milestone.line
            elif inside:
                out.append((number, text))
        return out


class Status:
    """What is ready, blocked, draft or waiting for conversion under some paths, or in one
    milestone of a feature wherever its items live (L-ready)."""

    def __init__(self, specs: Specs):
        self.specs = specs
        self.history = ChangeHistory(specs.current)
        self.files: set[str] = set()
        self.folders: set[str] = set()
        self.order: list[Path] = []
        self.old_blockers: dict[str, Doc] = {}  # old-format blocking specs, first dependant first
        self.scope: Scope | None = None  # the milestone being reported, if any

    # -- walk --------------------------------------------------------------------------------

    def walk(self, paths: list[Path]) -> list[Path]:
        for path in paths:
            path = path.resolve()
            if path.is_dir():
                self._walk_folder(path)
            else:
                self._add(path)
        return self.order

    def _add(self, path: Path) -> None:
        key = norm_key(path)
        if key not in self.files:
            self.files.add(key)
            self.order.append(path)

    def _walk_folder(self, folder: Path) -> None:
        key = norm_key(folder)
        if key in self.folders:
            return
        self.folders.add(key)
        index = folder / "README.md"
        if has_index(folder):
            self._add(index)
            doc = self.specs.doc(index)
            if doc and not self.specs.skip_reason(doc):
                for _, _, target in doc.links(doc.section_lines("specs")):
                    if target is None or target.suffix.lower() != ".md" or not target.is_file():
                        continue
                    sub = indexed_subfolder(folder, target)
                    if sub:
                        self._walk_folder(sub)
                    else:
                        self._add(target.resolve())
        entries = sorted(folder.iterdir(), key=lambda p: p.name.lower())
        for path in entries:
            if path.is_file() and path.suffix.lower() == ".md":
                self._add(path)
        for path in entries:
            if (path.is_dir() and not path.name.startswith(".") and path.name != "node_modules"
                    and not is_link(path)):
                self._walk_folder(path)

    # -- items -------------------------------------------------------------------------------

    def resolved(self, path: Path | None) -> Doc | None:
        """The spec at path when status mode can read it; an old-format one is noted to convert."""
        doc = self.specs.doc(path)
        if doc is None or doc.is_index or self.specs.skip_reason(doc):
            return None
        if doc.old_format:
            self.old_blockers.setdefault(norm_key(doc.path), doc)
        return doc

    def blocker(self, doc: Doc, entry: str) -> Blocker | None:
        ref = read_blocker(self.specs, doc, entry)
        if ref is None:
            return None
        target = self.specs.show(ref.spec.path) if ref.spec else None
        spec = self.resolved(ref.spec.path) if ref.spec else None
        if spec is None:
            return Blocker(ref.text, target, False)
        if ref.change is not None:
            return Blocker(ref.text, target, self.history.built(spec, ref.change),
                           self.in_milestone(spec, ref.change))
        return Blocker(ref.text, target, spec.status == "built", self.in_milestone(spec))

    def in_milestone(self, spec: Doc, change: str | None = None) -> bool:
        """Whether the spec (or its change) is an item of the milestone being reported."""
        return self.scope is not None and self.scope.has(spec, change)

    def blockers(self, doc: Doc, value: str | None) -> list[Blocker]:
        found = (self.blocker(doc, entry) for entry in split_entries(value or ""))
        return [b for b in found if b]

    def item(self, doc: Doc, change: Change | None) -> Item:
        shown = self.specs.show(doc.path)
        if change is None:
            build = doc.build_parts().get("delegation")
            joined = doc.blocked_by()
            return Item(shown, doc.id, None, doc.status, build.content or None if build else None,
                        self.blockers(doc, joined))
        part = change.parts.get("blocked by")
        blockers = self.blockers(doc, part.content if part else None)
        if doc.status != "built":
            blockers.append(Blocker(doc.id or shown, shown, False, self.in_milestone(doc)))
        delegation = change.parts.get("delegation")
        return Item(shown, doc.id, change.name, change.status,
                    delegation.content or None if delegation else None, blockers)

    def references(self, doc: Doc, value: str | None) -> set[Node]:
        """What the entries of a *Blocked by* value of `doc` name: a spec, or one of its changes."""
        out: set[Node] = set()
        for entry in split_entries(value or ""):
            ref = read_blocker(self.specs, doc, entry)
            if ref is not None and ref.spec is not None:
                out.add((norm_key(ref.spec.path),
                         None if ref.change is None else change_key(ref.change)))
        return out

    def not_yet_planned(self, doc: Doc, lines: list[tuple[int, str]],
                        under: str | None = None) -> list[Planned]:
        """The `- ` lines among `lines` (a section of `doc`), each running to the next or a blank,
        with the milestone heading it sits under; `under` is the milestone `lines` start in."""
        out: list[Planned] = []
        current: list[str] = []
        line = 0
        milestone = under  # of the line being read
        item_milestone = under  # of the item being collected
        names = {m.line: m.name for m in doc.milestones}
        shown = self.specs.show(doc.path)
        for number, text in lines + [(0, "")]:
            if number and doc.in_code[number - 1]:
                continue
            if text.startswith("### "):
                milestone = names.get(number)
            starts = text.startswith("- ")
            if current and (starts or not text.strip()):
                out.append(Planned(shown, line, squash(" ".join(current)), item_milestone))
                current = []
            if starts:
                line = number
                item_milestone = milestone
                current = [text[2:]]
            elif text.strip() and current:
                current.append(text)
        return out

    # -- report ------------------------------------------------------------------------------

    def open_milestone(self, path: Path, name: str) -> Scope | str:
        """The milestone's scope, or the problem with the path or the milestone."""
        path = path.resolve()
        if path.is_dir():
            if not has_index(path):
                return f"{self.specs.show(path)} holds no README.md"
            path = path / "README.md"
        elif path.suffix.lower() != ".md" or path.name == "README.md":
            return f"{self.specs.show(path)} is not a spec file (give the feature folder or a spec)"
        doc = self.specs.doc(path)
        if doc is None:
            return f"{self.specs.show(path)} is not a file"
        reason = self.specs.skip_reason(doc)
        if reason:
            return f"cannot read {self.specs.show(path)}: {reason}"
        key = milestone_key(name)
        milestone = next((m for m in doc.milestones if m.key == key), None)
        if milestone is None:
            return (f"{self.specs.show(path)} has no '### Milestone: {name}' heading under its "
                    "Not yet planned")
        return Scope(doc, milestone)

    def documents(self, paths: list[Path]) -> list[Path]:
        """The documents to look at: the walk of the paths, then, for a milestone, every other
        known document by path (its items may live anywhere)."""
        ordered = list(self.walk(paths))
        if self.scope is not None:
            seen = {norm_key(p) for p in ordered}
            ordered += sorted((p for k, p in self.specs.known.items() if k not in seen), key=norm_key)
        return ordered

    def readable(self, paths: list[Path], skipped: list[Skipped]) -> list[Doc]:
        """The documents at the paths that status mode can read; the others go to `skipped`."""
        out = []
        for path in paths:
            doc = self.specs.doc(path)
            if doc is None:
                continue
            reason = self.specs.skip_reason(doc)
            if reason:
                skipped.append(Skipped(self.specs.show(doc.path), reason))
            else:
                out.append(doc)
        return out

    def picks(self, docs: list[Doc]) -> list[Pick]:
        """The specs with the items they hold: an unbuilt spec and its changes, or, for a
        milestone, only those it names. An old-format spec's items are not judged."""
        specs = [d for d in docs if not d.is_index and not d.old_format]
        if self.scope is None:
            return [Pick(d, d.status != "built", d.changes) for d in specs]
        return [self.scope.pick(d) for d in specs]

    def not_yet_planned_lines(self, docs: list[Doc]) -> list[Planned]:
        """Every *Not yet planned* line of the documents, or the milestone's own."""
        if self.scope is not None:
            return self.not_yet_planned(self.scope.doc, self.scope.lines(),
                                        self.scope.milestone.name)
        return [p for d in docs for p in self.not_yet_planned(d, d.section_lines("not yet planned"))]

    def waiting(self, paths: list[Path], given: list[Node],
                skipped: list[Skipped]) -> list[Waiting]:
        """Every spec and change among the items under the paths that waits, through any chain
        of *Blocked by*, on the `given` specs and changes (a change waits on its own spec while
        that spec is not built). A given one is listed only when it waits on another."""
        found: list[tuple[Node, Waiting, set[Node]]] = []
        for pick in self.picks(self.readable(self.documents(paths), skipped)):
            doc, key, shown = pick.doc, norm_key(pick.doc.path), self.specs.show(pick.doc.path)
            if pick.spec_item:
                found.append(((key, None), Waiting(shown, None),
                              self.references(doc, doc.blocked_by())))
            for change in pick.changes:
                part = change.parts.get("blocked by")
                refs = self.references(doc, part.content if part else None)
                if doc.status != "built":
                    refs.add((key, None))
                found.append(((key, change_key(change.name)), Waiting(shown, change.name), refs))
        waits: set[Node] = set(given)  # what is waited on, growing by what waits on it
        listed: set[Node] = set()
        grown = True
        while grown:
            grown = False
            for node, _, refs in found:
                if node not in listed and refs & waits:
                    listed.add(node)
                    waits.add(node)
                    grown = True
        return [w for node, w, _ in found if node in listed]

    def report(self, paths: list[Path], milestone: str | None = None) -> Report | str:
        """The report for the paths, or for the named milestone of the feature at `paths[0]`; the
        message naming the problem when that milestone cannot be opened. Writes nothing."""
        if milestone is not None:
            found = self.open_milestone(paths[0], milestone)
            if isinstance(found, str):
                return found
            self.scope = found
        skipped: list[Skipped] = []
        docs = self.readable(self.documents(paths), skipped)
        report = Report([], [], [], [], self.not_yet_planned_lines(docs),
                        self.scope.milestone if self.scope else None, skipped)
        picks = self.picks(docs)  # all picked before any item is built: a blocker may name a later one
        # a milestone does not search old-format specs for items: it lists those that mention it
        old = [d for d in docs if not d.is_index and d.old_format
               and (self.scope is None or self.scope.mentions(d))]
        report.convert += [Convert(self.specs.show(d.path), d.id) for d in old]
        for pick in picks:
            items = ([self.item(pick.doc, None)] if pick.spec_item else []) + [
                self.item(pick.doc, c) for c in pick.changes]
            for item in items:
                if item.status != "ready":
                    report.draft.append(item)
                elif all(b.built or b.in_milestone for b in item.blockers):
                    report.ready.append(item)
                else:
                    report.blocked.append(item)
        walked = {norm_key(d.path) for d in old}
        for key, doc in self.old_blockers.items():
            if key not in walked:
                report.convert.append(Convert(self.specs.show(doc.path), doc.id))
        return report


def refusals(report: Report) -> list[Refusal]:
    """Each reason a milestone run refuses to start on this report of the milestone: an item
    not ready, a blocker outside the milestone that is not built, an old-format spec, a
    *Not yet planned* line under the milestone, a document skipped."""
    out = [Refusal("not ready", i.spec, i.change, i.status) for i in report.draft]
    out += [Refusal("blocked", i.spec, i.change, b.text) for i in report.blocked
            for b in i.blockers if not b.built and not b.in_milestone]
    out += [Refusal("old-format", c.spec, None, None) for c in report.convert]
    out += [Refusal("not yet planned", p.file, None, p.text) for p in report.not_yet_planned]
    out += [Refusal("skipped", k.file, None, k.reason) for k in report.skipped]
    return out


def format_json(report: Report) -> str:
    """The report as the JSON object: the five groups, and the milestone when one was reported."""
    out: dict[str, object] = {
        "ready": [asdict(e) for e in report.ready],
        "blocked": [asdict(e) for e in report.blocked],
        "draft": [asdict(e) for e in report.draft],
        "convert": [asdict(e) for e in report.convert],
        "not_yet_planned": [asdict(e) for e in report.not_yet_planned],
    }
    if report.milestone is not None:
        out["milestone"] = {"name": report.milestone.name, "slug": report.milestone.slug}
    return json.dumps(out, ensure_ascii=False, indent=2)


def _item_line(item: Item) -> str:
    return "  " + item.spec + (f" › {item.change}" if item.change else "")


def _ready_lines(item: Item) -> list[str]:
    lines = [_item_line(item)]
    if item.delegation:
        lines.append(f"    delegation: {item.delegation}")
    return lines


def _blocked_lines(item: Item) -> list[str]:
    return [_item_line(item), "    blocked by: " + ", ".join(
        f"{b.text}{' (in milestone)' if b.in_milestone else ''} "
        f"({'built' if b.built else 'not built'})" for b in item.blockers)]


def _group(title: str, lines: list[str]) -> list[str]:
    """A group's title and entry lines followed by a blank line; nothing when it has no entries."""
    return [f"{title}:", *lines, ""] if lines else []


def format_text(report: Report) -> str:
    """The text report: each non-empty group under its title, then the summary line."""
    lines: list[str] = []
    lines += _group("Ready now", [line for i in report.ready for line in _ready_lines(i)])
    lines += _group("Blocked", [line for i in report.blocked for line in _blocked_lines(i)])
    lines += _group("Draft", [_item_line(i) for i in report.draft])
    lines += _group("Needs conversion", [f"  {c.spec}" for c in report.convert])
    lines += _group("Not yet planned",
                    [f"  {p.file}:{p.line} {p.text}" for p in report.not_yet_planned])
    lines.append(f"spec_lint --status: {len(report.ready)} ready, {len(report.blocked)} blocked, "
                 f"{len(report.draft)} draft, {len(report.convert)} to convert, "
                 f"{len(report.not_yet_planned)} not yet planned")
    return "\n".join(lines)


def parse_given(arg: str) -> tuple[Path, str | None]:
    """A `--waiting` argument: a spec path, or a spec path, ` › ` and a change name."""
    path, sep, change = arg.partition(" › ")
    return Path(path.strip().replace("\\", "/")), (change.strip() or None) if sep else None


def main(argv: list[str]) -> int:
    """Status mode for the command-line arguments `argv` (those after `spec_lint.py`, `--status`
    among them). Prints the report to stdout, each message and `skipped` line to stderr, and
    returns the exit code."""
    args = list(argv)
    milestone = None
    if args.count("--milestone") > 1 or any(a.startswith("--milestone=") for a in args):
        print("spec_lint --status: give --milestone once, as '--milestone <name>'", file=sys.stderr)
        return 2
    if "--milestone" in args:
        at = args.index("--milestone")
        value = args[at + 1] if at + 1 < len(args) else ""
        del args[at:at + 2]
        if not milestone_key(value):
            print(f"spec_lint --status: --milestone needs a milestone name, not '{value}'",
                  file=sys.stderr)
            return 2
        milestone = value
    given: list[str] | None = None
    if "--waiting" in args:  # takes every argument up to the next option
        at = args.index("--waiting")
        end = next((i for i in range(at + 1, len(args)) if args[i].startswith("--")), len(args))
        given = args[at + 1:end]
        del args[at:end]
        if not given:
            print("spec_lint --status: --waiting needs at least one spec or change", file=sys.stderr)
            return 2
    if given is not None and milestone is not None:
        print("spec_lint --status: --waiting does not go with --milestone", file=sys.stderr)
        return 2
    if "--refusals" in args and milestone is None:
        print("spec_lint --status: --refusals goes with --milestone, and not with --waiting",
              file=sys.stderr)
        return 2
    paths = [Path(a.replace("\\", "/")) for a in args
             if a not in ("--status", "--json", "--refusals")]
    if not paths:
        print("spec_lint --status: give at least one spec file or folder", file=sys.stderr)
        return 2
    for path in paths:
        if not path.exists():
            print(f"spec_lint --status: no such file or folder: {path.as_posix()}", file=sys.stderr)
            return 2
    if milestone is not None and len(paths) != 1:
        print("spec_lint --status: --milestone takes exactly one feature folder or spec file",
              file=sys.stderr)
        return 2
    status = Status(Specs(paths, Path.cwd().resolve()))
    skipped: list[Skipped] = []
    if given is not None:
        nodes: list[Node] = []
        for arg in given:
            path, change = parse_given(arg)
            if not path.is_file():
                print(f"spec_lint --status: no such spec: {path.as_posix()}", file=sys.stderr)
                return 2
            nodes.append((norm_key(path.resolve()), None if change is None else change_key(change)))
        text = json.dumps({"waiting": [asdict(w) for w in status.waiting(paths, nodes, skipped)]},
                          ensure_ascii=False, indent=2)
    else:
        report = status.report(paths, milestone)
        if isinstance(report, str):
            print(f"spec_lint --status: {report}", file=sys.stderr)
            return 2
        skipped = report.skipped
        if "--refusals" in args:
            text = json.dumps({"refusals": [asdict(r) for r in refusals(report)]},
                              ensure_ascii=False, indent=2)
        else:
            text = format_json(report) if "--json" in args else format_text(report)
    for item in skipped:
        print(f"spec_lint --status: skipped {item.file}: {item.reason}; lint it", file=sys.stderr)
    print(text)
    return 0
