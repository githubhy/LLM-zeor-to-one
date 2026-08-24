# Reported-vs-Persisted Rule

Loaded on demand by `CLAUDE.md`. Read before writing or changing any tool that **mutates an
artifact and prints a summary of what it did** — an applier, an ingester, a grader, a migration, a
gate that writes.

## The rule

**A tool's printed summary must be derived from what LANDED, not from what it intended.** If the
report and the artifact are computed from different objects, one of them is wrong and only the
report gets read.

This is not the denominator problem. `campaign_common.Scope` and `cross-linking.md`'s "coverage is
not silent" answer *did the gate look?* — a green that means "did not look". This answers a
different question: *did the result reach the artifact?* The gate looked, decided correctly, said
so, and the decision never left the process.

## Why it needs a rule

Measured upstream — four instances in one session, and the class recurs:

| Instance | Printed | Persisted |
|---|---|---|
| a verdict ingester | `HELD (promotion withheld): 2 units` on every run for a week | both units `state: verified`, no hold block anywhere |
| a grading applier | `46 graded, 0 refused` | 14 `IDEALIZED` gradings reverted to `EXACT`, ladders dropped |
| an unasserted `str.replace()` | `logged` / `updated` | pattern never matched; a bug read `status: fixed` above "remedy not applied" |
| `git push … \| tail -5` | the last lines of a *successful-looking* log | the push had failed; the pipe swallowed the exit code |

Five prior upstream bugs share the shape — a declared override that never reaches the code path
that reads it, a grid extension that never reaches its branch, constants that never reach the
release overlay, cases that never write their output file, stage predicates that pass without
evidence. **"X never reaches Y" is a recurring bug title**, which is what makes this a rule rather
than a note.

**A report that does not enforce is worse than no report.** It reads as protection everywhere a
reader looks — logs, transcripts, commit messages — so nobody opens the artifact. The hold above
survived from the run that raised it until someone tried to *release* it and checked the state
first.

## The checks

1. **Order.** Every mutation of the object must precede the write. A statement that changes state
   *after* `write_text` changes an object nobody will read. Read the write site and ask what
   follows it.
2. **Derive the summary from disk.** Where the summary is load-bearing — a promotion, a grade, a
   count that gates something — re-read the artifact and report *that*. `campaign_common.assert_persisted`
   does it in one call. `[opt:RVP-SUMMARY · default ON · toggle .claude/skill-options.json]`
3. **Assert the edit landed.** A string replacement, a JSON key update, an in-place rewrite: check
   the match count, then check the *old* content is gone. An unasserted `str.replace` that matches
   nothing is a silent no-op that prints success.
4. **Never let a pipe eat an exit code.** `cmd | tail` reports the *tail's* status. Capture the
   command's own status (`PIPESTATUS`, or run it unpiped) and verify the outcome against the
   system of record — for a push, `git rev-parse origin/<branch>`.
5. **Test by reading the artifact back.** A test that inspects a return value re-checks the same
   in-memory object the report came from, and passes for the same wrong reason. Read the file.

## The mechanism

`viewer/tools/campaign_common.py::assert_persisted(expected, read_actual)` — compares what a tool
believes it wrote against what re-reading returns, and raises `PersistenceMismatch` naming every
divergence. No worked instance in this repo yet: wire it into the first tool here that mutates an
artifact and prints a summary of what it did.

It is deliberately small. Most of this rule is a reading habit; only check 2 mechanises cleanly.

## Cross-references

- `.claude/rules/campaign-lifecycle.md` — "every stage predicate RE-DERIVED rather than read from a
  status field". This is that principle applied to a tool's own report.
- `.claude/rules/cross-linking.md` § "Coverage is not silent" and `campaign_common.Scope` — the
  *denominator* half. Complementary, not the same check.
