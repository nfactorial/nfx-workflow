# nfx-workflow

nfx-workflow is a Claude Code plugin that helps you build software with Claude you can keep, extend
and trust. Before any code is written, you and Claude agree a short plan, called a **spec**,
for each part of your project. Agents then build from that spec, a separate agent reviews the
result against it, and once you're happy the spec is updated to match the code. You end up
with working code *and* an accurate, readable description of it, which every later session,
yours or Claude's, can pick up from.

## Contents

- [Why use it](#why-use-it)
- [Prerequisites](#prerequisites)
- [Install](#install)
- [Quick start](#quick-start)
- [Set up a project](#set-up-a-project)
- [A walkthrough: from idea to working code](#a-walkthrough-from-idea-to-working-code)
- [Exploring a UI with mockups](#exploring-a-ui-with-mockups)
- [A second opinion from Codex](#a-second-opinion-from-codex)
- [Working away from the computer](#working-away-from-the-computer)
- [Commands](#commands)
- [Glossary](#glossary)
- [Keeping costs down](#keeping-costs-down)
- [Updating and feedback](#updating-and-feedback)
- [Licence](#licence)

## Why use it

**Claude builds what you meant, not what it guessed.** Most problems with AI-generated code
come from a gap in the request that the agent filled with a plausible guess. nfx-workflow
moves the guessing up front: it reads your design, asks you about each decision it can't make
alone, with a suggested answer, and writes what you agree into a spec. Building starts only
when nothing is left to guess.

**Every change is checked by an agent that didn't write it.** An implementer agent builds
from your spec. A reviewer agent that never saw the build then checks the code against the
spec, and your project's build and tests run as well. Anything the implementer had to assume
comes back to you in the report, so you can veto it rather than discover it later.

**Your documentation stays true.** After each change, nfx-workflow folds it into the spec,
which always describes the code as it is now, not as it was planned months ago. A new
session, a new collaborator or you after a holiday can read one short document and know how
a part works and what must not change.

**Small changes keep Claude sharp.** Work moves one change at a time, each sized to build and
check in one session. Each session starts fresh, with the spec carrying everything it needs,
so the context stays small and the results stay focused.

**You can step away.** Because the plan is complete, building doesn't need you in the room. A
milestone run builds a group of changes on its own branch, and auto mode keeps planning and
building through the night, saving its questions for when you're back.

nfx-workflow is for code you intend to keep: features you'll extend, systems other code relies
on. For throwaway work (a prototype, a UI test bench, a one-off script), say in that project's
`CLAUDE.md` that it is vibe-coded and nfx-workflow stays out of the way.

## Prerequisites

- **Claude Code.** Each change is built, reviewed and fixed by several agents, each starting
  with a small, fresh context; see [Keeping costs down](#keeping-costs-down) for how usage is
  kept in check. Unattended runs use Claude Code's `--permission-mode auto`; if your plan
  doesn't offer it, those runs can't start, though everything else works.
- **Python 3**, standard library only. nfx-workflow's spec lint and its unattended runs are Python
  scripts. Sessions run `python3`, or `python` where `python3` doesn't exist (usually Windows).
- **Git.** nfx-workflow commits each change on its own, and its unattended runs work on branches.
- **Optional:**
  - [Codex CLI](https://github.com/openai/codex), for `/nfx:second-opinion` (see
    [A second opinion from Codex](#a-second-opinion-from-codex)).
  - [lizard](https://github.com/terryyin/lizard) (`pip install lizard`), for `/nfx:health`.
  - The `frontend-design` plugin and Claude Code's Artifact publishing, for `/nfx:mockup`.
    Without publishing, mockups are saved in the project instead.

## Install

In Claude Code:

```
/plugin marketplace add nfactorial/nfx-workflow
/plugin install nfx@nfx-workflow
```

Then start a new session. Every command is under the plugin's `nfx:` prefix: `/nfx:spec`,
`/nfx:implement` and so on.

nfx-workflow only shapes sessions where you run one of its commands; ordinary sessions are
unaffected.

## Quick start

1. Add your project's checks to its `CLAUDE.md` (see [Set up a project](#set-up-a-project)).
2. `/nfx:spec <a thing's name>` plans a spec with you.
3. `/nfx:implement <spec path>` builds it, reviews it and reports back.

The walkthrough below explains each step.

## Set up a project

**Tell nfx-workflow how to check your work.** Add the commands to your project's `CLAUDE.md`, for
example:

```markdown
Checks before a commit: `npm run build`, `npm test` and `npm run lint`.
```

Every build verifies with these. If `CLAUDE.md` names none, `/nfx:implement` stops at its start
and asks you for them, offering to add your answer.

**Know where your documents go.** nfx-workflow keeps them under `documents/`, one folder per role. You
only need `specs/` to start; the others appear when a feature needs them.

| Folder | Holds |
|---|---|
| `documents/specs/` | One spec per part of the project: what it is, how it's built, and its next changes. |
| `documents/design/` | What a feature is and why: the user's view, before any spec. |
| `documents/technical/` | Technical choices and the reasoning behind them, plus the evidence from experiments. |
| `documents/exploration/` | What was tried before deciding: reviews, competing directions, mockups. |

The folders under `specs/` mirror the application, for example `specs/inventory/` and
`specs/save-system/`. A feature with several specs gets a folder with a `README.md` index.

## A walkthrough: from idea to working code

Work moves through **design → plan → implement → tune**, one small change at a time. A small
feature can skip the design and start at step 3. Here is a
small feature taken all the way through: a command-line tool that renames photos by the date
they were taken. Run `/clear` between the steps: the documents carry everything the next
session needs, and a fresh context is cheaper and sharper.

### 1. Design: what you want and why

For anything bigger than a single small part, start with a **design doc**: a page in plain
language about what the feature is, who it's for and what it must do, with no code in it. Ask
Claude to write it with you:

```
Let's write a design doc for a photo renamer in documents/design/photo-renamer.md:
a CLI that renames photos by the date they were taken, for people with
thousands of holiday photos named IMG_1234.jpg.
```

Then have it questioned before you plan from it:

```
/nfx:interrogate documents/design/photo-renamer.md
```

`/nfx:interrogate` asks you the decisions the design leaves open, in rounds of up to four,
each with a recommended answer. For a design doc it starts with the foundations everything
else hangs on: the interfaces, the data, the file formats and the terms the design uses ("what
counts as the date taken: EXIF, or the file's modified time when there's none?"). When the
rounds end it offers to write your answers into the design doc, so it reads as one settled
description, not a list of questions and answers. Review it the way you'd review a colleague's: does it say
what you want, and nothing you don't?

### 2. Technical choices, when they're hard

Sometimes the design is clear but the way to build it isn't: which EXIF library, or whether
reading thousands of files in parallel is worth it. Those choices, the options you weighed and
why the others lost, go in a **technical doc** under `documents/technical/`, along with any
**spike**: a quick throwaway experiment that settles a question by trying it rather than
arguing it.

You rarely write one yourself: when planning hits a choice reasoning can't settle, `/nfx:spec`
proposes a spike, runs it with you, and records the evidence there. The spec then states only
the choice made. Like the design doc, the technical doc is background: it records *why*, so a
future session doesn't propose the rejected option again, but nothing is ever built from it
directly.

### 3. Plan the spec

Now turn the design into a spec:

```
/nfx:spec documents/specs/photo-renamer.md from documents/design/photo-renamer.md
```

nfx-workflow reads the design and technical docs and the code there is, proposes how to shape the work
(what is one thing, what comes first, what waits), and asks about anything it can't decide.
Once you agree, it writes the spec. It opens with a header like this:

```markdown
# Photo renamer — Spec

> - **Template:** v1 · **ID:** photo-renamer
> - **Status:** ready
> - **Blocked by:** none
```

and goes on to the goal, the scope (including what it deliberately won't do), the decisions it
keeps, its modules and interfaces, and acceptance criteria with expected values ("a photo taken
2024-07-14 13:05:09 is renamed `2024-07-14_130509.jpg`"). Read it through: it's the contract
for what gets built, so anything you'd answer differently, say now. A spec with questions left
open stays `draft`; `/nfx:interrogate documents/specs/photo-renamer.md` settles them in rounds.

### 4. Build it

```
/nfx:implement documents/specs/photo-renamer.md
```

An implementer agent builds the spec. A reviewer agent that never saw the build checks the
result against the spec, and your project's checks run; what they find goes back to the
implementer, for at most two rounds. You get a short report:

- **what to try yourself** (the change's *human check*, e.g. "run it on a folder of three
  photos and check the names");
- **assumptions** the implementer made where the spec was silent, already accepted unless you
  veto them;
- **findings and decisions** that need you, each with an ID and a recommendation.

Reply by ID (`d1 option b, t3 fix, a2 veto`). Once you confirm the human check, nfx-workflow folds the
change into the spec and commits.

For harder work, add `deep` to use a stronger model: `/nfx:implement <spec> deep`.

### 5. Change it later

A change to something already built is a **pending change** at the foot of its spec:

```
/nfx:spec documents/specs/photo-renamer.md add a --dry-run flag
/nfx:implement documents/specs/photo-renamer.md
```

### 6. Tune

Values found by eye or feel (sizes, timings, thresholds) are tuned with Claude in the main
session ("make the progress bar update less often"), and nfx-workflow records the final values
in the spec.

### See what's next

To see what's ready, what's blocked and what to do next across a folder:

```
/nfx:spec status documents/specs
```

Now and then, check the code's health too. `/nfx:health` reports on size, length and
complexity, read-only, and suggests refactors for `/nfx:spec` to plan:

```
/nfx:health src
```

## Exploring a UI with mockups

When a feature has a screen and you don't yet know what it should look like, explore before
you design. `/nfx:mockup` has an agent build two or three genuinely different directions on
your real data, and publish them as a page you can open, compare and share for comments:

```
/nfx:mockup the settings screen for the photo renamer: presets vs. a single form
```

It reports what each direction tries and what it recommends. Give feedback in plain words ("keep
B's layout with A's preview strip"), and the same agent iterates; ask it to "check the comments"
when others have commented on the page. Everything is built in its own git worktree, so your
working tree is untouched and you can build other changes alongside.

- `/nfx:mockup pause` saves where you are (feedback, open decisions, the latest round) and
  commits it, so another session can carry on.
- `/nfx:mockup settle B, because presets are what our users ask for` ends the exploration. The
  agent writes a `decision.md` beside the mockups, and nfx-workflow puts the decisions into the feature's
  design doc, creating it if needed, linking the mockups rather than copying them.

**From mockup to code.** A mockup is never built from directly: it is evidence for the design.
After settling, run `/nfx:spec` on the feature, naming the design doc. Planning reads the
design doc and the `decision.md` it links, and writes specs that describe the screen in their
own terms, so the mockup can keep evolving without making the specs wrong. Build those specs
as in the walkthrough.

## A second opinion from Codex

Before building a change that's risky (shared code, ordering or concurrency, a change many
other parts depend on), have a different model read the plan. `/nfx:second-opinion` sends the spec and the
code it touches to OpenAI's Codex, read-only, and asks it what would make an implementer guess.

**Setup, once:**

```
npm install -g @openai/codex
codex login
```

`codex login` signs in with your ChatGPT account (or set an `OPENAI_API_KEY`). Codex is only
ever run read-only: it can't edit your files.

**Use:**

```
/nfx:second-opinion documents/specs/photo-renamer.md
```

Name a pending change after the path when the spec has several. Codex can take a few minutes.
Claude then checks each point against the spec and the code, and sorts them:

- **Gaps:** real ambiguities that need your decision, each with a recommended answer;
- **Errors:** claims in the spec the code contradicts, with the fix;
- **New:** missing acceptance criteria or edge cases, added unless you veto them;
- **Follow-ups:** real problems outside this change, recorded for later;
- **Dismissed:** points that are wrong or already settled, each with a one-line reason.

It walks you through them a few questions at a time, and only edits the spec once you've agreed.
`/nfx:spec` suggests it whenever it marks a risky change `ready`.

## Working away from the computer

Planning needs you; building doesn't. Once a set of changes is fully planned, nfx-workflow can build
them without you and bring everything it would have asked into one report.

### A milestone run: build a batch, answer once

Group a feature's next changes into a **milestone**, a set that ends in something you can see
or run, with a `Check:` line saying how. `/nfx:spec outline <feature>` proposes milestones, and
`/nfx:spec <feature> Milestone <name>` plans one as a whole. Then:

```
/nfx:implement documents/specs/photo-renamer.md Milestone Dry run and undo
```

It builds every change on its own `milestone/…` branch, never pushed. Routine questions go to
an answering agent that decides in your place where the specs make the answer clear; it parks
the rest for you. At the end you get one report: what to read, what was *decided for you* (each
stands unless you veto it by ID), and what needs your answer. Answer it with `... Milestone
<name> answers` in a fresh session, run the milestone check, and merging the branch confirms
it. Use it when you have an afternoon of planned work and want to come back to it done.

### Auto mode: plan and build overnight

`/nfx:auto` goes further: it keeps picking whatever planned or plannable work can go ahead in a
feature, planning it and building it, one fresh non-interactive (`claude -p`) Claude Code session after another,
until nothing more can go ahead without you. Use it at the end of a day when a feature has
several changes queued or one-line items ready to plan, and you'd rather wake up to them done.

Auto mode works on a feature folder. By now the photo renamer has grown several specs, so it
lives in `documents/specs/photo-renamer/` with a `README.md` index:

```
/nfx:auto documents/specs/photo-renamer
```

Once it says the run has started, you can close the session: the run carries on, asks nothing,
and sends a notification when it stops. It works on an `auto/<date>` branch, sets aside any
change that fails rather than stopping, and stops by itself when, for example:

- nothing left can go ahead without you;
- it has used its share of your weekly usage (20% by default);
- three sessions in a row set their work aside;
- a session runs past three hours, or 200 sessions have run;
- your Claude Code sign-in is about to expire.

When you're back:

```
/nfx:auto status     # while a run is going
/nfx:auto answer     # walk through what it couldn't decide
```

**Before leaving either run alone,** check that non-interactive sessions can work here. They run with
`--permission-mode auto`, so your Claude Code permissions must let them edit files, run your
checks and use git without asking. Auto mode stops at once, saying so, when its first session
can't run.

## Commands

| Command | What it does |
|---|---|
| `/nfx:spec` | Plans specs: create one, plan a pending change, outline a feature into milestones, fold in answers or tuned values, audit specs against the code. `status` reports what to do next. |
| `/nfx:interrogate` | Asks you about a design, plan or spec in rounds of decisions until nothing is left to guess, then offers to file each answer where it belongs. |
| `/nfx:implement` | Builds one pending change (or a new spec) through an implementer agent, then reviews and fixes it. `Milestone <name>` builds a whole milestone as one run. Add `deep` for harder work, which uses a stronger model. |
| `/nfx:auto` | Plans and builds queued work unattended, one fresh session after another, on its own branch. `answer` walks you through what it couldn't decide; `status` shows a run in progress. |
| `/nfx:mockup` | Explores a UI question with two or three directions built on real data; `pause` and `settle` save or end the exploration. |
| `/nfx:second-opinion` | Sends a planned change to Codex for an independent read-only review, then sorts what it raises with you. |
| `/nfx:health` | A read-only code health report for a folder (size, length, complexity), with refactors for `/nfx:spec` to plan. |

## Glossary

- **Spec:** the document for one part of the project: what it is and how it's built. Its body
  describes the part as built; it never needs the design or technical doc to build from.
- **Design doc:** what a feature is and why, in plain language, before any spec.
- **Technical doc:** the technical choices for a feature, the options weighed and why, plus
  spike evidence.
- **Spike:** a short throwaway experiment that settles a technical question by trying it.
- **Pending change:** the next change to a built part, planned at the foot of its spec. It is
  `draft` until nothing in it is left to guess, then `ready`.
- **Fold:** writing a built change into the spec's body, as if it had always been so.
- **Blocked by:** the specs or changes a spec or change needs built first.
- **Milestone:** a group of changes that ends in something you can see or run.
- **Human check:** the step where you try a change yourself before it's folded and committed.
- **Index:** a feature folder's `README.md`, listing its specs and the work not yet planned.

## Keeping costs down

Using several agents per change sounds expensive, but nfx-workflow is built so each one does only the
work it is needed for:

- **The main session stays small.** When you build, your session only coordinates: it hands
  the spec to the implementer and reviewer and reads their short reports, never the source or
  the diffs. The heavy reading happens in the agents' own contexts, which end with their work.
  `/nfx:mockup` works the same way, keeping screenshots and HTML out of your session.
- **The spec replaces re-exploring.** A fresh session reads one short spec instead of
  rediscovering the code, which is why each step can start with `/clear`. That matters: a
  session's whole context is re-read on every call, so planning left in it when you build is
  paid for again and again.
- **Review effort matches the risk.** When a change is planned, nfx-workflow picks its review level and
  writes it in the spec's *Delegation* line. A change that nothing else relies on (no shared
  code, public interface or data format) gets a `light review` on a cheaper model; a riskier
  one gets the default `full review`. You can change either setting before you build. The
  stronger `deep` implementer runs only when you ask for it.
- **Every loop is bounded.** A build gets at most two fix rounds before what's left comes to
  you, and fixes after the report get a narrow check, not a second full review.
- **Unattended runs have a budget.** Auto mode stops once it has used its share of your weekly
  usage (20% by default). A milestone run adds a fixed overhead on top of its changes,
  for its end-of-run checks, fold and report.

## Updating and feedback

This is version 1.1.0. Update with `/plugin marketplace update nfx-workflow`, or remove the plugin with
`/plugin uninstall nfx@nfx-workflow`. Questions, bugs and ideas are welcome as
[GitHub issues](https://github.com/nfactorial/nfx-workflow/issues).

## Licence

MIT. See [LICENSE](LICENSE).
