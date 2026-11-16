<!-- Spec: process-rules. Behaviour changes go through it. -->
# Folding a built change

The fold's rules, and how a built change is folded into its spec's body by them (`L-fold`).
An unattended run's fold agent follows it at the run's end, for every change of the run at
once, with the differences the block before step 0 gives. The other rules it cites are in
[template.md](template.md), [lifecycle.md](lifecycle.md), [feedback.md](feedback.md),
[later-work.md](later-work.md) (it records follow-ups, `T-not-yet`) and [runs.md](runs.md),
beside this file: read the first four in full if they aren't in your context, and, when the
feature's index has milestones, [milestones.md](milestones.md) and `runs.md` too.

`/nfx:spec` reads this file at its step 3 in three cases:
- **After an implementation:** fold in the assumptions (`L-accepted`), settle any deviation or
  open question still undecided, and record values tuned during the human check in its
  *Tunables*. A rejected assumption sends the change back to `draft`. If it goes back to
  `draft` instead of being folded, record the run's follow-ups now, as the fold would, and end
  its run if it has a run record (`/nfx:implement`'s `worktree.md`, *End a run without a fold*).
- **Folding a built change**, only after the user confirms its human check (`L-fold`): follow
  the procedure below.
- **After tuning:** record the final values in the body's *Tunables* and fold the tuning
  change.

`/nfx:spec`'s step 4 report then gives, after a fold or a change sent back to `draft`, every
follow-up by its ID, one line each, with where it went
(`F1 → core/README.md › Not yet planned`) or `dropped by you`: every **F** ID from the run
appears. After it committed a fold, it suggests `/clear` before implementing the next one.

## Rules `L-fold`

- **A built change is folded in** `L-fold-in` only after the user confirms its human check.
  Each **Add** and **Replace** item is written into the body section it names, and each
  **Remove** item is deleted, as if the body had always said so. No marker and no
  trace of the old text remains. What exists only for the change (its brief, migration rules,
  by-hand cases, *Done when*, touchpoints, delegation) is dropped, because git holds it. A new
  thing's spec drops its *Build* and *Unanswered questions* sections the same way and is
  marked `built`.
- **A change that edits other specs** `L-fold-others` is folded into each of them the same way,
  in the same commit, and the pointer to it in each is deleted.
- **The reference check: specs that reference the folded one are checked, and only
  reported.** `L-fold-check`
  Each claim the build made false is listed with a proposed fix (a wording correction, a
  pending change, or back to `draft`); those specs are not touched (`L-edit-touched`). A
  `ready` pending change or unbuilt spec that relied on behaviour the build changed is
  put to the user as a decision, with the recommendation to send it back to `draft`, before
  the session ends.
- **A thing that goes away** `L-remove` is removed by a pending change in its own spec, blocked
  by the changes that stop every other spec referencing it. Folding it deletes the spec, its
  index line and its code pointers.
- **What a fold keeps of a criterion.** `T-acceptance` (its fold part; the rest is in
  `template.md`):
  - When a change is folded in, a criterion is dropped only when it restates its requirement.
  - When a change is folded in, a criterion stays in the body when it pins a value someone
    would otherwise have to work out (a round-room seat, a wall offset), or states a behaviour
    no requirement states (the vertical-entry facing in `T-acceptance`'s examples).

## Committing a fold

- **Same commit.** `L-same-commit` A change's fold (status, folded definition and
  assumptions, any index line, the run's follow-ups) is committed together with its code.
  When the code lives in another repo, commit it there first, then commit the fold with the
  code commit's hash in its message.

## Tuning `L-tune`

Values are tuned during the human check (`L-tweak`) or in a main-session change of their own
(`L-tune-change`); final values go in *Tunables*.

## Procedure

**In an unattended run** (`L-unattended`: a milestone run's fold agent, auto build's fold), read
[runs.md](runs.md) too, since steps 1 and 5 follow `L-unattended`, and these steps differ:
- **Step 1:** for each spec, apply its changes' items in the order given, with the assumptions
  and deviations given and the fixes made since (`L-unattended`).
- **Step 3:** once per spec, after the last of its changes, against the code at the branch's
  last commit.
- **Step 5:** run it once, after every spec is folded, and handle its findings as
  `L-unattended` says.
- **Step 6:** return the follow-ups to the run; don't record them (`L-unattended`).
- **Step 8:** don't commit or push. Return the lint result, the follow-ups, the step 4 edits,
  and what step 5 found; the run commits.

0. **Fold where it was built.** If the change has a run record (`/nfx:implement`'s
   `run-records.md`) whose `checkout` is a worktree other than this session's, move
   into it first (`EnterWorktree` with that `path`): its code, and the spec edits the fold
   commits with it, are there.
1. **Apply its *Changes* to the body.** Write each Add and Replace into the section it names
   and delete each Remove, with the folded assumptions and tuned values. The body reads as if
   it had always said this (`T-now`). Keep or drop each acceptance criterion as `T-acceptance`
   says. No test names enter the body. Items naming another spec are written into that spec
   the same way, and its pointer to the change is deleted (`L-fold-others`).
2. **Delete the change's entry,** and with it everything that existed only for the change.
   For a new thing's spec, delete its *Build* and *Unanswered questions* sections and mark it
   `built`. If the change removed the thing, delete its spec, index line and code pointers
   instead (`L-remove`).
3. **Bring the body in line with the code** wherever the build made them differ.
4. **Keep the touched specs consistent with the fold:** a *Blocked by* or an interface entry
   the build added, a pointer to a folded change. These, and the edits `L-edit-touched` allows
   in any document, are part of the fold, never a question for the user. List each one in the
   report.
5. **Run the reference check:** search the project's specs for links to it and for its ID,
   and check each against what was built. Report what it finds, and put what it raises to the
   user, as `L-fold-check` says.
6. **Record the follow-ups** as `L-findings` says: every **F** item from the run, and every
   finding outside the change raised since (`/code-review`, the human check). A *Not yet
   planned* line (`T-not-yet`) says what it does and which spec it belongs to, and goes in that
   spec's feature index, in the spec itself for a feature that is one file, or, for a new
   thing, in the index that will list it. Ask the user when no index fits. In an index with
   milestones, a line goes under the milestone that needs it, or under *Later*
   (`L-milestone-found`). One the user has planned now is shaped and agreed as in `/nfx:spec`'s
   step 2. A line changes nothing else in the document it goes in (`L-edit-touched`).
7. **Lint** every spec and index the fold edited, as `L-lint` says.
8. **Commit and push** the fold together with the code, with its trailers (`L-trailers`), once
   every follow-up is recorded or dropped, as `L-commit-ask` says. When it says to wait, tell
   the user what is waiting instead. Commit by path: the change's code and the documents the
   fold edited (`git add -- <paths>`, then `git commit -- <paths>`), so foreign and transient
   files stay out even when something else staged them.
   The change may have a run record (`/nfx:implement`'s `run-records.md`). On an
   `implement/…` branch in a worktree, follow `/nfx:implement`'s `worktree.md`, *Finish the worktree*,
   which deletes it. Otherwise delete it once committed: `<common dir>/nfx/runs/<record name>.json`, where
   `<common dir>` is `git rev-parse --git-common-dir`.
