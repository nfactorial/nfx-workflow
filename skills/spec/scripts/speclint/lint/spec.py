# Spec: spec-lint. Behaviour changes go through it.
"""A spec's header, body, modules, status and references, and its Blocked by fields."""

from __future__ import annotations

import re

from ..discovery import norm_key
from ..document import LINK_RE, Doc, parse_parts, squash
from .blockers import check_blocked_by
from .findings import (CODE_SPAN_RE, ID_RE, QUOTE_RE, SIZE_LIMIT, STATUSES, Context,
                       check_delegation, check_read_first)

MARKER_RE = re.compile(r"\*\*(Add|Replace|Remove)\*\*")
NOW_RE = re.compile(r"\b(previously|originally|no longer|used to|formerly)\b", re.IGNORECASE)
# An emphasis span closes on its own line; a lone `*` or `_` (bullet, snake_case, 2 * 3) is not one.
EMPHASIS_RE = re.compile(
    r"(?<![\w*])\*\*(?!\s)[^*]*[^*\s]\*\*(?![\w*])"
    r"|(?<![\w*])\*(?![\s*])[^*]*[^*\s]\*(?![\w*])"
    r"|(?<![\w_])_(?![\s_])[^_]*[^_\s]_(?![\w_])"
)
TEST_RE = re.compile(
    r"test_\w+\.py|::test_\w+|\btest_\w+\(\)|\w\.(?:test|spec)\.[jt]sx?\b|\w_test\.(?:py|go)\b"
    r"|(?<![\w.\-/])tests?/[\w.]"
)


def check_spec(ctx: Context, doc: Doc) -> None:
    f = ctx.findings
    for key, label in (("id", "ID"), ("status", "Status"), ("blocked by", "Blocked by"),
                       ("background", "Background")):
        if key not in doc.header:
            f.error("T-header", doc.path, 1, f"header has no **{label}:** field")
    if doc.status is not None and doc.status not in STATUSES:
        f.error("T-header", doc.path, doc.header["status"][1],
                f"status '{doc.status}' is not draft, ready or built")
    if doc.id is not None:
        line = doc.header["id"][1]
        if not ID_RE.match(doc.id):
            f.error("T-id", doc.path, line, f"ID '{doc.id}' is not a lower-case slug")
        others = [d for d in ctx.specs.ids.get(doc.id, []) if norm_key(d.path) != norm_key(doc.path)]
        for other in others:
            f.error("T-id", doc.path, line, f"ID '{doc.id}' is also used by {f.show(other.path)}")
    if doc.body_size > SIZE_LIMIT:
        f.warn("T-size", doc.path, 1, f"body is {doc.body_size // 1024} KB, well past the ~10 KB "
                                      "guide: does it define more than one thing?")
    check_refs(ctx, doc)
    check_body(ctx, doc)
    check_modules(ctx, doc)
    check_status(ctx, doc)
    build = doc.section_lines("build")
    if build:
        parts = parse_parts(build)
        if "done when" not in parts:
            f.error("T-minimum", doc.path, doc.section_line("build"), "Build has no **Done when:**")
        if "read first" in parts:
            check_read_first(ctx, doc, parts["read first"])
        if "delegation" in parts:
            check_delegation(ctx, doc, parts["delegation"])


def check_refs(ctx: Context, doc: Doc) -> None:
    f = ctx.findings
    blocked = doc.blocked_by()
    blockers: set[str] = set()
    if blocked is not None:
        line = doc.header["blocked by"][1]
        if not doc.links([(line, blocked)]) and squash(blocked).strip("*. ").lower() != "none":
            f.error("T-refs", doc.path, line, "Blocked by is neither links nor 'none'")
        else:
            blockers = check_blocked_by(ctx, doc, blocked, [(line, blocked)], True)
    in_out = False
    lines = []
    for number, text in doc.body_lines():
        if text.startswith("**Out"):
            in_out = True
        elif text.startswith("**") or text.startswith("#") or not text.strip():
            in_out = False
        if not in_out:
            lines.append((number, text))
    for number, target, resolved in doc.links(lines):
        if (ctx.specs.is_spec(resolved) and norm_key(resolved) != norm_key(doc.path)
                and norm_key(resolved) not in blockers):
            f.warn("T-refs", doc.path, number,
                   f"links spec '{target}', which is not in Blocked by (fine only for a "
                   "composition root naming what it mounts)")


def check_body(ctx: Context, doc: Doc) -> None:
    f = ctx.findings
    for number, text in doc.body_lines():
        if MARKER_RE.search(text):
            f.error("T-marks", doc.path, number, "Add/Replace/Remove marker above Pending changes")
        plain = EMPHASIS_RE.sub("", QUOTE_RE.sub("", CODE_SPAN_RE.sub("", LINK_RE.sub(r"\1", text))))
        words = [m.group(1).lower() for m in NOW_RE.finditer(plain)]
        if words:
            f.warn("T-now", doc.path, number,
                   f"revision word(s) {', '.join(repr(w) for w in dict.fromkeys(words))}: "
                   "is this history?")
        tests = TEST_RE.findall(text)
        if tests:
            f.warn("T-acceptance", doc.path, number, "names a test or test path: a spec names no tests")


def check_modules(ctx: Context, doc: Doc) -> None:
    lines = doc.section_lines("modules and interfaces")
    for position, (number, text) in enumerate(lines):
        if not text.startswith("### ") or doc.in_code[number - 1]:
            continue
        rest = [t.strip() for _, t in lines[position + 1:]]
        skip = 0
        while skip < len(rest) and rest[skip]:  # a heading is one line; text right under it is not prose
            skip += 1
        if skip:
            ctx.findings.error("T-responsibility", doc.path, number,
                               "heading continues on the next line, which renders as a paragraph: "
                               "keep the heading on one line")
        first = next((t for t in rest[skip:] if t), "")
        if not first or first.startswith(("**", "#")):
            ctx.findings.error("T-responsibility", doc.path, number,
                               "module block does not open with its responsibility")


def check_status(ctx: Context, doc: Doc) -> None:
    f = ctx.findings
    questions = doc.section_lines("unanswered questions")
    has_questions = any(t.strip() and not t.strip().startswith("*") and t.strip().lower() not in
                        ("none", "none.") for _, t in questions)
    if doc.status == "ready" and has_questions:
        f.error("L-ready", doc.path, doc.section_line("unanswered questions"),
                "a ready spec has unanswered questions")
    if doc.status == "built":
        for name in ("Build", "Unanswered questions"):
            line = doc.section_line(name.lower())
            if line:
                f.error("L-ready", doc.path, line, f"a built spec has no '## {name}' section")
