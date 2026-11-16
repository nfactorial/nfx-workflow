<!-- Spec: milestone-answers. Behaviour changes go through it. -->
# A milestone run: the user's answers (M11)

Read by a session started with `/nfx:implement <feature> Milestone <name> answers`, which
reads `milestone-run.md`'s rules (everything above `milestone-start.md`'s M0), then the report file, and none of M0
to M10. Read by a milestone run when, after M10, the user asks for the walk-through in the run's own
session, and only then. M0 to M4 are in `milestone-start.md`, M5 in `milestone-build.md`, M6 to
M9 in `milestone-end.md`, and M10 in `milestone-report.md`. "Step N" means a step of `build-loop.md`, which a later session reads at M11.

M11. **The user's answers**, by ID, in this session or a later one: read the report file first, and
    record each answer in it.
    - **The walk-through.** In the answers session, or when the user asks for it in the run's own
      session after M10, ask the user each open item as an AskUserQuestion question, up to 4 per
      call, in this order:
      **W** items, **M**, the open items the answerer didn't decide (**D**,
      **T**, **R** and **F**: those it parked, gave no verdict for or never saw, such as the **D**
      items M9 adds and the items the tidy round left on the list), then each change's **H**
      item, then the milestone check. A change waiting on a parked item is asked straight
      after that item. A decided fix the run couldn't make is reopened,
      so it is asked. The done, left and decided-for-you items are not asked: they stand
      unless a reply vetoes one by its ID (`2.d1 veto: <answer>`). Each question's header is its ID, and its text
      stands on its own, since the user answers it without the report in view: the change it
      concerns, then from the item's context what was found, what the code does now and why it
      matters, then what is asked. When a context is missing or too thin to say that, read the
      code and spec it cites before asking. Its first option is your recommendation, labelled
      "(Recommended)" and described "Decision: <what it does>", then why you recommend it; every
      other option's description says what it does and what it costs. The others are the rest
      of its set below. `preview` holds the finding or code it concerns when that is clearer
      than prose. Items that share one cause are one question.

      | Item | Options |
      |---|---|
      | **W** | rebuild as is · back to `draft` · move out of the milestone · for later |
      | **M** | fix · plan as a pending change · for later |
      | **D** | *the answerer's options* (`milestone-run.md`), two at most (name any others in the text) · for later |
      | **T**, **R** | *the answerer's options*, as above · for later |
      | **F** | *the answerer's options*, as above · plan into this milestone |
      | **H** | passed · not tested yet |
      | milestone check | passed: complete it · send it back · not tested yet |

      *Other* is the user's own answer, recorded word for word: for **H**, what failed. *For later* and
      *not tested yet* record only that the item was asked (so a re-run's M6b leaves it to the
      walk-through), so the item stays as reported. *Other* saying
      "discuss" stops the walk-through once that call's answers are recorded; when it is talked
      through, it carries on with the rest. A reply can go through the done and left
      items by ID: "keep" · "undo" (a done item) or "fix" (a left one). Record each call's answers in
      the report file before the next call. Act on the answers, as below, once the
      walk-through ends; choosing *complete it* is the user saying so.
    - **A veto** of a decided-for-you item (`2.d1 veto: <answer>`) is acted on as the user's answer to
      that item would be, and recorded in the report file. When it shows a habit beyond the one
      item (its words say so, or it matches an earlier veto or a preference's subject), write a
      standing preference for it, in the form the answerer's spec gives (`- **When** <scope>:
      <rule> (<sources>)`), citing the item's ID and the date: in the project's `preferences.md`
      (in its documents folder) when it concerns the project's code or domain, else in the
      personal file (`## General`, or `## Workflow` for steering nfx; the answerer's spec's
      *Standing preferences* say which file that is); with no personal file named, give the
      preference in the report's *Decided for you* section as one to add, and write no file. A
      veto also removes the *Not yet planned* line the vetoed decision wrote (an answer that
      sends work to planning, M5 or M6b, or a follow-up M9 recorded). A project `preferences.md`
      written, and a line removed, are committed on the branch with the veto's fixes or lines.
    - The fixes in one reply, or one walk-through, including undoing a done item (`r3 undo`), undoing a decided fix (a veto), and fixing a left one,
      go to one fresh implementer as one batch, briefed with the specs they concern, the
      commits involved and the fixes, word for word; then one quick verification (as in M5)
      and one fix check (step 8). An item the fix check finds not fixed goes back once, as in
      step 8; if it still fails, restore the tree, and the item stays on the list, saying so.
      Never one item at a time. A fix that would make a spec false is
      not in the batch: it is planned (next bullet). Commit the batch on the branch, with the
      `Spec:` trailers of the specs it concerns.
    - **Work sent to planning is written down before the session ends.** A vetoed assumption
      or deviation, a fix that changes what a spec says, an **M** item answered *plan*, a **D**
      item whose choice changes what a spec says, and an **F** item answered *plan into this
      milestone* are each planned as a pending change naming the milestone, with `/nfx:spec`.
      Before that, once the walk-through or the reply is answered, write each as a *Not yet
      planned* line under the milestone's heading in the index, or in the one-file spec
      (`T-not-yet`, `L-milestone-found`): what it does, which spec it belongs to, the decision
      taken, and its item ID, so the report's context can be found. Commit those lines on the
      branch. `/nfx:spec <feature> Milestone <name>` then plans them as a set, in this session
      or a later one, and M3 refuses a re-run until they are planned. The report alone is not
      enough: `/nfx:spec` never reads it, and a new session has only the index.
    - Each **W** item is answered: rebuild it as it is, send it back to
      `draft` to replan, or move it out of the milestone with `/nfx:spec`.
    - **Follow-ups are recorded as they are decided**, as `L-findings` says, under *Later* or a
      later milestone (`L-milestone-found`), each once. The
      ones the answerer decided were written at M9's fold. One the user keeps (answered *follow-up*, or
      *keep* for an **F** item), in the walk-through or a reply (`3.t1 follow-up`), is written
      when it is answered and committed on the branch with the answers' lines; one the user drops
      (`2.f1 veto: drop`, or *drop*) has no line, or loses the line M9 wrote. A follow-up the
      milestone's outcome needs is sent to planning instead (above).
    - **Send it back:** once every **W** item is answered and every line the
      answers wrote under the milestone is planned,
      `/nfx:implement <feature> Milestone <name>` again (M2's re-run).
    - **Complete it**, when the user says so. Completing is the user's confirmation of the milestone check.
      Before anything else:
      - The milestone must be done (`L-milestone-built`): else say which line, change or spec
        is left, and wait. A change left unfolded (M9) needs a send-back, which only folds it.
      - No **M** or **D** item may be open: else list them and wait, unless the user overrides each
        one by its ID (`m2 ship anyway`). Record each override in the report file.
      - If the user's answers changed the code since M8, run the full verification once; a failure is
        a must-fix for an implementer, then a fix check (step 8). A failure still left after
        that stops the completion, as an open **M** item.

      Then:
      1. Record the follow-ups still unrecorded, the ones the user left unanswered, which are kept,
         as `L-findings` says, under *Later* or a later milestone (`L-milestone-found`), and
         commit them on the branch.
      2. Switch to the base branch the report names and `git merge --no-ff` the milestone
         branch. A conflict stops here and comes to the user.
      3. Delete the milestone's heading and `Check:` line from the index (`L-milestone-built`) and
         commit that.
      4. Push the base branch, as `L-commit-ask` says.
      5. Delete the report, its patch files and the milestone branch. List its side branches
         and delete each one the user doesn't keep.
