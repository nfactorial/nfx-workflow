# Spec: spec-lint. Behaviour changes go through it.
"""Pending-change checks: the changes, their items, Read first, Delegation and pointer entries."""

from __future__ import annotations

import re
from pathlib import Path

from ..discovery import norm_key
from ..document import LINK_RE, Change, Doc, Entry, Part, change_key, milestone_key, squash
from .blockers import check_blocked_by
from .findings import QUOTE_RE, SIZE_LIMIT, STATUSES, Context, check_delegation, check_read_first

ITEM_RE = re.compile(r"^-\s+\*\*(Add|Replace|Remove)\*\*\s*(?:\(([^)]*)\))?")
PLANNED_LIMIT = 2


def check_pending(ctx: Context, doc: Doc) -> None:
    """The checks over a spec's Pending changes: each change, its size and count, each entry,
    and the **Milestone:** part of an unbuilt spec's `## Build` section."""
    f = ctx.findings
    for change in doc.changes:
        if change.size > SIZE_LIMIT:
            f.warn("T-size", doc.path, change.line, f"change is {change.size // 1024} KB, well "
                                                    "past ~15 KB: is it one session's work?")
    planned = [c for c in doc.changes if "milestone" not in c.parts]  # a milestone is planned as a set
    if len(planned) > PLANNED_LIMIT:
        f.warn("L-just-in-time", doc.path, doc.pending_start,
               f"{len(planned)} planned changes: is each next or nearly next?")
    build = doc.build_parts().get("milestone")
    if build and doc.status != "built":
        check_milestone_part(ctx, doc, build)
    for change in doc.changes:
        check_change(ctx, doc, change)
    for entry in doc.entries:
        check_entry(ctx, doc, entry)


def check_change(ctx: Context, doc: Doc, change: Change) -> None:
    f = ctx.findings
    if change.status is None:
        f.error("T-minimum", doc.path, change.line,
                "change heading has no status tag ([draft] or [ready])")
    elif change.status not in STATUSES:
        f.error("T-minimum", doc.path, change.line, f"status '{change.status}' is not draft or ready")
    for name in ("blocked by", "brief", "changes", "done when"):
        if name not in change.parts:
            f.error("T-minimum", doc.path, change.line,
                    f"change '{change.name}' has no **{name.capitalize()}:**")
    delegation = change.parts.get("delegation")
    if delegation:
        check_delegation(ctx, doc, delegation)
    questions = change.parts.get("unanswered questions")
    if change.status == "ready" and questions:
        content = questions.content.strip("*_ ").lower()
        if content and content not in ("none", "none."):
            f.error("L-ready", doc.path, questions.line, "a ready change has unanswered questions")
    if "milestone" in change.parts:
        check_milestone_part(ctx, doc, change.parts["milestone"])
    blocked = change.parts.get("blocked by")
    blocker_keys: set[str] = set()
    if blocked:
        lines = [(blocked.line + i, t) for i, t in enumerate(blocked.text)]
        blocker_keys = check_blocked_by(ctx, doc, blocked.content, lines, False)
    if "read first" in change.parts:
        check_read_first(ctx, doc, change.parts["read first"])
    if "changes" in change.parts:
        check_items(ctx, doc, change, change.parts["changes"], blocker_keys, blocked)


def check_milestone_part(ctx: Context, doc: Doc, part: Part) -> None:
    """A **Milestone:** part links one milestone of a document by its name (T-milestone)."""
    f = ctx.findings
    links = list(LINK_RE.finditer(" ".join(part.text)))
    if len(links) != 1:
        f.error("T-milestone", doc.path, part.line, "give one link to the milestone")
        return
    label, target = links[0].group(1).strip(), links[0].group(2)
    path = doc.resolve(target)
    home = ctx.specs.doc(path) if path is not None else None
    if home is None:
        f.error("T-milestone", doc.path, part.line, f"'{target}' is not a file")
    elif home.usable and not any(m.key == milestone_key(label) for m in home.milestones):
        f.error("T-milestone", doc.path, part.line, f"no milestone '{label}' in {target}")


def check_items(ctx: Context, doc: Doc, change: Change, part: Part, blocker_keys: set[str],
                blocked: Part | None) -> None:
    f = ctx.findings
    items: list[tuple[int, str]] = []
    for offset, text in enumerate(part.text):
        if offset == 0 and not text.strip():
            continue
        if text.startswith("- "):
            items.append((part.line + offset, text))
        elif items and text.strip():
            items[-1] = (items[-1][0], items[-1][1] + " " + text.strip())
    if not items and part.content:
        items.append((part.line, "- " + part.content))
    edited: dict[str, Doc] = {}
    for number, text in items:
        match = ITEM_RE.match(text)
        if not match:
            f.error("T-marks", doc.path, number, "Changes item is not marked Add, Replace or Remove")
            continue
        kind, section = match.group(1), match.group(2)
        if not section or not section.strip():
            f.error("T-marks", doc.path, number, f"{kind} item names no section")
            continue
        target = doc
        if "›" in section:
            named = ctx.specs.spec_by_name(section.split("›", 1)[0], doc)
            if named is not None:
                target = named
        if norm_key(target.path) != norm_key(doc.path):
            edited[norm_key(target.path)] = target
        if kind == "Add" or not target.usable:
            continue
        quote = QUOTE_RE.search(text[match.end():])
        if not quote:
            f.warn("T-marks", doc.path, number, f"{kind} item: could not find its quoted text")
            continue
        old = quote.group(1) if quote.group(1) is not None else quote.group(2)
        old = squash(re.sub(r"\\(.)", r"\1", old))
        fragments = [p.strip() for p in re.split(r"…|\.\.\.", old) if p.strip()]
        body = target.body_text()
        whole = squash(" ".join(target.lines))
        if all(fr in body for fr in fragments):
            continue
        where = "its own spec" if target is doc else f.show(target.path)
        if all(fr in whole for fr in fragments):
            f.warn("T-marks", doc.path, number, f"{kind} quote is not in the body of {where} "
                                                "(only in a pending change)")
        else:
            f.error("T-marks", doc.path, number, f"{kind} quote does not appear verbatim in {where}")
    for key, target in edited.items():
        back = [e for e in target.entries
                if change_key(e.name) == change_key(change.name)
                and norm_key(target.resolve(e.target) or Path()) == norm_key(doc.path)]
        if target.usable and not back:
            f.error("T-change", doc.path, change.line,
                    f"change edits {f.show(target.path)}, which has no one-line entry for it "
                    "under Pending changes")
        if blocked is not None and key not in blocker_keys:
            f.warn("T-change", doc.path, blocked.line,
                   f"Blocked by does not include {f.show(target.path)}, which this change edits")


def check_entry(ctx: Context, doc: Doc, entry: Entry) -> None:
    f = ctx.findings
    home_path = doc.resolve(entry.target)
    home = ctx.specs.doc(home_path)
    if home is None:
        f.error("T-change", doc.path, entry.line, f"entry links '{entry.target}', which does not resolve")
        return
    if home.usable and not any(change_key(c.name) == change_key(entry.name) for c in home.changes):
        f.error("T-change", doc.path, entry.line,
                f"entry names a change '{entry.name}' that {f.show(home.path)} does not hold")
    if entry.extra:
        f.warn("T-change", doc.path, entry.extra[0][0], "an entry is one line: the change lives "
                                                       "in its home spec")
