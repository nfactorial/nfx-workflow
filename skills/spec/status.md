<!-- Spec: status-report. Behaviour changes go through it. -->
# Status report

Read by `/nfx:spec` for `status [<folder>]`, and for `<folder>` when the folder holds no
`README.md` and no `.md` file directly in it. A folder with a `README.md` or a spec file in it is
planned as a feature folder instead (SKILL.md). The report answers "what does the user do next?": it
lists the pending work by feature and recommends one step. It reads and reports only: it edits,
lints and commits no document, runs nothing it recommends, skips SKILL.md's steps 1 to 4
(no gathering, no table), and reads no rule file (not `template.md`, `lifecycle.md` or
`milestones.md`): status mode's groups hold everything it reports.

**The folder.** With no folder given, it is `documents/specs`, else `docs/specs`; when neither
exists, ask for one.

## 1. Run status mode

Run status mode (`spec_lint.py --status`): `python3 <skill folder>/scripts/spec_lint.py
--status <folder> --json` (`L-python`). The JSON is the whole input: the groups are the readiness
(`L-ready`, `L-built`), so nothing here works readiness out again.
- Exit 2: the report is its message. Stop there.
- Each `skipped` line on stderr: list it with the command that lints that file
  (`spec_lint.py <file>`), and say its items are missing from the report.

## 2. List the pending work

Group the items by feature: the folder of the index or one-file spec each belongs to. For an
item (or a *Not yet planned* line), the feature is the folder of its spec (or file) when that
folder holds a `README.md`, else the spec file itself. Order the features by where status mode
first lists something from them. Under each feature, in this order, one line per entry:
- its `ready` items, each with its `delegation`;
- its `blocked` items, each with the blockers not built;
- its `draft` items;
- its `convert` specs;
- the count of its `not_yet_planned` lines, naming the `milestone` of the first one when it
  has one.

Leave out an empty group, and a feature with nothing pending. An item is its `spec` and, when
`change` is not null, that change. Write a path as status mode writes it (relative to the
working directory, forward slashes) and a change name as its heading writes it, without the
status tag.

## 3. Recommend one step

Recommend exactly one, the first of these that applies:
1. A ready item that `/nfx:implement <folder>` would pick (`pick.md` in `/nfx:implement`'s folder): the first
   item of `ready`, in the order listed, whose `delegation` does not say "main session only".
   `/nfx:implement <spec>` for an unbuilt spec, `/nfx:implement <spec> <change>` for a change.
2. The first `ready` item whose `delegation` says "main session only": name it as main-session
   work, with no command.
3. The first `draft` item: `/nfx:spec <spec>` or `/nfx:spec <spec> <change>`.
4. The first `convert` spec: `/nfx:spec <spec>`.
5. The first `blocked` item: name it with its blockers not built, as work whose *Blocked by*
   needs checking: `/nfx:spec <spec> <change>` (or `/nfx:spec <spec>` for a spec).
6. The first `not_yet_planned` line with a `milestone`: `/nfx:spec <feature> Milestone <name>`,
   where `<feature>` is the folder of its `file` when that file is a `README.md`, else the file.
7. The first `not_yet_planned` line: `/nfx:spec <feature>`, `<feature>` as in 6.
8. None: say there is no pending work under the folder.

Other ready items stay in the list; they are never offered as alternatives to choose from.
