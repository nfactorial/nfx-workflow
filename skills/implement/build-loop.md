<!-- Spec: implement-skill. Behaviour changes go through it. -->

The steps every run shares, read by its procedure: `single.md` at its start (its step 7 is the
report), a milestone run at M1 (M11 when answering), auto build when starting.

**The change** is the pending change being built, or a new thing's whole spec while it isn't
built. This main session only orchestrates it through subagents, reading no source file or
diff itself (step 6's leftovers the one exception) and keeping its messages short. If
the change has a `Repo:` line (its own, or a new spec's header), every git command below runs
in that repo. What a step **raises** (a stop and its reason, a question, a choice made) is the
procedure's to handle: a milestone or auto run handles it as its rules handle an ask.

0. **Baseline.** Run `git status`. The implementer's changes must be the only uncommitted
   changes, so the reviewer reviews only them and a failed attempt can be set aside cleanly.
   Files the project's CLAUDE.md says to keep out of commits don't count: note them as
   transient. Nor do changes under the documents folder's `exploration/` and `design/`,
   including ones that appear during the run (a `/nfx:mockup` session may pause or settle
   beside it): note them as foreign. Write the transient and foreign files, one repo-relative
   path per line (a folder ends in `/`), to the run's exclude file in the scratchpad, always
   written (an empty file when there are none); extend it when a file turns out to be one.
   Then read `run-records.md`. If there are other uncommitted or untracked
   changes, a live record names this checkout, or a `milestone/…` branch is checked out, the
   checkout is busy: follow `worktree.md`'s *Is the checkout busy?*. It either stops, raising
   a request to commit or stash them first (or to explicitly confirm carrying on), or moves
   this run into a worktree of its own once step 1 has picked the change. (For a `Repo:`
   change, do this check once step 1 has picked it.) Step 0 also raises a stop, before step 1,
   when the project's CLAUDE.md names neither a build agent nor the checks to run before a
   commit, saying that verification (step 4) has nothing to run: no implementer is spawned.
   One that names either goes on.
1. **Pick the change and confirm it's ready** (`L-ready`, `../spec/lifecycle.md`).
   Given a spec path with no change name, a spec not yet built is the change itself; a built
   one uses its first `ready` pending change whose *Blocked by* are all satisfied (`L-built`).
   Given a folder, read `pick.md`, which picks and names it; given a path, raise which. The checks
   below apply to either. Read only the spec's header lines, the change's heading,
   *Blocked by*, *Delegation* and *Unanswered questions*, each blocker's status, and the
   current version at the top of `../spec/template.md`. Stop, raising why, if it is still
   `draft`, an unanswered question remains, a blocker isn't satisfied, or its Delegation line
   says "main session only": in the first two cases the next step is planning it
   (`/nfx:spec`, or `/nfx:interrogate` for several questions), not implementing. If the spec
   is old-format (no `Template` line, or one below the current version: `T-version`), or
   the change edits another spec that is, stop, raising `/nfx:spec` to convert it first.
   Then, outside a milestone run and for a change with no `Repo:` line, follow
   `run-check.md`. Once it passes, write this run's
   record, or, when step 0 chose a worktree, follow `worktree.md`'s *Make the worktree*,
   which writes the record there.
2. **Choose the levels.** Read them from the change's *Delegation* line, and raise which; one
   that names no implementer or no review takes `T-minimum`'s default (`lifecycle.md`):
   - **Implementer:** always the `nfx:implementer` agent. If `deep` was given or the line says
     deep, spawn it with `model: "opus"` and `effort: "high"`; otherwise pass no model or
     effort, and it runs as its definition says.
   - **Review:** `light review` spawns every `nfx:spec-reviewer` with `model: "sonnet"` and
     `effort: "medium"`, and uses `/code-review low`. `full review` spawns it as its
     definition says, with `/code-review` at the level the project names, or `medium`.
   - **Fix checks** (step 8) always spawn `nfx:spec-reviewer` with `model: "sonnet"` and
     `effort: "medium"`.
3. **Delegate.** Give the implementer the spec path and the change name (none for a new
   thing's spec), plus the repo root if the change has a `Repo:` line (also pass it to the
   build agent and every reviewer). If this conversation holds decisions not yet in the
   change, list them in the prompt and raise them, so the spec can be updated. The
   tests are the implementer's to choose (`T-acceptance`); its report says
   which test covers each requirement and criterion, and which assertion in it would fail if
   that behaviour broke. Wait for its report.

   **If it finishes without a report** (e.g. it stopped with background work
   running), don't resume it to ask for one. Run `git status`. If the
   change's files changed, carry on and tell the reviewer the report is missing. If nothing
   changed, stop, raising it.
4. **Verify.** Read `verify.md` and follow it.
5. **Review.** Spawn a fresh `nfx:spec-reviewer` with the spec path, the change name, the rules
   folder (`../spec` from this file's folder, as an absolute path), the build report
   (step 4), the implementer's Assumptions, Deviations, Coverage and Code health sections (not
   the rest of its report), and the transient and foreign files to ignore. It reviews the
   uncommitted changes, checks the coverage, triages the assumptions and gives its view on
   each deviation.
6. **Loop.** A fix round runs only if the verdict is CHANGES_REQUIRED. Send ONLY the must-fix
   findings, plus that review's leftovers, back to the same implementer (continue it, keeping
   its context), then verify (step 4) and spawn a fresh reviewer. Tell it this is
   a re-review, and give it everything step 5 gives (with this round's build report), plus
   the earlier findings, the two snapshot trees, the round's files and the files set aside as
   the other run's (step 4), not the diff's text, the earlier triage of assumptions and
   deviations (which stands), and any Assumptions, Deviations, Coverage and Code health the
   fix round reported. If the implementer went without a report, use a fresh one, told its
   changes are already in the working tree. Maximum 2 fix rounds.

   **Leftovers never start a round.** When the loop ends, apply yourself every leftover no
   round carried (a passing review's, or any found after the round limit). Read only the lines
   each one names. Apply only fixes that change no behaviour; a leftover that needs judgement,
   or that you can't confirm changes no behaviour (e.g. a branch you can't show is
   unreachable), is raised instead. Then verify again (step 4). If that fails, undo your
   cleanups, verify once more, and raise them. No re-review follows.
8. **After the report, a fix check, never a full review.** Every fix asked for once the report
   is out (from triage, the human check, or `/code-review`) goes to the same implementer, in
   one batch per reply. Then verify (step 4, without the browser or end-to-end tests that
   CLAUDE.md names), and spawn a fresh `nfx:spec-reviewer` in fix-check mode at step 2's
   *Fix checks* level. Give it the spec path, the change name, the build report of that
   verification, what was asked for, word for word, and what step 6 gives a re-reviewer: the
   two snapshot trees (the snapshot of the last verification before this fix batch, and the
   one step 4 takes after it), the round's files and the files set aside as the other run's
   (step 4), not the diff's text. A must-fix from a fix check goes back to the implementer
   once; if it still fails, raise it under *Must fix*. Raise the fix check in one
   short block with the IDs it closes.

   Before the human check of the final code, run the full verification once (step 4, every
   verification step). If it fails, that's a must-fix for the implementer, then a fix check.
