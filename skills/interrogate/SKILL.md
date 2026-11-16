---
name: interrogate
description: Plan-phase questioning - ask the user in rounds of decisions about a feature, plan or spec until every branch is settled, then file each answer in the right document. Use when the user wants a design stress-tested, asks to be questioned, interrogated or grilled about a plan, or a spec or pending change has too many unanswered questions to be ready.
argument-hint: "[topic | design-doc path | spec-path [change name]]"
---

<!-- Spec: interrogate-skill. Behaviour changes go through it. -->
# /nfx:interrogate: settle every decision, and file it where it belongs

**Topic:** `$ARGUMENTS`, or the plan under discussion in this conversation.

**Read `${CLAUDE_SKILL_DIR}/../spec/workflow.md` at the start, before any other file:** the
rules every nfx session follows.

This skill is interactive, so it runs in the main session. A subagent can't ask questions.
Where an answer goes follows `L-documents` and `L-ambiguity` and, for specs, the spec rules.
Before filing an answer, read `workflow.md` (again, if a compaction has dropped it) with
`${CLAUDE_SKILL_DIR}/../spec/template.md`, `lifecycle.md`, `folders.md` and `later-work.md`,
those four for an answer in a spec. This skill is the procedure.

## 1. Prepare the agenda

- **Walk the design's foundations first, for a design doc only.** When the topic is a design
  doc, or a feature whose index or spec links one, the agenda opens with the design's
  foundations, before its other decisions, since those hang on them. A spec, or a spec and
  change name, gets no walk. A foundation is settled by what it must offer or mean, never by
  how it is built: how is the spec's. There are four kinds:
  - an **interface** other code calls: its operations and the guarantees each gives;
  - a **data model**: its fields, what each holds, and the rules across them;
  - a **file format**: its structure, and what a reader does with a version or field it
    doesn't know;
  - a **domain term**: what it means, and what it does not.

  List every foundation the design names or implies (its features, flows and screens rely
  on it), with the design's own `## Foundations` section if it has one. Each foundation
  whose design doesn't say, for its kind, all of the above is one agenda decision per
  missing part. A foundation the design already settles gets no decision. The user is still
  asked each decision in the rounds of step 2, with a recommendation.
- Read what already exists: the design, technical and spec docs for this topic, and the code
  it touches. Don't ask anything they already answer.
- List the **open decisions** and how they depend on each other. A decision others hang on
  comes first. If the topic is a spec, start from the *Unanswered questions* of the pending
  change being planned (or of the spec itself, while it isn't built). Share the
  list briefly as the agenda, and keep it current: answers often open new branches.

## 2. Ask in rounds

- **Separate facts from decisions.** A *fact* is something the code, the docs or the engine can
  answer. A *decision* is the user's to make. Never ask the user a fact.
- **Send facts to a subagent.** For any fact that needs more than a glance at one known file,
  dispatch a background Explore subagent (`model: "sonnet"`) with one precise question and
  keep going. Only the decisions that depend on that fact wait for it.
- **Facts that need an experiment:** propose a spike (a small throwaway experiment) rather than
  guessing. Its evidence goes to the technical doc; its code is discarded.
- **A round asks every decision whose prerequisites are settled.** Independent discrete
  choices go together in one AskUserQuestion call (up to 4), with the recommended option first
  and marked. Decisions that depend on an unanswered one wait for the next round. Open-ended
  questions go in prose, one at a time.
- **Lead with a recommendation:** your suggested answer and a one-line reason. Word prose
  questions so that a plain "yes" accepts the recommendation.
- **Push back once** if an answer conflicts with an earlier decision, a stated constraint or
  the code. Then accept the user's call.

## 3. Sort each answer as you go

- **Resolved ambiguity** (most answers): becomes plain-fact content in the design doc, or in
  the pending change (or new spec) being planned, wherever the gap was.
- **Foundation decision** (from the step 1 walk): a resolved ambiguity whose place is the
  design doc's `## Foundations` section, under the sub-heading for its kind
  (`### Interfaces`, `### Data models`, `### File formats`, `### Terms`), one entry per
  foundation, named in bold and followed by what it must offer or mean. Create the section
  when the design has none, with only the sub-headings that hold an entry.
- **Technical choice** (real options weighed): the spec gets the selected approach; the
  technical doc gets the reasoning, if the rejected options are worth recording.
- **Value to be found by feel:** becomes a knob for the spec's *Tunables*, not a decision now.

Keep a concise running log in the conversation. Don't edit documents mid-interrogation
unless asked.

## 4. Finish

Stop when the agenda is resolved or the user calls time. Then report:

1. **Content updates** for the design doc (the foundation entries among them) and spec, and
   any **technical choices** with their options and reasoning for the technical doc.
2. **Still open:** each with the specs and pending changes it affects.
3. **Next step:** usually `/nfx:spec` to fold the answers in and promote changes (or new specs)
   to `ready`; or a
   technical doc first, when real technical choices were reasoned; or a spike.

Offer to make those document updates. Don't make them unprompted.
