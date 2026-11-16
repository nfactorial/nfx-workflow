<!-- Spec: implement-skill. Behaviour changes go through it. -->

The shape of a single run's report. `single.md`'s step 7 reads it.

It is read top to bottom and ends at the user's prompt, so it has two parts: first
what the user reads through, then everything they have to respond to, with the most important last,
right above their next input. Every item the user might answer starts with a bold ID, its letter and its number
within it (e.g. **D1**, **T3**). This report uses **C**, **A**, **T**, **F**, **D** and **M**;
the letters are defined in *Terms*' *Report item letters* table in `../spec/terms.md`,
and the milestone run's and auto's reports use more of them. The user replies by ID, in any order or case (`d1 option b, t3 fix, a2 veto`). An item
in *Needs your decision* or *Must fix* that the user doesn't mention is still open; ask about it
rather than assume. A **T** item the user doesn't mention takes its recommendation, and an **F**
item is kept. The IDs hold for the rest of this session and are never renumbered. Items
that share one cause (the same missing feature of shared code, the same convention) are
given once, under the lowest ID, naming the IDs it covers; an answer to it answers them all.
The fix check batch (`build-loop.md` step 8) for the user's first reply includes every **T** item recommended as a fix that they didn't
mention.
Give, in this order:

*To read:*
- the implementer's summary and reading map
- **Cleaned up:** the leftovers you applied in the loop (`build-loop.md` step 6), one short line each with file:line.
- **Auto-accepted:** the assumptions the reviewer accepted, and the deviations it accepted
  under `L-deviations`'s exception, one short line each. The user can veto one (`a2 veto`); the rest
  are folded as `L-accepted` says.
- **Left as is:** should-fix and nit items the reviewer recommends leaving and didn't refer
  (preferences, harmless nits), one short line each. The user can still ask for one (`t4 fix`).
- the final build verdict (which modes and tests ran, and what didn't) and review verdict,
  including the reviewer's coverage verdict
- one line: `Run:` the fix rounds and what triggered each, whether the limit was hit,
  transient files ignored, and anything else that slowed the run (e.g. a missing report, a
  re-review disputing earlier triage)

Then a `---` rule and a **Your turn** heading. Directly under the heading, with every report, goes
a two-line legend. The first line shows a reply by ID in any order or case, with one example for
each answer the report takes (`d1 option b, t3 fix, a2 veto, f2 drop`); the second says what an
item the reply leaves out becomes (a **T** item takes its recommendation, an **F** item is kept,
a **D** or **M** item stays open). Under the legend, together:
- **For your triage:** the should-fix and nit items recommended as a fix, and leftovers you
  didn't apply (with why), each with its recommendation.
- **Follow-ups:** findings outside this change's scope (gaps in shared code, out-of-scope
  notes, the reviewer's Code health notes), one line each, naming the spec of the thing it
  concerns (or "new thing"). The user can drop one (`f2 drop`) or have it planned now (`f1 plan`);
  `/nfx:spec` records each as `L-findings` says.
- **Needs your decision:** deviations not auto-accepted, open questions, and assumptions
  and findings the reviewer marked *ask*. One per line with its location, the reason, and the reviewer's view inline (e.g.
  "*reviewer: fine, matches Fixed*"). A rejected assumption sends the change back to
  planning.
- **Must fix:** must-fix findings still open after the round limit. If the verdict is not
  PASS, say here whether the cause is the **spec** (a gap, an ambiguity, a wrong statement in
  the change), which means going back to the plan phase to fix it before re-running, or the
  **execution** with a sound spec (re-run with `deep` / finish together / override the
  reviewer). Give the reason.
- **Next steps**, always last (below).

Leave out any section that has nothing in it, with no heading and no "none". The build and
review verdicts, the `Run:` line and the next steps are always given.

The next steps: the human check must test the code that will be committed, so anything
that can still change the code comes first:
1. If the project's CLAUDE.md requires other reviews before a commit (e.g. `/code-review`),
   they come next, with their findings settled. For `/code-review`, give the command with
   the level `build-loop.md` step 2 chose, because a bare one reuses whatever level the user typed last; `low` also
   suits a change that is mostly data, docs or config. The user can change it. When their findings are settled, give each one outside this
   change the next free **F** ID, as a follow-up.
2. Then the change's human check from its "Done when", in the worktree when the run has
   one (give its absolute path), giving any file it needs as an
   absolute path or the exact command that produces it. If those reviews changed the code,
   the human check comes after their fixes. Small by-eye value tweaks may be made during it
   (`L-tweak`).
3. Once the user has confirmed the human check, `/nfx:spec <spec-path> <change name>` folds the change into
   the spec's body, with the accepted assumptions and any values tuned during the human check,
   records the follow-ups as `L-findings` says, deletes the change-only material, and commits
   that with the code.

Do not commit yet: the commit is that `/nfx:spec` step's. If the change's knobs still have a
tuning change of their own, remind the user that it's the next, main-session step.
