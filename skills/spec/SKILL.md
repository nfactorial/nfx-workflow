---
name: spec
description: Plan a spec - create a thing's spec, add or plan a pending change, fold in answers, implementer assumptions or tuned values, fold a built change into the body, convert an old-format spec, audit specs against the code or each other - and report which specs and changes are ready to implement, or what to do next across a folder of specs (status). Use when the user asks to write, create, plan, update, revise, convert, audit or bring a spec up to date.
argument-hint: "[status | audit [interfaces] | outline] [spec-path [change name] | feature-folder [Milestone <name>] | feature or thing name]"
---
<!-- Spec: spec-skill. Behaviour changes go through it. -->

# /nfx:spec: the plan phase

Read `workflow.md` first.

**Target:** `$ARGUMENTS`
- `audit` and a spec path or feature folder → **audit** it; `audit interfaces` and a folder →
  the cross-spec review. Follow `audit.md`.
- A path to an existing spec → **update** it; a change name after it names the pending change.
- `status`, optionally with a folder → the **status report**: follow `status.md`, not the steps.
- A folder with no `README.md` and no `.md` file directly in it → the status report too.
- A feature folder (its `README.md` index) → plan its next change or spec, or update the index;
  with `Milestone <name>` after it, plan that milestone's lines as a set (`L-just-in-time`),
  reading `milestones.md`, `runs.md` and `terms.md`.
- `outline` and a feature folder, or a one-file feature's spec → order its later work into
  milestones: read `milestones.md` and follow its *Outline*.
- A new path or a thing's name → **create** a spec, with its feature folder per `T-feature`.
- `<feature folder> auto`, or a one-file feature's spec path and `auto` → **auto mode**
  (`/nfx:auto`'s driver): before step 1 read `auto-plan.md` and `auto.md`, and follow them in
  place of the steps' asking. `auto` last is never a change name; with another target it stops,
  saying so.
- Nothing → work it out from the conversation; ask if it's ambiguous.

**Follow every rule in `template.md` and `lifecycle.md`,** cited by ID; project conventions
win. Above all: **one spec per thing, a change already planned never grows (`T-found`), and
only touched documents are edited (`L-edit-touched`).**

**Except for the status report (which reads no rule file), read [template.md](template.md) and
[lifecycle.md](lifecycle.md) in full before step 2, and read them again after a compaction.**
`lifecycle.md` says when each other rule file is read; one so read is read again after a
compaction too.

## 1. Gather

- Read the project's spec conventions, the feature's index, design and technical docs, and any
  exploration `decision.md` the design doc links (`T-inputs`).
- A touched spec that is old-format (`T-version`) is converted first: say so, agree its scope
  as step 2 does, then follow `conversion.md`.
- Read the code the work touches; in update mode, check the body's claims against it.
- Use what the conversation has settled (an implementer's report, tuning); don't re-ask it.

## 2. Shape the work, and agree it before writing

**For a `Milestone <name>` target or a feature whose index has milestones,** read
`milestone-plan.md`, even when this step is skipped, and follow it at steps 2 to 4.

Propose briefly:
- **The work:** a new thing or a change (`T-newthing`), buildable and checkable in one session;
  if more, the split: what comes now, what becomes *Not yet planned* lines.
- **Which thing it belongs to** (`T-one`, `T-own`, `T-users`), where a new spec lives
  (`T-folders`, `T-feature`), and its ID (`T-id`).
- **Code with no spec that the work specifies:** its small spec, written first (`T-nospec`);
  ask where it goes when unclear.
- **Other specs a change edits** (`T-change`): name each; an old-format one is converted first.
- **Modules** (prefer deep ones), their requirements and acceptance criteria (`T-acceptance`).
- **Blocked by** (`T-refs`, `L-built`). Ask: "are these blocking edges right?"
- **Unsettled decisions** → *Unanswered questions* (`L-questions`); with several, suggest
  `/nfx:interrogate`.
- **Spikes** (`L-spike`), for platform event behaviour (focus, pointer vs touch, timing) too.
- **Values found by feel or eye** → knobs (`L-knobs`), and a tuning change (`L-tune-change`)
  unless human-check tweaks (`L-tweak`) will settle them.
- **Delegation:** the implementer and review (`T-minimum`), with a one-line reason.

Use AskUserQuestion for discrete choices, and wait for agreement before writing. In update
mode, skip this step when the work only folds, records follow-ups as *Not yet planned* lines,
or brings the body in line with the code. A follow-up the user asks to plan now is shaped here.

## 3. Write

**Lint what you write,** as `L-lint` says.

**Create a thing's spec:** read `spec-skeletons.md` and `change-skeletons.md` (for *Build*'s
parts), and fill in the spec skeleton with the current version and a new ID. Add its index
line (making the index from its skeleton if needed), and the code pointer (`T-pointer`) to
each existing module it names; a module not written yet gets its pointer under *Fixed*. Its
*Not yet planned* line leaves (`T-not-yet`).

**Add a pending change:** a `### <Change name>  [draft]` entry under *Pending changes*, from
the pending-change block in `change-skeletons.md` (read it), with the parts it needs
(`T-minimum`); each other spec it edits gets the skeleton's pointer. Its *Not yet planned* line
leaves; the index needs no other edit.

**Update mode**, as applies:
- **Planning a change:** its *Changes* as marked items (`T-marks`), criteria with expected
  values from the spec, no test names (`T-acceptance`); its agent-checkable *Done when*: each is
  covered by a test.
- **Answered questions:** fold each into every part it affects and delete it (`L-questions`);
  fully specified work is made `ready` (`L-ready`).
- **Taking an implementer's report, folding a built change, or recording tuning:** read
  `fold.md` and follow its opening, here and at step 4.
- **Housekeeping, on touched documents only** (`L-edit-touched`), fix: a status that disagrees
  with its *Unanswered questions*; what a body rule forbids that a conversion missed; a missing
  code pointer; an old "Open questions" section (open ones → *Unanswered questions*, answered
  ones folded in); what building needs that only the technical doc holds (bring it in);
  rejected alternatives (into the technical doc, asking if it lacks them).

**Commit what you wrote** (planning, answers folded in, a new spec or change), once it lints
clean, as `L-commit-ask` says: by path, only the documents this session edited (`git add --
<paths>`, then `git commit -- <paths>`), with their trailers (`L-trailers`). A fold makes its own
commit instead. When `L-commit-ask` says to wait, step 4 says what is waiting.

## 4. Report

Summarise what changed, without pasting the spec. Then a row per spec of the feature and per
pending change, from their headers and headings:

| Spec / change | Status | Delegation | Why | Blockers |
|---|---|---|---|---|
| *spec, or "spec › change"* | *draft / ready / built* | *Sonnet / deep / main session only; full / light review* | *one line* | *unanswered question, blocking spec or change, old-format, missing touchpoint or `Repo:` line, asset work, or none* |

A built spec's own row has no Delegation. End with the next change or spec to implement
(`/nfx:implement <spec-path> [<change name>]`), or the planning it still needs. Give that
command, and the fresh session before it, only once this session's edits are committed
(`L-commit-ask`); otherwise say what is uncommitted and what the commit waits on. Work made
`ready` gets a line on `/nfx:second-opinion <spec-path> [<change name>]`, recommended when risky
(shared code, async or concurrent ordering, deep Delegation, high blast radius), else optional.
