# Field notes — 2026-08-15 — the multimodal-llms max-mode expansion

## Context

`/deep-research-survey max mode on Multimodal Large Language Models` over a survey that already
existed (30,351 words, authored 2026-06-28 in the same mode) and still read *"under construction
(Phase 4 synthesis)"*. The pass tiered it, deepened all six appendices, re-swept the frontier, and
was gated by two independent Opus re-derivations. Survey ended at ~39.6k words, 45 equations,
53 references, 21 depth tiers where there had been none.

## The theme: I made the same class of error three times, and only grep caught it

I wrote wrong citation numbers **three times** — `[50]` (did not exist), `[11]` for Chameleon (it
is MMMU), `[1]` for ViT (it is CLIP). Seven markers in one case. Every one was written while I was
thinking hard about the *mathematics*, and every one was caught by `grep -E '^\[N\]' references.md`,
never by re-reading my own prose.

The citation-integrity rule says never write a citation from memory. I had internalized that as
*never write a citation whose **content** you have not read* — and I had read all the content, from
the evidence ledgers. What I was recalling from memory was the **index**. That is the same failure
with a smaller surface: a number I was confident about, which was wrong, in a position where being
wrong attributes a real finding to the wrong paper. The Chameleon case would have credited a
training-stability derivation to a benchmark paper across seven markers.

**Practice that worked, and should be the default:** before writing any `cite:N`, grep
`references.md` for the author or title. Cost is one command; the failure it prevents is invisible
to every gate — `link-references` and `validate-refs` both pass a wrong-but-existing number, because
the marker resolves. Nothing mechanical can catch it. At the end of the pass I verified all 17
citation numbers I had introduced this way, in a single command.

I also caught myself, mid-draft, writing a ViT-g width from memory to make a compression ratio
concrete. Replaced with patch arithmetic the survey can verify. Same root cause: the *value* was
recalled while attention was on the argument.

## What the re-derivations bought, including against me

Two Opus reviewers, deriving before reading. **All displayed equations in both target appendices
were correct**; every defect was in the prose around them — the third session running where that
distribution held.

The Appendix B review **corrected a correction of mine**, which is the most useful thing that
happened all session. I had found that the InfoNCE bound's published step is invalid pointwise
(it needs $r \le 1$), bounded the damage at $\log\frac{N}{N-1}$, and concluded the honest form was
$I \ge \log(N-1) - \mathcal{L}$. The first half is right. The conclusion is wrong: **the step is
never used pointwise** — it sits inside an expectation, where $\phi(u) = \log(e^u + N - 1) - \log N$
is convex and $\mathbb{E}[u] = I \ge 0$, so Jensen gives $\mathbb{E}\phi \ge \phi(I) \ge \phi(0) = 0$
unconditionally. The published bound stands exactly as printed. I had solved a real problem that
does not arise, and *weakened a sound result in the name of rigour*.

That is a failure mode worth naming, because it is invisible from inside: my algebra was correct at
every step, the numerics I ran confirmed everything I checked, and the conclusion was still wrong —
because I checked the inequality in the wrong place. **An inequality used only under an expectation
must be checked under that expectation.** A pointwise counterexample to a step that is never applied
pointwise is not a defect.

The Appendix F review then found a table of mine contradicting itself: "infeasible by three orders
of magnitude" assumes an 8k context, while the two rows above it only make sense at a context in the
hundreds of thousands. Both statements were mine, four lines apart. And it caught me asserting a
*mechanism* I had no source for — that two encoders' shared 50 Hz was inherited from the 10 ms hop,
when that hop gives 100 Hz and the missing factor of two is a conv stride one of them is never
claimed to share. I had written that in an appendix whose opening paragraph promises not to fill
gaps from memory.

## Gate holes found (three, all independent)

- **`bugs/2026-08-15-04`** — `validate-refs`'s bare-section-ref pattern required the digit to
  immediately follow `§`, so `§ 2.3` was invisible. 59 dead cross-references sat in delivered files
  while the gate reported clean at error severity. The repair tool was blind the same way, so the
  error message would have named an `--init` that could not fix it. Fixed detector, linked-form
  recognizer and promoter together; 6 regression tests, 2 confirmed RED first.
- **Scope, not pattern** — pre-push runs bare-refs over `surveys/` only; `wikis/` is never checked.
  Widening a regex does nothing for a directory the gate does not scan.
- **`lint-math` is not in the pre-push gate at all.** It runs only as a `PostToolUse` hook, i.e.
  exclusively on files this harness edits. It is the gate the math-authoring rule leans on hardest,
  and its failures are the ones *invisible in source* — they surface only as literal `$x$` in the
  rendered page. Both tracked in `todos/2026-08-15-prepush-bare-ref-scope.md`.

Worth noting the contrast: `crosslink.py` **refused** to report "no gaps" when I handed it a
mis-quoted scope, rather than false-greening. That is the behaviour the other three lack.

## Smaller things, resolved inline

- R-GOV's addendum says the tier table's Section cell is "the delivered heading-anchor id
  (`sec-N`)"; `depth-tier-coverage.py` keys on the bare number. Following the documentation
  literally produced 21 false MISSING-TIER rows and zero joins. Doc-vs-implementation, not a bug in
  either alone.
- The evidence agents corrected **my** brief twice — I asserted SALMONN's two encoders run at
  different rates (they are both 50 Hz), and they overrode me because the brief said to. That
  instruction is cheap and it worked; it should stay standard rather than lucky.
- Both frontier agents died at the step cap (31 and 33 tool calls) after answering 3 of 4 questions.
  The file-first deliverable meant ~18 KB and ~23 KB were already on disk, and a trimmed
  resume-only-Q4 relaunch cost ~15 calls each. The hardening policy did exactly what it claims.

## Patterns worth carrying

**The index is memory too.** Citation-integrity intuitions attach to content; the reference *number*
is equally a recalled fact, equally wrong-able, and uniquely un-gateable because a wrong-but-valid
number resolves cleanly. Grep before every `cite:N`.

**A rigour-motivated weakening is still an error.** The B finding was not sloppiness — it came from
being *more* careful than the source. Being wrong in the conservative direction still ships a
weaker claim than the evidence supports, and nothing flags it, because conservative errors look like
diligence.

**Publish the reason a table cannot be built.** The frontier sweep's most valuable output was that
it could not produce the SOTA refresh it was launched for, and why: a ~14-point spread across four
sources for one benchmark name in two weeks (`decisions/2026-08-15-02`). The temptation is to drop a
null result; here the null result bounds every comparative claim in two sections.

## Refs

- `bugs/2026-08-15-04`; `decisions/2026-08-15-02`;
  `todos/2026-08-15-prepush-bare-ref-scope.md`, `-multimodal-sota-single-harness.md`,
  `-multimodal-residual-gaps.md`.
- `surveys/multimodal-llms/_scratch/review-appendix-{b,f}.md` — the preserved re-derivations.
- `field-notes/2026-08-15-mi-appendix-deepening.md` — the same-day sibling pass, whose lesson
  ("agent findings are input, not verdict — in both directions") held again here in both directions.
