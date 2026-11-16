# Spec: spec-lint. Behaviour changes go through it.
"""Module and code pointer checks: a module's `Spec:` pointer, and pointers in the repo's code."""

from __future__ import annotations

import re
from pathlib import Path

from ..discovery import git
from ..document import Doc
from .findings import CODE_SPAN_RE, ID_RE, Context

POINTER_LINE_RE = re.compile(
    r"^\s*(?:#+|//+|/\*+|\*|<!--|--|;+|%|')?\s*Spec:\s*([^\s,]+(?:\s*,\s*[^\s,]+)*)")
REPO_ID_RE = re.compile(r"^[A-Za-z0-9._-]+/([a-z0-9]+(?:-[a-z0-9]+)*)$")
OLD_POINTER_RE = re.compile(r"^\s*(?:#+|//+|/\*+|\*|<!--|--|;+|%|')\s*Specified by\b")


def pointer_tokens(text: str) -> list[str] | None:
    """The tokens of a pointer line, or None when `text` is not one."""
    match = POINTER_LINE_RE.match(text)
    if not match:
        return None
    return [t.rstrip(".,;:)\"'") for t in re.split(r"\s*,\s*", match.group(1))]


def check_module_pointers(ctx: Context, doc: Doc) -> None:
    if ctx.specs.root is None:
        return
    base = ctx.specs.root
    repo = doc.header.get("repo")
    if repo:
        written = repo[0].strip().strip("`")
        candidate = Path(written).expanduser()
        if not candidate.is_absolute():
            candidate = ctx.specs.root / candidate
        if not candidate.is_dir():
            ctx.findings.warn("T-pointer", doc.path, repo[1],
                              f"**Repo:** '{written}' does not resolve to a folder; its module "
                              "pointers are not checked")
            return
        base = candidate
    for number, text in doc.section_lines("modules and interfaces"):
        if not text.startswith("### "):
            continue
        match = re.search(r"\(([^)]*)\)\s*$", text)
        if not match:
            continue
        spans = CODE_SPAN_RE.findall(match.group(1)) or [match.group(1)]
        if len(spans) != 1:
            continue
        name = spans[0].strip("` ")
        path = base / name
        if not path.is_file():
            continue
        try:
            head = path.read_text(encoding="utf-8", errors="replace").splitlines()[:10]
        except OSError:
            continue
        tokens = [t for line in head for t in pointer_tokens(line) or []]
        qualified = any((m := REPO_ID_RE.match(t)) and m.group(1) == doc.id for t in tokens)
        if qualified or (not repo and doc.id in tokens):
            continue
        if doc.id in tokens:
            ctx.findings.warn("T-pointer", doc.path, number,
                              f"{name}'s pointer names '{doc.id}' without its repo: write "
                              f"'Spec: <repo>/{doc.id}'")
        else:
            ctx.findings.warn("T-pointer", doc.path, number,
                              f"{name} does not open with a 'Spec: "
                              f"{'<repo>/' if repo else ''}{doc.id}' pointer")


def check_code_pointers(ctx: Context) -> None:
    if ctx.specs.root is None:
        return
    output = git(ctx.specs.root, "grep", "-n", "-I", "-E", "Spec:", "--", ".", ":(exclude)*.md")
    if not output:
        return
    for raw in output.splitlines():
        parts = raw.split(":", 2)
        if len(parts) < 3:
            continue
        rel, number, text = parts
        tokens = pointer_tokens(text)
        if tokens is None:
            continue
        path = ctx.specs.root / rel
        if len(tokens) > 1:
            ctx.findings.warn("T-one-file", path, int(number),
                              f"file covered by {len(tokens)} specs ({', '.join(tokens)}): "
                              "it holds several things; splitting it is found work")
        for token in tokens:
            if "/" in token or "\\" in token or token.lower().endswith(".md"):
                target = ctx.specs.root / token.replace("\\", "/")
                doc = ctx.specs.doc(target) if target.is_file() else None
                if doc and doc.usable and doc.id:
                    ctx.findings.error("T-pointer", path, int(number),
                                       f"pointer names a path; name the ID '{doc.id}'")
                continue
            if ID_RE.match(token) and token not in ctx.specs.ids:
                ctx.findings.error("T-pointer", path, int(number),
                                   f"pointer names '{token}', which no spec header has as "
                                   f"its ID; for a spec in another repo, write '<repo>/{token}'")
    old = git(ctx.specs.root, "grep", "-n", "-I", "-E", "Specified by", "--", ".",
              ":(exclude)*.md")
    for raw in (old or "").splitlines():
        parts = raw.split(":", 2)
        if len(parts) == 3 and OLD_POINTER_RE.match(parts[2]):
            ctx.findings.warn("T-pointer", ctx.specs.root / parts[0], int(parts[1]),
                              "old-format pointer ('Specified by …'): name the spec's ID")
