# Audit

The audit rules and the procedure `/nfx:spec audit` follows. The other rules are in
[template.md](template.md), [lifecycle.md](lifecycle.md), [folders.md](folders.md) and
[later-work.md](later-work.md).

## Rules `L-audit`

An audit is run on request (`/nfx:spec audit`), edits nothing and commits nothing. It is
reported in two tables, which are never merged:

- **Contradictions:** `L-contradictions` the code and a spec disagree, so something must
  change. A body claim the code contradicts, a pending change whose Touchpoints or *Read
  first* no longer match the code, a code pointer naming the wrong spec. Each gets the evidence
  and a proposed fix: a wording correction (the code is right) or a pending change (the spec is
  right). The user decides each one; accepted corrections are committed on their own.
- **Non-compliance:** `L-non-compliance` a document breaks a body rule, but nothing in the
  code is wrong. Old-format, a user named in the body (`T-users`), a missing code pointer, an
  index holding state, a spec well over the size guide. It never implies a code change, and it
  waits until the spec is next touched or converted.

**Interfaces** (`/nfx:spec audit interfaces <folder>`) is a third, cross-spec scope, run on
request or on a schedule (`/schedule`): it reads the specs of a folder together and reports what no
single-spec check can see. Two specs defining the same concept; a requirement in one spec that
is really about another thing (a misplaced boundary); *Blocked by* edges that don't match the
references; duplicate IDs. It is report-only, and its findings become pending changes,
new specs or index lines as the user decides.

## Procedure

Report only: edit nothing and commit nothing (`L-audit`). For a folder of several specs, fan
out to `general-purpose` subagents spawned with `model: "sonnet"`, one spec each, told to edit
nothing (an Explore agent reads excerpts, which isn't enough to check claims against code).

First run the lint, `L-lint`'s command, on the whole scope (the spec or folder), and fold its
output into the two tables rather than fixing it: a `T-pointer` ERROR on a code file is a
contradiction, every other ERROR is non-compliance, and a WARN enters a table only once you
confirm it.

**A spec or folder:** for each spec, check every body claim against the code, each pending
change's Touchpoints and *Read first* against what exists, each code pointer, and the spec
against the body rules of the current version. Report two tables per spec, leaving out empty
ones:

*Contradictions*

| Claim | Code | Proposed fix |
|---|---|---|
| *the spec's line, quoted* | *file:line, and what it does instead* | *correction (code is right) / pending change (spec is right) / ask* |

*Non-compliance*

| Rule | Where | What is wrong |
|---|---|---|
| *rule ID* | *section or line* | *one line* |

Say how many specs were clean. Then ask which contradictions to fix: accepted corrections are
made and committed on their own, and pending changes are planned as in update mode.
Non-compliance waits until the spec is next touched.

**Interfaces** (`audit interfaces <folder>`): read the folder's specs together and report
overlapping concepts, misplaced boundaries, *Blocked by* edges that don't match references,
and duplicate IDs, one line each with the specs involved and a proposed home. Ask which become
pending changes, new specs or index lines.
