<!-- Spec: spec-rules. Behaviour changes go through it. -->
# Spec folders

The body rules for where specs live. Read this file, with `template.md`, when the work creates,
places or moves a spec or edits an index's specs list; audits and conversions read it too. Its
rules are versioned with [template.md](template.md) (`L-version`), and this file states no version
of its own. *Not yet planned* and milestones are in [later-work.md](later-work.md). A rule is cited
by the ID in backticks after its lead.

- **Spec folders mirror the application.** `T-folders` Specs are grouped in folders named for
  what they do in the application (`user_interface/views/project_browser/`,
  `data/changeable_properties/`), nested as the application's own areas are, never one flat
  folder. A new spec goes in the folder of the area its thing belongs to; when no folder fits
  or it is unclear which does, ask the user.
- **A feature folder holds a thing and its parts.** `T-feature` When a feature has more than
  one thing, its specs live in a folder named after the thing it is about, the head, with a
  `README.md` index (skeleton in `spec-skeletons.md`). The folder's root holds only the index and
  the head's spec, so a newcomer knows where to start. Each part has a sub-folder named for it,
  holding its spec; a part with parts of its own holds their sub-folders the same way. A part
  is a thing the head is made of (in the head's *Blocked by*), or, when the head is a
  composition root, a thing it mounts (`T-refs`). Any other thing that uses the head (a debug
  tool, an importer, a consumer) is never in its folder: it lives in its own area's folder
  (`T-folders`). A feature that is one thing is a single file, with no folder.
- **An area folder collects things with no head.** `T-area` An area (e.g. core modules, code
  quality) is a folder whose index header names it an area; it has no head, and its things
  sit in it as files or feature folders.
- **The index is a map, not a status board.** `T-index` It names the head (or that the folder
  is an area) in its header, then lists the specs it covers in reading order, head first, each
  with one line on what it defines, plus *Not yet planned*: one line per later
  change or thing that has no spec or pending change yet (`T-not-yet`). It links the design
  doc. It holds no spec and no state: status, *Blocked by* and pending changes live only in
  the specs. It changes only when a spec is added, removed or renamed, a *Not yet planned*
  line comes or goes, or a milestone is added, reworded or removed (`T-milestone`).
