<!-- Spec: process-rules. Behaviour changes go through it. -->
# Workflow rules

The rules every nfx session follows. They hold in every session that runs an nfx command, which
reads this file at its start, before any other file. **Project conventions win** where they differ: a
project's CLAUDE.md or docs that define their own way of working are followed; these rules cover
the rest. A rule is cited by the ID after its lead (e.g. `L-fold`).

In a skill's files other than `SKILL.md`, `<skill folder>` is the folder the skill's `SKILL.md`
is in (the base directory its skill header names), and `<rules folder>` is the `spec` folder
beside it, the folder this file is in.

## Workflow

**Work moves through (explore →) design → plan → implement → tune, in short iterations.**
`L-workflow` The goal is specs that are unambiguous and readable by people and AI.

- **Scope:** the workflow is for code the user cares about. A project whose CLAUDE.md says it
  is vibe-coded (a UI bench, a prototype) skips it entirely: build, show, iterate, with no
  specs and no `/nfx:implement`. Its output, e.g. a UI handoff, can still feed a real project's
  plan phase.
- **Explore (optional):** before design, when the direction isn't clear yet: a review of what
  exists, competing directions, mockups on real data (`/nfx:mockup`). The work is throwaway, but
  what it produces is kept in `exploration/` and feeds the design doc.
- **Design:** the design doc, a high-level definition of what the user wants.
- **Plan:** make the next change unambiguous: answer its questions, and run spikes where needed
  (`/nfx:interrogate`, `/nfx:spec`).
- **One spec per thing:** a change to a built thing is a pending change in that thing's spec,
  and a new thing is a new spec.
- **Plan just in time:** a change is planned just before it is built, and later ones stay
  one-line entries in the index; when the user orders later work into milestones, each ending
  in something the user can see or run, the next is planned as a whole (`L-milestone`).
- **Work found along the way** is a new pending change or a new spec, never added to a change
  already planned.
- **Implement:** one change at a time, from the spec alone (`/nfx:implement`), one session per
  change: `/clear` once it is committed.
- **Back to plan:** a change that fails or is unacceptable because of the spec.
- **A milestone at once:** when the user asks for one instead, `/nfx:implement` builds all its
  changes as one run on a milestone branch and brings what it would have asked to the run's end
  (`L-milestone-run`).
- **Tune:** values found by feel or eye, in the main session with the user; the final values
  are recorded in the spec.
- **The spec rules** start from [template.md](template.md) (what a spec holds) and
  [lifecycle.md](lifecycle.md) (how work is shaped and moves), whose *Rules kept in other files*
  maps the rest. Older specs are converted when next touched (`L-convert-what`).

## Documents

**A project's documents live under `documents/`, one folder per role.** `L-documents` An older
project that uses `docs/` is followed.

- **`exploration/`:** what was tried before deciding: reviews, directions, mockups, each with
  the sources that rebuild it. Evidence for the design doc, never spec.
- **`design/`:** what the feature is and why, where it has one.
- **`technical/`:** where technical choices are reasoned, for intricate features: the options, the
  one selected, and why the others were not ("deemed unacceptable because…"), plus spike evidence. A
  rejected option is recorded when a future session would plausibly propose it again: a real
  trade-off, and costly to reverse or surprising without the reasoning. It is **not** a store for
  answered questions.
- **`specs/`:** how each thing is built, one spec per thing. A spec is self-contained: it never
  needs the design or technical doc to build from. Its body records the thing as built; the
  pending changes at its foot specify what comes next. A feature with several things is a
  folder with a `README.md` index.
- **Each document references the one above it** rather than copying its reasoning, or they
  drift.
- **The folders mirror the application.** `specs/` is grouped by what each thing does in the
  application (`T-folders`), and the other three follow its area folders where they can. A document
  that serves several specs sits in their shared area's folder, and each spec links it from its
  header: the header, not the path, ties a spec to its docs.

## Open questions are ambiguities

**An open question means the document is ambiguous; it is not a record.** `L-ambiguity`

- An open question is not a technical choice.
- When it is answered, the affected content is rewritten throughout the document so the
  ambiguity no longer exists, and the question is deleted.
- A question is never stored together with its answer, in any document.
- An answered question is never moved into the technical doc, or anywhere else.

## Edits outside a change

**Code changed outside a pending change keeps the specs true.** `L-outside`

- A quick fix, a by-eye tweak or a cleanup that makes a spec body claim false updates that body
  in the same commit, written as if it had always been so, and the spec counts as touched
  (`L-touched`).
- Work needing more than a body correction (a new requirement, an interface another thing
  relies on) is not a quick fix: it is a pending change.
- When the spec is old-format, the correction is reported instead, and waits for its
  conversion.

## By-eye tweaks

**Small by-eye tweaks may be made during a change's human check, in the main session.**
`L-tweak`

- A tweak changes values only (knob values, or visual constants such as sizes and
  offsets), because the code review has already passed.
- A change to logic or structure is a fix instead: it goes through `/nfx:implement`'s fix
  check.
- The build and tests are re-run after a tweak.
- Each tweak is recorded in the spec's *Tunables*, adding a row if it wasn't a planned knob.

## Python

**Scripts run with `python3`, or `python` where `python3` doesn't exist.** `L-python`

- A session that chooses its Python command chooses `python3` when `python3 --version` exits 0,
  else `python`.
- A skill's script call is written with `python3`, or with `<python>` in a skill that has the
  session make that choice first.
- Each such call, or the skill's one sentence making the choice, cites this rule by its ID instead
  of naming an alternative command or restating the choice.

## Commits

**Ask before committing and pushing, unless allowed.** `L-commit-ask`

- By default a session asks the user before each commit and before each push.
- When the user's or the project's CLAUDE.md says the session may commit, or commit and push,
  without asking, it does so only when the work is clean: the build and tests pass, every
  review it has had passed (the project's required reviews included, their findings settled),
  and nothing waits on the user (an open question, a deviation not auto-accepted, a finding or
  assumption marked *ask*, an unconfirmed human check, doubt about what belongs in the commit).
- When something waits on the user, the session tells the user what, instead of committing.
- A "don't commit" or "don't push" in the session, or a project rule, wins.
- A push goes only to the current branch's upstream.
- A session never force-pushes, rewrites pushed history or skips hooks.
- An unattended run (a milestone run, an auto-mode session) commits on its own branch as
  `L-unattended` in [runs.md](runs.md) says (`L-auto-branch` for auto mode's
  branch).
