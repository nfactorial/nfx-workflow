<!-- Spec: implement-skill. Behaviour changes go through it. -->

How a run verifies what was built. `build-loop.md` step 4 sends you here, and steps 6 and 8 and the
milestone run send their verification to that step. For a change with a `Repo:` line (its own, or
a new spec's header), every git command here runs in that repo. Do these sub-steps, in this order:

- **Run the checks.**
  - If the project's CLAUDE.md names a build agent, spawn it yourself, from this session.
  - Ask it for its full verification (every build mode and the full test suite it defines), not
    a quick check.
  - With no build agent, run the checks CLAUDE.md requires before a commit yourself:
    - run them in the foreground;
    - send output to a log in the scratchpad;
    - read only each command's result line and any errors.
  - The build agent's report, or your own run's, is the build report and the build evidence of
    record; the implementer's own build claims are not.
  - Every review and fix check is given the build report, and none reruns what it ran.
- **Snapshot.**
  - Snapshot what was verified, for the next round's diff, with
    `python3 <rules folder>/scripts/git_helper.py snapshot --scratch <scratchpad> --name round-N`
    (`L-python`), and note the tree and HEAD it prints.
  - The snapshot catches new files and changes neither the real index nor any ref.
  - For a change with a `Repo:` line, pass `--cwd <repo root>` before `snapshot`.
- **The round's diff.**
  - The round's diff is `git_helper.py --exclude-file <exclude file> round-diff <previous tree> <previous HEAD> <this tree> <this HEAD>`,
    and the files it lists are the round's files.
  - For a change with a `Repo:` line, pass `--cwd <repo root>` before `round-diff`.
  - The files it sets aside as `other_run` (another run's fold landed in this checkout) are that
    run's, and the reviewer is told so.
