<!-- Spec: spec-rules. Behaviour changes go through it. -->
# Spec template

**Current version: v1.** This line is the only place the current version is stated.

Used by `/nfx:spec`. **This file** holds what a spec is and what goes in it.
Beside it: [lifecycle.md](lifecycle.md) (how work moves; its last section maps every rule file), `terms.md` (terms, item
letters), `folders.md` (where specs live), `later-work.md` (later work), `spec-skeletons.md` (specs), `change-skeletons.md` (changes), `workflow.md` (every session's).
A rule is cited by the ID in backticks after its lead (e.g. `T-users`, `L-fold`).
**Project conventions win:** if a project's CLAUDE.md or docs define spec rules (location,
naming, tags, verification), follow those and use these files for everything they don't cover.

*Body rules* say what a spec, its index and its code pointers must be, and are versioned
(`L-version`); *process rules*, in [lifecycle.md](lifecycle.md), say how work is shaped and planned.

## Body rules

### Header and identity

- **Every spec and index opens with its header** `T-header`. A spec's header gives its
  template version, ID, status, *Blocked by*, `Repo:` when it works outside this repo, and its
  background links. An index's gives its template version and background links. Each header
  line is written as `spec-skeletons.md` writes it, with or without its leading `- `.
- **`Template: vN` is the body-rules version the document complies with.** `T-version` A
  document with no `Template` line, or one below the current version, is old-format
  (`L-convert`).
- **The ID is a stable name for the thing.** `T-id` A short lower-case slug (`location`,
  `string-import`), unique in the repo and never reused. It survives renaming or moving the
  file. Code pointers and commit trailers name the ID, not the path; a spec is found from its
  ID by searching spec headers for `**ID:** <id>`. When a thing is split, the part that keeps
  the thing's identity keeps the ID and the others get new ones.

### One spec, one thing

- **A spec defines one thing:** `T-one` a location, a landmark, a trial harness. It is that
  thing's only definition. No other spec describes it, adds to it or restates it; another spec
  that depends on it states what it requires of it.
