# Triage Labels

The skills speak in terms of five canonical triage roles. This repo keeps the **default
label strings verbatim** on GitHub — the label namespace is GitHub's own and the repo had
no issues when this was set up, so there was nothing to collide with — and additionally
documents how each role **projects onto the in-repo record vocabulary** when an issue
graduates (see `issue-tracker.md`).

Two columns do the work of the usual one: the middle column is what `triage` applies; the
right column is what the record carries after graduation.

| Label in mattpocock/skills | Label in our tracker | Projection when it graduates into a record |
| -------------------------- | -------------------- | ------------------------------------------ |
| `needs-triage`             | `needs-triage`       | *(none yet — not decided, so no record exists)* |
| `needs-info`               | `needs-info`         | `todos/` `status: open`, with the blocker named in *What is left* |
| `ready-for-agent`          | `ready-for-agent`    | `todos/` `status: open` (or `in-progress` once picked up) |
| `ready-for-human`          | `ready-for-human`    | `todos/` `status: open` (or `in-progress` once picked up) |
| `wontfix`                  | `wontfix`            | `bugs/` `status: wontfix` + a `**Reason.**` line — or simply close the issue with a reason if no record was ever warranted |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the label
string from the middle column.

## Notes

- **`wontfix` is shared vocabulary already.** `CLAUDE.md`'s Bug Capture defines
  `status: open | fixed | wontfix | duplicate`, so this role maps onto an existing field
  rather than introducing a new one.
- **There is no `fixed` / `closed` triage label, deliberately.** Completion is recorded by
  the record's own `status` transition (`closed` for a todo, `fixed` for a bug) and the
  issue is closed pointing at it. A label asserting completion on the intake surface would
  be a second source of truth for the same fact.
- **`in-progress` has no label either.** GitHub assignment (`--add-assignee @me`) marks
  who is on it; the record's `status: in-progress` marks that the work started. Both are
  already covered.
- Edit the middle column only if the GitHub label vocabulary changes; edit the right
  column only if `CLAUDE.md`'s capture conventions change.
