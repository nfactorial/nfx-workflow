<!-- Spec: milestone-run. Behaviour changes go through it. -->
# A milestone run on its own branch (M1)

Read at M1 by a milestone run that finds its milestone branch checked out (`milestone-start.md`),
before step 0's busy check. The run's rules are in `milestone-run.md` and M0 to M4 in `milestone-start.md`, which
the run has read. Read the branch's report file first: what follows acts on what it shows.

- **The end session.** When the report shows its last run ended its build session (M5) but not
  M10, this is that run's end session (M2), which no one is there to answer:
  - The milestone branch checked out doesn't make the checkout busy.
  - The paths the report records as the user's are not asked about: add them to the run's exclude
    file, so they stay the user's, out of every commit and restore.
  - Any other change still makes it busy, as step 0 says, but for those the next part takes.
- **A run stopped during M7–M9.** When the report shows the last run stopped during M7–M9, save
  the uncommitted changes outside the foreign and transient files as
  `<git dir>/nfx/milestone-<feature>-<slug>--unfinished-<run>.patch` (`save-patch`), restore the
  tree (`restore`), and say so, rather than ask. They are most likely that run's unfinished
  work; the patch keeps anything of the user's among them.
