---
name: implement
description: Implement a pending change in a spec, or a new thing's spec, via an implementer subagent, then review and fix it in a bounded loop; or a whole milestone as one run that brings its questions to the end.
disable-model-invocation: true
argument-hint: "<spec-path | feature-folder> [change name | Milestone <name> [answers]] [deep]"
---
<!-- Spec: implement-skill. Behaviour changes go through it. -->

**Read `${CLAUDE_SKILL_DIR}/../spec/workflow.md` at the start, before any other file**:
the rules every nfx session follows (`L-workflow`, `L-commit-ask` among them).

Arguments: `$ARGUMENTS`. These are a spec path or a feature folder, optionally the name of a
pending change, and optionally the word `deep` at the end. The change name is matched against
the `### <name>  [status]` headings under the spec's *Pending changes*, ignoring case and the
status tag. **`Milestone <name>`** in its place names a milestone of the feature's index (or of
the spec, for a feature that is one file): read `${CLAUDE_SKILL_DIR}/milestone-run.md` and
follow it. **`Milestone <name> answers`** (`answers` after the name, any case) is a session
that only answers that milestone's report: read `milestone-run.md`'s rules, then
`${CLAUDE_SKILL_DIR}/milestone-answers.md` (M11), and none of M0 to M10. The order is
`Milestone <name> [answers] [deep]`: `answers` comes last but for any `deep`, and `deep` in an
answers session applies to every implementer it spawns. Its rules folder is
`${CLAUDE_SKILL_DIR}/../spec`.

**Match the name whole first.** The text after the path is first matched whole against the
change names (or, after `Milestone`, the milestone names), so a name that ends in `deep` or
`answers` can be reached. Only when it matches none is a final `deep` read as the flag and
then, after `Milestone <name>`, a final `answers` as the answers form, and the rest matched
again. When both readings match a name, stop and ask the user which was meant. `auto` as the last
word is always auto mode and never part of a name.

**`auto`** last, after any `deep`: `/nfx:implement <feature> [deep] auto` builds one change
with no user present, `<feature>` being a feature folder, or a one-file feature's spec path.
It is for `/nfx:auto`'s driver only; a session the user is in never uses it. Read
`${CLAUDE_SKILL_DIR}/pick.md`, then `${CLAUDE_SKILL_DIR}/auto-build.md`, and follow that file.
With `finish` just before `auto` (`<feature> [deep] finish auto`), the session finishes the
change the last build session committed: read `${CLAUDE_SKILL_DIR}/auto-finish.md` in place of
both, and follow it.

**Any other target is one change:** a spec path or a folder, with or without a change name. Read
`${CLAUDE_SKILL_DIR}/single.md` and follow it.
