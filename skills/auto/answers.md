<!-- Spec: auto-answers. Behaviour changes go through it. -->
# Auto run: the user's answers

Read by `/nfx:auto answer`, in an interactive session. It reads `../implement/milestone-run.md`'s
rules above `milestone-start.md`'s M0 (*Names*, *The list*, the answerer's options, brief and verdict handling, the
report file, the run's own files), `../implement/milestone-answers.md` (M11),
`../implement/build-loop.md` (at M11), `../spec/auto.md` (the auto report's layout),
`../spec/SKILL.md` (its update mode) and `../spec/lifecycle.md` (`L-lint`), then the
auto report, and none of M0 to M10. "Step 0" means the baseline step of
`../implement/build-loop.md`, which says which changes are foreign or transient.

This is M11 applied to an auto run's report. M11 holds the walk-through's mechanics (the
question format, up to 4 per call, *Other*, *discuss*, recording each call's answers in the
report as they are given), vetoes, the fix batch, follow-ups and standing preferences; this file
states only how an auto run differs, and everything else is M11 as written. Read "the milestone
branch" there as the run branch, "the index" as the place `T-not-yet` names for the change's
spec, and "the report file" as the auto report.

## Starting

1. **The lock:** while `<git dir>/nfx/auto-running` exists and names a live process, the run is
   still going: say so and end, changing nothing. A lock whose process is gone is a dead run: choose
   the Python command (`L-python`) and run `<python> <skill folder>/driver.py --recover` with
   it from the repo root and give its output. A non-zero exit ends the session with that output,
   changing nothing more. The tree check then runs on the recovered checkout.
2. **The tree** is checked before any branch is switched to: a tree with changes that are
   not foreign or transient (step 0) ends the session, saying which, and nothing is switched.
3. **The run branch** (`L-auto-branch`) is found: the checked-out branch when it is a run
   branch (`auto/…` with no `--` in its name); a side branch (`auto/…` with `--`) or a
   `milestone/…` branch checked out ends the session, naming it; otherwise the only run branch.
   With none, say so and end, changing nothing; with more than one, name them and end.
4. **The report** is `<git dir>/nfx/auto-<date>.md` (`git rev-parse --git-dir`), `<date>` being
   the found branch's. A missing report ends the session, saying so, still without switching.
5. Only once the lock, the tree and the report have passed is the found run branch switched to,
   when it is not already checked out.

## The items asked

In *Your turn*'s order, each with the work waiting on it (asked straight after it, as M11 says):

1. *Waiting on your direction*
2. *Set aside and must-fix*, with the **W** item of a `## Session <n>: interrupted` section,
   whether or not *Your turn* lists it
3. *Human checks*, each with its pre-check verdict, what was not tried and its evidence folder
   (`<git dir>/nfx/auto-<date>/<session>/`) given in the question
4. The merge, in place of M11's milestone check

*Decided for you* is not asked and *Design gaps* is only given: a decided item stands unless a
reply vetoes it by ID (`2.d1 veto: <answer>`), acted on as M11 says and recorded in the report,
and a veto that shows a habit writes a standing preference, as M11 says. A veto removes the
*Not yet planned* line the vetoed decision wrote, as M11 says.

**Options.** M11's table applies, with these differences, since a run has no milestone to move
work into or out of: a **W** item's options are **rebuild as is** (the change goes back to
`ready`, so the next run builds it again) · **send to planning** (a *Not yet planned* line, as
below) · **drop** (the pending change, or the new thing's spec, goes back to `draft` in its spec, with
a line under its *Unanswered questions* saying the run set it aside and why, from the report, so
it is not rebuilt until planned again; the spec is linted (`L-lint`) and committed on the run
branch with a `Spec:` trailer only, no `Spec-Change:`; its side branch and patch are deleted
with the merge's cleanup) · *for later*. An **F** item's options
are keep (a *Not yet planned* line under *Later*) · drop. One the answerer parked because a
source would plan it into a milestone also has **plan into <milestone>**, when its change's
**Milestone:** part names one: a *Not yet planned* line under that milestone's heading, written as
work sent to planning is.
There is no milestone-check row. The **W** item of an interrupted session's section has its own
options: **discard the patch** · **keep the patch** (moved to `<git dir>/nfx/` with the merge's
cleanup, saying where) · *for later*. Neither edits a spec, since the session's commits stay on
the run branch and its other items are asked as usual. A **Q** item and the merge are below.

## A Q item

A Q item (a planning question parked or sent back) is asked with the planner's options from its
context in the report, its recommendation first (M11's question format), and *for later* last.
A Q item parked with no options (it needs a spike, or was left unasked) is asked as an open
question offering *for later* and *Other*. Its answer is folded
into the work's spec as `/nfx:spec`'s update mode folds an answered question: the parts it
affects rewritten throughout, the question deleted from *Unanswered questions*, and the work
promoted to `ready` once none is left. The spec is linted (`L-lint`), and the fold is committed
on the run branch with a `Spec:` trailer for the spec only, no `Spec-Change:`. An answer of
*for later* leaves the question as reported.

## The merge

Asked last, with the options **merge it** · **not yet**, and **revert that change's commits
first, then merge** besides when a failed human check was sent to planning (below). *Not yet*
records only that it was asked.

*Merge it* is M11's *complete it*, with these differences: no milestone-done condition
(`L-milestone-built`) applies and no milestone heading is deleted from an index (its step 3 is
dropped). In order:

1. No **M** or **D** item may be open and every **W** item must be answered (one answered *for
   later* counts as unanswered): else list them and merge nothing, unless the user overrides each by its
   ID (`2.m1 ship anyway`, `2.w1 merge anyway`), recorded in the report. An overridden **W**
   item goes ahead unanswered, and its side branch and patch are always kept: step 8 never
   deletes them.
2. When *revert that change's commits first, then merge* was chosen, revert that change's
   commits on the run branch, its fold commit included (naming them from the report). If a later
   change on the branch is blocked by or built on it, list both and merge nothing.
3. If the user's answers changed the code (a revert included), run the full verification once (a
   failure is handled as in *complete it*).
4. Record the follow-ups still unrecorded, as *complete it* does, and commit them on the run
   branch.
5. `git switch <base>`, the base branch being the name before ` @ ` in the report's **Base:**
   line, noting its commit, and `git merge --no-ff` the run branch. A conflict stops here and
   comes to the user.
6. Verify the merged result (the base may have moved since the run). A failure undoes the merge
   (`git merge --abort` before it is committed, else reset the base branch to the commit noted
   in step 5, which is before anything is pushed) and comes to the user.
7. Push the base branch, as `L-commit-ask` says.
8. Before deleting the run's folder `<git dir>/nfx/auto-<date>/`, move the patch of every
   overridden **W** item and of every interrupted session's **W** item answered *keep the
   patch*, which it holds, to `<git dir>/nfx/` beside it, saying where. Then
   delete the run branch, the report and the folder. List the side branches (`auto/<date>--…`)
   and delete each one the user doesn't keep, bar the side branch of an overridden **W** item.

## A failed human check

What the user says failed, recorded word for word as M11 says. A fix that leaves every spec true goes
into the answers' fix batch before the merge, as M11's fixes do. One that changes what a spec
says is sent to planning (below), and the merge question then also offers the revert option
above.

## Work sent to planning

Each is written down as a *Not yet planned* line (`T-not-yet`) with its item ID, as M11 says,
under the milestone the change named, as the item's context in the report gives it, or under
*Later* when it named none (`L-milestone-found`). The lines are committed on the run branch,
before the merge, as M11's are.
