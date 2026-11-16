# Spec: spec-lint. Behaviour changes go through it.
"""Blocked by cycles among the specs linted."""

from __future__ import annotations

import sys

from ..discovery import norm_key
from ..document import Doc
from .blockers import header_blocker_docs
from .findings import Context


def check_cycles(ctx: Context, linted: list[Doc]) -> None:
    graph: dict[str, list[str]] = {}
    names: dict[str, Doc] = {}
    queue = list(linted)
    while queue:
        doc = queue.pop()
        key = norm_key(doc.path)
        if key in graph:
            continue
        names[key] = doc
        graph[key] = []
        if not doc.usable or "blocked by" not in doc.header:
            continue
        for other in header_blocker_docs(ctx.specs, doc):
            graph[key].append(norm_key(other.path))
            queue.append(other)
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []
    counter = [0]

    def visit(node: str) -> None:
        index[node] = low[node] = counter[0]
        counter[0] += 1
        stack.append(node)
        on_stack.add(node)
        for nxt in graph.get(node, []):
            if nxt not in index:
                visit(nxt)
                low[node] = min(low[node], low[nxt])
            elif nxt in on_stack:
                low[node] = min(low[node], index[nxt])
        if low[node] == index[node]:
            component = []
            while True:
                top = stack.pop()
                on_stack.discard(top)
                component.append(top)
                if top == node:
                    break
            if len(component) > 1 or node in graph.get(node, []):
                components.append(component)

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, 10 * len(graph) + 100))
    try:
        for node in sorted(graph):
            if node not in index:
                visit(node)
    finally:
        sys.setrecursionlimit(old_limit)
    linted_keys = {norm_key(d.path) for d in linted}
    for component in components:
        members = sorted(component)
        reporter = next((m for m in members if m in linted_keys), None)
        if reporter is None:
            continue
        doc = names[reporter]
        label = ", ".join(names[m].id or names[m].path.stem for m in members)
        ctx.findings.error("T-refs", doc.path, doc.header["blocked by"][1],
                           f"Blocked by cycle among: {label}")
