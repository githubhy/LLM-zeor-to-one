# Field notes — 2026-07-01 — mechanistic-interpretability survey authoring

## Context
End-to-end `deep-research-survey` (proposed · scale:wide · practitioner) on mechanistic
interpretability: 14-cluster Phase-3 evidence workflow → 63-PDF acquisition → 24-file
main-thread synthesis → mechanical gate → citation-audit. Several issues surfaced and were
resolved within the session; the two wrong-value ones are also in `bugs/2026-07-01-01`.

## Issues found and resolved

- **Wrapped-framing-paragraph citation hazard.** The framing sections (exec summary, fundamentals)
  were authored with hard line-wrapping *before* the single-unwrapped-line discipline kicked in.
  A bare `[N]` sitting at a wrap point is lint-clean — until `link-references.py --init` promotes
  it to `<!-- cite:N -->`, which then trips `lint-math` check #11 (comment at line start = Type-2
  HTML block). Root: the hazard is *latent* at authoring time and only fires after the citation
  pass. Fix: joined the offending lines; **lesson — apply the single-unwrapped-line rule for any
  paragraph carrying `[N]`/markers from first authoring, not as a retrofit.** No todo: the
  discipline is already in the skill's Phase-4 gotchas; this is a "follow it earlier" note.

- **Literal `>` before a digit at a wrap-start became a blockquote.** "defection at >99% AUROC"
  wrapped so `>99% AUROC` started a line → markdown parsed a blockquote → `renumber-paragraphs
  --init` then inserted a spurious mid-paragraph anchor and left an orphan. Fix: reworded to
  "over 99%" and removed the stray anchor. Near-miss: would have rendered a random blockquote on
  GitHub. **Lesson — treat a leading `>` (and leading `[N]`, `<!-- ... -->`) as line-start hazards
  the same way the display-math rules treat `- * + #`.** No todo: mechanical, fully resolved.

- **Citation-audit temp-file race → a false NOT_FOUND.** The audit workflow brief told each Sonnet
  verifier to extract its PDF to a *fixed* path `/tmp/paper.txt`. Concurrent agents overwrote each
  other's file, so the Arditi verifier grep'd Miller's text and reported "file contains the wrong
  paper" (NOT_FOUND ×2). Direct in-process re-check confirmed `arditi-refusal-direction-2024.pdf`
  is the correct Arditi paper (13 models, up to 72B, Qwen/Yi/Gemma/Llama). **Lesson — parallel
  verifier briefs must use per-agent temp paths (e.g. `/tmp/paper-$AGENT.txt`) or extract
  in-memory; a shared scratch path silently cross-contaminates and manufactures false alarms.**
  The agents themselves flagged the race and several recovered by re-extracting in-memory — so the
  MATCH/MISMATCH verdicts stood, only the NOT_FOUND was spurious. No todo: resolved by
  re-verification; the two real MISMATCHes (ROME, Zou) were confirmed and fixed.

- **Two secondary-source value drifts caught at the audit gate.** ROME 8.7%→MLP (actually 6.6%
  MLP / 8.7% individual-state) and RepE LoRRA +6.6/+13.1 (actually +11.3/+11.6). Both had been
  *inline-flagged* at authoring time ("verify in citation-audit pass") per the citation-integrity
  gap-marking fallback — the prevention rule and the audit gate worked exactly as designed.
  Recorded in `bugs/2026-07-01-01` (the wrong-value category).

## Patterns / lessons
1. The "flag-then-audit" discipline paid off: every value the evidence ledger marked
   secondary-sourced was the one the audit had to correct. Marking uncertainty at authoring time
   turned a potential silent error into a caught one.
2. Latent line-start hazards (bare `[N]`, `>`, raw comments) are invisible until a later
   deterministic pass (citation promotion, paragraph init) transforms them — author defensively.
3. Parallel-verifier workflows need per-agent scratch isolation; a shared temp path is a
   correctness bug, not just a nuisance.
