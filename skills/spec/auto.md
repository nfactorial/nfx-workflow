<!-- Spec: auto-mode. Behaviour changes go through it. -->
# Auto mode

Read by `/nfx:spec` and `/nfx:implement` when `auto` is the last word of their arguments:
`/nfx:spec <feature> auto`, `/nfx:implement <feature> auto` and `/nfx:implement <feature> finish
auto`. Only `/nfx:auto`'s driver
starts a session this way; neither skill's `argument-hint` shows it, because a session the user
is in asks them instead. Each skill's own auto-mode steps say what it does; this file holds
what the sessions of one run share: the branch, the report, the work that waits on the user,
and where the rules auto mode sets aside are stated. "Milestone run" rules are
`L-milestone-run` in `runs.md`, and `../implement/milestone-run.md` holds its
report's items.

## What a session in auto mode does

- **Its kind.** A session is a planning session (`/nfx:spec <feature> auto`), a build session
  (`/nfx:implement <feature> auto`) or a finish session (`/nfx:implement <feature> finish
  auto`). A finish session starts on a run branch whose last change is committed and not
  folded, and folds it; the driver runs one after each build session that commits its change.
- **It never asks.** It calls no AskUserQuestion and never stops to wait. Where its procedure
  would ask, the question goes to the answerer (`nfx:answerer`), or, for the shape of work
  that the procedure has the user agree, its own proposal stands and is recorded. Where its
  procedure would stop for the user, it records why and ends.
- **Rules set aside.** A session sets the core rules aside as `L-unattended` in
  `runs.md` says, in its entries for every unattended run and in those for auto mode
  alone.

## The branch

**The run's branch.** `L-auto-branch` A run works on one branch, `auto/<date>`, `<date>` being
the day (`YYYY-MM-DD`) its first session started, and never pushes it. A **run branch** is an
`auto/…` branch whose name holds no `--`; a **side branch** is one whose name holds `--`
(`auto/<date>--<slug>`), kept for set-aside work, and is never a run's branch. A session finds
its work first, then takes the branch, by the first of these that holds:

1. The current branch is a run branch: it works there.
2. Another run branch exists: it stops, naming it, because the last run isn't merged.
3. Otherwise it creates `auto/<today>` from the current branch with `git switch -c`.

A session that finds no work creates no branch.

