<!-- Spec: process-rules. Behaviour changes go through it. -->
# Spec lifecycle

How a spec and its pending changes are shaped and move from planned to built. What a spec is and
what goes in it are in [template.md](template.md), the other rule files in the last section.
**Project conventions win** where they differ. A run with no user present (a milestone run, an
auto-mode session) sets some of these rules aside, as `L-unattended` in [runs.md](runs.md) says.

## Phases `L-phases`

The workflow ((explore →) design → plan → implement → tune, `L-workflow`) and the document
roles (`L-documents`) are in [workflow.md](workflow.md). For a spec they mean:

- **Plan just in time.** `L-just-in-time` Write a pending change, or a new thing's spec, when
  it is next or nearly next. Later work stays one-line entries under the index's *Not yet
  planned*. More than about two planned changes in one spec: ask whether each is next. When
  the later work is ordered into milestones (`T-milestone`), "next" is the next milestone:
  every line of it may be planned together, and its changes and specs are agreed as a set.
  Lines in later milestones stay one-line entries. A change planned ahead that the reference
  check (`L-fold-check`) finds relying on changed behaviour goes back to `draft`, as any other.
- **Spikes** `L-spike` (plan): run one where reasoning alone can't settle a technical choice.
  The evidence goes to the technical doc, the spike code is discarded, and the spec states the
  chosen approach. Design adjustments go back to the design doc.
- **Back to plan:** `L-back-to-plan` when an implementation fails or is unacceptable because
  of the spec, the spec is fixed. The code is not patched around it.

## Shaping work `L-shape`

- **A change to a thing is a pending change in its spec,** `T-change` at the bottom, under
  *Pending changes*. It is the unit of work: an implementer builds it in one session, and it
  gets one review, one human check and one commit. If it needs more than that, it is two
  changes. A change that must also edit other things stays one change: it lives in the spec of
  the thing it starts from, its *Changes* items name each other spec they edit, and each of
  those specs carries a one-line pointer to it under *Pending changes* and is in its *Blocked
  by*, since the change alters that thing's code. An existing thing that
  starts using a new thing changes its code, so that is a pending change in the existing spec,
  blocked by the new one.
- **New thing or change?** `T-newthing` Work is a **new thing** (a new spec) when it has its
  own interface that other code calls, and it could be removed without removing the thing it
  sits beside. Otherwise it is a **change** to the thing it alters. When it is unclear, ask
  the user rather than extending the existing spec by default.
- **A new thing is a new spec.** `T-newspec` Until it is built, the whole document is its spec,
  and its *Build* and *Unanswered questions* sections play the part a pending change's do.
- **Code with no spec gets one when work needs to specify it.** `T-nospec` When a change must state
  behaviour of existing code that no spec defines (a consumer of this thing, a module of an
  older pipeline), that code becomes a thing with its own small spec, never a section in the
  spec that needed it. The new spec records only the part of the code the work concerns, as the
  code is now, and is `built`; later changes grow it. It is placed per `T-folders`.
- **A fix to a thing is planned in that thing's spec,** `T-fix` never as a spec of its own.
  When that spec is old-format, it is converted first (`L-old-waits`).
- **Work found along the way** `T-found` (a follow-up, a gap in shared code, a cleanup) is a
  new pending change in the spec of the thing it concerns, or a new spec for a new thing. Until
  it is next, it may instead wait as a *Not yet planned* line (`T-not-yet`). It never joins a
  change already planned or in progress.
- **A pending change marks its edits.** `T-marks` Each item under a change's *Changes* is
  marked **Add**, **Replace** or **Remove** and names the body section it affects (prefixed
  with the spec's name when it is another spec's), so the implementer never reads two
  conflicting statements as both true. The markers exist only inside the change; the fold
  leaves none (`T-now`).
- **A pending change carries what it needs, no more.** `T-minimum` Every change has its
  heading (with status), *Blocked by*, *Brief*, *Changes* and *Done when*. The other parts are
  added only when they carry something. An omitted *Delegation* means the Sonnet implementer
  and a full review. A light review suits a change that touches nothing another thing relies
  on: no shared code, public interface, data format, or async or ordering-dependent behaviour.
- **A human check is something the user can do with what is at hand.** `L-human-check` A file
  to open, a command to run, a screen to look at, a thing to play, named so they can do it. A
  behaviour that shows only in runs (a skill's step, an agent's instruction) is proven by use
  or by a milestone check, never by reading the procedure, so such a change's human check names
  what the user can see of it, says what proves the rest, and may be none.
- **A change that builds tunable behaviour specifies the knobs** `L-knobs` (name, range,
  default) in *Tunables*.
- **Tuning that needs a session of its own is a separate main-session change** `L-tune-change`
  whose *Done when* is the user's sign-off; it records the final values. Layout or look
  iterated with the user after a build is the same: its own small main-session change, not a
  reason to keep the build in the main session.

## Touched `L-touched`

- **A spec is touched only when the work names it.** `L-touch-scope` The cases are examples
  of it, indexes included, not a closed list; a situation they don't name is judged by the
  principle:
  - The home spec of the change being planned, built or folded is touched, and so is each spec
    named in that change's *Changes* items.
  - A new spec is touched by its creation.
  - A conversion touches the specs it converts or creates, and their folder's index.
  - An outline touches the specs whose planned work it places in a milestone.
  - An index is also touched when a touched spec is added to it, removed from it or renamed in
    it.
