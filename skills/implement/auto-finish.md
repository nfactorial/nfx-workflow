<!-- Spec: auto-build. Behaviour changes go through it. -->
# Auto build: the finish session

Read by `/nfx:implement` when `finish auto` ends its arguments, in place of `pick.md` and
`auto-build.md`. It follows `../spec/auto.md` (read it first, with `runs.md`, `feedback.md`
and `terms.md`) and states its steps in order, "step *n*" a numbered step of `build-loop.md`,
read when starting: they run as written there, but for the differences this file gives. It
never reads the milestone run's files, `milestone-answers.md` among them: M11 never runs.

`/nfx:implement <feature> [deep] finish auto` finishes the change the build session committed
(`auto-build.md`), as `/nfx:auto`'s driver runs it next, with no user present. It never asks:
what a step would ask or wait on is recorded in the run's report instead. Every item ID is
prefixed with this session's number (**4.R1**, `L-auto-report`). Each implementer and reviewer
it spawns is told this is a milestone run, and briefed with every change committed on the
branch but not folded, this one among them (`L-unattended`). Its commits name the run's own
files by path, as `python3 <rules folder>/scripts/git_helper.py --exclude-file <exclude file>
own-files` lists them (`L-python`), and it restores the tree with the helper's `restore`, never
with `git reset --hard`, `git clean` or a stash.

In this order:

