# Personal working preferences: an example

An example of a user's own preferences, to copy into your own CLAUDE.md and change: nfx never
requires it. The rules every nfx session follows ship with nfx, in
`skills/spec/workflow.md`, which nfx's commands read at their start; what follows is
preferences on top of them. **A project's own CLAUDE.md wins where it differs.** Older projects encode earlier
versions of this workflow, so follow the project rather than "correcting" it, and mention the
difference if it matters.

nfx preferences: ~/.claude/nfx-preferences.md

## Machines

- **Windows:** PowerShell in Windows Terminal (Git Bash is installed but not used interactively).
- **macOS:** iTerm2.
- When a feature, command or shortcut behaves differently between the two, say so explicitly.

## Workflow

I follow the workflow as `L-workflow` gives it.

## Documents

My documents follow `L-documents`.

## Open questions are ambiguities, not records

An open question is an ambiguity, settled as `L-ambiguity` says.

## Delegation

- **The main session is the thinking thread:** planning, investigation, review, decisions.
  Well-specified implementation goes to subagents so the main context stays clean.
- **Keep in the main session:** edit → test → tweak iteration, quick fixes, anything underspecified,
  tuning, and anything judged by look or feel. Such edits keep the specs true (rule `L-outside`).
- **Code changed outside a pending change** follows `L-outside`, and **small by-eye tweaks**
  during a change's human check follow `L-tweak`.
- **Implementers guess conservatively and report.** Routine assumptions are auto-accepted for
  my veto; questionable ones, deviations (bar those `L-deviations` lets through) and open
  questions come to me (rule `L-feedback`).
- **Delegated implementers never commit or push.** Committing is the main session's job, after
  review (see Version control).

## Version control

- **Commit and push without asking when the work is clean, as `L-commit-ask` defines it.**
- When I complete a milestone, its branch is merged with `--no-ff` and the main branch is
  pushed.
