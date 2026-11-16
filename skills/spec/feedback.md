<!-- Spec: process-rules. Behaviour changes go through it. -->
# Feedback from implementation

What comes back from a build and what happens to it (`L-feedback`). Read by the spec reviewer
at its triage step, by a milestone run before M3 and by auto build (with `auto.md`), and by
`/nfx:spec` when it folds an implementation's report. The other rules are in
[template.md](template.md), [lifecycle.md](lifecycle.md), [folders.md](folders.md) and
[later-work.md](later-work.md).

## Feedback from implementation `L-feedback`

- **An assumption is a decision the spec should have made:** `L-assumption` behaviour, a public
  interface or data, or anything another thing relies on. An implementer fills such gaps
  conservatively and reports each one. Choices within the change's *Free* latitude are not
  assumptions: they are neither approved nor folded in.
- **The reviewer triages assumptions and its own should-fix and nit findings.** `L-triage` What
  it refers, what it accepts or recommends, and how low the bar is:
  - The reviewer refers an assumption or a should-fix or nit finding to the user when it:
    - contradicts the spec;
    - changes behaviour a user would notice that the spec doesn't state;
    - reaches into another thing, a non-goal, code the change didn't write or a rule of the
      project's CLAUDE.md;
    - would be costly to reverse.
  - Every other assumption the reviewer agrees with is **auto-accepted**, and every other
    finding gets a recommendation (fix or leave) that is acted on: both are listed for the
    user, who can still veto them.
  - An assumption the reviewer thinks is wrong becomes a review finding.
  - Bringing code in line with the spec is never a reason to refer: code that differs from
    what the spec states is a must-fix, however visible.
  - The bar is low because the user's human check and later testing follow; when in doubt,
    refer.
- **Accepted assumptions** `L-accepted` are folded into the change, as if a question had been
  answered, and so reach the body when the change is folded. A rejected one sends the change
  back to `draft`.
- **Deviations and open questions go to the user.** `L-deviations` How a deviation is settled,
  the one kind that is auto-accepted, and open questions:
  - A deviation (the code had to differ from the spec) is settled by changing the spec or the
    code; either way the body ends true.
  - The one exception, a deviation that doesn't go to the user, is one that the reviewer
    judges fine and that changes one of these, and nothing else:
    - only tests and test helpers;
    - only comments and docs (never a spec);
    - or only where the code sits (its Touchpoints), not what it does.
  - Such a deviation is auto-accepted as an assumption would be.
  - Open questions always go to the user.
- **A kept test keeps what it checked.** `T-kept-tests`: a test may follow code that moved or
  was renamed (its imports, the module it calls), and may lose duplicated setup to a shared
  helper. It may not lose assertions or cases, loosen an expected value, or be skipped.
- **Findings outside the change** `L-findings` (a review's out-of-scope notes, a gap in shared
  code) are follow-ups (`T-found`). Each is recorded as a *Not yet planned* line
  (`T-not-yet`) unless the user drops it, or planned now as a pending change or a new spec
  when the user asks. They are recorded in the session that found them: by the fold, or, when
  the change goes back to `draft` instead, with that edit; an unattended run records them as
  `L-unattended` says. The report gives each one's destination by its ID, so one left
  unrecorded shows. A follow-up's line goes in the feature index of the spec it concerns
  (`T-not-yet`); one that concerns no spec goes under *Later* in the index of the feature whose
  change found it (in the one-file spec, for a feature that is one file), saying that it
  concerns no spec.