- **A spec defines its thing, not its users.** `T-users` References follow use: when A uses B
  (calls it, reads its data, builds on it), A may name B ("characters are placed in the
  location defined in `locations/`"), and B never names A. A composition root names what it
  mounts (`T-refs`).
  - A thing may name the context it sits in, as a word only ("a landmark is an object within
    a location"; "a location can be part of a scene"): never what that context is, who builds
    it, or what anything does with this thing. **Test each sentence:** would it need rewriting
    if a user of this thing changed how it works? If so, it belongs in that user's spec.
  - A slot that something else fills is described by what it holds and when it is empty ("its
    resolved placement; None until resolved"), not by who fills it.
  - The body describes the thing's public contract: what it provides, never how anything gets
    or uses it. "`compass_vector` gives a word's unit vector, +Z north" is the contract; "the
    plan view draws each facing arrow from `compass_vector`" names a user. A thing may state
    that it is reachable only through its own interface ("a word's vector is read only
    through `compass_vector`"): that is its own contract and names no user. The body never
    links to a user.
  - When a change alters what users rely on, the users that only follow the new interface are
    listed in the change's *Touchpoints* and *Guardrails* and dropped with the change at the
    fold; a user whose own behaviour must be specified gets a pending change in its spec, or a
    small new spec (`T-nospec`).
- **A spec checks only its own thing.** `T-own` Its requirements are about the thing's own
  properties. A check that needs another thing (resolving against it, a cross-reference
  between them) belongs to the spec of the thing that holds both.
- **References follow dependencies.** `T-refs` What a spec may reference, what its *Blocked by*
  lists and how each entry is written:
  - A spec may reference any other spec, built or not, and states what it requires of it (an
    interface, a guarantee).
  - A spec's *Blocked by* needs to list only the specs whose interface or guarantee it
    requires, and every spec a change edits (`T-change`).
  - A link in *Out* requires nothing.
  - A *Blocked by* is written as the skeletons write it and `change-skeletons.md` states, in the form
    the lint checks (`L-lint`).
  - A composition root, a thing that assembles others (an app shell mounting their routers),
    may name what it mounts.
  - What a composition root mounts stays out of its *Blocked by*.
  - The mounted thing is blocked by the root.
  - Two things that can only be built together are one thing, or the interface between them
    is built first.
- **The body describes the code as it is now.** `T-now` A built change is folded into it
  (`L-fold`), so the spec never accumulates history. The body has no revision history: it
  never says "replaced", "since", "now", "was" or "previously". Git tracks changes, and the
  reason for a change goes in its commit message.
- **Size is a guide, not a cap.** `T-size` Its body and each pending change are sized on their
  own. The body, everything above *Pending changes* with its acceptance criteria, aims under
  ~10 KB; well past ~15 KB, ask whether it defines more than one thing. A pending change well
  past ~15 KB: ask whether it is one session's work (`T-change`).

### Code pointers

- **The code points back.** `T-pointer` The main file of each module a spec names opens with a
  one-line comment naming that spec's ID (skeleton in `spec-skeletons.md`), so anyone who opens the
  code to change it, any agent or person, finds the spec. A pointer to a spec that lives in
  another repo names that repo too, `Spec: <repo>/<id>`, `<repo>` being the name of the spec's
  repo, because the code's repo cannot find the spec's repo to look the ID up. The comment is a
  pointer, never spec. Agent instruction files (`CLAUDE.md`, `AGENTS.md`) carry no pointers.
  A project's own convention wins.
- **A code file belongs to one spec.** `T-one-file` Its pointer names one ID. When two specs
  need the same file, it holds two things, and splitting it is found work (`T-found`). Until
  it is split, its pointer lists every ID that covers it.

### Content

- **The body is the record; a pending change is the spec.** `T-record` The body describes the
  thing as built, for a future session asking "how does this work and what's fixed?". A
  pending change is what an implementer works from. A new thing's spec is all pending work until
  it is built.
- **Background, not source.** `T-background` The header links the design and technical docs;
  never copy their reasoning into the spec, or they drift. A constraint's one-clause *because*
  (`T-because`) is the only reasoning a spec holds.
- **Self-contained.** `T-self` The spec alone, with the code and CLAUDE.md, is enough to build
  from. Every decision, constraint and value needed to build is stated in the spec, including
  what it requires of the things it references. What other things built is reached through
  their specs' bodies and the code, which is the authority once built. *Read first* may list a
  built spec as a map to that code; it never lists an unbuilt one.
- **Inputs are not spec.** `T-inputs` Prototypes, UI handoffs, mockups and other upstream
  artefacts feed the plan phase. The spec describes the implementation in its own terms rather
  than pointing at them, so the upstream work can keep evolving without invalidating the spec
  or the code. Record which version an input was planned from in the background line, so a
  later revision can be diffed and planned. An input the spec names is saved in the repo (e.g.
  `documents/exploration/`), never only in a scratchpad or a private link.
- **Each module says what it is for.** `T-responsibility` A module block opens, under its
  heading, with its responsibility in one or two sentences: what the module is for and what it
  owns. A reader knows what belongs in it before reading its interface, and work that doesn't
  fit is noticed rather than absorbed. It names no users (`T-users`).
- **State requirements, never copy code.** `T-requirements` A spec says what it requires: of a
  field ("`width_m` is above 0"), of a combination ("a vertical entry has no facing"), of a
  result ("every entry lies inside its location"). It gives pseudo-signatures for the
  interfaces other code calls, algorithm steps and formulas. It never mirrors a class, field
  by field, and never holds headers or function bodies. Once code exists it is the source of
  truth for exact declarations; the spec states the claim and points to the file.
- **Acceptance criteria, not tests.** `T-acceptance` What a criterion states and how it is
  verified (what a fold keeps of one is in `fold.md`):
  - What must be shown to hold is written as acceptance criteria beside the requirements they
    illustrate, with expected values derived from the spec, not observed output.
  - Each criterion states what must be true, observable from outside, at whatever level the
    behaviour lives: a unit's result ("an entry `{wall: north}` in a 10 × 8 room arrives at
    (0, 0, 4), moving (0, 0, −1)"; "an entry naming an unknown door is rejected, naming the
    entry"), a behaviour across modules ("an entrant through a vertical entry faces along the
    staging axis, never up or down") or a pipeline or user-visible outcome ("the trial report
    lists every import error with its sample").
  - A criterion is verified at the level it is stated: one across modules needs a test that
    crosses those modules.
  - Criteria are a minimum, not a limit: they say what must be true.
  - The implementer decides how to verify each criterion, names its tests as it sees fit, and
    adds any further tests it judges necessary.
  - Once built, the test files are the source of truth for the tests, so a spec never names or
    lists one.
  - Behaviour a change keeps is stated as "existing tests still pass, each checking what it
    checked", never as tests that "pass unchanged"; `T-kept-tests` says what a kept test may
    change.
- **State the choice, with at most one clause of why.** `T-because` A constraint may end with
  a single *because* clause when the reason helps the implementer handle cases the rule
  doesn't name: "door positions are stored in room-local space, because rooms are moved at
  runtime". It states a fact about the system as it is now, never a past or rejected approach
  ("because the world-space version broke" is history). Longer reasoning lives in the design
  doc. Naming a rejected approach primes the implementer toward it, so rejected approaches
  live in the technical doc. Phrase constraints and guardrails positively: what the code
  does, not what it doesn't.