- **Starting.** Sweep the run reports and folders, as `auto.md` says. Check the checkout
  (`auto.md`'s) with step 0's `git status`, its exclude file and `run-records.md`, the main
  checkout's live run record counting, because no one is there to say whether it still runs:
  one `auto.md` refuses stops the session with its reason. It never takes a worktree and writes
  no run record.
- **Its change** is the one the run's last section records as committed and not folded, when
  that is a build session's section that records its end (`auto-build.md`, *End*). With no run branch checked out, no such section, or the change
  folded already, the session finds no work: it says and records so as `L-auto-report` gives
  it, and ends. Otherwise it starts its section (`## Session <n>: <command>`, `<n>` the last
  section's number plus one) with the commit it starts at, and works from the build's section:
  its change, items, contexts, assumptions, deviations, leftovers and starting commit. A stop
  is said and recorded as `L-auto-report` gives it.
- **End reviews.** Run the reviews the project's CLAUDE.md requires before a commit, once, over
  the branch from the commit the build session started at (`/code-review` at the level step 2
  reads from the change's *Delegation* line). Their findings are **R** items, each with your
  recommendation (fix, leave or follow-up) and whether `L-triage` would refer it; one that
  repeats an item is merged into it.
- **Answers.** Gather the build's items and the **R** items that `L-milestone-run` gives the
  answerer. With none, skip this. Otherwise spawn one `nfx:answerer`, briefed as its *Your
  brief* says: the rules folder and the repo root as absolute paths, the branch's HEAD commit
  as the commit it reads, the change's spec and the specs its *Changes* edit, the feature's
  design doc, and each item as a question, its ID as `id`, not multi-select, with its options,
  its recommendation and its context. A **D** item's options are every choice it names; a **T**
  or **R** item's fix, leave and follow-up; an **F** item's keep and drop. Give each option
  with what it does and what it costs. The run's own decisions are never given as the user's
  answers. Write each verdict under its item. `decide` answers the item with that option,
  marked as the answerer's, and acted on as the user's answer would be: a fix joins the tidy
  round, and an answer that sends work to planning (a **D** choice that changes what a spec
  says) is only recorded, with the decision and the item's ID, for the fold's *Not yet planned*
  line. `park` and `send_back` leave it open, the condition or misreading added to its context,
  as does no verdict (the agent failed, left it out, or gave an option it wasn't offered).
- **Waiting.** Where a milestone run makes changes wait (`L-milestone-run`), the session
  records the cause in the report instead (`L-auto-waiting`), and skips nothing itself: later
  sessions' picks drop the waiting work. The **M** and **D** items of this list that say so make
  the work blocked by the change wait too. Under each item that makes work wait, the session
  names the work waiting on it that it can see: each item of status mode's output for its
  feature (`python3 <rules folder>/scripts/spec_lint.py --status <feature> --json`, `L-python`)
  blocked by the change, directly or through another, through the *Blocked by* links of its
  change, or of its spec's header for a new spec (for a **D** item of the fold, the work it
  names).
- **Tidy round, once.** Gather every item recommended as a fix and not referred: the **T**
  items and leftovers the reviewer recommended fixing, the **R** items you did, and the items
  the answerer decided as a fix. Give them in one batch to a fresh implementer with the specs
  they concern, then a quick verification (lint, the type check, and the tests of the files the
  batch touched), then a fix check (step 8). A failed verification goes back to the
  implementer once, and an item the fix check finds not fixed goes back once, then a quick
  verification again; when either still fails, restore the tree, and every item stays open,
  saying so. Commit the batch with the `Spec:` trailers of the specs its items concern, and
  mark each item it closed as done; one still not fixed stays open, saying why. An item the
  answerer decided as a fix that the run could not make is **reopened**: no longer the
  answerer's, and treated as an open item it didn't decide.
- **End verification, once.** Run the full verification (step 4, every verification step). If
  it fails, give the failure and the branch's diff from the build session's starting commit to
  a fresh implementer, then verify again and a fix check (step 8), and commit what it fixes with
  the `Spec:` trailer of the change's spec. A fix that needs more than the code to change (a new
  requirement, an interface another thing relies on) is not made: it is an **M** item, as is a
  failure left.
- **The pre-check**, when the change's *Done when* has a *Human check* (a new spec's, in its
  *Build*). Spawn one `nfx:prechecker` with the repo root, at the branch's HEAD with the run's
  files all committed; the spec path; the change name (none for a new spec); and the session's
  evidence folder (`L-auto-report`: `<git dir>/nfx/auto-<date>/<session>/`), as an absolute
  path. Its verdict:
  - `pass`: recorded.
  - `cannot run`: recorded, with its reasons. Nothing waits on it. A pre-checker that ends with
    no reply in its definition's shape is recorded the same way, as giving no verdict.
  - `fail`: the failed parts, each with what the pre-checker observed, go as one fix batch to a
    fresh implementer briefed with the change, then a quick verification and a fix check
    (step 8), with the tidy round's returns. The batch is committed with the `Spec:` trailer of
    the change's spec and recorded as a fix since the change's commit. Then a second
    pre-check, the same, in the `<session>-2/` folder. A part the second pre-check fails, a
    failed part it doesn't try, or a batch that can't be made (the tree restored, and no second
    pre-check) is an **M** item, and the work blocked by the change waits on it
    (`L-auto-waiting`).

  The change's **H** item records each pre-check's verdict, its parts not tried with their
  reasons, and its evidence folders. A change whose *Done when* has no *Human check* gets no
  pre-check, and its **H** item says it has none.
- **The fold.** Spawn one `nfx:spec-folder`, briefed with the rules folder as an absolute
  path, the change (spec path and change name), its Assumptions and Deviations with the
  reviewer's triage, and the fixes since its commit. It returns the lint result, the
  follow-ups, its consistency edits, and what its reference check found. A false claim in a
  spec the run didn't touch, or a stale change or unbuilt spec, is a **D** item with its
  proposed fix; a ready change or unbuilt spec relying on changed behaviour is a **D** item,
  and that work waits on it (`L-auto-waiting`). Commit the fold as one commit, with a `Spec:`
  trailer per spec edited and the change's `Spec-Change:` trailer. Just before it, write the
  *Not yet planned* lines (`T-not-yet`) for answers that send work to planning, each with what
  it does, its spec, the decision and its item ID, under the milestone the change's
  **Milestone:** part names, or under *Later* when it names none. The follow-ups the answerer
  decided (a **T** or **R** item decided *follow-up*, an **F** item decided *keep*) are
  recorded as `L-findings` says, under *Later*. All are committed with the fold, or on their
  own when the fold fails. A fold or lint that fails restores the specs and leaves the change
  committed, not folded: record its **M** item and the change as waiting on it
  (`auto-build.md`, *Committed, not folded*), so no later session builds it again.
- **Report.** Write the session's section (above the `---`), and rewrite *Your turn* (below
  it) at the report's top, after its Base line, from every session's items (`L-auto-report`):
  copy this skeleton and fill it in. It holds the parts' order, and the bullets after it what
  fills each; a part with nothing in it is left out.

  ```
  *To read:*
  - <change>: folded (<commit>) | committed, not folded (<commit>, <M item>)
  - **Done for you**
    - **<ID>** <what was done>
  - **Left as is**
    - **<ID>** <the item>
  - Verification: <the end verification's verdict> · Reviews: <the end reviews' verdicts>
  - Run: <what slowed the run>
  ---
  ## Your turn

  **Waiting on your direction**
  - **<ID>** <its question>: <the condition or misreading>; waiting: <work>
  **Set aside and must-fix**
  - **<ID>** <side branch or patch | what is left>; waiting: <work>
  **Human checks**
  - **<ID>** <change>: <verdict>; not tried: <parts>; evidence: <folders>
  **Decided for you**
  - Session <n>: **<ID>** [near: <n>] <the answer>: <the reason>
  **Design gaps**
  - **<ID>** <what the decision fixed>: extend <the design doc>
  - `/nfx:interrogate <the design doc>`
  ```

  - *To read:* **Done for you**, each item the tidy round closed and the fold's consistency
    edits; **Left as is**, the items recommended *leave* and not referred; the `Run:` line, from
    the build's section and this session: fix rounds and their triggers, any round limit hit,
    transient files ignored, and anything else that slowed it.
  - **Waiting on your direction:** each open item the answerer didn't decide (parked, sent
    back, given no verdict or never seen, reopened, or a **D** item of the fold), with any work
    waiting on it.
  - **Set aside and must-fix:** each **W** item and each open **M** item. **Human checks:** each
    **H** item.
  - **Decided for you:** one line per item the answerer decided, grouped by session; in each,
    the items with a `near` condition first, each tagged with it, then the rest by ID. An item
    listed here is not also under *Done for you*.
  - **Design gaps:** each decided item with `near: 2`, with what the decision fixed and the
    design doc the feature's index header links (the one-file spec's); with none, the line says
    so and names the design folder that mirrors the feature's specs folder.

  The chat gets a short summary: the change and its outcome, its commits, the count in each
  part of *Your turn*, and the report's path. There is no notification and no walk-through.
