<!-- Spec: spec-rules. Behaviour changes go through it. -->
# Spec skeletons

The skeletons to copy when creating a spec, a code pointer comment or a feature's index; a pending
change's are in [change-skeletons.md](change-skeletons.md). The rules each one follows are in
[template.md](template.md), [folders.md](folders.md) and [later-work.md](later-work.md).

## Spec skeleton

Copy from here. Delete guidance in *italics* once filled in. Omit sections that genuinely
don't apply rather than writing "N/A". For a new thing, the body is its spec, with *Build*
and *Unanswered questions* in the body; when it is built, *Build* is dropped, *Unanswered
questions* is empty and goes, and later work goes under *Pending changes*.

```markdown
# <Thing name> — Spec

> - **Template:** v1 · **ID:** <slug>
> - **Status:** draft | ready | built *(the spec's own status; each pending change carries its own in its heading)*
> - **Blocked by:** *links to every spec whose interface or guarantee this one requires, and any change as
> [<spec>](<file>) › `<change name>` (`T-refs`; satisfied as `L-built` says), or "none"*
> - **Repo:** *only when it works outside this spec's repo: that repo's root*
> - **Background (not needed to build):** Feature: <index link, if in a folder> · Design: <link or "none"> · Technical: <link or "none"> · Inputs: <e.g. UI handoff `tool-wheel` @ tag, or "none">

## Goal

*2–5 sentences: what this thing is and does. Link the design doc for the why; don't restate it.*

## Scope

**In:** *bullet list*
**Out (non-goals):** *bullet list. Things a reasonable implementer might otherwise add.*

## Constraints and key decisions

*The rules the thing keeps, one line each: the choice, stated positively and completely
enough to build from without any other document. At most one "because" clause each, when
the reason guides cases the rule doesn't name: a fact about the system now, never history.*

## Modules and interfaces

*One block per module. Prefer deep modules: a lot of functionality behind a small, stable,
testable interface.*

### <ModuleName>  (<path>)

*Responsibility in one or two sentences: what the module is for and what it owns
(`T-responsibility`).*

**Interface** *(pseudo-signatures for what other code calls):*
- `ReturnType FunctionName(const FInput&, …)`: *what it guarantees*

**Requirements** *(what the data and results must satisfy, one line each; never a copy of
the class):*
- *`width_m` is above 0*
- *exactly one of `door` and `position`*

**Acceptance:** *(what must be true, observable from outside, with expected values derived
from the spec; once built, those that only restate a requirement go. A criterion across
modules or for the whole thing sits beside the constraint it illustrates instead):*
- *an entry `{wall: north}` in a 10 × 8 room arrives at (0, 0, 4), moving (0, 0, −1)*
- *an entry naming an unknown door is rejected, naming the entry*

## Tunables

*Values found by feel or eye. Planned as knobs; final values recorded after tuning.*

| Knob | Range | Default | Final |
|---|---|---|---|

## Build

*New thing only, until it is built; then dropped. The same parts as a pending change
(`change-skeletons.md`: Milestone, Read first, Touchpoints, Fixed / Free / Guardrails, Migration, Done when,
Delegation), with the same minimum. Its agent-checkable Done when covers every requirement and acceptance
criterion in the body.*

## Unanswered questions

*New thing only. Each keeps the spec `draft`. Answered → rewrite every affected part, delete
the entry, and promote the spec to `ready` once none is left.*

## Pending changes

*Each pending change from the block in `change-skeletons.md`; in each other spec a change
edits, the one-line pointer from it.*

## Not yet planned

*Only in a feature that is one file (`T-not-yet`): one line per later change with no pending
change yet, saying what it does. A spec in a feature folder uses its index's.*
```

## Code pointer skeleton

The first comment in the main file of each module a spec names, in the language's comment
syntax, naming the spec's ID:

```python
# Spec: location. Behaviour changes go through it.
```

For a spec in another repo, the spec's repo is named too:

```python
# Spec: <repo>/<id>. Behaviour changes go through it.
```

Only while a file is waiting to be split (`T-one-file`), it lists every ID that covers it:

```python
# Spec: location, landmark. Behaviour changes go through them.
```

## Index skeleton

The feature folder's `README.md`.

```markdown
# <Feature name>

> - **Template:** v1
> - **Head:** [<head's name>](<head>.md)
> - **Design:** <link or "none"> · **Technical:** <link or "none">

*An area writes `> - **Area:** <one line on what it collects>` in place of the Head line.*

*One or two sentences: what the feature is, for orientation only. No spec, no status.*

## Specs

- [<head's name>](<head>.md): *one line on what it defines; the head comes first*
- [<part's name>](<part>/<part>.md): *one line on what it defines*

## Not yet planned

- *One line per later change or thing with no spec or pending change yet: what it does and
  which spec it belongs to.*
```

When the user orders the later work into milestones (`T-milestone`), *Not yet planned* groups
its lines:

```markdown
## Not yet planned

### Milestone: <the outcome the user can see or run>

Check: *what the user runs or looks at to confirm it*

- *One line per later change or thing, as above.*

### Later

- *Lines in no milestone.*
```
