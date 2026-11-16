<!-- Spec: implement-skill. Behaviour changes go through it. -->
# Can it run beside the live runs?

Whether a single-change run can run beside the live ones. `build-loop.md` step 1 sends a run
here, for a change with no `Repo:` line, outside a milestone run. The records, and when one is
live, are `run-records.md`'s.

Once step 1 has picked the change, read each live record's change: its spec's header, the
change's heading, *Blocked by*, *Changes* and *Touchpoints* (the spec's *Build* for a new
thing). A change's **edited specs** are its home spec and every spec its *Changes* items name.
Refuse, naming the run, when this change and that one:

- edit a spec in common;
- have either's *Blocked by* name the other's home spec or change;
- have Touchpoints that overlap: the same file, or one a folder holding the other;
- leave it unclear, because either has no Touchpoints: ask the user whether to run anyway.

Two changes whose follow-ups both add *Not yet planned* lines to one index can run together:
`worktree.md`'s *Finish the worktree* merges such lines. A run picked from a folder that is refused tells the user,
and stops; it doesn't pick another.
