# Citation Audit — `surveys/llms-for-coding/` — 2026-06-13

**Target:** the 19-file "Large Language Models for Code" survey.
**Method:** adversarial fan-out workflow (`wf_0a879215-105`) — one verifier per source PDF, each instructed to refute. Verifiers reproduced every load-bearing numeric/claim citation from the actual PDF locus (targeted `pdftotext`/`pymupdf` reads, not whole-document reads) and returned structured verdicts. Prevention discipline (`.claude/rules/citation-integrity.md`) was applied at authoring time; this is the after-the-fact gate.

## Result summary

| metric | value |
|---|---|
| Sources verified (PDFs) | 32 |
| Load-bearing claims audited | 84 |
| `correct` | 83 |
| `wrong-value` | 1 (fixed) |
| `wrong-source` / `fabricated` / `unverifiable` | 0 |
| dead/empty verifiers (`tool-unavailable`) | 0 |

All 45 `local:` references resolve to acquired PDFs (`check-citation-sources.py`: 45 strong / 8 weak / 0 errors). The 8 weak-form references (7 `web`, 1 `abstract-only`) back only dated/contextual claims, not load-bearing derivations — chiefly the deliberately caveated SOTA band in the State-of-the-Art section.

## The one finding (fixed)

**ref 17 — Magicoder — `wrong-value`.** §8 stated the Code Llama-Python-7B base as "48.2% HumanEval pass@1." The verifier read Magicoder Table 1 and found 48.2 is **WizardCoder-CL-7B**; the true Code Llama-Python-7B base is **37.8 (34.1)**. The dependent figures (Magicoder-CL 60.4, MagicoderS-CL 70.7, MagicoderS-DS 76.8) were all correct.

- **Impact (Phase 5 citation-impact audit):** the wrong value was a *base anchor* in a before→after comparison, not an input to any derivation. The section's conclusion — that OSS-Instruct substantially improves the base — holds and is in fact *strengthened* by the correction (the real gain is +22.6, not the +12.2 the wrong base implied). Classified load-bearing-to-a-headline-claim but not derivation-propagating → severity `med`.
- **Fix:** 48.2 → 37.8 in `instruction-tuning-and-alignment.md`, re-verified against `download/magicoder-2023.pdf` Table 1. Logged as bug `2026-06-13-01`.

## Two drifts caught earlier (during authoring, pre-audit)

Authoring-time verification against newly acquired PDFs corrected two figures the Phase-3 scratch notes had drifted, before they reached the survey:

1. **o-series Codeforces (ref 26).** Scratch reported o1 at 1807/89th; the primary paper shows o1 = **1673/89th** and 1807 is the domain-specific *o1-ioi*. Survey uses the corrected 1673; o3 = **2724/99.8th** (scratch had ~2706).
2. **RLEF (ref 20).** Scratch carried abstract-only figures; verified against full text (70B test 41.2 vs 38.0 public-only; SOTA at 8B/70B; ~10× fewer samples) before writing.

## Conclusion

The survey passes the citation gate: every external claim traces to an acquired source, and every audited load-bearing number is reproduced from its source. One transcription error was caught and fixed; it did not change any conclusion. Combined with a green `/check-survey` (lint-math, equation/section/paragraph anchors, cross-file links, bare-ref prohibition, reference source tags), the deliverable is signed off.

**Sources added to `download/` for this survey:** 45 PDFs (see `surveys/llms-for-coding/references.md` `local:` tags and `_scratch/ledger-index.md`).
