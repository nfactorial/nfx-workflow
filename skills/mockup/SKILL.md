---
name: mockup
description: Explore a UI question with mockups built by a mockup subagent, then iterate on them through it. Part of the optional explore phase before a design doc.
disable-model-invocation: true
argument-hint: "<what to explore> | pause | settle [<choice and why>]"
---

Arguments: `$ARGUMENTS`: the UI question to explore, exactly `pause`, or `settle` followed
optionally by the chosen direction and the reasons for it.

This main session stays on the design conversation. The `nfx:mockup` agent does the building, so
its screenshots, HTML and iterations stay out of this context. Do not read the mockup's files
yourself, except its `continue.md` on resume and its `decision.md` at settle.

**Worktree.** With git, an exploration is built in its own worktree, so it never leaves
changes in the main checkout and an `/nfx:implement` can run beside it. When an exploration
starts or resumes, create it from HEAD, checking out only the exploration folder (plus the
repo's root files), so it costs seconds even in a repo of large binary assets:

```
git worktree add --no-checkout -b mockup/<topic> .claude/worktrees/mockup-<topic> HEAD
git -C .claude/worktrees/mockup-<topic> sparse-checkout set <documents>/exploration/<topic>
git -C .claude/worktrees/mockup-<topic> checkout
```

If `.claude/worktrees/` isn't ignored (`git check-ignore -q`), add it to `<common dir>/info/exclude`
(`<common dir>` is `git rev-parse --git-common-dir`, which every worktree shares), not
`.gitignore`, so the main checkout stays unchanged. If the branch already exists, an
earlier session left it: offer to resume from it rather than replace it. Until a pause or
settle brings it back, the work lives only in the worktree. **Bringing it back** means:
commit the exploration folder in the worktree, then in the main checkout run
`git restore --source=mockup/<topic> --staged --worktree -- <documents>/exploration/<topic>`.
That touches only that folder, whatever else is uncommitted there. Then remove the worktree
(`git worktree remove`) and its branch (`git branch -D`). Without git, or with other version
control, there is no worktree: the exploration is saved in place.

**Pause.** When the arguments are exactly `pause` (a question that merely starts with the word,
such as "pause menu layout", is a new exploration), write `continue.md` in the exploration folder
so a later session can carry on without this one. Ask the agent, if it can still be continued,
for its state first. Write down everything this session holds that the files don't:
- The brief, as sent, and any changes to it since.
- The link, the latest round's path, and where its rebuild command is.
- What the user has reacted to and why: what's kept, dropped, liked and disliked, round by round.
- Feedback the user has given that the agent hasn't applied yet, and what they said they'd try next.
- The decisions still open, and which way the user is leaning on each.

Then bring the exploration back (see Worktree), commit only that folder, `continue.md` with it
(`git commit -- <folder>`), and push, so a pause never leaves work only on this machine or in
a worktree. The open decisions are the exploration's, not a reason to hold the commit. Never
commit other uncommitted work. With git, push to the current
branch's upstream; with no upstream, say so. With other version control, follow the project's
CLAUDE.md; if it doesn't say how, ask the user rather than guess. With none, say the files are saved
locally only. Then tell the user the path and what was committed.

**Settle.** When the first word of the arguments is exactly `settle` (as with `pause`, a
question that merely starts with the word is a new exploration), the exploration ends with a
choice. Find the exploration: the one this session is running, or else a paused one, found and
resumed as below (with several, ask which in one round). The rest of the arguments are the
choice and its reasons; if they are missing, or don't name a direction the agent built, ask in
one round, offering the directions from the latest report. Then run step 5.

**Resume.** Otherwise, first look for `continue.md` files under the project's `exploration/`
folders, and for `mockup/*` worktrees an earlier session left (`git worktree list`). With no
arguments, or arguments that are about a paused exploration's topic, resume it (with several
candidates, ask which in one round): read its `continue.md`, create its worktree (or reuse the
one left behind), spawn a fresh agent with the brief, the exploration's path in the worktree,
its latest round and the link, and tell it to check the
comments, since reviewers may have commented while it was paused. Send it any unapplied feedback
the file lists. Once the agent has reported, relay it as in step 3, delete `continue.md` and carry
on from step 4. With arguments about something else, start a new exploration and mention the
paused ones. With no `continue.md` and no arguments, ask what to explore.

1. **Brief.** From the arguments and this conversation, write the agent a brief: the question,
   who the UI is for, constraints and anything already decided, where real data comes from (a
   local backend, fixtures), and the save path, `exploration/<topic>/` under the project's
   documents folder, given as an absolute path inside the worktree, plus the main checkout's
   root, which it reads the project from. Say whether the data is sensitive (then it's saved,
   not published). Also:
   - **Fidelity:** `greybox`, `mid` or `polished`. Default `mid`; `greybox` for layout and flow
     questions, since polish biases the choice.
   - **Axis:** what the directions should differ on (density, navigation model, modal vs
     inline), if the conversation shows it. Otherwise the agent names it.
   - **Profile:** `web` (desktop, tablet, phone) or `game` (1080p, 4K, 21:9, Steam Deck 16:10,
     TV distance, title-safe area), plus any optional states wanted (loading, error).
   - **Look:** say so if the look itself is the question; otherwise the agent builds inside the
     project's design system.

   If the question is too vague to give two or three distinct directions, ask the user first, in one
   round.
2. **Spawn** the `nfx:mockup` agent with the brief and wait for its report.
3. **Relay** the report in a few lines: the link, the saved path, the axis and the directions,
   its recommendation, its assumptions (such as a look it chose) and the decisions the user needs to
   make.
4. **Iterate.** Send the user's feedback to the same agent (continue it, so it keeps its context) and
   relay its short reply. Batch small changes into one message where you can. When the user says to
   check the comments, forward that: reviewers comment on the published page, and the agent
   reads and answers them. If the agent can't be continued, spawn a fresh one and tell it the
   existing mockup's path in the worktree and its latest round.
5. **Settle.** When the user has chosen (by `settle` or in conversation), send the agent the choice and
   the reasons they gave; it drafts `exploration/<topic>/decision.md`, the handoff the plan phase
   works from. Read it, correct it against this conversation, then put the decisions into the
   design doc (create it if needed), which references the decision file and the exploration
   folder rather than copying them. List each simulated item it names under the design doc's
   *Dependencies* (add the section if needed), unless the design doc already covers it. The design
   doc is written in the main checkout. Delete any `continue.md` in the worktree: the exploration
   is no longer paused. Then bring the exploration back (see Worktree); it and the design doc are
   committed under the usual rules. End by
   offering to run `/nfx:spec` on the feature next, naming the design doc.
