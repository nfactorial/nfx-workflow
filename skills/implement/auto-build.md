<!-- Spec: auto-build. Behaviour changes go through it. -->
# Auto build: the build session

Read by `/nfx:implement` when `auto` ends its arguments with no `finish` before it, after
`pick.md`. It follows `../spec/auto.md` (read it first, with `terms.md`: the report cites
the item letters) and states its steps in order, "step *n*" a numbered step of
`build-loop.md`, read when starting: they run as written there, but for the differences this
file gives. The finish session (`auto-finish.md`) reviews, verifies, pre-checks and folds what
this session commits. A milestone run reads neither file.

`/nfx:implement <feature> [deep] auto`, `auto` last, builds one change with no user
present, as `/nfx:auto`'s driver runs it. `<feature>` is a feature folder, or a one-file
feature's spec path: a spec with no folder holding a `README.md` from its own folder up to and
including the specs root. A spec path of a feature that has an index stops the session, naming
the index's folder to give in its place; the stop is said and recorded as `L-auto-report`
gives it. This session builds and commits one change, and the finish session the driver runs
next folds it, because each session starts with fresh context and plans or builds against the
specs alone. It never asks: what a step raises is recorded in the run's report instead.

**Starting**, in place of step 0's busy check and step 1's pick. Given a one-file feature's
spec, its first act is `pick.md`'s index check (*In auto mode*): a spec path inside an indexed
feature stops the session, before the sweep, the checkout check, the pick and the branch, and
nothing below runs:

1. **Sweep** the run reports and folders, as `auto.md` says.
2. **The checkout** is `auto.md`'s. Run step 0's `git status`, write its exclude file, and read
   `run-records.md`: a checkout `auto.md` refuses stops the session, with its reason; the main
   checkout's live run record counts, because no one is there to say whether it still runs. It
   never takes a worktree and writes no run record. When step 0 raises that CLAUDE.md names no
   checks, the session builds nothing: it adds a **D** item to the run's report saying that the
   project's CLAUDE.md names no checks to run before a commit and asking the user to add them,
   and ends with no commit, so the session makes no progress.
3. **The pick** (`pick.md`, *In auto mode*) chooses the change, and step 1's checks apply to
   it, as for a change named directly; a change or new spec with a `Repo:` line is refused,
   because the run branch and the report are this repo's. One refused either way is waiting
   work (`L-auto-waiting`): the pick records its **M** item and tries the next item.
4. **The branch** is `L-auto-branch`'s: it works on the run branch checked out, stops when
   another run branch exists, naming it, or creates `auto/<today>` and starts the report with
   the base branch and its commit (`L-auto-report`). Then the session starts its section of the
   report: its heading (`## Session <n>: <command>`, `L-auto-report`, `<n>` the last section's
   number plus one, or 1) and the commit it starts at.

**Committed, not folded.** A change or new spec committed on the branch but not folded, left by
a finish session that never ran, was cut short or whose fold failed, is waiting work
(`L-auto-waiting`): the pick drops it, the work it blocks and the other work of its spec.

**A stop** is said and recorded as `L-auto-report` gives it, and the session ends.

**The run's own files** are what `python3 <rules folder>/scripts/git_helper.py --exclude-file
<exclude file> own-files` lists (`L-python`). A commit names them by path (`git add --
<paths>`, then `git commit -- <paths>`). To restore the tree is the helper's `restore`, and to
save a patch its `save-patch <patch file>`; the session never uses `git reset --hard`, `git
clean` or a stash.

**The build**, steps 2 to 6 for the change, in this order:

- **Steps 2 to 6.** The implementer and every reviewer are told this is a milestone run, and
  briefed, as a milestone run briefs them (`L-unattended`), with every change committed on the
  branch but not folded (those the pick found: `L-auto-waiting`). The baseline is the branch's
  last commit. Step 4's verification is a quick one: lint, the type check, and the tests of the
  files the change touched (with a build agent, ask it for just that). The full verification
  is the finish session's; tell every reviewer so, so that what the quick one didn't run is not
  a gap. An implementer that ends with no report and no changes sets the change aside. Step 6's
  fix round carries its review's leftovers to the implementer; the leftovers no round carried
  are not applied here, but written to the report for the finish session's tidy round.
- **Set aside** the change when the build still fails or a must-fix remains after the round
  limit. `git switch -c auto/<date>--<change slug>-<session>`, commit the change's own files
  there, and switch back. If a hook refuses that commit, save a patch as
  `<git dir>/nfx/auto-<date>/<change slug>-<session>.patch`, inside the run's folder, so
  `auto.md`'s sweep deletes it with the run, and restore the tree. `<change slug>` is the
  change slug of `run-records.md`'s record name (the spec's ID for a new spec). A set-aside
  change waits itself (`L-auto-waiting`): record it as a **W** item naming its side branch or
  patch, with its findings as **M** items, and under the **W** item the work waiting on it that
  the session can see: each item of status mode's output for its feature (its folder, or its
  one-file spec) blocked by the change, directly or through another, the chain followed as the
  pick follows it. Then rewrite *Your turn* (`L-auto-report`), give the chat the change, its
  side branch or patch and the report's path, and end: no finish session follows.
- **Commit** the change's own files on the branch with its `Spec:` and `Spec-Change:` trailers
  (`L-trailers`). If a hook refuses the commit, send the hook's output to the implementer once,
  then a fix check (step 8); if it still fails, set the change aside.
- **Record** in the session's section, for the finish session: the change (its spec path and
  name) and its outcome, committed (`<commit>`) and not folded; its items, by *Terms*' letters,
  each with its ID and its context (what was found and where, what the code does now, why it
  matters, and what each option would change); its Assumptions and Deviations with the
  reviewer's triage; the leftovers no round carried; and what the `Run:` line gives of it: its
  fix rounds and what triggered them, any round limit hit, the transient files ignored, and
  anything else that slowed it.
- **End.** Record in the section that the build session ended, with the branch's last commit:
  the finish session finds its change by it. Then give the chat the change, its commit and the
  report's path, saying the finish session folds it, and end.
