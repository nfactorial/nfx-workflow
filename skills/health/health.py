"""Measures code health for a folder in a git repo and prints a markdown report.

The file list comes from git (tracked plus untracked-but-not-ignored), so every
.gitignore in the repo applies and generated folders such as Intermediate/ are
skipped without any per-project setup. Lizard measures each function.

Usage: python health.py [path] [--file-lines N] [--fn-nloc N] [--ccn N]
                        [--params N] [--exclude GLOB ...] [--top N]
"""

import argparse
import fnmatch
import re
import subprocess
import sys
import sysconfig
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_EXCLUDES = ["*/ThirdParty/*", "ThirdParty/*", "*/third_party/*", "*/vendor/*"]

# Path segments or file names that mark test code. Tests are reported separately.
TEST_DIR = re.compile(r"(^|/)(tests?|specs?|__tests__)(/|$)", re.IGNORECASE)
TEST_FILE = re.compile(r"(^test_.*\.py$|_test\.\w+$|\.(test|spec)\.\w+$|Tests?\.(cs|cpp|h|hpp)$)")


@dataclass
class Limits:
    file_lines: int
    fn_nloc: int
    ccn: int
    params: int


@dataclass
class FunctionResult:
    name: str
    line: int
    nloc: int
    ccn: int
    params: int
    over: list
    excess: float


@dataclass
class FileResult:
    path: str
    is_test: bool
    lines: int
    nloc: int
    function_count: int
    flagged: list = field(default_factory=list)

    def severity(self, limits: Limits) -> float:
        """How far over the limits this file is, so a CCN-51 function outranks three 7-parameter ones.

        Each over-limit function adds its worst excess ratio above 1 (CCN 30 against a limit of 15 adds 1.0),
        and the file adds its own excess if it is over the line limit.
        """
        score = sum(fn.excess for fn in self.flagged)
        if self.lines > limits.file_lines:
            score += self.lines / limits.file_lines - 1
        return score


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}")
    return result.stdout


