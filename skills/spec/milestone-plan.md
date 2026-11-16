<!-- Spec: spec-skill. Behaviour changes go through it. -->
# Milestone planning

The milestone parts of `/nfx:spec`'s shaping and report: how a milestone's lines are shaped and
agreed as a set, and how the report shows milestones. `SKILL.md` reads this file at step 2 for a
`Milestone <name>` target and for a feature whose index has milestones, and `auto-plan.md` where
it plans a milestone's lines. "Step *n*" means a numbered step of `SKILL.md`. The rules it cites
are in [milestones.md](milestones.md) (`L-milestone`), [runs.md](runs.md) (`L-milestone-built`,
`L-milestone-run`) and [later-work.md](later-work.md) (`T-milestone`).

## Step 2: shaping

- **A milestone's set** (`Milestone <name>` in the target, `L-just-in-time`): shape every line
  under it, each as its own change or spec as step 2 says, and propose the order and the
  *Blocked by* edges between them. A line that turns out to be more than one change becomes
  several, all in the milestone. A line blocked by planned work that is in no milestone or a
  later one: propose adding that work to this milestone (its **Milestone:** part), rather than
  waiting for it to be built (`L-milestone`). Agree the set once.
- **A split** in a feature with milestones: its *Not yet planned* lines go under the milestone
  they belong to.

## Step 3: writing

- A pending change, or a new spec's *Build*, planned from a milestone's line names that
  milestone in a **Milestone:** part (`T-milestone`).
- After writing a milestone's set, run `audit.md`'s interfaces review over the specs the set
  touches, and fix what it finds in them before reporting.

## Step 4: the report

Add the milestone each row belongs to, and say when a milestone is done (`L-milestone-built`),
with its milestone check for the user to run; once they confirm it, delete its heading and
`Check:` line, and commit that edit on its own. A milestone whose run is waiting on its report
is not reported done (`L-milestone-run`): name the report file in `<git dir>/nfx/` (the dir from
`git rev-parse --git-dir`).
