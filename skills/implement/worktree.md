<!-- Spec: implement-skill. Behaviour changes go through it. -->
# Runs side by side

How a single-change run moves into a worktree of its own when another run holds the main
checkout, and ends. `build-loop.md` step 0 (a busy checkout) and step 1 (making the worktree), and
`../spec/fold.md` step 8, send you here, and so does a run that ends without a fold
(`run-records.md`, `/nfx:spec`'s update mode), to *End a run without a fold*; a milestone run
never comes. A change with a `Repo:` line never takes a worktree: its busy checkout stops as
step 0 says. The run records are in `run-records.md` and the conflict check in `run-check.md`;
`run-records.md`'s *record name* names the branch and worktree below.

## Is the checkout busy?

The main checkout is busy when step 0 finds changes other than foreign and transient files,
when a live record names the main checkout, or when a `milestone/…` branch is checked out
there (a milestone run is in progress, or waits on its report).

- **On a `milestone/…` branch,** stop: name the branch and its report file in
  `<git dir>/nfx/`, and say the milestone must be completed, or the base branch checked out,
  first. A run started from there would build on the milestone branch and fold into it.
- **With a `Repo:` change, or when worktrees aren't allowed** (below), stop and ask the user to
  commit or stash the changes first, or to confirm carrying on, as step 0 says.
- **Otherwise** say the checkout is busy, name the live runs from the records, and offer this
  run a worktree of its own (AskUserQuestion: a worktree, or stop). On a worktree, step 1
  picks the change in the main checkout, then the check
  (`run-check.md`) runs, and only once it passes is the worktree made.

## Are worktrees allowed?

Decide once per run, in this order, and say which rule decided it:

1. **The project's CLAUDE.md line.** A line in the project's own `CLAUDE.md`, matched exactly:
   `Implement worktrees: allowed`, optionally followed by ` (setup: <command>)`, or
   `Implement worktrees: not allowed`. It wins.
2. **Ask the user once.** Otherwise ask whether worktrees suit this project, and for any command a
   new worktree needs before it builds (`npm ci`, a venv). Then offer to record the answer as
   the CLAUDE.md line. When the user agrees to an *allowed* line, write it in the worktree once it is
   made, and commit it there on its own (`git add -- CLAUDE.md`, then
   `git commit -m "Record that implement worktrees are allowed" -- CLAUDE.md`) before the implementer starts, so the main
   checkout's other run never sees it. A *not allowed* line waits until the main checkout is
   clean: tell the user the line to add.

## Make the worktree

1. If `.claude/worktrees/` isn't ignored (`git check-ignore -q`), add it to
   `<common dir>/info/exclude`, which every worktree of the repo reads.
2. Note the main checkout's current branch as the base. Then
   `git worktree add -b implement/<record name> .claude/worktrees/impl-<record name> HEAD`.
   The worktree holds the base branch's last commit; the other run's uncommitted files stay in
   the main checkout.
3. Run the setup command, if the CLAUDE.md line names one, in the worktree, in the
   foreground, with its output in a log in the scratchpad. If it fails, run
   `git worktree remove --force <worktree>` and `git branch -D implement/<record name>` (both
   hold nothing yet), and stop with its error.
4. Move the session in: `EnterWorktree` with `path` set to the worktree's absolute path. From
   here every agent, build, review and git command runs in the worktree, and the worktree is
   the checkout step 0's baseline describes: it is clean.
5. Write the run record, and the CLAUDE.md line's commit if the user agreed to one. Then go on with
   step 2.

Step 7's report gives the worktree's absolute path for the human check, since the change's
files are only there.

## Finish the worktree

`fold.md` step 8 sends the fold here once it has committed on an `implement/…` branch in a
worktree. The record gives the base and the main checkout (`<main>`). Each stop below keeps
the worktree, the branch and the record, and tells the user what is left to do.

1. **The main checkout is on the base.** `git -C <main> symbolic-ref --short HEAD` must print
   the base. If not, stop: name the branch it is on.
2. **Rebase.** First note whether the base has moved since the worktree was made: it has
   unless `git merge-base --is-ancestor <base> HEAD` succeeds. Then `git rebase <base>`. On a
   conflict:
   - when every conflicting file is an index, resolve each so it holds both sides' *Not yet
     planned* lines, then lint them as `L-lint` says, `git add -- <files>`, and
     `GIT_EDITOR=true git rebase --continue` (no editor can open here);
   - otherwise `git rebase --abort` and stop, naming the files.
3. **Verify what will land.** If the base had moved, run `/nfx:implement` step 4's full verification in the worktree, with
   every verification step. If it fails, stop with the build report: the code that would land
   was never built.
4. **Fast-forward the base:** `git -C <main> merge --ff-only implement/<record name>`. If it
   refuses (the main checkout's uncommitted files overlap the branch), stop with its message.
5. **Push** from the main checkout (`git -C <main> push`), as `L-commit-ask` says.
   If that says to wait, say so and carry on: the base holds the work.
6. **Clean up.** `ExitWorktree` (`action: "keep"`; it was entered by path), then, in the main
   checkout, `git worktree remove <worktree>` and `git branch -d implement/<record name>`, and
   delete the record. If the removal refuses (files left in the worktree, such as setup
   output), keep the worktree and its record, and name the files: the work has landed, and
   *End a run without a fold* clears it on the user's answer. Report the commit the base branch now
   holds.

## End a run without a fold

When a change goes back to `draft` instead of being folded, when the user drops a run, or when a
record names a run the user says no longer runs:

- **In the main checkout:** delete the record. The working tree is the user's to commit, stash or
  discard; say so, and touch nothing.
- **In a worktree:** ask the user whether to keep its work. *Keep* commits the worktree's changes on
  its branch, less transient files (in the worktree, `git add -- <paths>`, then
  `git commit -m "Set aside: <change name>" -- <paths>`),
  then removes the worktree and keeps the branch. *Discard* runs
  `git worktree remove --force <worktree>` and `git branch -D implement/<record name>`, only
  on that answer. Either way, `ExitWorktree` first when this session is in it, run the removal
  from the main checkout, and delete the record.
