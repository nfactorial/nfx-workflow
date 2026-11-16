<!-- Spec: milestone-run. Behaviour changes go through it. -->
# A milestone run

Read by `/nfx:implement` when its argument names a milestone. "Step N" means a step of
`build-loop.md`; the rules folder is `../spec`, which its SKILL.md names, and rule IDs are
in its `template.md`, `lifecycle.md` and the files `lifecycle.md`'s last section maps.
Read `runs.md`, `feedback.md` and `terms.md` before M3. A run, not an answers session, reads
`milestone-start.md` once it has read the rules below, and follows it from M0.

The run is in six files, read as it reaches them: this one holds the rules below, and
`/nfx:implement` reads it for a milestone; `milestone-start.md` holds M0 to M4, read by a run
once it has read the rules, and never by an answers session; `milestone-build.md` M5 (read at
M5), `milestone-end.md` M6 to M9 (read at M6), `milestone-report.md` M10, which M10's line in
`milestone-end.md` reads, and `milestone-answers.md` M11. The answers are a session of their
own by default (`/nfx:implement <feature> Milestone <name> answers`, started as M10 tells),
which reads the run's rules, then `milestone-answers.md` (M11), the report file first and
`build-loop.md` at M11, and none of M0 to M10.

`/nfx:implement <feature> Milestone <name> [deep]` builds every change and new spec whose
**Milestone:** part names that milestone (`T-milestone`), as one run on a milestone branch
(`L-milestone-run`). The user starts it and goes: it
never waits on them from its start to its report. Anything in steps 2–6 that would stop for
the user goes on the run's list, or sets aside only its own change. `deep` applies to every
change. A change with a `Repo:` line can't be in a milestone run: the run works in one repo.

**Names.** `<feature>` is the index's folder name (the spec's ID for a feature that is one
file). Before M1, run `python3 <rules folder>/scripts/git_helper.py run-names <feature>
"<name>"` (`L-python`): `<slug>` is its `slug`, the branch its `branch` and the report file's
path its `report`; `<git dir>` is what `git rev-parse --git-dir` prints. A set-aside change's
side branch is `milestone/<feature>-<slug>--<change slug>-<run>`, `<run>` counting this
milestone's runs from 1. `<change slug>` is the change's name lower-cased, each run of
characters other than `a`–`z` and `0`–`9` made one `-` and any `-` at either end removed, as
`run-records.md`'s record name makes it (the spec's ID for a new spec).

**The list.** Every item has an ID, the change it concerns, what is asked, and a
recommendation. Its letters are **A**, **T**, **F**, **D**, **M**, **H**, **R** and **W** of *Terms*'
*Report item letters* table (`../spec/terms.md`); a **W** item names its side branch,
patch or what it waits on. An item of one change is numbered within its letter
and prefixed with that change's place in the order (**2.D1**); an item of the whole branch
(M6–M9) has no prefix (**R1**, **M1**). IDs are never renumbered, across re-runs too: a
re-run's changes take places after the last one its report used, so its first is the last
run's highest place plus one.
An item that waits on the user's answer (**W**, **M**, **D**, an **R** item you'd refer,
a **T** item left to the user, an **F** item) also has a **context**, written to the report file when the item goes
on the list, because the walk-through may come in a later session with only that file: what was found and where (file:line, spec), what the code
does now, why it matters, and what each option would change. A few lines.

**The run acts on its own recommendations, and asks only what it must** (`L-milestone-run`,
`L-triage`): a fix it makes itself is reported as done, one it leaves as left; what is referred
goes first to the answerer, which is given the items `L-milestone-run` names when it says, and
what the answerer doesn't decide waits on the user's answer. The reviewer judges `L-triage`'s test for
its own findings, leftovers and assumptions (its fix / leave / ask stands); you judge it for
each **R** item, from its text and `L-triage`'s criteria. When unsure, it waits on the user.

**The answerer's options.** Per item letter, the options an item is answered with, each given to the answerer with a description of what
it does and what it costs:

| Item | Options |
|---|---|
| **D** | every choice the item names |
| **T**, **R** | fix · leave · follow-up |
| **F** | keep · drop |

An **F** item its sources would plan into this milestone is parked, never decided (`nfx:answerer`'s *Deciding*).

**The answerer's brief.** Each answerer (M5, M6b) is briefed as `nfx:answerer`'s *Your brief*
says: the rules folder and the repo root as absolute paths, the commit it reads (so it reads
committed code), the milestone's specs and the feature's design doc, and each item as a
question, its ID as `id`, not multi-select, with its options (*The answerer's options*), its
recommendation, and its context from the report file, adding the user's earlier answers there that
bear on it. The answerer's own decisions are never given to it as the user's answers.

**Writing a verdict.** Each verdict goes in the report file under its item:
- `decide`: the item is answered with that option, marked as the answerer's, and acted on as
  the user's answer would be. An answer that sends work to planning (a **D** choice that changes what a
  spec says) is only recorded in the report file here, with the decision and item ID. Its
  *Not yet planned* line goes under the milestone's heading in the index (or in the one-file
  spec), per `T-not-yet`, with what it does, which spec it belongs to, the decision taken and
  its item ID, so a re-run's M3 sees it, and is written at M9, so no index edit sits
  uncommitted through M7 and M8.
- `park`: the item stays open, its condition and reason added to its context.
- `send_back`: the item stays open as a parked one, its misreading added to its context.
- An item with no verdict (the agent failed, left it out, or returned an option it wasn't
  offered) stays open, as with no answerer.

**Changes are folded at the end (M9), so until then the specs lag the branch.** Brief every
implementer and reviewer with this milestone's changes committed but not folded (spec path and
change name), as `L-unattended` says: they are not other pending changes to stay out of.

**The report file is the run's memory.** It holds the base branch and commit, the run number,
the step reached, each change's outcome and items, the fixes made since each change's commit,
the commit each run ended at, the checks M1 recorded, and the user's answers by ID. It is written as
the run goes, so a run cut short (a usage limit, a crash) loses nothing its commits kept, and
the user can answer it in a later session.

**The run's own files** are what `python3 <rules folder>/scripts/git_helper.py --exclude-file
<exclude file> own-files` lists (`L-python`). The exclude file is the run's, in the scratchpad: the
foreign and transient files, and the paths M1 recorded as the user's. Every commit names the run's files
by path (`git add -- <paths>`, then `git commit -- <paths>`), with the paths `own-files` lists, so
files someone else staged stay out; the helper does not commit. To **restore the tree** is
`git_helper.py --exclude-file <exclude file> restore`, and to **save a patch** is `git_helper.py
--exclude-file <exclude file> save-patch <patch file>`. The run never uses `git reset --hard`, `git
clean` or a stash; the helper undoes only the run's own files.
