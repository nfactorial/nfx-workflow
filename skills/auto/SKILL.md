---
name: auto
description: Run queued planning and building work unattended - a driver runs one fresh headless /nfx:spec or /nfx:implement session after another on an auto/<date> branch, until no queued work can go ahead or a stopping rule holds, then notifies; `answer` answers the last run's report, and `status` shows a run in progress.
disable-model-invocation: true
argument-hint: "[feature-folder] | answer | status"
---
<!-- Spec: auto-loop. Behaviour changes go through it. -->

**Read `${CLAUDE_SKILL_DIR}/../spec/workflow.md` at the start, before any other file:** the
rules every nfx session follows (`L-workflow`, `L-commit-ask` among them).

Arguments: `$ARGUMENTS`.

**`answer`** as the argument: read `${CLAUDE_SKILL_DIR}/answers.md` and follow it. Nothing
else in this file applies.

**Before running any script**, choose the Python command (`L-python`).
Every script this file runs uses that command, written `<python>` below.

**`status`** as the argument: run `<python> "${CLAUDE_SKILL_DIR}/status.py"` from the repo root,
give its output as it is, and do nothing else in this file.

**Otherwise** the argument, if any, is a feature folder, and this session starts a night's run.
The driver does the run: it runs each unit of work as its own headless session, and every change
to the repo is one of those sessions'. This session only starts it and gives its end.

1. **Check no run is going:** run `<python> "${CLAUDE_SKILL_DIR}/started.py" check` from the repo
   root (`git rev-parse --show-toplevel`). When it exits 1, give its line and end, starting
   nothing.
2. **Start the driver** from the repo root, through Bash with `run_in_background`:

   ```
   <python> "${CLAUDE_SKILL_DIR}/driver.py" [<feature-folder>]
   ```

   Pass the feature folder as the one argument when one was given, and nothing else. Then run
   `<python> "${CLAUDE_SKILL_DIR}/started.py" wait` from the repo root, in the foreground.
3. **When `wait` exits 0, tell the user the session can be left:** the run goes on without it, asks
   nothing, and raises a notification when it stops. When it exits 1, say nothing about leaving.
   Nothing said before `wait` exits 0 claims the run has started. Then wait for the driver to
   exit; don't poll its output.
4. **When the driver exits**, read its output:
   - **Exit 1:** it refused to start and ran no session. End the session with its reason, its
     output's last line.
   - **Exit 0:** when its output has a `report: <path>` line, read that report and give its
     *To read* section as the report holds it (from its *To read:* line up to the `---` rule above *Your turn*), then the driver's last line, the stop reason, then
     the report's *Your turn* section as the report holds it, without rewording or shortening
     either section, then end with `/nfx:auto answer`. With no `report:` line, no
     run branch exists: give the stop reason alone.