- **Only touched documents are edited.** `L-edit-touched` What may be edited, and where:
  - Housekeeping, code pointer additions and conversion apply to touched specs only.
  - Every other spec is read, never edited: what is found in it is reported to the user.
  - Any document, old-format or not, may take an edit that keeps the documents consistent with
    a move, a fold, a recorded line or a confirmed milestone, and that changes nothing else in
    it; the edits are exactly these, and one that fits the principle but no case isn't covered,
    and is raised so a change can extend the list:
    - When a spec file is moved, renamed, split or deleted, links to it are repointed.
    - A *Blocked by* naming a change that has been folded is pointed at its spec.
    - A *Not yet planned* line (`T-not-yet`) is added or removed, adding the section if the
      document has none.
    - A confirmed milestone's heading and `Check:` line are deleted (`L-milestone`).

## Readiness `L-ready`

- **Status** `L-status` belongs to a new thing's spec and to each pending change: `draft`
  (being planned, or an unanswered question remains) · `ready` (fully specified, no
  unanswered question) · `built` (implemented and confirmed by the user's human check). The spec's
  header gives the spec's own status; each pending change's status is in its heading. A built
  spec stays `built` while it has pending changes.
- **Only a `ready` spec or change whose *Blocked by* are all satisfied is implemented.**
  `L-only-ready` A spec may be planned, and even be `ready`, while its *Blocked by* are
  not yet satisfied; it waits for them. The implementer builds exactly one change and never edits a
  spec.
- **When a blocker is satisfied.** `L-built` A blocking spec is satisfied once its status is
  `built` (with or without pending changes). A blocking change is satisfied once it has been
  folded, so it no longer appears under its spec's *Pending changes*. A pending change is also
  blocked by its own spec: it is implemented only once that spec is `built`.
- **Old-format specs wait.** `L-old-waits` A touched spec that is old-format (`T-version`) is
  converted (`L-convert`) before it is planned, built, folded or corrected.
- **Unanswered questions** `L-questions` keep the change, or the new spec, `draft`. They sit
  with the change they affect. An answer is folded in and the question deleted
  (`L-ambiguity`). A status always agrees with its questions: a `ready` spec or change has
  none.
- **One repo per change.** `L-one-repo` A change that works outside its spec's repo has a
  `Repo:` line giving that repo's root, and its Touchpoints are relative to it. A change that
  would span repos is two changes. A change whose Touchpoints lie outside its repo isn't fully
  specified until it has that line.

## Commits `L-commit`

- **Lint what you write.** `L-lint` Every spec and index the work writes is linted after each write
  and before any commit: `python3 <rules folder>/scripts/spec_lint.py <files>`, the rules folder
  being this file's (`L-python`). Every ERROR in a document the work touches (`L-touched`) is fixed.
  The rest is reported, with the WARNs left: an ERROR in an untouched document (a *Blocked by* cycle
  that runs through one, say) is fixed by its own change, so the report says whether one is planned.
- **Trailers.** `L-trailers` A commit that folds a change, converts a spec, or creates or
  deletes one ends its message with a `Spec: <id>` trailer for each spec it edits, creates or
  deletes, and, for a fold, a `Spec-Change: <change name>` trailer (for a new spec, its ID),
  above any attribution lines. A conversion's is `Spec-Change: convert to vN`.
  `git log --grep "Spec: <id>"` then finds a thing's history.

## Rules kept in other files

Read each when the work needs it, as named here; rule IDs are cited the same way.

- [workflow.md](workflow.md) (`L-workflow`, `L-documents`, `L-ambiguity`, `L-outside`, `L-tweak`,
  `L-python`, `L-commit-ask`): read whenever this file is.
- [feedback.md](feedback.md) (`L-feedback`, `L-assumption`, `L-triage`, `L-accepted`,
  `L-deviations`, `L-findings`): read for the reviewer's triage, a milestone run and auto build,
  and `/nfx:spec` folding an implementation's report.
- [terms.md](terms.md) (terms and report item letters): read to plan a change or a
  milestone, for auto mode, and for a milestone run and auto build.
- [folders.md](folders.md) (`T-folders`, `T-feature`, `T-area`, `T-index`): read to create, place
  or move a spec or edit an index's specs list, and for an audit or a conversion.
- [later-work.md](later-work.md) (`T-not-yet`, `T-milestone`): read to write a *Not yet planned*
  line, a milestone or a **Milestone:** part, and for an audit or a conversion.
- [spec-skeletons.md](spec-skeletons.md) (spec, code pointer and index skeletons): read to
  create a spec or an index.
- [change-skeletons.md](change-skeletons.md) (pending change and pointer): read to plan a
  change or a milestone, or to create a spec.
- [fold.md](fold.md) (`L-fold`, `L-fold-in`, `L-fold-others`, `L-fold-check`, `L-remove`,
  `L-same-commit`, `L-tune`, `T-acceptance`'s fold part): read to take an implementer's
  report or fold a change, a tuning change included.
- [milestones.md](milestones.md) (`L-milestone`, `L-milestone-ask`): read for `outline`, a
  `Milestone <name>` target and a feature whose index has milestones.
- [runs.md](runs.md) (`L-milestone-built`, `L-milestone-run`, `L-milestone-found`,
  `L-unattended`): read for a milestone run, auto mode, and with `milestones.md`.
- [audit.md](audit.md) (`L-audit`, `L-contradictions`, `L-non-compliance`): read for an audit.
- [conversion.md](conversion.md) (`L-convert`, `L-convert-what`, `L-convert-does`,
  `L-convert-agent`, `L-convert-commit`): read for a touched old-format spec.
- [changelog.md](changelog.md) (`L-version`, `L-versioned`, `L-additive`, `L-breaking`,
  `L-changelog`): read for a body-rule change or a conversion.
- [auto.md](auto.md) (`L-auto-branch`, `L-auto-report`, `L-auto-waiting`): read for `auto` last
  in a target.
