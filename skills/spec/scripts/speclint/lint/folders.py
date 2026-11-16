# Spec: spec-lint. Behaviour changes go through it.
"""Folder and index checks: indexes, the tree an index lists, feature folders, Not yet planned."""

from __future__ import annotations

import re
from pathlib import Path

from ..discovery import has_index, norm_key
from ..document import Doc
from .blockers import header_blocker_docs
from .findings import Context


def check_index(ctx: Context, doc: Doc) -> None:
    f = ctx.findings
    for key, label in (("design", "Design"), ("technical", "Technical")):
        if key not in doc.header:
            f.error("T-header", doc.path, 1, f"index header has no **{label}:** field")
    if "status" in doc.header:
        f.error("T-index", doc.path, doc.header["status"][1], "an index holds no status")
    if "head" in doc.header and "area" in doc.header:
        f.error("T-feature", doc.path, doc.header["area"][1],
                "an index has a **Head:** or an **Area:** field, not both")
    for key in ("blocked by", "id"):
        if key in doc.header:
            f.error("T-index", doc.path, doc.header[key][1],
                    f"an index holds no {key} field: it lives in the specs")
    if doc.pending_start:
        f.error("T-index", doc.path, doc.pending_start, "an index holds no pending changes")
    for name in ("Specs", "Not yet planned"):
        if doc.section_line(name.lower()) is None:
            f.error("T-index", doc.path, 1, f"index has no '## {name}' section")
    for number, text in doc.section_lines("specs"):
        if re.search(r"\[(draft|ready|built)\]|\*\*Status", text, re.IGNORECASE):
            f.error("T-index", doc.path, number, "an index holds no status")
    listed = set()
    all_lines = [(i + 1, t) for i, t in enumerate(doc.lines) if not doc.in_code[i]]
    for number, target, resolved in doc.links(all_lines):
        if resolved is None:
            continue
        if not resolved.exists():
            f.error("T-index", doc.path, number, f"link '{target}' does not resolve")
        listed.add(norm_key(resolved))
    covered = ctx.specs.covered(doc.path.parent)
    for spec in covered:
        if norm_key(spec) not in listed:
            f.error("T-index", doc.path, doc.section_line("specs") or 1,
                    f"does not list {f.show(spec)}")
    if len(covered) == 1:
        f.warn("T-feature", doc.path, 1, "index of a folder with one spec: a feature that is one "
                                         "thing is a single file")
    check_tree(ctx, doc)


def header_blockers(ctx: Context, doc: Doc) -> set[str]:
    return {norm_key(blocker.path) for blocker in header_blocker_docs(ctx.specs, doc)}


def root_specs(ctx: Context, folder: Path) -> list[Path]:
    return sorted((p for p in folder.glob("*.md")
                   if p.name != "README.md" and ctx.specs.is_spec(p)), key=norm_key)


def check_tree(ctx: Context, index: Doc) -> None:
    """A feature folder holds its head at the root and each part in a sub-folder (T-feature)."""
    f = ctx.findings
    folder = index.path.parent
    if "area" in index.header:
        return
    head_field = index.header.get("head")
    if head_field is None:
        f.error("T-header", index.path, 1, "index header has no **Head:** (a feature) or "
                                           "**Area:** (a folder with no head) field")
        return
    heads = [r for _, _, r in index.links([(head_field[1], head_field[0])])
             if r is not None and r.is_file()]
    if len(heads) != 1 or norm_key(heads[0].parent) != norm_key(folder):
        f.error("T-feature", index.path, head_field[1],
                "**Head:** must link the one spec at this folder's root")
        return
    check_head_folder(ctx, folder, heads[0], index.path, head_field[1])


def check_head_folder(ctx: Context, folder: Path, head: Path, where: Path, line: int) -> None:
    f = ctx.findings
    others = [p for p in root_specs(ctx, folder) if norm_key(p) != norm_key(head)]
    for extra in others:
        f.warn("T-feature", where, line,
               f"{f.show(extra)} sits beside the head {head.name}: each part has its own "
               "sub-folder")
    head_doc = ctx.specs.doc(head)
    if head_doc is None or not head_doc.usable:
        return
    head_blockers = header_blockers(ctx, head_doc)
    mounted = {norm_key(r) for _, _, r in head_doc.links(head_doc.body_lines())
               if r is not None and r.is_file()}  # a composition root names what it mounts
    for sub in sorted(p for p in folder.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if has_index(sub):
            continue  # a feature of its own, checked through its own index
        roots = root_specs(ctx, sub)
        if not roots:
            continue
        if len(roots) > 1:
            f.warn("T-feature", roots[1], 1, f"{f.show(sub)} holds {len(roots)} specs at its "
                                             "root: a part folder holds one part and its "
                                             "part folders")
        for path in roots:
            part = ctx.specs.doc(path)
            if part is None or not part.usable:
                continue
            if norm_key(path) in mounted and norm_key(path) not in head_blockers:
                pass  # mounted by a composition-root head: a part
            elif norm_key(head) in header_blockers(ctx, part):
                f.error("T-feature", path, part.header.get("blocked by", ("", 1))[1],
                        f"uses {head.name} (in its Blocked by) and {head.name} doesn't mount "
                        "it: a user, not a part; it lives in its own area's folder")
            elif norm_key(path) not in head_blockers:
                f.warn("T-feature", path, 1, f"not in {head.name}'s Blocked by or mounted by "
                                             "it: a part is something the head is made of")
        check_head_folder(ctx, sub, roots[0], roots[0], 1)


def check_folders(ctx: Context, linted: list[Doc]) -> None:
    done: set[str] = set()
    for doc in linted:
        if doc.is_index:
            continue
        folder = doc.path.parent
        if norm_key(folder) in done:
            continue
        done.add(norm_key(folder))
        if ctx.specs.nearest_index(folder) is not None or ctx.specs.is_root(folder):
            continue
        group = ctx.specs.covered(folder)
        if len(group) >= 2:
            ctx.findings.error("T-feature", doc.path, 1,
                               f"folder {ctx.findings.show(folder)} holds {len(group)} specs "
                               "and no README.md index")


def check_milestones(ctx: Context, doc: Doc) -> None:
    """The milestone headings of a document's Not yet planned: written `### Milestone: <name>`,
    each name once (T-milestone)."""
    f = ctx.findings
    for number, heading in doc.bad_milestones:
        f.error("T-milestone", doc.path, number,
                f"'{heading}' is not a milestone heading: write '### Milestone: <name>'")
    for at, milestone in enumerate(doc.milestones):
        earlier = next((m for m in doc.milestones[:at]
                        if m.key == milestone.key or m.slug == milestone.slug), None)
        if earlier is not None:
            f.error("T-milestone", doc.path, milestone.line,
                    f"milestone '{milestone.name}' repeats the one at line {earlier.line}")


def check_not_yet(ctx: Context, doc: Doc) -> None:
    """Only a feature that is one file holds its own Not yet planned lines, at its foot (T-not-yet)."""
    f = ctx.findings
    line = doc.section_line("not yet planned")
    if not line:
        return
    if doc.pending_start and line < doc.pending_start:
        f.error("T-not-yet", doc.path, line, "'## Not yet planned' sits at the foot, after Pending changes")
    index = ctx.specs.doc(ctx.specs.nearest_index(doc.path.parent))
    if index and index.usable and "head" in index.header:
        f.error("T-not-yet", doc.path, line, "a spec in a feature folder keeps its Not yet planned "
                                             f"lines in {f.show(index.path)}")
