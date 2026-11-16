<!-- Spec: implement-skill. Behaviour changes go through it. -->
# Run records

How a single-change run records itself so other runs see it: where the records live, what one
holds, when a record is live, and when it goes. `build-loop.md` step 0 and `../spec/fold.md`
steps 0 and 8 send you here; a milestone run reads it only for the check `milestone-start.md` M1
makes. A change with a `Repo:` line writes no record and never takes a worktree. `worktree.md`
holds the rest, read only when the checkout is busy, a worktree is made or finished, or a run
ends without a fold.

Every single-change run records itself, so another run can see it, whichever checkout it is
in. The records live in `<common dir>/nfx/runs/`, where `<common dir>` is
`git rev-parse --git-common-dir`, which every worktree of the repo shares. A record is one file
named `<spec-id>--<change-slug>.json` (the **record name** is that without `.json`), where the
change slug is the change's name lower-cased, each run of characters other than `a`–`z` and
`0`–`9` made one `-` and any `-` at either end removed (`spec-id` alone for a new thing's
spec). It holds:

```json
{"spec": "<spec path, relative to the repo root>", "change": "<change name, or null>",
 "checkout": "<absolute path of the checkout the run is in>",
 "base": "<the branch it merges into: the main checkout's branch when it started>",
 "main": "<absolute path of the main checkout>"}
```

- **Write it** once step 1 has picked the change and `run-check.md` has
  passed: in the main checkout with `checkout` equal to `main`, or in the worktree once it
  is made.
- **A record is live** while its `checkout` exists. Before reading the records, delete each
  whose `checkout` is gone: its run ended without a fold. A record for the main checkout can't
  show whether its run still goes (its implementer may not have written yet, or the run was
  dropped while other changes sit there): name it, ask the user whether it still runs, and end it
  (`worktree.md`'s *End a run without a fold*) only when the user says no.
- **It goes when the run ends:** the fold deletes it after its commit (`worktree.md`'s
  *Finish the worktree*, or `fold.md` step 8 in the main checkout), and `worktree.md`'s *End a
  run without a fold* deletes it otherwise.
