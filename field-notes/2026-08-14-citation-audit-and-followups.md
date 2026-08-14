# Field notes — 2026-08-14 — closing the max-mode follow-ups

## Context

Second half of the `llms-for-coding` max-mode session. The first half expanded the survey and
left six tracked follow-ups; this half closed them. Along the way several things were found
and fixed inline that do not individually warrant their own record, but share themes worth
keeping.

## Issues found and resolved

- **A wrong-axis table read is a *class*, not an incident.** `bugs/2026-08-14-01` (RLEF,
  found by accident in the first half) and `bugs/2026-08-14-03` (DeepSeek-R1, found by the
  audit) are the same error: a multi-column results table read along the wrong axis, so every
  digit is genuinely present in the source and only the row/column assignment is wrong. Two
  instances in one survey is a pattern. **Both are invisible to a substring check**, which is
  what a naive "verify the numbers appear in the paper" pass would do. The audit brief
  therefore named this class explicitly and told verifiers to read tables in `pdftotext
  -layout` and check the row *and* column — and that instruction is what caught the second
  one. No todo: the instruction is now embodied in the reusable packets under
  `_scratch/audit/`.

- **The adversarial refute stage paid for itself immediately — 3 of 10 alleged errors were
  false alarms.** Refuted: DeepSeek-Coder's 87/10/3 mixture (verbatim in the source); an
  efficiency claim the accuser had scoped to the wrong *section* of a survey; and a sentence
  carrying **two** citations where the accuser audited only one and declared the claim
  unsupported. Acting on any of the three would have introduced an error into correct prose.
  The lesson is that a citation *accusation* needs the same verification as a citation:
  "the survey is wrong" is itself a claim about a source. No todo — this is now how the
  audit workflow is shaped.

- **A prose fix can leave the wrong value live in the data.** Correcting "CodeRL runs over
  ~10⁴ APPS problems" to 5,000 fixed the sentence, but the same wrong number was in the
  figure's generator (`training-and-serving-economics.py`, four places including the plot
  annotation) and its `.json` sidecar — the result-of-record artifacts the figure regenerates
  from. Had only the prose been fixed, the next re-render would have silently reasserted the
  error *in a figure*, which is harder to notice than in text. The audit agent flagged this
  itself. Generalisable check: when a corrected value appears in a figure, grep the figure's
  generator and sidecar before calling the fix done.

- **An exhausted WebSearch budget is not an exhausted evidence budget.** The session's
  harness-enforced search pool was spent in the first half, and the first-half report
  recorded the 2026 leaderboard numbers as unobtainable. They were obtainable: the SWE-bench
  team publishes every submission's `results.json` in a public repo, so a plain HTTP fetch
  gives 134 dated submissions with resolved-instance lists — better data than the leaderboard
  page, because it carries the **denominator**. Likewise the arXiv API (over **HTTPS** — the
  `http://` endpoint returns empty here) answered the "does code training improve reasoning?"
  question that two agents had died trying to search for. **Reflex to keep: when search is
  unavailable, ask whether the primary source publishes structured data.** Often the thing
  behind the webpage is a file.

- **A too-broad escape rule corrupted a math span.** Escaping currency `$` in the evidence
  ledgers, I matched `$` followed by whitespace as well as by a digit — which caught the
  *closing* delimiter of `$\binom{n}{k}$`. Lint caught it immediately, but the near-miss is
  the point: a mechanical fix applied across files needs its match set checked against the
  cases it should *not* touch, not only the ones it should.

- **`depth-tier-coverage.py`'s contract is the bare token.** The Phase-1 outline wrote
  Section cells as `sec-4`; the tool wants `4`. It reported `0 TIER-DRIFT` while binding
  nothing — a green gate that had not looked. Fixed in the first half, recorded here because
  it is the same false-green family as the grammar-drift bugs in
  `heading_grammar.py`'s docstring, and because the tally line (`headline 8, load-bearing 6`)
  looked correct *while* the per-section diff was empty, which is what made it easy to miss.

## Patterns / lessons

1. **Distrust agreement between a summary and a number.** Both high-severity citation errors
   this session had correct digits and wrong meaning. Any verification that greps for the
   value and stops will pass them. Verification has to re-read the *structure* the value sits
   in — the table axis, the model column, the split.

2. **Verify the accusation, not just the claim.** A 30% false-alarm rate on alleged citation
   errors means an audit that applies its findings unchecked will damage correct prose at a
   material rate. Adversarial confirmation is not optional polish on an audit; it is half of it.

3. **Follow a corrected value into its artifacts.** Prose, generator, sidecar, rendered asset.
   The survey's own rules already say a figure's numbers must live in its caption *and* its
   data; the corollary at fix time is that a correction has to land in all of them.

4. **"Not available" is often "not available *that way*".** Two of the six follow-ups were
   filed as blocked on a search budget and were closed with `curl`.

## Cross-links

- `bugs/2026-08-14-01`, `bugs/2026-08-14-03` — the two wrong-axis table reads.
- `bugs/2026-08-14-04` — the six medium/low audit findings.
- `bugs/2026-08-14-02` — the `/study` pulse-check over-count (same false-green family as the
  drift-diff note above).
- `todos/2026-08-14-llms-for-coding-followups.md` — the six items this session closed.
- `reports/2026-08-14-llms-for-coding-max-mode-expansion.md` — the Phase-5 report.
