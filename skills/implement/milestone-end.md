<!-- Spec: milestone-run. Behaviour changes go through it. -->
# A milestone run: the end (M6 to M9)

Read by a milestone run when M5 has finished its last change (`milestone-build.md`), in the end
session M5 starts, or when M3 sends a re-run with nothing left to build straight to M6 or to M9
(`milestone-start.md`). M9 ends by sending the run to M10
(`milestone-report.md`).
The run's rules are in `milestone-run.md` and M0 to M4 in `milestone-start.md`, which the run
has read, and M5 in `milestone-build.md`. "Step N" means a step of `build-loop.md`.

M6. **End reviews.** Run the reviews the project's CLAUDE.md requires before a commit, once,
    over the branch from the base, or on a re-run from the commit the last run ended at (for
    `/code-review`, the level a full review would use if any change had one, otherwise `low`).
    Their findings go on the list as **R** items, each naming the change it concerns, with
    your recommendation (fix, leave or follow-up) and whether `L-triage` would refer it. An R
    item that repeats an item already on the list is merged into it.
M6b. **Answer the rest.** Gather the items `L-milestone-run` gives the answerer that have no
    verdict yet: the **R** items, items carried over from an earlier run, and items the
    answering of M5 failed on or left out. Leave out **W** items, and any item
    carried over from an earlier run (M2) that the report file shows the user was already asked and
    answered *for later*: these stay open for the walk-through. With none, skip this step.
    Otherwise spawn one `nfx:answerer` agent with the answerer's brief (`milestone-run.md`), the
    branch's HEAD commit being the commit it reads.

    Write each verdict to the report file as *Writing a verdict* (`milestone-run.md`) says. An
    item decided as a fix joins the tidy round (M7).
M7. **Tidy round, once.** Gather every item recommended as a fix and not referred: the **T**
    items and the leftovers no step 6 round carried (a passing review's, or those found after the
    round limit) that the reviewers recommended fixing, the **R** items you did, and the items
    the answerer decided as a fix at M6b (M5's are already committed). Give
    them in one batch to a fresh implementer, as a milestone run, with the specs they concern;
    then verify (a quick verification: lint, the type check, and the tests of the files the
    batch touched). A failure goes back to the same implementer
    once; if it still fails, restore the tree, and every item stays
    on the list, saying so. Otherwise spawn a fix check (step 8). An item the fix check finds not fixed
    goes back once, as in step 8, then a quick verification again; if that fails, restore the
    tree, and every item stays on the list, saying so. Commit the
    batch, with the
    `Spec:` trailers of the specs its items concern, and mark each item it closed as done in
    the report; one still not fixed stays on the list, saying why, with the commit named. An
    item the answerer decided as a fix that the run could not make (a restored tree, or
    still not fixed; in M5, a batch that still fails) is **reopened**: no longer marked as the answerer's, so M10 does not list
    it under *Decided for you*, and M10 and M11 treat it as an open item the answerer didn't
    decide.
M8. **The end verification, once.** Run the full verification (step 4, every verification step). If it
    fails, give the failure and the branch's diff from the base to a fresh implementer, as a
    milestone run, then verify again and spawn a fix check (step 8). Commit what it fixes, with the
    `Spec:` trailers of the specs it concerns. A fix that needs more than the code to change
    (a new requirement, an interface another thing relies on) is not made: it goes on the list
    under **M**, as does a failure left.
M9. **Fold, once.** Spawn one `nfx:spec-folder` agent to fold every change committed in this run,
    and any an earlier run committed but didn't fold. Its brief:
    - the rules folder, written out as an absolute path
    - the changes in the run's order (spec path and change name), each one's Assumptions and
      Deviations with the reviewer's triage, and the fixes since each change's commit, from
      the report file

    It returns the lint result, the follow-ups, its consistency edits, and what its reference
    check found. Then:
    - A false claim in a spec the run didn't touch, or a stale change or unbuilt spec outside
      the milestone, becomes a **D** item with its proposed fix.
    - A change of this milestone whose spec relied on behaviour an earlier change altered
      becomes a **D** item when committed already, recommending its code and spec be looked at;
      set aside or waiting, its **W** item gets the reason and the recommendation to go back to
      `draft`, and no **D** item is added.
    - Commit the folds as one commit on the branch, with a `Spec:` trailer per spec edited and
      a `Spec-Change:` trailer per change folded. Just before it, write the answers the answerer
      recorded (M5, M6b) as sending work to planning, each as a *Not yet planned* line as *Writing a verdict* (`milestone-run.md`) says, and commit them with it. Write the follow-ups the answerer decided
      (a **T** or **R** item decided *follow-up*, an **F** item decided *keep*) too, as
      `L-findings` says, under *Later* or a later milestone (`L-milestone-found`), never under
      this milestone's heading, whatever a verdict's reason says, and commit them with it. An **F** item recommended *plan into this
      milestone* is not one: the answerer never sees it.
    - If the fold or its lint fails, restore the specs and leave them unfolded: the code stays
      committed, and it goes on the list under **M**, to be folded by the next run. The
      *Not yet planned* lines, follow-ups included, are then committed on their own.
M10. **Report.** Read `milestone-report.md` and follow it.
