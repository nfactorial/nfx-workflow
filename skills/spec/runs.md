<!-- Spec: process-rules. Behaviour changes go through it. -->
# Runs

When a milestone is done, where work found during one goes, the milestone run's own rules and
the rules an unattended run sets aside. A milestone run reads this file before M3, auto mode
with `auto.md`, and `/nfx:spec` for a `Milestone <name>` target. The other rules are in
[template.md](template.md), [lifecycle.md](lifecycle.md), [feedback.md](feedback.md) and
[milestones.md](milestones.md).

## Milestone runs

- **A milestone is done** `L-milestone-built` once no line is left under it and no pending
  change or unbuilt spec names it in a **Milestone:** part. The report then gives its milestone
  check. Once the user confirms it (completing a milestone run confirms it), its heading and
  `Check:` line are deleted. When the milestone check fails, the milestone stays open: a fix that leaves
  every spec true is made by the milestone run's answers (its fix batch and fix check), or, with no
  run, as a quick fix in the main session (`L-outside`); one that changes what a spec says is
  a pending change, planned now, naming the milestone.
- **A milestone run defers the user's part to its end.** `L-milestone-run` When the user asks
  `/nfx:implement` for a milestone, it builds every change naming it on a milestone branch
  (procedure in `implement/milestone-run.md`), and sets the core rules aside as
  `L-unattended` says. On that branch:
  - The fixes the reviews recommend that pass `L-triage`'s test are made by the run itself, at
    its end. Open questions, the findings and assumptions `L-triage` refers, the deviations
    `L-deviations` sends to the user, follow-ups and human checks go to the run's report
    rather than stopping it.
  - **The answerer (`nfx:answerer`) answers what it can of them, in the user's place.** The
    items are named by the letters of the run's list (`milestone-run.md`, *The list*):
    - It is given the **D** items, the **T** items the reviewer marked *ask*, the **R** items
      the run would refer, and the **F** items bar those recommended *plan into this
      milestone*.
    - It is never given human checks, the milestone check, **M** items, or set-aside or
      waiting changes: they need the user's judgement of the running product, or a failure
      only the user can settle.
    - A change's own items are given to it once the change is committed and before the next
      change is built, because later changes build on what its answers decide; the rest at
      M6b, before the tidy round (M7). The **D** items the fold (M9) adds go to the user,
      unseen by the answerer.
    - What it decides is acted on as the user's answer would be and reported as *Decided for
      you*, to be vetoed by ID; what it parks, or gives no verdict for, waits on the user's
      answer.
    - A change waits when a change it is blocked by, directly or through another, has a **D**
      or **T** item the answerer parked or sent back, or a **D** item it decided with a choice
      that sends work to planning: it would build on a direction the user hasn't settled, or
      on a spec about to change. A parked **F** item, an item with no verdict and a reopened
      item make no change wait.
  - Merging the branch is the user's confirmation of every change on it, and of the
    milestone check.
- **Work found during a milestone** `L-milestone-found` (`T-found`, `L-findings`) goes under
  the milestone when its outcome needs it, otherwise under *Later* or a later milestone. Ask
  the user when it is unclear.

## Unattended runs `L-unattended`

A run with no user present (a milestone run, an auto-mode session) sets aside these core rules
for what each entry says holds instead. This is the one list: the entries for auto mode alone
are in it too, each naming auto mode, and no other file holds a list of its own.

- Each change is committed once its review passes, without asking and before the user's human
  check, on the run's branch only, which is never pushed; what would wait on the user goes to
  the run's report (`L-same-commit`, `L-commit-ask`).
- The reviews the project's CLAUDE.md requires before a commit run once, at the run's end,
  over the commits the run made (`L-commit-ask`).
- A committed change satisfies a *Blocked by*, so the run builds on changes whose human check
  is not confirmed (`L-built`).
- The implementer and every reviewer are briefed with the run's changes committed but not
  folded, whose *Changes* items, Assumptions and Deviations count as part of the body
  (`L-fold-in`).
- The run's changes are folded at its end, once every one is committed, together, in one
  commit, without their human checks, and a new spec is marked `built` there, because merging
  the branch confirms them (`L-fold-in`, `L-status`).
- Every assumption and deviation is folded as built, because on the run's branch the code is
  the authority; one the user later rejects becomes a pending change, naming the milestone the
  change named when it named one (`L-accepted`, `L-deviations`).
- The reference check's findings go to the run, and a false claim in a spec the run touched is
  corrected as part of the fold, since it is touched (`L-fold-check`).
- Follow-ups are recorded by the run's fold (M9, or auto build's fold), each as soon as the run
  or the user decides to keep it, rather than by each change's fold (`L-findings`).
- A change's code commit carries its `Spec:` and `Spec-Change:` trailers, ahead of its fold,
  and a fix commit carries a `Spec:` trailer for each spec whose change it fixes
  (`L-trailers`).
- In auto mode alone, a session outlines a feature into milestones without being asked
  (`L-milestone-ask`).
- In auto mode alone, the only branches a session merges or deletes are its own side branches
  (`L-commit-ask`).
