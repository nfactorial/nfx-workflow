# Spec: spec-lint. Behaviour changes go through it.
"""Lint mode: the rule checks over the documents given, and the report of their findings.

One module per kind of check: `folders`, `spec`, `change`, `cycles` and `pointers`. `findings`
collects what they find; `Linter` runs them and prints the report."""

from __future__ import annotations

from pathlib import Path

from ..blockers import ChangeHistory
from ..discovery import Specs, norm_key
from ..document import Doc
from . import change, cycles, folders, pointers, spec
from .findings import Context, Findings


class Linter:
    def __init__(self, paths: list[Path], cwd: Path):
        specs = Specs(paths, cwd)
        self.ctx = Context(specs, Findings(specs.show), ChangeHistory(specs.current))
        for path in paths:
            if not path.is_dir() and not path.is_file():
                self.ctx.findings.error("T-header", path, 1, "no such file or folder")

    def run(self) -> int:
        ctx = self.ctx
        seen: set[str] = set()
        linted: list[Doc] = []
        for path in ctx.specs.targets:
            key = norm_key(path)
            if key in seen:
                continue
            seen.add(key)
            doc = ctx.specs.doc(path)
            if doc is None or not self.lintable(doc):
                continue
            linted.append(doc)
            folders.check_milestones(ctx, doc)
            if doc.is_index:
                folders.check_index(ctx, doc)
            else:
                spec.check_spec(ctx, doc)
                change.check_pending(ctx, doc)
                folders.check_not_yet(ctx, doc)
                pointers.check_module_pointers(ctx, doc)
        folders.check_folders(ctx, linted)
        cycles.check_cycles(ctx, [d for d in linted if not d.is_index])
        if any(not d.is_index for d in linted) or ctx.specs.has_current_format_document():
            pointers.check_code_pointers(ctx)
        return self.report(len(seen))

    def lintable(self, doc: Doc) -> bool:
        """Whether the document is in the current format and readable; when it is not, reports
        why (the only finding it gets)."""
        ctx = self.ctx
        if doc.error:
            ctx.findings.error("T-header", doc.path, 1, f"cannot read as UTF-8: {doc.error}")
            return False
        if doc.old_format:
            found = doc.header.get("template")
            why = (f"Template {found[0].strip()} is below v{ctx.specs.current}" if found
                   else "no Template line")
            ctx.findings.error("T-version", doc.path, found[1] if found else 1,
                               f"old-format ({why}): convert it (L-convert)")
            return False
        if doc.version is not None and doc.version > ctx.specs.current:
            ctx.findings.error("T-version", doc.path, doc.header["template"][1],
                               f"Template v{doc.version} is above the current v{ctx.specs.current}")
            return False
        return True

    def report(self, count: int) -> int:
        errors = warnings = 0
        for file, line, level, rule, message in self.ctx.findings.sorted():
            print(f"{level} {rule} {file}:{line} {message}")
            if level == "ERROR":
                errors += 1
            else:
                warnings += 1
        print(f"spec_lint: {count} file(s), {errors} error(s), {warnings} warning(s)")
        return 1 if errors else 0
