---
name: second-opinion
description: Send a finished spec change (a pending change, or a new thing's spec) to Codex for a read-only second opinion, then triage what it raises into questions, corrections, additions or dismissals.
disable-model-invocation: true
argument-hint: "<spec-path> [change name]"
---
<!-- Spec: second-opinion. Behaviour changes go through it. -->

Arguments: `$ARGUMENTS`. This is a spec path, optionally followed by the name of one of its
pending changes. With no path, use the spec this conversation has been working on; ask if
that's ambiguous. Below, **the change** is the named pending change; with no name, the spec's
only pending change, or the spec itself while it isn't built. Ask if it has several.

Codex reviews the change against the code. Its view is input, not a decision: you triage it,
and the user decides what changes. Do not edit the spec until they have agreed (step 6).

1. **Gather.** Read the spec's header and the change's heading: note the change's status, the
   technical doc link (if any) and the feature index (if any). If it isn't `ready`, say so
   and ask whether to run anyway: Codex can still review its structure. If the spec is
   old-format (no `Template` line, or one below the current version at the top of
   `${CLAUDE_SKILL_DIR}/../spec/template.md`), suggest `/nfx:spec` to convert it first. Note any extra context Codex needs, from the spec (a `Repo:` line, the specs and
   changes its *Blocked by* names) or from this conversation: other repos, and specs whose
   interfaces must agree with this one. Give each as an absolute path.
2. **Build the prompt.** Name the run after the spec's file name, plus the change's name in
   lower case with spaces as hyphens; every file below carries it, so parallel runs don't
   overwrite each other. Write `second-opinion-<run>-prompt.md` in the
   scratchpad: the text of [brief.md](brief.md) with its placeholders filled in, followed by
   each of these files whole, copied in full, from `${CLAUDE_SKILL_DIR}/../spec/`:
   `template.md` (the body rules), `terms.md`, `lifecycle.md`, `folders.md`, `later-work.md` and
   `feedback.md`.
3. **Run Codex** from the project root, read-only, in the background (it can take several
   minutes), with its progress log sent to a file you don't read unless it fails:
   - Windows (PowerShell): `Get-Content <prompt> -Raw | codex exec -s read-only --skip-git-repo-check -o <scratchpad>\second-opinion-<run>.md - *> <scratchpad>\second-opinion-<run>.log`
   - macOS: `codex exec -s read-only --skip-git-repo-check -o <scratchpad>/second-opinion-<run>.md - < <prompt> &> <scratchpad>/second-opinion-<run>.log`

   If it fails (not installed, not logged in, usage limit), show the last lines of the log
   and stop.
4. **Triage.** Read Codex's output. Check each point against the spec, the spec rules (template and lifecycle, read as needed),
   the technical doc and the code it cites. Read only what you need to settle the point. Put
   each in one of:
   - **Gap:** a real ambiguity or risk that needs the user's decision.
   - **Error:** a spec claim the code contradicts. The code is the authority, so the fix
     is factual; give it.
   - **New:** a missing acceptance criterion, check or edge case whose correct behaviour
     the spec already makes clear, so adding it needs no decision. Give the exact addition. If the behaviour
     isn't clear, it's a Gap instead.
   - **Follow-up:** a real problem outside this change. It is recorded as a *Not yet planned*
     line (`T-not-yet`) unless the user drops it, or planned now as a pending change or a new spec if
     they ask; never an addition to this change (`L-findings`).
   - **Dismissed:** wrong, already settled (the spec or technical doc covers it), within the
     change's *Free* latitude, or style. One-line reason.

   Report: one line with the counts and Codex's confidence line, then Gaps, Errors,
   New items (accepted unless the user vetoes), Follow-ups (recorded unless the user drops one), and Dismissed
   (one short line each, so the user can veto any). Each item starts with a bold ID, its section's
   letter and its number within it (**G1**, **E2**, **N1**, **F1**, **X3** for dismissed; the
   letters are defined in *Terms*' *Report item letters* table in `../spec/terms.md`), and
   each Gap gives your recommended answer. Give the absolute path of Codex's full output.
5. **Walk the user through it.** Straight after the report, ask the user each item as an AskUserQuestion
   question, up to 4 per call, in the report's order. Each question's header is its ID, and
   its text stands on its own, since the user answers it without the report in view: what Codex found
   and where (spec section, file:line), what the spec or code says now and why it matters, then
   what is asked. Build it from Codex's full output, not the report's one line. Its first
   option is your recommendation, labelled "(Recommended)" and described "Decision: <what it
   does>", then why you recommend it; every other option's description says what it does and
   what it costs. The others are the rest of its set below. `preview` holds the spec text or
   code it concerns when that is clearer than prose. Items that share one cause are one
   question.

   | Item | Options |
   |---|---|
   | **G** | your answer · one alternative (name any others in the text) · for later |
   | **E** | accept · reject |
   | **N** | add · veto |
   | **F** | record · drop · plan now |

   *Other* is the user's own answer, recorded word for word. *For later* leaves the question
   unanswered. *Other* saying "discuss" stops the walk-through once that call's answers are
   in; when it is talked through, it carries on with the rest. The dismissed items are one
   question, last ("keep all dismissed" · "go through them"); going through them asks each
   with "dismiss" · "reconsider", and a reconsidered one is triaged again and asked in its
   new section. Answering by ID in a reply works too. The walk-through's end is the user's agreement
   for step 6.
6. **File, once the user agrees.** Following the spec rules: add each question the user doesn't answer on the
   spot to the change's *Unanswered questions*, and move the change back to `draft` if it was
   `ready` (its heading, or for a new thing the spec's header). Fold in the answers the user gives and the
   additions they don't veto into the change, and the corrections they accept into wherever the
   claim was made. Record each follow-up the user doesn't drop as a *Not yet planned* line
   (`T-not-yet`), or as a pending change or a new spec where the user asked for one, and list where
   each went. If there are several questions, suggest `/nfx:interrogate`.
   Leave committing to the usual rules.
