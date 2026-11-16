<!-- Spec: spec-rules. Behaviour changes go through it. -->
# Later work

The body rules for later work: *Not yet planned* lines and milestones. Read this file, with
`template.md`, when the work writes a *Not yet planned* line or a milestone, as a milestone plan,
an outline and the fold do; audits and conversions read it too. Its rules are versioned with
[template.md](template.md) (`L-version`), and this file states no version of its own. A rule is
cited by the ID in backticks after its lead.

- **Later work waits as one line.** `T-not-yet` A *Not yet planned* line says what the later
  work does and which spec it belongs to. A line about a thing with a spec goes in its
  feature's index. A feature that is one file has no index, so its spec holds its lines in a
  `## Not yet planned` section of its own, at its foot after *Pending changes* and outside
  the body. A line about a new thing goes in the index that will list its spec. A line leaves
  when its work gets a spec or a pending change.
- **Later work may be ordered into milestones.** `T-milestone` *Not yet planned* may group its
  lines under `### Milestone: <name>` headings, the name saying the outcome. They are listed
  in the order they are to be built, and milestones have no numbers: moving one changes when it
  is built. Each name is unique in its document. Each
  heading is followed by a `Check:` line: what the user runs or looks at to confirm the
  outcome. Lines in no milestone sit under a last `### Later` heading. A pending change, or a
  new thing's *Build*, planned from a milestone's line names it in a **Milestone:** part, a
  link labelled with its name to the document that holds it
  (`[Playback and preferences](../README.md)`); the part goes with the change at the fold.
  Renaming a milestone updates every **Milestone:** part that names it. A milestone keeps its heading and `Check:` line, even with no line left under it, until
  the user confirms its milestone check (`L-milestone-built`, in `runs.md`). *Not yet planned* without milestones is a plain list.
