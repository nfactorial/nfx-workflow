<!-- Spec: spec-rules. Behaviour changes go through it. -->
# Terms

The terms the rules and skills use, and the one table of report item letters. Read when planning
a change or a milestone, and by a report that uses letters beyond **C**, **A**, **T**, **F**, **D**
and **M** (`report.md` defines those itself): a milestone run's, auto build's and auto mode's. Versioned with [template.md](template.md)
(`L-version`); this file states no version of its own.

**Terms** used with one meaning throughout the rules and skills, each with where it is
defined: a rule's ID, when a rule defines it, and that rule alone says when it holds (what an
unattended run does differently is `L-unattended`'s, in [runs.md](runs.md)):
- **`built`**: a status value (`L-status`); "built" in plain prose means implemented.
- **folded**: a built change written into its spec's body (`L-fold-in`).
- **satisfied**: a *Blocked by* that no longer holds its work back (`L-built`).
- **done**: a milestone ready for its milestone check (`L-milestone-built`).
- **confirmed**: a milestone whose milestone check the user has confirmed.
- **human check**: the user's check in a change's *Done when*.
- **milestone check**: a milestone's `Check:` line.
- **fix check**: the reviewer's narrow pass over a fix round after the report
  (`/nfx:implement` step 8).
- **reference check**: the fold's check of the specs that reference the folded one
  (`L-fold-check`).
- **fix batch**: the fixes of one reply, round or verdict, given to one implementer together,
  then one quick verification and one fix check; a failed verification, or an item the fix
  check finds not fixed, goes back once (`/nfx:implement` step 8, M7).

**Report item letters.** The one table of the letters a report's items start with; a report
cites it and defines no letter. An item's ID is its letter and its number within it, prefixed
as each report says (a change's place in the order, a session's number in
auto's: **2.D1**, **3.R1**).

| Letter | Meaning | Appears in |
|---|---|---|
| **A** | an assumption or deviation auto-accepted | every run's report |
| **C** | a leftover cleaned up | a single run |
| **T** | a finding for the user's triage | every run's report |
| **F** | a follow-up outside the change | every run's report, `/nfx:second-opinion` |
| **D** | a decision the user must make | every run's report |
| **M** | a must-fix still open | every run's report |
| **H** | a human check | a milestone or auto run |
| **R** | an end review's finding | a milestone or auto run |
| **W** | a change the run set aside, with its side branch or patch, or, for a milestone run, a change left waiting, with the item it waits on | a milestone or auto run |
| **Q** | a planning question | auto mode |
| **G** | a gap in the spec needing the user's decision | `/nfx:second-opinion` |
| **E** | an error: a spec claim the code contradicts | `/nfx:second-opinion` |
| **N** | a new criterion, check or edge case | `/nfx:second-opinion` |
| **X** | a point dismissed | `/nfx:second-opinion` |

A letter's meaning is written here only.
