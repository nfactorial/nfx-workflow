---
name: health
description: Read-only code health report for a folder in a git repo. Lizard measures file size, function length, complexity and parameter count, then an agent reviews the worst files and suggests refactor changes for /nfx:spec to plan.
disable-model-invocation: true
argument-hint: "[path] [script options]"
context: fork
agent: general-purpose
---

Arguments: `$ARGUMENTS`. These are a folder inside a git repo (default: the current directory),
optionally followed by options for the measuring script.

Produce a code health report for that folder. This is **read-only**: do not create, modify or
delete any file, and do not commit. The report is an input to planning. Structural fixes go
through `/nfx:spec` as a refactor change (a pending change in the spec of the thing the code
belongs to, or a new spec), so describe problems and seams rather than writing code.

1. **Limits.** If the project's CLAUDE.md has a "Code health" section, pass its limits and
   excludes to the script as options. Otherwise use the script's defaults.
2. **Measure.** Run the script (`python` on Windows, `python3` on macOS):

   ```
   python "${CLAUDE_SKILL_DIR}/health.py" <path> [--file-lines N] [--fn-nloc N] [--ccn N] [--params N] [--exclude GLOB]... [--top N]
   ```

   It lists files through git, so ignored and generated files are skipped. If it reports that
   lizard is missing, stop and show the user the install command it printed; don't install it yourself. If
   the path isn't in a git repo, stop and say so.
3. **Review the candidates.** For each file under "Review candidates" (production code only),
   read the file, in parts if it's long, and its header if it has one. Assess:
   - **Responsibilities:** the distinct jobs the file does, each named with the functions that
     belong to it.
   - **Seams:** where it would split naturally and what each new file would contain. Prefer
     splits along existing responsibilities, so each piece has a small interface.
   - **Over-limit functions:** why each one is long or complex (one switch over many cases,
     several phases in sequence, deep nesting, repeated blocks) and how it would break up. A long
     flat list or a plain switch can be fine as it is; say so rather than forcing a split.
   - **Long parameter lists:** whether the parameters travel together and would form a struct.
   - **Interface docs:** missing or stale comments on what other code calls. Match the
     codebase's existing comment density. Private helpers need a comment only where the reason
     isn't obvious.
   - **Duplication** you notice between the candidates.

   Read neighbouring files only where you need them to judge a seam.
4. **Return the report** in the format below. Your final message is the report and nothing else.

## Report format

```markdown
# Code health: <path> (<date>)

**Verdict:** one or two sentences. The overall state, and whether anything needs a refactor now.

## Numbers

The script's Limits line and Summary table, its production tables (trim the function table to
the 15 worst and say how many were left out), and the review candidates with their severity.
Tests in one short paragraph: counts and the worst two or three items.

## Findings

One subsection per reviewed file: responsibilities, seams, over-limit functions, interface
docs. Each point with `file:line`.

## Suggested refactor changes

In order, for `/nfx:spec` to plan, each one change (one session, one review). Each: the spec it
belongs to, if you can tell, what moves or changes, what stays fixed (public
interface, behaviour), and how it is verified (existing tests, or tests that need to exist
first). Say which are worth doing now and which can wait. If none is worth doing, say so.

## Fine as it is

Over-limit items you judged acceptable, each with the reason.
```
