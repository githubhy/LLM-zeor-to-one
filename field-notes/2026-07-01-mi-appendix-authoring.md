# Field Notes — Authoring Appendix I (Mechanistic Interpretability)

## Context

Built a new 9-section, 22-equation, 24-source MI appendix for the llms-for-coding survey in one session (plan `2026-07-01-mi-clusters-survey-buildout.md`). Sources were acquired to `download/`, extracted to a pdftotext cache, and every citation verified in-source before/at authoring time. This note records the issues the verification pass caught and resolved inline.

## Issues found and resolved

- **Mis-attributed linearity (Li Othello).** Draft §I.7 called the Othello board-state representation "linearly-decodable" and cited Li et al. [83]. In-source check: Li's abstract states an *emergent nonlinear* representation and that "Linear probes, however, produce poor results" — the *linear* result is Nanda et al. [84]'s later correction (board state linear in "MINE vs. YOURS" relative coordinates). Fixed: [83] now credits the emergent, causally-intervenable representation; [84] credits the linear reading. *Why missed initially:* the two Othello papers are routinely conflated in summaries; the linear/nonlinear split is the whole point of the second paper. *No todo* — corrected inline before delivery.
- **Citation to content not in the source (superposition geometry).** Draft §I.2 attributed the superposition "phase transitions / antipodal-digon-tegum geometry" to Cunningham [70]. Grep of the acquired PDF: 0 hits — that material is Elhage's *Toy Models of Superposition* (transformer-circuits.pub, not acquired). Fixed: removed the unsourced geometry; kept the "features must be sufficiently sparse for superposition to arise" point, which Cunningham *does* state. *Why missed initially:* the phase-transition picture is strongly associated with the superposition topic generally, so it read as "obviously in the SAE paper." *No todo* — corrected inline.

## Patterns / lessons

- **The signature-term grep confirms a paper is *about* a topic; it does not confirm *this specific claim* is in *this* paper.** Both errors passed the coarse signature grep (Cunningham is full of "superposition"; Li is full of "board state") but failed the precise-claim check. Lesson: for any load-bearing attribution, grep the *specific* sub-claim (phase-transition, linear-vs-nonlinear), not just the topic.
- **Conflation risk is highest between a paper and its follow-up** (Li→Nanda, Cunningham→Elhage). When two papers sit in a lineage, verify *which* one owns each claim, not just that the lineage owns it.
- The pdftotext-cache + grep workflow (the §C.8 grokking-pass discipline) scaled cleanly to 24 sources and caught both errors pre-delivery — cheap insurance, kept as the default for multi-source authoring.
