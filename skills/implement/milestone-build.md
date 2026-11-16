<!-- Spec: milestone-run. Behaviour changes go through it. -->
# A milestone run: each change (M5)

Read by a milestone run when M4 has started the branch, or when M3 finds a re-run with changes
left to build (`milestone-start.md`). M5 ends by starting the end session, which goes on to
`milestone-end.md`. The run's rules are in `milestone-run.md` and M0 to M4 in
`milestone-start.md`, which the run has read; M6 to M9 are in `milestone-end.md`, M10 in
`milestone-report.md` and M11 in `milestone-answers.md`. "Step N" means a
step of `build-loop.md`.

M5. **Each change, in order:**
    - If any change it is blocked by was set aside or is waiting, or an earlier change's answers
      make it wait (`L-milestone-run`), skip it: it waits, as a **W** item naming what it waits
      on (that change, or the item), with the change's context.
    - Run steps 2–6 for it:
      - Tell the implementer and every reviewer that this is a milestone run. The baseline is
        the branch's last commit.
      - An implementer that ends with no report and no changes sets the change aside.
      - Step 4's verification is a quick one here: lint, the type check, and the tests of the
        files the change touched (with a build agent, ask it for just that).
      - The full verification runs once, at M8; tell every reviewer so, so that what the quick
        one didn't run is not a gap.
      - Step 6's fix round carries its review's leftovers to the implementer. The leftovers no
        round carried (a passing review's, or those found after the round limit) are not
        applied here: they wait for the tidy round (M7), so you read no code. They are written
        to the report file with the change's items, for the end session.
    - **Set it aside** when the build still fails or a must-fix remains after the round limit:
      - `git switch -c` its side branch, commit the change's own files there (foreign and
        transient files left out), and switch back, so the next change starts from a clean tree.
      - If a hook refuses that commit, save a patch of the change (`save-patch`) as
        `<git dir>/nfx/milestone-<feature>-<slug>--<change slug>-<run>.patch` and restore the
        tree (`restore`) instead.
      - Its findings go on the list as **M** items, and the change as a **W** item naming its
        side branch or patch.
    - **Commit** the change's own files on the branch, foreign and transient files left out,
      with its `Spec:` and `Spec-Change:` trailers (`L-trailers`). Its fold comes at M9. If a
      hook refuses the commit, send the hook's output to the implementer once, then a fix check
      (step 8); if it still fails, set the change aside.
    - **Collect** the change's items for the list, and append its outcome and items to the
      report file, with each waiting item's context from the implementer's and reviewer's
      reports, and what M10's `Run:` line gives of it: its fix rounds and what triggered them,
      any round limit hit, the transient files ignored, and anything else that slowed it. Carry
      forward in your own context only the list and each change's one-line outcome: the
      contexts live in the report file.
    - **Answer** the change's items, before the next change starts. Gather its open items that
      `L-milestone-run` gives the answerer. With none, go on to the next change. Otherwise
      spawn one `nfx:answerer`, briefed as *The answerer's brief* (`milestone-run.md`) says, at the change's
      commit (so it reads committed code). A set-aside change's items are not
      answered. Write each verdict as *Writing a verdict* (`milestone-run.md`) says. Then:
      - The change's decided fixes go to its implementer as one batch (a fresh implementer
        briefed with the change, or the same one), as a milestone run, then a quick
        verification, a fix check (step 8) and the tidy round's returns (M7: a failed
        verification goes back to the implementer once; an item the fix check finds not fixed
        goes back once, then a quick verification again), and are committed on the branch with
        the `Spec:` trailer of the change's spec, before the next change is built; the commit is
        added to the report file as a fix since the change's commit. If the batch still fails,
        restore the tree to the change's commit and reopen every item in the batch (M7).
      - The changes its verdicts make wait (`L-milestone-run`) are skipped by M5's first bullet,
        and the walk-through (M11) asks each straight after the item it waits on.
      - An item with no verdict stays for M6b: the changes blocked by this one are built, and
        M6b gives the item to the answerer.
    When the last change has been answered, or set aside or left waiting, the build session hands off:
    - Record in the report file that the build session ended, with the branch's last commit.
    - Start the end session as this session's own background command (the shell tool's
      `run_in_background`), and do not poll it: this session wakes when the command exits. Its
      command is `claude -p "/nfx:implement <feature> Milestone <name>" --permission-mode auto`,
      with the feature and milestone as this run was given them (and `deep` if it was), started
      from the repo root, its input empty and its output written to
      `<git dir>/nfx/milestone-<feature>-<slug>.end.log` (`<command>` and `<log>` below):
      - Bash tool: `<command> < /dev/null > "<log>" 2>&1`.
      - PowerShell tool: `$null | <command> *> "<log>"`.
    - End this turn with a message that names the log, says this session wakes when the end
      session finishes, and says that closing this console stops the end session, and that
      `/nfx:implement <feature> Milestone <name>` then resumes it (M2). The end
      session reads `milestone-run.md` and `milestone-start.md`, where M2 finds it is the end session and M3 sends it to M6
      (`milestone-end.md`).
    - While the end session runs, this session answers questions and does other work as usual, and
      asks the user before it changes files or git state in this checkout, saying the end session
      is working there.
    - When the end session exits, read only the report file, and the log only when the report does not record M10. When it records M10, give the end
      session's summary as the report gives it, name the report file, and offer the answers:
      here by item ID, or with `/nfx:implement <feature> Milestone <name> answers` in a new
      session (recommended). Do not start the answers yourself. When it does not record M10, say
      the end session stopped, show the last lines of the log, and name the command that resumes
      it.
