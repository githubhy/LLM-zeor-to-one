# Citation Audit — Foundations Enrichment (refs [54]–[58]) — 2026-06-13

**Scope:** the five primaries added for the Section 3 primer — Vaswani (Transformer) [54], Kaplan scaling laws [55], Hoffmann/Chinchilla [56], Su/RoPE [57], Fedus/Switch Transformer [58].
**Method:** numbers extracted verbatim from the PDFs at authoring time (`_scratch/scaling-evidence.md`), then an adversarial transcription cross-check of the Section 3.6 prose against the source loci (value layer for numeric-load-bearing; claim layer for the rest).

## Result: 5 sources, 0 discrepancies

| Ref | Materiality | Checked | Verdict |
|---|---|---|---|
| [55] Kaplan | numeric-load-bearing | exponents αN≈0.076, αD≈0.095, αC≈0.050 reproduced from Eqs (1.1)–(1.3) | correct |
| [56] Chinchilla | numeric-load-bearing | L(N,D)=E+A/N^0.34+B/D^0.28 with E=1.69, A=406.4, B=410.7 (Eq 10); a=0.46/b=0.54 and a=b=0.50; C≈6ND; 70B / 1.4T tokens; Gopher 280B / GPT-3 175B — all matched verbatim | correct |
| [54] Vaswani | claim-load-bearing | softmax(QK^T/√dk)V attention form present in source | correct |
| [57] Su (RoPE) | claim-load-bearing | rotary embedding encodes *relative position* (phase) — confirmed | correct |
| [58] Fedus (Switch) | claim-load-bearing | sparse token routing to experts; trillion-parameter scaling — confirmed | correct |

Every Section 3.6 numeric value matches the acquired PDF exactly (value layer reached for both scaling papers). The claim-level refs ([54],[57],[58]) confirm at the cited locus. No `wrong-value` / `wrong-source` / `fabricated` / `unverifiable` rows; no `bugs/` entry needed.

**Reference invariant:** `check-citation-sources.py` → 58 entries, 0 errors (49 strong `local:` + 9 weak). **Full `/check-survey` gate:** green (lint-math, equation/section/paragraph anchors, cross-file links, bare-refs at error severity, source tags).

**Sources added to download/ (LFS):** vaswani-attention-is-all-you-need-2017, kaplan-scaling-laws-2020, hoffmann-chinchilla-2022, su-rope-2021, fedus-switch-transformer-2021.
