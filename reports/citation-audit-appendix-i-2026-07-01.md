# Citation Audit — Appendix I (Mechanistic Interpretability)

- **Date:** 2026-07-01
- **Target:** `surveys/llms-for-coding/appendix-i-mechanistic-interpretability.md`
- **Scope:** references [70]–[93] and every in-text use
- **Method:** locus-targeted verification against acquired sources (pdftotext cache, sub-claim grep); values reproduced from source, not recalled.

## Result

**24 citations, 24 `correct`.** No `wrong-source`, `wrong-value`, `fabricated`, or `unverifiable` in the final document. Two attribution errors existed in the draft and were **caught + fixed during authoring-time verification, before this audit** (recorded in `field-notes/2026-07-01-mi-appendix-authoring.md`): Li [83] linear→nonlinear (linear result is Nanda [84]); Cunningham [70] superposition phase-transition/tegum geometry removed (not in [70]; that is Elhage TMS, unacquired). Both are `correct` as they now stand.

| Tag | Count |
|---|---|
| correct | 24 |
| wrong-source | 0 |
| wrong-value | 0 |
| fabricated | 0 |
| unverifiable | 0 |

## Ledger

| Ref | Claim in Appendix I | Materiality | Verdict | In-source evidence |
|---|---|---|---|---|
| [70] Cunningham | polysemanticity; superposition = more features than neurons, overcomplete directions; sparsity necessary; SAEs pin causal features finer than neurons | claim-LB | correct | abstract + §1: "represent more features than they have neurons… overcomplete set of directions"; "must be sufficiently sparsely activating" |
| [71] Gao | top-$k$ SAE fixes $L_0=k$, removes $L_1$ shrinkage; Pareto/loss-recovered | claim-LB | correct | "TopK… fixed sparsity (number of active latents) k" |
| [72] Rajamanoharan (gated) | gate/magnitude split, $L_1$ on gate, solves shrinkage, ~half firing features | numeric-LB | correct | abstract: "solve shrinkage… half as many firing features" |
| [73] Rajamanoharan (JumpReLU) | thresholded jump; train $L_0$ via STE; no shrinkage above threshold | claim-LB | correct | abstract: "straight-through-estimators… directly train L0… avoiding… shrinkage" |
| [74] Meng (ROME) | causal tracing → mid-layer FFN; rank-one edit | claim-LB | correct | abstract: "middle-layer feed-forward modules… Rank-One Model Editing" |
| [75] Wang (IOI) | 26 heads / 7 classes; duplicate/induction/S-inhibition/name-mover; faithfulness/completeness/minimality; path patching | numeric-LB | correct | abstract: "26 attention heads grouped into 7 main classes… faithfulness, completeness and minimality" |
| [76] Belrose | logit lens biased; tuned lens = per-layer learned affine | claim-LB | correct | "train an affine probe for each block… refinement of the earlier logit lens" |
| [77] Conmy (ACDC) | automate circuit discovery by iterative edge pruning | claim-LB | correct | "iterative series of patching experiments… removing… components and connections" |
| [78] Geiger (DAS) | gradient-descent alignment; rotated (non-standard) basis; distributed | claim-LB | correct | "gradient descent rather than brute-force… rotated with a change-of-basis matrix… non-standard bases" |
| [79] Olsson | induction heads; ICL | claim-LB | correct | signature verified (induction head / in-context, 102 hits) |
| [80] Hanna | GPT-2 greater-than via final MLPs + attention circuit | claim-LB | correct | abstract: "final multi-layer perceptrons boost the probability of end years greater than the start year" |
| [81] Gould | successor heads increment ordinals (Monday→Tuesday); OV maps $n\to n+1$ | claim-LB | correct | abstract + Fig 1: "increment tokens with a natural ordering… WOV… maps it to its successor value" |
| [82] McDougall | copy-suppression: attend to over-predicted token, write against it; calibration; self-repair | claim-LB | correct | abstract: "If components… predict a certain token… the head suppresses it… improves… calibration" |
| [83] Li | emergent board-state world model; intervention steers predictions | claim-LB | correct | abstract: "emergent nonlinear internal representation… Interventional experiments… control the output" (fixed: not "linear") |
| [84] Nanda | board state linear in "mine vs. theirs" coordinates | claim-LB | correct | Fig 1: "encoded relative to the current player's colour (MINE vs. YOURS)" |
| [85] Jin & Rinard | LM on programs represents intermediate program state; interventional baseline | claim-LB | correct | abstract: "increasingly accurate representations of… intermediate grid world states… novel interventional baseline" |
| [86] Troshin | code models encode syntax/identifiers/namespaces; may fail semantic equivalence | claim-LB | correct | abstract verbatim: "syntactic structure, the notions of identifiers, and namespaces, but… fail… semantic equivalence" |
| [87] Wan | structural analysis; attention/hidden states carry AST/syntax motifs | decorative | correct | title + 109 hits (syntax tree/AST/attention); general structural-analysis attribution |
| [88] Turner | ActAdd: contrast-pair steering vector added at inference | claim-LB | correct | abstract: "contrasts… activations on prompt pairs… compute a steering vector… adding… during the forward pass" |
| [89] Zou | representation engineering; reading vectors (LAT) | claim-LB | correct | ToC/Fig 4: "Representation Reading… Linear Artificial Tomography (LAT)… reading vectors" |
| [90] Meng (MEMIT) | mass-edit thousands of memories | numeric-LB | correct | abstract: "scale up to thousands of associations for GPT-J (6B)" |
| [91] Bolukbasi | interpretability illusion: same direction, inconsistent meaning across datasets | claim-LB | correct | abstract + §: "testing hypotheses on multiple data sets"; neuron-221 cross-dataset example |
| [92] Jain | attention can be adversarially altered without changing the prediction | claim-LB | correct | Fig 1: "adversarially constructed… attention weights… same prediction" |
| [93] Wiegreffe | rebuttal: attention can be explanation under stricter tests | claim-LB | correct | abstract: "propose four alternative tests… when/whether attention can be used as explanation" |

## Phase 5 — impact audit

No `wrong-*` or `fabricated` rows in the final document, so no wrong citation propagated into a derivation. The two draft errors were both caught before delivery; neither was load-bearing on a *derivation* (all derivations in Appendix I are self-contained — interference, JL capacity, $L_1$ soft-threshold, ROME rank-one, MEMIT least-squares are proved inline; citations credit empirical findings, not derivation steps). The Li/Nanda fix corrected an attribution, not a result; the Cunningham fix removed an unsupported empirical aside, no equation depended on it.

## Conclusion

Appendix I passes the citation-integrity gate: every external citation is faithful at the bibliographic, locational, claim, and (where numeric) value layer, and every source is a strong `local:` in `download/`. No `bugs/` entry warranted (no wrong citation shipped; the two draft errors were caught by authoring-time verification and are recorded in field-notes).
