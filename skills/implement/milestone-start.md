<!-- Spec: milestone-run. Behaviour changes go through it. -->
# A milestone run: the start (M0 to M4)

Read by a milestone run once it has read the rules in `milestone-run.md`, and by the end session
M5 starts (`milestone-build.md`), which runs M0 to M3 again; never by an answers session. M5 is
in `milestone-build.md`, M6 to M9 in `milestone-end.md`, M10 in `milestone-report.md` and M11 in
`milestone-answers.md`. "Step N" means a step of `build-loop.md`.

M0. **Sweep.** Delete every report, patch and log file in `<git dir>/nfx/` whose milestone branch
    no longer exists.
M1. **Baseline:** step 0 (read `build-loop.md`). With the milestone branch checked out, read
    `milestone-resume.md` before step 0's busy check, and follow it. Until the branch is started
    or switched to (M2–M4), the run may stop to ask; after that it never does. A busy checkout
    stops and asks, as step 0 says; a milestone run never takes a worktree. A live single-change
    run record (`run-records.md`) stops it too, naming each run: the milestone branch would take
    the main checkout from under that run's fold. Start again once they end. When the user
    confirms carrying on with a changed tree, record those paths in the report file: they stay
    the user's, out of every commit and restore. Step 0 raising that CLAUDE.md
    names no checks is asked of the user at M1, before M4: the answer is the checks for every
    change, recorded in the report file and offered for CLAUDE.md, written only once the user
    agrees. A re-run reads them from the report file.
M2. **A re-run?** If the milestone branch exists, switch to it and read its report file. If its
    last run ended its build session (M5) but not M10, this is that run's **end session**, which
    M3 checks as a first run. Otherwise the user sent the milestone back: this run's number is the
    report's plus one, and its unanswered and unrecorded items carry into this run's list with
    their IDs. If the report records answers that send work to planning (M5, M6b) whose *Not yet
    planned* lines are not in the index (a run that ended before M9), write those lines and
    commit them on the branch now, so M3 sees them. If the branch exists but its report doesn't,
    stop and ask.
M3. **Gather and confirm readiness.** In these sub-steps, in this order:
    - **Gather.**
      - Run `python3 <rules folder>/scripts/spec_lint.py --status <feature folder or spec>
        --milestone "<name>" --json` (`L-python`), which gathers every change and new spec whose
        **Milestone:** part links this feature's index (or its one-file spec) by the milestone's
        name, wherever they live.
      - Read each item's heading and parts (its `spec` and `change`).
    - **Refuse** to start, and report what still needs planning
      (`/nfx:spec <feature> Milestone <name>`), when:
      - the command exits 2;
      - the same command with `--refusals` in place of `--json` exits 2 or prints a refusal (a
        change not `ready`, an old-format spec, a blocker outside the milestone not built, a *Not
        yet planned* line, a skipped file to lint first), naming each with its `spec` and
        `change`: the run checks none of these itself, even where its own reading would agree.
    - **Done.** When the milestone is done (`L-milestone-built`), report its milestone check
      instead of starting.
    - **Refuse an item**, as above, when:
      - an item still has *Unanswered questions* (status mode does not lint, so a `[ready]`
        change with one is in *Ready now*);
      - an item's blockers marked `in_milestone` allow no build order (a cycle);
      - a Delegation says "main session only";
      - a change has a `Repo:` line;
      - a spec that only a change's *Changes* items edit is old-format (`--refusals` names only
        old-format blockers and specs that mention the milestone);
      - on a re-run, a **W** item of the last run is still unanswered (M11).
    - **Already committed.** A change the report records as committed, or whose `Spec-Change:`
      trailer is on the branch since the base, is not built again: it waits for the fold (M9).
    - **Order.**
      - Order the changes by their blockers marked `in_milestone`, ties in the order listed.
      - Say the order in one line.
      - Carry on without waiting.
      - A re-run with nothing left to build goes straight to M6 (`milestone-end.md`) if there are
        commits since the last run ended.
      - A re-run with nothing left to build and no commits since the last run ended goes to M9
        (`milestone-end.md`).
      - A re-run with changes left to build goes to M5 (`milestone-build.md`).
      - The end session (M2) goes to M6 (`milestone-end.md`).
M4. **Start the branch** (a first run only). If the current branch is itself a milestone branch
    (`milestone/…`), refuse: a milestone starts from the branch it will merge into, so ask the user to
    complete the other milestone or switch first. Record the current branch as the base, and its
    commit. `git switch -c` the milestone branch, which keeps uncommitted foreign files as they
    are, and start the report file with the base and run 1. Never push the milestone branch.
    Then read `milestone-build.md` and follow it from M5.
