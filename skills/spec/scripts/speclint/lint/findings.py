# Spec: spec-lint. Behaviour changes go through it.
"""What the checks share: the findings they collect and sort, the run's context, and the other
checks two checkers both use."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..blockers import ChangeHistory
from ..discovery import Specs
from ..document import Doc, Part

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CODE_SPAN_RE = re.compile(r"`[^`]*`")
QUOTE_RE = re.compile(r"\"((?:[^\"\\]|\\.)*)\"|“([^”]*)”")
STATUSES = {"draft", "ready", "built"}
SIZE_LIMIT = 15 * 1024  # the body, and each pending change
DELEGATIONS = ("sonnet", "deep", "main session only")


class Findings:
    def __init__(self, show: Callable[[Path], str]):
        self.show = show
        self.items: set[tuple[str, int, str, str, str]] = set()

    def add(self, level: str, rule: str, path: Path, line: int, message: str) -> None:
        self.items.add((self.show(path), line, level, rule, message))

    def sorted(self) -> list[tuple[str, int, str, str, str]]:
        """The findings in report order: by file (ignoring case), line, ERROR before WARN, rule,
        message."""
        order = {"ERROR": 0, "WARN": 1}
        return sorted(self.items, key=lambda f: (f[0].lower(), f[1], order[f[2]], f[3], f[4]))

    def error(self, rule: str, path: Path, line: int, message: str) -> None:
        self.add("ERROR", rule, path, line, message)

    def warn(self, rule: str, path: Path, line: int, message: str) -> None:
        self.add("WARN", rule, path, line, message)


@dataclass
class Context:
    """What every check reads and writes: the run's discovery, findings and change history."""
    specs: Specs
    findings: Findings
    history: ChangeHistory


def check_read_first(ctx: Context, doc: Doc, part: Part) -> None:
    f = ctx.findings
    lines = [(part.line + i, t) for i, t in enumerate(part.text)]
    for number, target, resolved in doc.links(lines):
        if resolved is None:
            continue
        if ctx.specs.is_spec(resolved):
            other = ctx.specs.doc(resolved)
            if other and other.usable and other.status != "built":
                f.error("T-self", doc.path, number,
                        f"Read first lists '{target}', a spec that is not built")
        if resolved.suffix.lower() == ".md" and {"design", "technical"} & {
                p.lower() for p in resolved.parts}:
            f.error("T-self", doc.path, number, f"Read first lists '{target}', a design or "
                                                "technical doc")
    for number, text in lines:
        for span in CODE_SPAN_RE.findall(text):
            if re.search(r"(^|/)(design|technical)/\S*\.md\b", span.strip("`")):
                f.error("T-self", doc.path, number,
                        f"Read first lists {span}, a design or technical doc")


def check_delegation(ctx: Context, doc: Doc, delegation: Part) -> None:
    value = delegation.content.strip("*_ ").lower()
    if not value.startswith(DELEGATIONS):
        ctx.findings.error("T-minimum", doc.path, delegation.line,
                           "Delegation is not Sonnet implementer, deep implementer or main session only")
    if "review" in value and not re.search(r"\b(full|light) review\b", value):
        ctx.findings.error("T-minimum", doc.path, delegation.line,
                           "Delegation names a review that is not full review or light review")