def list_source_files(target: Path, extensions: set, excludes: list):
    """Returns (repo_root, [repo-relative posix paths], excluded_count) for lizard-supported files under target."""
    root = Path(git(target, "rev-parse", "--show-toplevel").strip())
    listing = git(target, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--full-name", "--", ".")
    files, excluded = [], 0
    for rel in sorted(set(p for p in listing.split("\0") if p)):
        if rel.rsplit(".", 1)[-1] not in extensions or not (root / rel).is_file():
            continue
        if any(fnmatch.fnmatch(rel, pattern) for pattern in excludes):
            excluded += 1
            continue
        files.append(rel)
    return root, files, excluded


def is_test_path(rel: str) -> bool:
    return bool(TEST_DIR.search(rel) or TEST_FILE.search(rel.rsplit("/", 1)[-1]))


def count_lines(path: Path) -> int:
    data = path.read_bytes()
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def analyse(root: Path, rel: str, limits: Limits, lizard) -> FileResult:
    path = root / rel
    info = lizard.analyze_file(str(path))
    result = FileResult(rel, is_test_path(rel), count_lines(path), info.nloc, len(info.function_list))
    for fn in info.function_list:
        forgiven = getattr(fn, "forgiven_metrics", set()) or set()
        checks = [("nloc", fn.nloc, limits.fn_nloc),
                  ("ccn", fn.cyclomatic_complexity, limits.ccn),
                  ("params", fn.parameter_count, limits.params)]
        breaches = [(label, value / limit) for label, value, limit in checks if value > limit and label not in forgiven]
        if breaches:
            result.flagged.append(FunctionResult(fn.name, fn.start_line, fn.nloc, fn.cyclomatic_complexity,
                                                 fn.parameter_count, [label for label, _ in breaches],
                                                 max(ratio for _, ratio in breaches) - 1))
    return result


def summary_column(results: list, limits: Limits) -> list:
    return [len(results),
            sum(r.nloc for r in results),
            sum(r.function_count for r in results),
            sum(len(r.flagged) for r in results),
            sum(1 for r in results if r.lines > limits.file_lines)]


def print_file_table(results: list, limits: Limits) -> None:
    big = sorted((r for r in results if r.lines > limits.file_lines), key=lambda r: -r.lines)
    if not big:
        print(f"None over {limits.file_lines} lines.\n")
        return
    print("| File | Lines | NLOC | Functions | Over-limit functions |")
    print("|---|---|---|---|---|")
    for r in big:
        print(f"| `{r.path}` | {r.lines} | {r.nloc} | {r.function_count} | {len(r.flagged)} |")
    print()


def print_function_table(results: list) -> None:
    flagged = [(r.path, fn) for r in results for fn in r.flagged]
    if not flagged:
        print("None.\n")
        return
    flagged.sort(key=lambda item: (-item[1].ccn, -item[1].nloc))
    print("| Function | Location | NLOC | CCN | Params | Over |")
    print("|---|---|---|---|---|---|")
    for path, fn in flagged:
        print(f"| `{fn.name}` | `{path}:{fn.line}` | {fn.nloc} | {fn.ccn} | {fn.params} | {', '.join(fn.over)} |")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--file-lines", type=int, default=800, help="physical lines per file (default 800)")
    parser.add_argument("--fn-nloc", type=int, default=60, help="lines of code per function, excluding comments and blanks (default 60)")
    parser.add_argument("--ccn", type=int, default=15, help="cyclomatic complexity per function (default 15)")
    parser.add_argument("--params", type=int, default=6, help="parameters per function (default 6)")
    parser.add_argument("--exclude", action="append", default=[], help="extra glob on repo-relative paths; repeatable")
    parser.add_argument("--top", type=int, default=5, help="production files to list as review candidates (default 5)")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    try:
        import lizard
        from lizard_languages import languages
    except ImportError:
        # A Python marked externally managed (PEP 668, e.g. Homebrew) refuses a plain pip install.
        marker = Path(sysconfig.get_path("stdlib")) / "EXTERNALLY-MANAGED"
        extra = " --user --break-system-packages" if marker.exists() else ""
        fail("lizard is not installed for this Python. Install it with: "
             f'"{sys.executable}" -m pip install{extra} lizard')

    target = Path(args.path).resolve()
    if not target.is_dir():
        fail(f"{target} is not a directory")

    limits = Limits(args.file_lines, args.fn_nloc, args.ccn, args.params)
    extensions = {ext for language in languages() for ext in getattr(language, "ext", [])}
    root, files, excluded = list_source_files(target, extensions, DEFAULT_EXCLUDES + args.exclude)

    results, unreadable = [], []
    for rel in files:
        try:
            results.append(analyse(root, rel, limits, lizard))
        except Exception as error:  # one unreadable file shouldn't sink the report
            unreadable.append(f"{rel} ({error.__class__.__name__})")

    production = [r for r in results if not r.is_test]
    tests = [r for r in results if r.is_test]

    print(f"# Code health numbers: `{target.relative_to(root).as_posix() if target != root else '.'}`\n")
    print(f"Repo: `{root.as_posix()}`. Files come from git, so ignored and generated files are skipped. "
          f"{excluded} file(s) matched excludes: {', '.join(f'`{p}`' for p in DEFAULT_EXCLUDES + args.exclude)}.\n")
    print(f"Limits: file > {limits.file_lines} lines, function > {limits.fn_nloc} NLOC, "
          f"CCN > {limits.ccn}, > {limits.params} params.\n")

    print("## Summary\n")
    print("| | Production | Tests |")
    print("|---|---|---|")
    labels = ["Files", "Lines of code (NLOC)", "Functions", "Functions over a limit", "Files over the line limit"]
    for label, prod, test in zip(labels, summary_column(production, limits), summary_column(tests, limits)):
        print(f"| {label} | {prod} | {test} |")
    print()

    print("## Production files over the line limit\n")
    print_file_table(production, limits)
    print("## Production functions over a limit\n")
    print_function_table(production)

    print("## Review candidates\n")
    print("Ranked by how far over the limits each file is, not by how many items are over.\n")
    ranked = sorted((r for r in production if r.severity(limits) > 0),
                    key=lambda r: (-r.severity(limits), -r.lines))[:args.top]
    if ranked:
        for r in ranked:
            print(f"- `{r.path}`: severity {r.severity(limits):.1f}, {r.lines} lines, "
                  f"{len(r.flagged)} over-limit function(s)")
    else:
        print("None. Nothing in production code is over a limit.")
    print()

    print("## Tests\n")
    print_file_table(tests, limits)
    print_function_table(tests)

    if unreadable:
        print("## Not analysed\n")
        for item in unreadable:
            print(f"- `{item}`")
        print()


if __name__ == "__main__":
    main()
