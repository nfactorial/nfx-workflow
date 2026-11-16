#!/usr/bin/env python3
# Spec: git-helper. Behaviour changes go through it.
"""The git work of a run's orchestrator, with the run's exclusions applied, printing JSON.

Usage: git_helper.py [--cwd <dir>] [--exclude-file <path>] <command> ...

Commands:
  snapshot --scratch <dir> --name <name>      -> {"tree", "head"}
  round-diff <prev tree> <prev head> <tree> <head>
                                              -> {"files", "other_run"}
  own-files                                   -> {"tracked", "untracked"}
  restore                                     -> {"restored", "deleted"}
  save-patch <patch file>                     -> {"patch", "files"}
  run-names <feature> [<milestone>]           -> {"slug", "branch", "report"}

`run-names` gives a run's names: a milestone run's from the feature and milestone, else the
auto run's from the branch checked out (or today).

The exclude file holds one repo-relative path per line; a line ending in `/` excludes
everything under that folder; blank lines and lines starting with `#` are ignored.
Exits 0 with one JSON object on stdout; a git failure, or `restore` or `save-patch` meeting a folder
entry (an untracked nested repo, which `own-files` lists as `sub/`),
prints {"error", "command"} and exits 1;
a usage error exits 2. Python 3 standard library and the plugin's own `speclint` only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from speclint.document import milestone_slug


class GitError(Exception):
    """A failure that prints as {"error", "command"}, plus `done` (what a command had
    already changed) when given."""

    def __init__(self, message: str, command: list[str], done: dict[str, list[str]] | None = None):
        super().__init__(message)
        self.message = message
        self.command = command
        self.done = done


class UsageError(Exception):
    pass


@dataclass(frozen=True)
class RunNames:
    """The names of a run: its slug, its branch and its report file (`milestone-run.md`'s
    *Names*, `auto.md`'s *The branch*)."""

    slug: str
    branch: str
    report: str


@dataclass(frozen=True)
class Excludes:
    """Paths a run leaves alone: exact files, and folders (each ending in `/`)."""

    files: frozenset[str]
    folders: tuple[str, ...]

    def excludes(self, path: str) -> bool:
        return path in self.files or any(path.startswith(f) for f in self.folders)

    def keep(self, paths: list[str]) -> list[str]:
        return [p for p in paths if not self.excludes(p)]


def read_excludes(path: Path | None) -> Excludes:
    """The exclude file's lines; a leading `./` or `/` is dropped, case is kept."""
    if path is None:
        return Excludes(frozenset(), ())
    if not path.is_file():
        raise UsageError(f"exclude file not found: {path}")
    files: set[str] = set()
    folders: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().replace("\\", "/")
        if not line or line.startswith("#"):
            continue
        while line.startswith("./"):
            line = line[2:]
        line = line.lstrip("/")
        if not line:
            continue
        if line.endswith("/"):
            folders.append(line)
        else:
            files.add(line)
    return Excludes(frozenset(files), tuple(folders))


@dataclass(frozen=True)
class OwnFiles:
    """What `git status` lists, less excluded files. `intent_to_add` is the subset of
    `untracked` that already has an intent-to-add index entry; `staged_new` the subset of
    `tracked` that is new in the index (`git restore` removes it from the working tree)."""

    tracked: list[str]
    untracked: list[str]
    intent_to_add: list[str]
    staged_new: list[str]


def is_run_branch(branch: str) -> bool:
    """An `auto/…` branch whose name holds no `--` (a side branch holds one)."""
    return branch.startswith("auto/") and "--" not in branch


class Repo:
    """Runs git in the repo's top folder."""

    def __init__(self, cwd: Path):
        self.root = cwd  # until git says where the top folder is
        self.root = Path(self.git("rev-parse", "--show-toplevel").decode("utf-8", "replace").strip())

    def git(self, *args: str, env: dict[str, str] | None = None) -> bytes:
        argv = ["git", *args]
        full_env = {**os.environ, "GIT_LITERAL_PATHSPECS": "1", **(env or {})}
        try:
            done = subprocess.run(argv, cwd=self.root, env=full_env, capture_output=True)
        except OSError as error:
            raise GitError(str(error), argv) from error
        if done.returncode != 0:
            message = done.stderr.decode("utf-8", "replace").strip() or f"git exited {done.returncode}"
            raise GitError(message, argv)
        return done.stdout

    def lines(self, *args: str) -> list[str]:
        """Git's NUL-separated output (`-z`), as paths."""
        return [p for p in self.git(*args).decode("utf-8", "replace").split("\0") if p]

    def own_files(self, excludes: Excludes) -> OwnFiles:
        entries = self.lines("status", "--porcelain", "-z", "--untracked-files=all")
        tracked: list[str] = []
        untracked: list[str] = []
        intent_to_add: list[str] = []
        staged_new: list[str] = []
        i = 0
        while i < len(entries):
            status, path = entries[i][:2], entries[i][3:]
            i += 1
            paths = [path]
            if "R" in status or "C" in status:  # a rename or copy is followed by its source
                paths.append(entries[i])
                i += 1
            if status == "??":
                untracked.append(path)
            elif status == " A":  # intent-to-add
                untracked.append(path)
                intent_to_add.append(path)
            else:
                tracked.extend(paths)
                if status[0] == "A":
                    staged_new.append(path)
        return OwnFiles(
            excludes.keep(tracked),
            excludes.keep(untracked),
            excludes.keep(intent_to_add),
            excludes.keep(staged_new),
        )

    def changing_own_files(self, excludes: Excludes) -> OwnFiles:
        """`own_files` for the commands that delete or patch them: an untracked nested repo
        shows as a folder entry, which they refuse before touching anything."""
        own = self.own_files(excludes)
        folders = [p for p in own.tracked + own.untracked if p.endswith("/")]
        if folders:
            argv = ["git", "status", "--porcelain", "-z", "--untracked-files=all"]
            raise GitError(f"folder entries (a nested repo?) are not handled: {folders}", argv)
        return own

    def snapshot(self, scratch: Path, name: str) -> dict[str, str]:
        scratch.mkdir(parents=True, exist_ok=True)
        index = scratch / f"{name}.idx"
        index.unlink(missing_ok=True)
        env = {"GIT_INDEX_FILE": str(index)}
        self.git("add", "-A", env=env)
        # `add -A` skips tracked files that match an ignore rule; add them back (those still on
        # disk) rather than seeding from the real index, whose stat data can hide a rewrite.
        ignored = [
            p for p in self.lines("ls-files", "-z", "--cached", "--ignored", "--exclude-standard")
            if (self.root / p).exists()
        ]
        if ignored:
            self.git("add", "-f", "--", *ignored, env=env)
        tree = self.git("write-tree", env=env).decode().strip()
        head = self.git("rev-parse", "HEAD").decode().strip()
        return {"tree": tree, "head": head}

    def round_diff(
        self, excludes: Excludes, prev_tree: str, prev_head: str, tree: str, head: str
    ) -> dict[str, list[str]]:
        changed = excludes.keep(
            self.lines("diff-tree", "-r", "--no-renames", "--name-only", "-z", prev_tree, tree)
        )
        committed: set[str] = set()
        if prev_head != head:
            committed = set(self.lines("diff", "--no-renames", "--name-only", "-z", prev_head, head))
        return {
            "files": sorted(p for p in changed if p not in committed),
            "other_run": sorted(p for p in changed if p in committed),
        }

    def restore(self, excludes: Excludes) -> dict[str, list[str]]:
        own = self.changing_own_files(excludes)
        restored = [p for p in own.tracked if p not in set(own.staged_new)]
        deleted: list[str] = []
        try:
            if own.tracked:
                self.git("restore", "--source=HEAD", "--staged", "--worktree", "--", *own.tracked)
            for path in own.staged_new:  # git restore removed them; drop the folders left empty
                self.prune_empty_parents(self.root / path)
                deleted.append(path)
            if own.intent_to_add:
                self.git("rm", "--cached", "--quiet", "--", *own.intent_to_add)
            for path in own.untracked:
                self.delete(path)
                deleted.append(path)
        except OSError as error:
            done = {"restored": restored, "deleted": deleted}
            raise GitError(str(error), ["git_helper.py", "restore"], done) from error
        return {"restored": restored, "deleted": deleted}

    def delete(self, path: str) -> None:
        target = self.root / path
        target.unlink(missing_ok=True)
        self.prune_empty_parents(target)

    def prune_empty_parents(self, target: Path) -> None:
        parent = target.parent
        while parent != self.root:  # drop folders the deletion left empty
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def run_names(self, feature: str, milestone: str | None, today: date) -> RunNames:
        """A milestone run's names, or, with no milestone, those of the auto run: the slug is its
        date, that of the run branch checked out, else `today`'s (a session then creates it)."""
        reports = Path(self.git("rev-parse", "--absolute-git-dir").decode().strip()) / "nfx"
        if milestone is not None:
            slug = milestone_slug(milestone)
            if not slug:
                raise UsageError(f"milestone has no name: {milestone!r}")
            return RunNames(slug, f"milestone/{feature}-{slug}",
                            (reports / f"milestone-{feature}-{slug}.md").as_posix())
        branch = self.git("branch", "--show-current").decode().strip()
        if is_run_branch(branch):
            slug = branch.removeprefix("auto/")
        else:  # auto.md: another run branch exists, so the last run isn't merged
            argv = ["git_helper.py", "run-names", feature]
            others = [b for b in self.git("branch", "--list", "auto/*", "--format=%(refname:short)")
                      .decode().split() if is_run_branch(b)]
            if others:
                raise GitError(f"another auto run branch exists, the last run isn't merged: "
                               f"{others[0]}", argv)
            slug = today.isoformat()
        return RunNames(slug, f"auto/{slug}", (reports / f"auto-{slug}.md").as_posix())

    def save_patch(self, excludes: Excludes, patch: Path) -> dict[str, object]:
        git_dir = Path(self.git("rev-parse", "--absolute-git-dir").decode().strip()).resolve()
        target = patch.resolve()
        if target.is_relative_to(self.root.resolve()) and not target.is_relative_to(git_dir):
            raise UsageError(f"patch file is inside the working tree: {patch}")
        own = self.changing_own_files(excludes)
        files = own.tracked + own.untracked
        if not files:
            return {"patch": str(patch), "files": []}
        added = [p for p in own.untracked if p not in set(own.intent_to_add)]
        try:
            if added:
                self.git("add", "--intent-to-add", "--", *added)
            diff = self.git("diff", "--binary", "--no-textconv", "--no-ext-diff", "--no-color",
                            "--src-prefix=a/", "--dst-prefix=b/", "HEAD", "--", *files)
            patch.parent.mkdir(parents=True, exist_ok=True)
            patch.write_bytes(diff)
        except (GitError, OSError):
            if added:  # leave no intent-to-add entries behind
                try:
                    self.git("rm", "--cached", "--quiet", "--", *added)
                except GitError:
                    pass
            raise
        return {"patch": str(patch), "files": files}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="git_helper.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--cwd", type=Path, default=None, help="run in this repo's directory")
    parser.add_argument("--exclude-file", type=Path, default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--scratch", type=Path, required=True)
    snapshot.add_argument("--name", required=True)
    round_diff = commands.add_parser("round-diff")
    for name in ("prev_tree", "prev_head", "tree", "head"):
        round_diff.add_argument(name)
    commands.add_parser("own-files")
    commands.add_parser("restore")
    save_patch = commands.add_parser("save-patch")
    save_patch.add_argument("patch_file", type=Path)
    run_names = commands.add_parser("run-names")
    run_names.add_argument("feature")
    run_names.add_argument("milestone", nargs="?")
    return parser


def absolute(path: Path | None, start: Path) -> Path | None:
    return None if path is None else (start / path)


def run(args: argparse.Namespace, start: Path) -> dict[str, object]:
    """Run the command; relative paths in `args` resolve against `start`, never `--cwd`."""
    repo = Repo(absolute(args.cwd, start) or start)
    if args.command == "snapshot":
        return repo.snapshot(absolute(args.scratch, start), args.name)
    if args.command == "run-names":  # reads no exclude file
        return asdict(repo.run_names(args.feature, args.milestone, date.today()))
    excludes = read_excludes(absolute(args.exclude_file, start))
    if args.command == "round-diff":
        return repo.round_diff(excludes, args.prev_tree, args.prev_head, args.tree, args.head)
    if args.command == "own-files":
        own = repo.own_files(excludes)
        return {"tracked": own.tracked, "untracked": own.untracked}
    if args.command == "restore":
        return repo.restore(excludes)
    return repo.save_patch(excludes, absolute(args.patch_file, start))


def error_report(message: str, command: list[str], done: dict[str, list[str]] | None = None) -> dict:
    report: dict[str, object] = {"error": message, "command": command}
    if done is not None:
        report["done"] = done
    return report


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)  # a usage error exits 2
    try:
        result = run(args, Path.cwd())
    except UsageError as error:
        print(f"git_helper: {error}", file=sys.stderr)
        return 2
    except GitError as error:
        print(json.dumps(error_report(error.message, error.command, error.done)))
        return 1
    except OSError as error:
        print(json.dumps(error_report(str(error), ["git_helper.py", *argv])))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
