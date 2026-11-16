# Spec: spec-lint. Behaviour changes go through it.
"""The checks of a Blocked by field: the T-refs findings for its entries, and the specs a
header Blocked by names. Entries are read by `read_blocker`, and the changes they name are
looked up in `ChangeHistory`."""

from __future__ import annotations

from ..blockers import read_blocker, split_entries
from ..discovery import Specs, norm_key
from ..document import Doc
from .findings import Context


def header_blocker_docs(specs: Specs, doc: Doc) -> list[Doc]:
    """The specs the readable entries of a spec's header Blocked by name, as `read_blocker`
    reads them. An entry it cannot read, and a link to no spec, names none."""
    text = doc.blocked_by()
    if text is None:
        return []
    refs = (read_blocker(specs, doc, entry) for entry in split_entries(text))
    return [ref.spec for ref in refs if ref and ref.problem is None and ref.spec is not None]


def check_blocked_by(ctx: Context, doc: Doc, text: str, lines: list[tuple[int, str]],
                     header: bool) -> set[str]:
    """The T-refs findings for a Blocked by field, `text` being its entries joined and
    `lines` its lines. Returns the keys of the specs it links.

    A link that does not resolve is an ERROR (a header link without a path too); a link to
    a non-spec is a WARN; so is an entry that is unreadable, or names a
    change its spec never held, unless it already has a finding for the same cause."""
    f = ctx.findings
    blockers: set[str] = set()
    for entry in split_entries(text):
        ref = read_blocker(ctx.specs, doc, entry)
        if ref is None:
            continue
        for link in ref.links:
            number = next((n for n, t in lines if f"({link.target}" in t), lines[0][0])
            if link.state == "does not resolve" or (link.state == "no target" and header):
                f.error("T-refs", doc.path, number,
                        f"Blocked by link '{link.target}' does not resolve")
            elif link.state == "not a spec":
                f.warn("T-refs", doc.path, number,
                       f"Blocked by link '{link.target}' is not a spec")
            elif link.state == "no target":
                f.warn("T-refs", doc.path, number,
                       f"Blocked by link '{link.target}' points at no document")
            elif link.path is not None:
                blockers.add(norm_key(link.path))
        line = lines[0][0]
        if ref.problem == "unreadable":
            f.warn("T-refs", doc.path, line,
                   f"Blocked by entry '{ref.raw}' is not a form spec_lint reads: use a link, "
                   "or a link then › and the change name in backticks")
        elif (ref.problem is None and ref.change is not None and ref.spec is not None
                and ctx.specs.skip_reason(ref.spec) is None
                and ctx.history.never_held(ref.spec, ref.change)):
            f.warn("T-refs", doc.path, line,
                   f"Blocked by names change '{ref.change}', which {f.show(ref.spec.path)} "
                   "does not hold and never held")
    return blockers
