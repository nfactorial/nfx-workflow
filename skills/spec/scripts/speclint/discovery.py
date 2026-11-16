# Spec: spec-reading. Behaviour changes go through it.
"""Which documents exist and how one is found: the repo root, the known documents, the cache of
parsed documents and the lookup of a spec by name. It loads lazily, so a run parses only the
documents it asks for."""

from __future__ import annotations

import os
import subprocess
from functools import cached_property
from pathlib import Path

from .document import Doc, find_current_version


def norm_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    if result.returncode not in (0, 1):
        return None
    return result.stdout


def is_link(path: Path) -> bool:
    """A symlink or (on Windows) a junction: lint mode's rglob doesn't follow them either."""
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def has_index(folder: Path) -> bool:
    """Whether the folder holds a file named exactly README.md (the same on every OS)."""
    return any(p.name == "README.md" and p.is_file() for p in folder.iterdir())


def indexed_subfolder(folder: Path, target: Path) -> Path | None:
    """The outermost sub-folder of `folder` above `target` that has a README.md of its own."""
    try:
        rel = target.relative_to(folder)
    except ValueError:
        return None
    chain = folder
    for part in rel.parts[:-1]:
        chain = chain / part
        if has_index(chain):
            return chain
    return None


class Specs:
    """Discovery for the repo the first path lies in. Nothing is listed or parsed until asked."""

    def __init__(self, paths: list[Path], cwd: Path):
        self.current = find_current_version()
        self.cwd = cwd
        self.paths = paths
        first = paths[0] if paths[0].is_dir() else paths[0].parent
        top = git(first, "rev-parse", "--show-toplevel")
        self.root = Path(top.strip()).resolve() if top and top.strip() else None
        self._docs: dict[str, Doc] = {}

    @cached_property
    def targets(self) -> list[Path]:
        """The files the paths name, a folder's every .md in sorted order."""
        found: list[Path] = []
        for path in self.paths:
            if path.is_dir():
                found += sorted(p.resolve() for p in path.rglob("*.md"))
            elif path.is_file():
                found.append(path.resolve())
        return found

    @cached_property
    def roots(self) -> list[Path]:
        """The `specs` folders the known documents are found under."""
        roots: dict[str, Path] = {}
        if self.root:
            listing = git(self.root, "ls-files", "-co", "--exclude-standard") or ""
            for rel in listing.splitlines():
                parts = Path(rel).parts
                if "specs" in parts:
                    root = self.root.joinpath(*parts[: parts.index("specs") + 1])
                    roots[norm_key(root)] = root
        for path in self.paths:
            resolved = path.resolve()
            ancestor = next((p for p in [resolved, *resolved.parents] if p.name == "specs"), None)
            if ancestor is None:
                ancestor = resolved if resolved.is_dir() else resolved.parent
            roots[norm_key(ancestor)] = ancestor
        return list(roots.values())

    @cached_property
    def _root_keys(self) -> set[str]:
        return {norm_key(r) for r in self.roots}

    @cached_property
    def known(self) -> dict[str, Path]:
        """The known documents, keyed by `norm_key`."""
        known: dict[str, Path] = {}
        for root in self.roots:
            for path in root.rglob("*.md"):
                # Only the parts below the walked folder are tested, so where the repo sits is free.
                below = path.relative_to(root).parts
                if not any(part.startswith(".") or part == "node_modules" for part in below):
                    known[norm_key(path)] = path.resolve()
        for path in self.targets:
            known[norm_key(path)] = path
        return known

    @cached_property
    def ids(self) -> dict[str, list[Doc]]:
        """Each ID, with the known specs that carry it. Parses every known document."""
        found: dict[str, list[Doc]] = {}
        for doc in (self.doc(p) for p in self.known.values()):
            if doc and doc.id and not doc.is_index:
                found.setdefault(doc.id, []).append(doc)
        return found

    def show(self, path: Path) -> str:
        """A path as the output writes paths: relative to the working directory when under it."""
        try:
            return Path(os.path.relpath(path, self.cwd)).as_posix() if norm_key(path).startswith(
                norm_key(self.cwd)) else path.as_posix()
        except ValueError:
            return path.as_posix()

    def doc(self, path: Path | None) -> Doc | None:
        """The parsed document at a path, parsed once; None when it is not a file."""
        if path is None:
            return None
        key = norm_key(path)
        if key not in self._docs:
            if not path.is_file():
                return None
            self._docs[key] = Doc(path.resolve(), self.current)
        return self._docs[key]

    def is_spec(self, path: Path | None) -> bool:
        return path is not None and norm_key(path) in self.known and path.name != "README.md"

    def spec_by_name(self, name: str, home: Doc) -> Doc | None:
        """The spec a Changes item's prefix names: by ID, file stem or title."""
        wanted = name.strip().strip("`*").strip().lower()
        candidates = [home] + [self.doc(p) for p in self.known.values()]
        for test in (lambda d: (d.id or "").lower(), lambda d: d.path.stem.lower(),
                     lambda d: d.title.lower()):
            for doc in candidates:
                if doc and not doc.is_index and test(doc) == wanted:
                    return doc
        return None

    def skip_reason(self, doc: Doc) -> str | None:
        """Why the document cannot be read for its items, if it cannot: a Template version above the
        current one, or text that is not UTF-8."""
        if doc.error:
            return f"cannot read as UTF-8: {doc.error}"
        if doc.version is not None and doc.version > self.current:
            return f"Template v{doc.version} is above the current v{self.current}"
        return None

    def has_current_format_document(self) -> bool:
        """Whether any known document, an index too, is in the current format. Parses documents
        until it finds one."""
        return any((d := self.doc(p)) and not d.old_format for p in self.known.values())

    def is_root(self, folder: Path) -> bool:
        """Whether the folder is one of the `specs` folders the known documents lie under."""
        return norm_key(folder) in self._root_keys

    def covered(self, folder: Path) -> list[Path]:
        """Specs in folder and in its subfolders that have no index of their own."""
        out = []
        for path in sorted(self.known.values(), key=norm_key):
            if path.name == "README.md":
                continue
            try:
                path.relative_to(folder)
            except ValueError:
                continue
            if indexed_subfolder(folder, path) is None:
                out.append(path)
        return out

    def nearest_index(self, folder: Path) -> Path | None:
        """The README.md of the nearest folder above (or at) `folder`, stopping at a `specs` folder."""
        for ancestor in [folder, *folder.parents]:
            if has_index(ancestor):
                return ancestor / "README.md"
            if self.is_root(ancestor):
                break
        return None
