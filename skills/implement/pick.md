<!-- Spec: implement-pick. Behaviour changes go through it. -->
# Picking from a folder

Read by `/nfx:implement` when its argument is a folder with no `Milestone <name>`, or, with
`auto` last, a one-file feature's spec. "Step N" means that skill's numbered step; the rules
folder is the one its SKILL.md names (`spec`, beside this skill's folder).

`/nfx:implement <folder> [deep]` picks the item to build, with or without a `README.md` in
the folder. `/nfx:implement <folder or one-file spec> [deep] auto` is the pick in auto mode, for
`/nfx:auto`'s driver; given a one-file feature's spec, it picks from that spec alone (*In auto
mode*, below). A folder or one-file spec names no change, so text after it other than a final
`deep`, or `deep auto` or `auto`, stops the run: ask what was meant. The pick reads no index:
status mode gives the walk order, and its groups are the readiness (`L-ready`, `L-built`), so
nothing here works readiness out again.

1. **Run status mode** (`spec_lint.py --status`). Run `python3 <rules folder>/scripts/spec_lint.py
   --status <folder> --json` (`L-python`). When it exits 2, stop with its message. Name each
   `skipped` line on stderr, with the note that its items were not considered.
2. **Take the pick.** It is the first item of `ready`, in the order listed, whose `delegation`
   does not say "main session only": work done by feel or in the editor is not delegated. The
   item is its `spec` and, when `change` is not null, that change.
3. **Tell the user.** Name the pick (its spec, and its change when it is one), then every other
   `ready` item, one line each with its command `/nfx:implement <spec> [<change>]`, marking
   those whose `delegation` says "main session only".
4. **Carry on.** The pick goes through step 1's checks and the steps after, as for a spec path
   naming that item (the `deep` given still applies). Status mode does not lint, so a `[ready]`
   change may still hold *Unanswered questions*, and the spec may be an old-format one the
   change edits: step 1 stops the run on either, as it does there.

**No pick.** When `ready` holds no item that is not main session only, stop. Give the counts of
`ready` items that are main session only, of `blocked`, `draft` and `convert` items, and
suggest `/nfx:spec status <folder>`.

## In auto mode

With `auto` last, the pick follows `../spec/auto.md` and never asks. It runs as above, with
these differences:

- **Before step 2, drop the waiting work** (`L-auto-waiting`). The run's report is
  `<git dir>/nfx/auto-<date>.md` for the run branch checked out (`L-auto-report`);
  with no run branch checked out there is none, and nothing is dropped. Drop from `ready`
  each item that is waiting work by that rule: one the report records as waiting, and one
  blocked, directly or through another, by waiting work or by a change the report records with
  an item that makes the work blocked by it wait. Each change or new spec committed but not
  folded is dropped too, with the work it blocks and the other work of its spec (`auto-build.md`,
  *Committed, not folded*).
  Status mode gives only each blocker's text, so follow the chain through the *Blocked by*
  links of the item's change, or of its spec's header for a new spec: a link names a spec, and
  a change a session built is named by its spec once it is folded. Then step 2 takes the first
  item left that step 1's checks and `auto-build.md`'s `Repo:` refusal accept; each one they
  refuse is waiting work, recorded with its **M** item (`L-auto-waiting`), and the next is
  tried.
- **A one-file feature's spec** given in place of the folder: first of all, before any pick or
  branch, check that no folder holds a `README.md` from the spec's own folder up to and
  including the specs root. When one does, the spec belongs to an indexed feature: stop, naming
  that folder to give in its place. Otherwise run `spec_lint.py --status <spec> --json` in step
  1 in place of the folder's, and everything else is as for a folder.
- **Step 3** names the pick in one line, and lists no other item.
- **Step 4** carries the pick, which step 1's checks accepted, to `auto-build.md`,
  from its step 4 (the branch) and the build: its sweep and checkout check ran before the pick.
- **No pick:** the session ends, suggesting nothing, and records that it found no work, with the
  **M** items it found (`L-auto-waiting`); that and every other stop above (status
  mode's exit 2, text after the folder other than `deep`, a spec path inside an indexed feature) are said and recorded as
  `L-auto-report` gives them.
