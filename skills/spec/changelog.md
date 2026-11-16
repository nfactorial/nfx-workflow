# Spec body-rules changelog

Changes to the body rules in [template.md](template.md), [terms.md](terms.md), [folders.md](folders.md),
[later-work.md](later-work.md), [spec-skeletons.md](spec-skeletons.md) and
[change-skeletons.md](change-skeletons.md), newest first (rules: `L-version`, below).
Process-rule changes are not recorded here. Not loaded by `/nfx:spec`: read it when converting
a spec from an older version, or when changing the body rules (`L-version`).

## Rules `L-version`

- **Body rules are versioned; process rules are not.** `L-versioned` The current version is
  stated once, at the top of `template.md`. Each spec and index states the version it complies
  with (`T-version`).
- **An additive change keeps the version:** `L-additive` one after which every document that
  complied still complies (a new optional section, a looser rule).
- **A breaking change bumps it:** `L-breaking` one that can make a complying document
  non-compliant (a new required header field, a stricter rule, a renamed section). Breaking
  changes are batched and released together, rarely, because each bump makes every older
  document old-format.
- **Every body-rule change is recorded** `L-changelog` in `changelog.md`, newest first:
  version, date, what changed, and whether it is additive or breaking.

## Versions

| Version | Date | Change | Kind |
|---|---|---|---|
| v1 | 2026-11-16 | The body rules are frozen for release: v0's rules, unchanged. A v0 document converts by its `Template` line alone. | breaking (every v0 document is old-format) |
| v0 | 2026-11-10 | The body rules are split by who reads them, each keeping its ID and meaning: *Terms* and the report item letters move to `terms.md`; `placement.md` splits into `folders.md` (`T-folders`, `T-feature`, `T-area`, `T-index`) and `later-work.md` (`T-not-yet`, `T-milestone`), and `skeletons.md` into `spec-skeletons.md` and `change-skeletons.md`; `T-acceptance`'s two bullets on what a fold keeps of a criterion move to `fold.md`; how a *Blocked by* entry (`T-refs`) and a header line (`T-header`) are written is cited from the skeletons and the lint. | additive |
| v0 | 2026-11-04 | `T-refs` is restated as its lead and one requirement per bullet; its meaning is unchanged. | additive |
| v0 | 2026-11-04 | `T-acceptance` is restated as its lead and one requirement per bullet; its meaning is unchanged. | additive |
| v0 | 2026-11-04 | `T-kept-tests` (what a kept test may change) moves to `feedback.md` as a process rule; `T-acceptance` keeps how kept behaviour is stated and cites it. | additive |
| v0 | 2026-10-30 | A code pointer to a spec in another repo names that repo, `Spec: <repo>/<id>` (`T-pointer`). | additive (such a pointer already failed the lint in its own repo) |
| v0 | 2026-10-24 | A *Blocked by* entry is a link to a spec, or for a change a link to its spec followed by ` › ` and the change's name in backticks, one in the same spec included (`T-refs`). | breaking (the lint reports an entry in any other form) |
| v0 | 2026-10-24 | Each header line is a list item inside the quote (`> - **Status:** built`), so a Markdown viewer shows one per line; a line written without `- ` is still valid (`T-header`). | additive |
| v0 | 2026-10-24 | Milestones are named, not numbered: `### Milestone: <name>` headings in build order, and a **Milestone:** part links one by its name (`T-milestone`). | breaking (the lint reports a numbered heading and a link to no milestone) |
| v0 | 2026-10-24 | A change's *Blocked by* includes every other spec it edits, as the skeleton and the lint already expected (`T-change`, `T-refs`). | breaking (already warned by the lint) |
| v0 | 2026-10-23 | *Not yet planned* may group its lines under numbered `### Milestone <N>: <outcome>` headings, each with a `Check:` line, and a last `### Later`; a change or new spec planned from a milestone names it in a **Milestone:** part, dropped at the fold (`T-milestone`, `T-index`). | additive |
| v0 | 2026-10-22 | A pending change's *Delegation* may name its review, `full review` or `light review`; an omitted one means a full review (`T-minimum`). | additive |
| v0 | 2026-10-21 | A feature that is one file holds its *Not yet planned* lines in a `## Not yet planned` section of its own, at its foot after *Pending changes* and outside the body; a spec in a feature folder uses its index's (`T-not-yet`). | additive |
| v0 | 2026-10-20 | Each module block opens with its responsibility in one or two sentences: what it is for and what it owns (`T-responsibility`). | breaking |
| v0 | 2026-10-20 | PRDs are renamed specs: they live in a `specs/` folder, a spec's title ends `— Spec`, the index lists them under `## Specs`, and code pointers read `Spec: <id>` (`T-header`, `T-folders`, `T-index`, `T-pointer`). `T-newprd` and `T-noprd` are renamed `T-newspec` and `T-nospec`. Commits before the rename carry `PRD:` and `PRD-Change:` trailers, so a history search greps both. | breaking |
| v0 | 2026-10-19 | Size is measured per part: the body (acceptance criteria included) against the ~10 KB guide, and each pending change on its own past ~15 KB (`T-size`). A spec's pending changes no longer count toward its body's size. | additive |
| v0 | 2026-10-19 | A feature folder holds its head's spec and index at the root and each part in a sub-folder named for it; a thing that uses the head lives in its own area (`T-feature`). An area folder has no head (`T-area`). The index header names its **Head:** or says **Area:** (`T-index`). | breaking |
| v0 | 2026-10-19 | A code file belongs to one spec; until it is split, its pointer lists every ID that covers it (`T-one-file`). A conversion touches its folder's index, and a feature folder may be converted together (process: `L-touch-scope`, `L-convert-what`). | breaking |
| v0 | 2026-10-19 | "Only access path" invariants: a thing may state that it is reachable only through its own interface, as its own contract that names no user (`T-users`). The counter-example now names a user. | additive |
| v0 | 2026-10-19 | Composition roots: *Blocked by* lists only the specs whose interface or guarantee this one requires, and a link in *Out* requires nothing; a composition root may name what it mounts, which stays out of its *Blocked by* and is blocked by the root (`T-refs`, `T-users`). | additive |
| v0 | 2026-10-19 | First versioned template. Headers carry `Template` and `ID` (`T-header`, `T-version`, `T-id`); code pointers name the ID (`T-pointer`); the index is a map with no status (`T-index`); the body names no users (`T-users`); folders mirror the application (`T-folders`); a constraint may carry one *because* clause (`T-because`). A document with no `Template` line is old-format. | breaking |
