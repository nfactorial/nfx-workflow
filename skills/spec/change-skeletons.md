<!-- Spec: spec-rules. Behaviour changes go through it. -->
# Change skeletons

The skeletons to copy when planning a change: the pending-change block, and the one-line pointer to
the change in each other spec it edits. The rules each follows are in [template.md](template.md)
and [lifecycle.md](lifecycle.md), and, for a **Milestone:** part, [later-work.md](later-work.md).
Delete guidance in *italics* once filled in.

## Pending change

Goes under the spec's `## Pending changes`. Its *Blocked by* entries are separated by commas; a
change is named as its heading writes it, without its status, and a comma inside a change name's
backticks is part of the name.

```markdown
### <Change name>  [draft | ready]

**Blocked by:** *specs or changes that must be satisfied first (`L-built`), every other spec its Changes edit
included, or "none": a spec as a link, a change as [<spec>](<file>) › `<change name>`, one in
this spec too (`T-refs`)*
**Repo:** *only when it works outside this spec's repo*
**Milestone:** *only when planned from a milestone's line (`T-milestone`): [<milestone name>](<the
index, or this spec for a feature that is one file>)*

**Brief:** *What this change does to the thing. Self-contained.*

**Changes:** *what the body will say once this is built: constraints, interfaces,
requirements and the acceptance criteria it adds. Each item is marked and names the body
section it affects; an item for another spec names it first, as <spec> › <section>:*
- ***Add** (<section>): the new text, written as the body will hold it*
- ***Replace** (<section>): the current text, quoted, then the text that takes its place*
- ***Remove** (<section>): the text to delete, quoted*

**Migration:** *one-off work the change needs (corpus or data migration rules, by-hand
cases). Dropped when the change is folded in.*

**Read first:** *specific code files, and built specs as maps to code. Never the design or
technical doc.*

**Touchpoints:**

| Path / symbol | Create / modify | Kind |
|---|---|---|
| *src/…/invoice.py `Invoice.total`* | *modify* | *code* |
| *assets/…/logo.svg* | *create* | *asset* |

*Kind = code / config / asset. Use any finer tags the project defines. Agents can only author
`code` and `config` directly.*

**Fixed:** *public names, contracts, defaults, constraints the implementer must keep, the
code pointer comment of each module the change creates, and the shape of any extension point
it adds (the base or interface, and how a new kind is registered), since later changes copy it.*
**Free:** *what the implementer may decide: private helpers, file split, internal structure,
and the tests (`T-acceptance`).*
**Guardrails:** *where a plausible-but-wrong implementation is likely, state the correct
behaviour positively. Use a negative only when no positive phrasing can express it.*

**Done when:**
- *Agent-checkable:* *every requirement and acceptance criterion in Changes is covered by a
  test · tests and build pass, existing ones each checking what it checked (`T-kept-tests`) ·
  facts a grep can confirm*
- *Human check:* *what you look at, play-test or judge by eye, with what is at hand
  (`L-human-check`); a behaviour that shows only in runs is proven by use or by a milestone
  check, so name what you can see of it and what proves the rest*

**Delegation:** *Sonnet implementer | deep implementer | main session only*, *full review |
light review*. *One-line reason, e.g. "pure C++ with stated requirements", "high blast
radius", "tuning by feel", "values and layout in one component". A human check alone, even by
eye, does not make it main session only: that is for work done by feel or in the editor.
Light or full review per `T-minimum`.*

**Unanswered questions:** *each keeps the change `draft`. Answered → rewrite every affected
part, delete the entry, and promote the change to `ready` once none is left.*
```

## Pointer in another spec

```markdown
### <Change name>  (in [<home spec>](<file>.md))

*A pointer, in each other spec a change edits: one line, no status. The change, its status
and its edits to this spec live in its home spec. Deleted when the change is folded.*
```
