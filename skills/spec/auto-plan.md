<!-- Spec: spec-skill. Behaviour changes go through it. -->
# Auto plan

Read by `/nfx:spec` when `auto` ends its target, after `auto.md`, `runs.md`, `terms.md`, `template.md`,
`lifecycle.md`, `folders.md` and `later-work.md` (auto planning outlines milestones, creates specs
and writes *Not yet planned* lines) and, for a milestone, `milestones.md`. "Step *n*" means a numbered step of `SKILL.md`. An
interactive session never reads this file.

`/nfx:spec <feature> auto` plans a feature's next work with no user present, as `/nfx:auto`'s
driver runs it. It follows [auto.md](auto.md) (`L-auto-branch`, `L-auto-report`,
`L-auto-waiting`). It runs steps 1 to 4 as written, but for the differences below.

**It never asks.** It calls no AskUserQuestion. A question goes to the answerer, because a
planner that judged its own questions would tend to confirm itself; a shape it would agree with
the user stands as proposed.

**Starting.** Sweep the run reports and folders, and check the checkout, as `auto.md` says. A
stop, and finding no work, are said and recorded as `L-auto-report` gives them. Then find the
work (below); with none, end. With work,
take the branch (`L-auto-branch`), start the report if the branch is new, and start the
session's section: its heading (`## Session <n>: <command>`, `L-auto-report`, `<n>` the last
section's number plus one, or 1) and the commit it starts at.

**Its work**, the first that applies, leaving out waiting work (`L-auto-waiting`), read from
`spec_lint.py --status <feature> --json`:

1. the first `draft` pending change or unbuilt spec of the feature, in status mode's order: it
   plans that work, and its *Unanswered questions* are its first questions
2. else, when the feature's *Not yet planned* is a plain list with lines and no milestones: it
   outlines them (`milestones.md`, *Outline*) with its own proposal standing in for the user's
   agreement, commits the outline as that procedure says, and goes on to 3
3. else the first milestone that is not done (`L-milestone-built`): when it has lines, it plans
   them as a set, as a `Milestone <name>` target, reading `milestone-plan.md`; when it has none,
   there is no work, since its planned work is to be built first
4. else there is no work

Lines under *Later* are never planned.

**Never converting.** Auto planning converts no spec: where step 1 would convert a touched
old-format spec first, it records the work as waiting, "needs conversion" (`L-auto-waiting`),
and takes the next work, so `conversion.md` is never read in auto mode.

**The shape** (step 2) is not put to anyone: its proposal stands, and the session's report
section records it in one line per spec or change (new or changed, its *Blocked by*, its
delegation).

**Questions.** Every decision step 2 would leave unsettled, and every choice it would put to the
user, goes to the answerer as a question with an ID (**Q** items, numbered as `auto.md` says),
its options, its recommendation and its context: what was found and where, what the code does
now, why it matters, and the user's earlier answers in the specs and design doc that bear on it
(the run's own decided items are never given as the user's answers). Spawn one `nfx:answerer`
per round, at the branch's HEAD commit, with the rules folder and repo root as absolute paths
and the feature's design doc and specs as paths. A question that depends on one not yet decided
waits for the next round, up to three rounds; a question still unasked after them is written to
*Unanswered questions* and recorded as waiting on the question it depends on. By verdict:

- `decide`: write the answer into every part it affects, as an answered question would be, and
  record it under *Decided for you* with its `near`.
- `park`: write the question to the work's *Unanswered questions*, which keep it `draft`, and
  record it as waiting, with its condition.
- `send_back`: rewrite the question once from the misreading and ask it in the next round; sent
  back again, it is parked.

**Spikes and tuning.** A choice that needs a spike is written to *Unanswered questions* and
recorded as waiting on the spike. A tuning change is planned as step 2 would plan it.

**The plan review.** Each change or new spec it would make `ready` is first reviewed by one
`nfx:plan-reviewer`, given the rules folder and repo root as absolute paths, the spec path and
change name (none for a new spec), and the design and technical docs. Make each finding's
`fix`; a fix that needs a choice the rules don't settle is a question for the next round. When
you made a `must-fix` finding's fix, spawn a fresh plan reviewer once more. A `must-fix` finding
still open is written to *Unanswered questions*, and the work stays `draft`, waiting on that
finding as an **M** item. Each `out_of_scope` entry is an **F** item, written as a *Not yet
planned* line under *Later*.

**Ready.** Work is made `ready` once it has no unanswered question and its plan review left no
`must-fix` finding open.

**The commit.** Once the lint (`L-lint`) passes on every document written, commit them on the
run's branch in one commit, without asking (`L-unattended`), with a `Spec:` trailer for each spec
created or edited. When the lint still reports an ERROR in a document touched, restore the
documents written, record the ERROR as an **M** item, and the work waits on it.

**The report.** Write the session's section as it goes (`L-auto-report`): the work planned, each
spec and change with its status, the shape, and its items; then rewrite *Your turn*. End the
chat output with a short summary of the same.