**The checkout.** A session starts only from a tree whose changes are all
foreign or transient (`/nfx:implement`'s step 0), with no live run record
(`../implement/run-records.md`), with no `milestone/…` branch or side branch
checked out, and, with a run branch checked out, only when its report exists, because without it
the run's waiting work can't be known; else it stops, saying why. It checks this before finding
its work. It never takes a worktree.

## The report

**The report file.** `L-auto-report` `<git dir>/nfx/auto-<date>.md` (`git rev-parse --git-dir`).
Its first line after the title, before *Your turn*, is `- **Base:** <branch> @ <full commit
hash>`, recorded when the branch is created and never rewritten (the auto loop's driver reads
the base from it). Then one section per session, in order, numbered from 1: each opens with the
heading `## Session <n>: <command>`, `<command>` the session's own command as the driver gives it
(`/nfx:implement documents/specs/a auto`), and a section the driver writes for an interrupted session
is `## Session <n>: interrupted`, numbered in the same sequence; then the session's
outcome (what it planned or built, with its commits, or that it
found no work); and its items with their contexts.

A session writes the file as it goes, so a session cut short loses nothing its commits kept. A
stop, and a session that finds no work, is said in the session's output, and recorded as the
session's section only when a run branch is checked out and its report exists; otherwise the
session writes nothing and creates no branch.

**Item IDs.** Every item a session records is numbered within its letter and prefixed with the
session's number (**3.D1**), its whole-session items included (**3.R1**). Its letters are **A**, **T**, **F**, **D**, **M**, **H**, **R**, **W** and **Q** of
*Terms*' *Report item letters* table (`terms.md`); a set-aside change is a **W** item. IDs are never renumbered.

**Evidence folders.** The evidence folder of a session's pre-check is
`<git dir>/nfx/auto-<date>/<session>/`, and `<session>-2/` for its second pre-check.

**Your turn.** The report opens with *Your turn*, rewritten at the end of each session from
every session's items. It opens with the two-line legend `../implement/report.md` gives, its
example IDs session-prefixed (`2.d1 option b, 3.t1 fix, 2.d1 veto: <answer>`) and its second line
saying that a decided-for-you item stands unless a reply vetoes it. Then, in this order:

1. **Waiting on your direction:** each parked or sent-back item, and each item recorded as
   waiting on the user, by ID, with its question, the answerer's condition or misreading, and
   the work waiting on it, directly or through other work.
2. **Set aside and must-fix:** each **W** item with its side branch or patch, and each
   open **M** item, with the work waiting on it.
3. **Human checks:** each built change's **H** item, with its pre-check verdict, what was not
   tried, and its evidence folder.
4. **Decided for you:** one line per item the answerer decided (its ID, the answer and the
   reason), grouped by session; in each group, the items with a `near` condition first, each
   tagged with it, then the rest by ID.
5. **Design gaps:** each decided item with `near: 2`, as a milestone run's report gives them
   (`../implement/milestone-report.md`, M10), ending with `/nfx:interrogate <the design doc>`;
   left out when there is none.

A part with nothing in it is left out.

## Waiting work

**Work that waits on the user.** `L-auto-waiting` Work (a pending change or an unbuilt spec)
waits on the user when a session has recorded, on it or on work it is blocked by, a cause only
the user can settle; the cases are examples of that, not a closed list:

- its *Unanswered questions* hold a question a session recorded as waiting (parked, sent back
  twice, left unasked after the rounds, or needing a spike), or an open **M** item from its
  plan review;
- it was set aside;
- it is a pending change, or a new spec, committed on the run branch but not folded: the
  report records it as committed, or a commit on the branch since the report's base commit
  carries both a `Spec:` trailer naming its home spec's ID and a `Spec-Change:` trailer naming
  the change (for a new spec, a `Spec-Change:` naming the spec's ID). It waits on an **M**
  item, "committed, not folded", and is never built again;
- it is a pending change in a spec that holds a change committed but not folded: it waits on
  that change's **M** item, because a spec's changes fold in build order;
- it was refused when picked, by `/nfx:implement`'s step 1 checks (a `[ready]` change or
  `ready` new spec with *Unanswered questions*, an old-format spec it edits) or by auto build's
  refusal of a `Repo:` line (a change's own, or a new spec's header's): it waits on an **M**
  item, "refused: <the check>", the check being "unanswered questions", "old-format <spec ID>"
  or "`Repo:` line";
- auto planning found it needing a conversion: its home spec, a spec its *Changes* items edit,
  or a spec its planning would edit or create a line in is old-format (`T-version`). It waits
  on an **M** item, "needs conversion: <spec ID>", one per spec, and the user converts it with
  `/nfx:spec <spec>` in a session of their own;
- a session's reference check found it relying on behaviour a build changed;
- it is blocked, directly or through another, by waiting work, or by a change a session built
  (named by its spec once it is folded) that has an open **M** item, a **D** or **T** item the
  answerer parked or sent back, or a **D** item the answerer decided with a choice that sends
  work to planning.

Its record in the report names the item it waits on, through any blocker. A session that finds
work waiting for one of these causes, which the report doesn't yet record, records its **M**
item in its own section, whatever its outcome, when it has a section. A session never plans or
builds waiting work. Status mode doesn't read the report, so each skill drops the waiting work from status
mode's items before choosing.

**Sweep.** Each session deletes every `auto-<date>.md` report and `auto-<date>/` folder in
`<git dir>/nfx/` whose `auto/<date>` branch no longer exists.
