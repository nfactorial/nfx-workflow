<!-- Spec: process-rules. Behaviour changes go through it. -->
# Milestones

The milestone planning rule and the outline procedure. `/nfx:spec` reads this file for
`outline`, for a `Milestone <name>` target, and whenever the feature's index has milestones. The
other rules are in [template.md](template.md), [lifecycle.md](lifecycle.md) and
[later-work.md](later-work.md) (the milestone headings, `T-milestone`, and *Not yet planned*,
`T-not-yet`); when a milestone is done, where work found during one goes, and a milestone run's
rules are in [runs.md](runs.md), which a `Milestone <name>` target reads too.

## Rules `L-milestone`

- **Milestones are the user's choice.** `L-milestone-ask` They are written when the user asks
  for a feature's later work to be ordered, or agrees to it; a feature without them is planned
  just in time (`L-just-in-time`). Each ends in an outcome the user can see or run, and its milestone check (its `Check:` line) says how. Work
  already planned but not built belongs to a milestone like any line, through its
  **Milestone:** part, and a milestone holds the planned work its lines are blocked by, unless
  an earlier milestone does.

## Outline

For `outline <feature>`, or when the user asks to order a feature's later work
(`L-milestone-ask`). It plans no change.

1. **Read** the index (or the one-file spec), the design doc, and any exploration it links.
2. **Propose milestones** (`T-milestone`): each ends in an outcome the user can see or run,
   with a milestone check (`Check:` line) that says how. The first is the smallest such outcome. For a UI from a settled
   mockup it is usually a provisional contract (models and stub routes serving the mockup's
   fixtures) and the mockup's pages on it, so the look arrives first and the backend follows.
   Place every existing *Not yet planned* line in a milestone or under *Later*, and add lines
   for work the outcomes need that has none. Place work already planned but not built too
   (the feature's pending changes and unbuilt specs, and any elsewhere that a placed line is
   blocked by): it is usually next, so it usually belongs to the first milestone. Placing it
   adds a **Milestone:** part to it, which touches its spec; when that spec is old-format, say
   so and propose converting it first (`L-old-waits`). A milestone's lines are never
   blocked by planned work outside it and its earlier milestones. A milestone that would take
   more than about five changes is split.
3. **Agree** it with the user (AskUserQuestion for discrete choices), then write it into *Not
   yet planned*, and add the **Milestone:** parts to the planned work it placed. A new
   milestone goes where it is to be built. Lint what it edited (`L-lint`) and commit it
   alone.
4. **Report** the milestones, one line each with its milestone check, and the next step:
   `/nfx:spec <feature> Milestone <name>`.

When a milestone's design changes, revise it the same way.
