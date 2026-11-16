<!-- Spec: milestone-run. Behaviour changes go through it. -->
# A milestone run: the report (M10)

Read by a milestone run at M10, where `milestone-end.md` sends it. M10 ends the run by telling
the user to start the answers (M11, `milestone-answers.md`) in a new session.
The run's rules are in `milestone-run.md`, which the run has read.

M10. **Report**, in the chat and in the report file: copy this skeleton and fill it in. It holds
    the order of the report's parts, and the bullets after it what fills each.

    ```
    *To read:*
    - <change>: committed (<commit>) | set aside (<side branch or patch>) | waiting (on <what>)
    - **Done for you**
      - **<ID>** <what was done>
    - **Auto-accepted**
      - **<ID>** <the assumption or deviation>
    - **Left as is**
      - **<ID>** <the item>
    - Base branch: <base>; single-change runs stop until the milestone is completed or <base> is checked out
    - Verification: <the end verification's verdict> · Reviews: <the end reviews' verdicts>
    - Run: <what slowed the run>

    ---
    **Your turn**
    Reply by ID, in any order or case: `2.d1 option b, 3.t1 fix, 2.d1 veto: <answer>`
    An item you leave out: a decided-for-you item stands unless a reply vetoes it.

    **Not built**
    - **<ID>** <the change>: <what it waits on, or its side branch or patch>
    **For your triage**
    - **<ID>** <the item> (recommended: <fix | leave | follow-up>)
    **Follow-ups**
    - **<ID>** <the finding> (<its spec, or "new thing">)
    **Decided for you**
    - **<ID>** [near: <n>] <the answer>: <the reason>
    **Design gaps**
    - **<ID>** <what the decision fixed>: extend <the design doc>
    - `/nfx:interrogate <the design doc>`
    **Needs your decision**
    - **<ID>** <location>: <the decision and its reason> (*reviewer: <view>*)
    **Must fix**
    - **<ID>** <what is left> (cause: <spec | execution>, <why>)
    **Human checks**
    - **<ID>** <the change's human check>
    **Milestone check**
    - <the milestone's Check: line>
    **Next steps**
    - <as below>
    ```

    Across the report: every item the user might answer starts with a bold ID; IDs are never
    renumbered; items that share one cause are given once, under the lowest ID, naming the IDs
    it covers, and an answer to it answers them all; a **T** item the user doesn't mention takes its
    recommendation and an **F** item is kept; and a part with no items is left out, with no
    heading and no "none" (the verdicts, the `Run:` line and *Next steps* are always given).
    What fills each part:
    - *To read:* one line per change, with its outcome. **Done for you**: each item the tidy
      round closed, and the folds' consistency edits. **Auto-accepted**: the assumptions and
      deviations the reviewer accepted; the user can veto one (`2.a1 veto`). **Left as is**: the items
      recommended *leave* and not referred; the user can still ask for one (`2.t4 fix`). The `Run:`
      line: each change's fix rounds and what triggered them, any round limit hit, transient
      files ignored, and anything else that slowed the run.
    - **Not built**: one line per **W** item, with what it waits on or where its work went (its
      side branch or patch), so none sits under *Needs your decision*.
    - **For your triage**: the open **T** items, a reopened one included, each with its
      recommendation.
    - **Follow-ups**: the open **F** items, each naming the spec of the thing it concerns, or
      "new thing".
    - **Decided for you**: one line per item the answerer decided, with its ID, the answer and
      the reason. Items with a `near` condition come first, each tagged with it; then the rest,
      by ID. An item the answerer decided is listed only here, not also under *Done for you* or
      *Follow-ups*.
    - **Design gaps**: one line per item the answerer decided with `near: 2` (the design doc
      left a structure unsettled), by ID, with the ID, what the decision fixed (from the item's
      question and the answerer's reason) and the design doc to extend. That is the design doc
      the feature's index header links (the one-file spec's, for a feature that is one file);
      when it links none, the line says the feature has no design doc and names the design
      folder that mirrors the feature's specs folder (`documents/specs/implementing/` becomes
      `documents/design/implementing/`, under the project's documents folder). A last line
      suggests `/nfx:interrogate <the design doc>`. Its items stay under *Decided for you* too,
      and the walk-through does not ask them.
    - **Needs your decision**: the open **D** items, and each **R** item you'd refer that the
      answerer didn't decide (a reopened one included), which stays open: each with its
      location, the reason and the reviewer's view inline.
    - **Must fix**: the open **M** items, each saying whether its cause is the **spec** (back
      to planning) or the **execution**, and why.
    - **Human checks**: each change's **H** item. **Milestone check**: the milestone's `Check:`
      line from the index.
    - *Next steps:* `/nfx:implement <feature> Milestone <name> answers` in a new session, with
      the feature and milestone filled in, starts the walk-through (M11); answering by ID in a
      reply works too, and a decided-for-you item stands unless a reply vetoes it (`2.d1 veto:
      <answer>`). What the user doesn't answer stays as reported: done items stay done, left items stay
      left, decided items stay decided, follow-ups are kept, and **D** and **M** items stay
      open. Every **W** item needs an answer before the milestone can be sent back, and the work
      the answers send to planning is planned first, from the lines under the milestone
      (`/nfx:spec <feature> Milestone <name>`). Then **send it back** or **complete it**
      (`milestone-answers.md`). The repo stays on the milestone branch: what the user commits before
      then (e.g. planning for a send-back) lands there.
    Then notify the user that the run has ended, naming the report file: Claude Code's push
    notification if this session has one (find it with ToolSearch), otherwise a desktop
    notification by the platform's own means (PowerShell on Windows, `osascript` on macOS).
    Then tell the user to start `/nfx:implement <feature> Milestone <name> answers` in a new session,
    with the feature and milestone filled in, and end the run. M11 runs in this session only
    when the user asks for it here: then read `milestone-answers.md` and follow it.
