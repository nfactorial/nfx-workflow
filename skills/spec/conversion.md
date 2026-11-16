# Conversion

The conversion rules and the procedure `/nfx:spec` follows to convert an old-format spec
(`L-old-waits`). The `nfx:spec-converter` agent reads the rules. The other rules are in
[template.md](template.md), [lifecycle.md](lifecycle.md), [folders.md](folders.md) and
[later-work.md](later-work.md).

## Rules `L-convert`

- **What is converted:** `L-convert-what` a touched old-format spec (`T-version`), before any
  other work on it. The whole spec of the thing is converted, never part of it, so every spec is
  at one version. An old spec that defines several things has only the thing being worked on
  split out into its own spec at the current version; the rest stays as it is until it is
  touched. A feature folder may be converted as one conversion: one claim-equivalence report
  per spec, one commit. The folder's index is converted with the first conversion in it.
- **What conversion does:** `L-convert-does` content is regrouped by the thing it defines and
  brought up to the current body rules; each built thing's record is checked against the
  code; unbuilt stages become pending changes (or new specs for new things); a *Testing* table
  becomes acceptance criteria beside the requirements where they pin a value or state a
  behaviour no requirement states; per-stage history and revision notes are dropped; content
  about another thing moves to that thing's spec (`T-users`, `T-nospec`). It changes no code
  except code pointers: an old path pointer (`Specified by …`) is replaced by the conversion
  of any spec it named, and a file several converted specs cover lists their IDs
  (`T-one-file`).
- **It is run by the `nfx:spec-converter` agent** `L-convert-agent` and produces a
  **claim-equivalence report**: every claim of the old document, labelled *unchanged*,
  *reworded*, *moved* (to which spec and section), *dropped* (and why) or *changed* (and the
  code that shows the old claim false). A fresh `nfx:spec-converter` in verify mode then checks
  every *unchanged*, *reworded* and *moved* label against the old and new text. The user
  reviews only the *changed* and *dropped* claims and any label the verifier disputes.
- **It is its own commit,** `L-convert-commit` made by the main session once the user accepts
  the report, with nothing else in it. Old files that are deleted or replaced are named in
  the message, and links to them are pointed at the new specs.

## Procedure

For a touched old-format spec (`L-convert`), before any other work on it, and on its own:
1. **Scope it** in SKILL.md's step 2 proposal: the spec of the thing, whole; for an old spec that defines
   several things, only the thing being worked on is split out; a whole feature folder may be
   converted together (`L-convert-what`). Name the new specs, their places and IDs, and where
   content about other things moves, and include the folder's index if it is old-format.
   Agree it with the user.
2. **Convert:** spawn an `nfx:spec-converter` with the old file paths, the agreed scope,
   the current version, the repo root and the rules folder (this file's folder, as an absolute path). It writes the new specs and returns its
   claim-equivalence report.
3. **Verify:** spawn a fresh `nfx:spec-converter` in verify mode with the old files (from
   git, as committed), the new files, the report and the rules folder. It returns the labels it disputes.
4. **Review:** show the user only the *changed* and *dropped* claims and the disputed labels,
   with counts of the rest. Settle each with the user; fix the new specs as agreed.
5. **Lint** the new specs and the index, as `L-lint` says.
6. **Commit** the conversion alone, naming deleted or replaced files, with its trailers
   (`L-trailers`). Then carry on with the work that needed it.
