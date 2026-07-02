# Plan — Mechanistic-Interpretability Cluster Buildout for the LLMs-for-Coding Survey

- **Status:** executed 2026-07-01 — all 9 sections shipped; report `reports/2026-07-01-mi-appendix-buildout.md`
- **Date:** 2026-07-01
- **Owner survey:** `surveys/llms-for-coding/`
- **Tracks:** `todos/2026-07-01-mi-coverage-gaps.md`; gap analysis in `wikis/mechanistic-interpretability-coverage-gaps.md`
- **Flow owner:** `.claude/skills/deep-research-survey/SKILL.md` (Phase 3 acquire → Phase 4 author → Phase 5 audit/validate)

## 1. Goal

Add the missing mechanistic-interpretability (MI) material to the survey — the five gap clusters (A representational, B intervention, C circuits/heads, D code-specific, E payoff/epistemics) — authored **from first principles, math-rich, no intermediate step skipped, intuition-forward**, and **fully cited to acquired sources** under `.claude/rules/citation-integrity.md`. The result should read like the existing anatomy appendices (§A/§C): boxed results, derivations, "what it buys", "intuition".

## 2. Placement — a new Appendix I (+ minimal forward-links)

- **New file** `surveys/llms-for-coding/appendix-i-mechanistic-interpretability.md`, registered in `order.json` **after** `appendix-h-synthesis.md` and **before** `references.md`. Use `viewer/tools/init-doc.py` / `split-markdown.py` if the file crosses the split threshold (100 KB standard).
- **Why a new appendix, not inline into §A/§C:** the no-cascade discipline. Appending one new highest-lettered appendix shifts no existing section number, equation tag, or `secxref`. Extending §A/§C mid-file would cascade. New numbered equations live at the **end of Appendix I** and extend the tag sequence there (Appendix I has its own `eq:I-*` namespace).
- **Forward-links to add (small, in-place, non-cascading):** [§C.10] superposition line → I.2; [§A.22] induction/ablation → I.4 and I.6; [§A.9] induction head → I.6; the safety chapter → I.8. Each is a one-clause `secxref` insertion, batched at the end via `/cross-link` or by hand.

## 3. Section spec (I.1–I.9): derivation targets + sources

Each section: intro (one-line answer + ties to the existing model) → the core artifact (numbered equations) → term-by-term prose → "what it buys" → "intuition". Equation counts are estimates. **All sources are acquisition targets — fetch + read + verify before citing; no claim is written from memory.**

### I.1 — Two Levels of Interpretability: Circuit vs Feature (framing)
- Content: the weight-level circuit view the appendices already give vs the activation-level feature view; the linear-representation hypothesis stated. Ties [§A.2]/[§A.8]/[§C.10].
- Equations: ~1–2 (feature-as-direction decomposition of a residual vector). Sources: framing; leans on already-acquired + I.2 sources.

### I.2 — Superposition: More Features Than Dimensions (cluster A, P1)
- Derive: a feature as a stream direction; the interference cost of packing $m>d$ near-orthogonal features into $\mathbb{R}^d$; the sparsity condition under which superposition wins; the representation/drop **phase transition**; privileged vs non-privileged basis.
- Equations: ~6–9 (feature set + importance; reconstruction under a random/tied projection; interference term; capacity-vs-sparsity threshold; Johnson–Lindenstrauss near-orthogonality bound as the "how many fit" lemma).
- Sources: toy-models-of-superposition, a-mathematical-framework-for-transformer-circuits (both transformer-circuits.pub → likely `web` tag); derive the geometry inline (JL bound is a provable lemma, no citation needed).

### I.3 — From Polysemantic Neurons to Monosemantic Features: Sparse Autoencoders (cluster A, P1)
- Derive: the SAE as an over-complete dictionary; the reconstruction + sparsity objective; $L_1$ as a convex surrogate for $L_0$ and the shrinkage bias it induces; the **gated**, **top-$k$**, and **JumpReLU** fixes for that bias; evaluation (fraction of loss recovered, $L_0$, feature interpretability); dead features.
- Equations: ~8–12 (encoder/decoder; loss $\lVert x-\hat{x}\rVert^2 + \lambda\lVert f\rVert_1$; the $L_1$ shrinkage derivation; top-$k$ / JumpReLU forward + straight-through gradient; loss-recovered metric).
- Sources: sparse-autoencoders-find-interpretable-features (arXiv 2309.08600); scaling/evaluating-sparse-autoencoders / top-$k$ (arXiv 2406.04093); gated SAEs (arXiv 2404.16014); JumpReLU SAEs (arXiv 2407.14435); towards-/scaling-monosemanticity (transformer-circuits, `web`).

### I.4 — The Intervention Toolkit (cluster B, P2)
- Derive: ablation (mean/zero/resample) as a necessity test; **activation patching** / causal tracing (the clean-vs-corrupted run, the patched metric); **path patching** (edge-level attribution); **attribution patching** (the first-order Taylor approximation to patching, why it's cheap); **causal scrubbing** (the hypothesis-as-equivalence formulation); the **logit lens** and **tuned lens** (reading intermediate states through the unembedding, and the learned affine correction); DAS in one paragraph.
- Equations: ~6–9 (patched-metric definition; attribution-patching gradient approximation; logit-lens read; tuned-lens affine map).
- Sources: locating-and-editing-factual-associations / ROME (arXiv 2202.05262); interpretability-in-the-wild / IOI (arXiv 2211.00593); tuned-lens (arXiv 2303.08112); automated-circuit-discovery / ACDC (arXiv 2304.14997); causal-scrubbing + attribution-patching + logit-lens (`web`); DAS (arXiv).

### I.5 — A Discovered Circuit in a Real Model (cluster C, P2)
- Walk one reverse-engineered circuit end to end (IOI as the worked case): the task, the discovered heads (name-mover, S-inhibition, duplicate-token), the path-patching evidence, the minimality/faithfulness checks; then the greater-than and docstring circuits as shorter parallels; ACDC as the automation.
- Equations: ~2–4 (the circuit's logit contribution decomposition; the faithfulness metric). Sources: IOI (2211.00593); greater-than (arXiv 2305.00586); docstring (`web`); ACDC (2304.14997).

### I.6 — The Attention-Head Zoo (cluster C, P2)
- Catalog the empirical head families with the mechanism of each: previous-token, duplicate-token, induction ([§A.9]/[§A.22]), name-mover / negative-name-mover, copy-suppression, successor. Frame via the QK/OV circuit language already in §A.
- Equations: reuse §A's $M$/$W_{OV}$; ~1–2 new (successor as an ordinal OV map; copy-suppression as a negative OV eigenvalue). Sources: induction-heads (arXiv 2209.11895); successor-heads (arXiv 2312.09230); copy-suppression (arXiv 2310.04625); IOI (2211.00593).

### I.7 — What Code Models Represent (cluster D, P1)
- Derive/organize: the probing methodology (linear probe, the control/selectivity caveat); evidence for AST/syntactic structure, scope/binding, types; the **execution-state / world-model** result (a model trained on programs representing semantic state, not just surface form); code-specific circuits (bracket/indentation matching, variable tracking, repo-context copy as specialized induction).
- Equations: ~3–5 (linear probe + selectivity; a world-state-recoverability statement). Sources: emergent-world-representations / Othello (arXiv 2210.13382); emergent-linear-representations (arXiv 2309.00941); evidence-of-meaning-in-programs (arXiv 2305.11169); probing-pretrained-models-of-source-code (arXiv 2202.08975); structural-analysis-of-code-PLMs (arXiv 2202.06840).

### I.8 — The Payoff: Steering, Editing, Auditing (cluster E, P3)
- Derive: activation addition / steering vectors (add a feature direction at inference); representation engineering; weight editing (ROME rank-one update; MEMIT mass edit) from the key-value-memory view ([§A.6]/[§C.2]); MI → safety (auditing, backdoor/sleeper detection); automated interpretability (neuron explanations, attribution graphs).
- Equations: ~4–6 (steering add; ROME rank-one closed form; MEMIT multi-fact least squares). Sources: activation-addition (arXiv 2308.10248); representation-engineering (arXiv 2310.01405); MEMIT (arXiv 2210.07229); ROME (2202.05262); neuron-explanations + circuit-tracing (`web`).

### I.9 — Limits and Epistemics (cluster E, P3)
- Content: interpretability illusions (including the activation-patching illusion); ablation ≠ necessity; attention-weights-are-not-explanations and the rebuttal; faithfulness and how MI claims are evaluated; the streetlight caveat. Closes the appendix honestly.
- Equations: ~0–1. Sources: an-interpretability-illusion-for-BERT (arXiv 2104.07143); is-attention-interpretable / attention-is-not(-not)-explanation (arXiv 1902.10186, 1908.04626); activation-patching-illusion (arXiv); evaluate as prose.

## 4. Source acquisition (Phase 3)

- Use `.claude/skills/source-fetch/` (`oa_fetch.py "arxiv:ID" --download`) — keyless, arXiv-direct, as in the grokking pass. Resolve the interpreter via the py-launcher probe (Windows Store-stub trap).
- **This turn:** acquire the P1 arXiv set (I.2/I.3 SAE + I.7 code) up front so authoring is unblocked: 2309.08600, 2406.04093, 2404.16014, 2407.14435, 2210.13382, 2309.00941, 2305.11169, 2202.08975 (+ anchors 2211.00593 IOI, 2209.11895 induction).
- transformer-circuits.pub items (toy-models-of-superposition, monosemanticity, causal scrubbing, logit lens, neuron explanations, circuit tracing) are not on arXiv → acquire the page and tag `web`, or lean on the arXiv equivalents and **derive the math inline** (the superposition geometry and the SAE objective are both first-principles-derivable, so `web` sources credit the empirical finding, not the derivation — the §C.8 "derive-now, cite-the-finding" pattern).
- Add every acquired paper to `references.md` with a strong `local:` tag; verify each cited claim/number in-source (grep the extracted text) before it goes in.

## 5. Authoring discipline (non-negotiable)

- **Citation-integrity:** never write a citation or a concrete value from memory; every one traces to an acquired source read at authoring time. Derivations are self-contained; weak (`web`) citations credit findings, never carry a load-bearing value.
- **Math-authoring:** `eq:I-*` / `ref` / `sec:I.*` / `secref`/`secxref` / `para` markers; blank line after every `$$`; no inline-`$`-abutting-a-digit; `\lVert…\rVert` / `\mid` in tables; new equations appended at section end (no cascade).
- **First-principles + intuition:** each result derived step-by-step (the survey's "no step skipped" rule), each with an intuition paragraph and a "what it buys" block, tied back to the toy / GPT-2 / Llama models the appendices build.
- **Register:** practitioner/Staff, matching §A/§C.

## 6. Sequencing & gates

1. **P1 — I.2, I.3, I.7** (representational + code-specific): the highest-value, most-cited-arXiv clusters. Land these first.
2. **P2 — I.4, I.5, I.6** (intervention + discovered circuit + head zoo).
3. **P3 — I.1 framing polish, I.8, I.9** (payoff + epistemics + the framing intro).

After each cluster: run the renumber/link/validate sweep on the new file; after all clusters: `citation-audit` skill, `/cross-link` sign-off, `/check-survey llms-for-coding` (the delivery gate).

## 7. Cross-link & validation

- New appendix → gap detector will fire heavily by design; clear high-value gaps with `/cross-link` at sign-off (per `.claude/rules/cross-linking.md`).
- Add the forward-links of §2 (§C.10, §A.22, §A.9, safety chapter → Appendix I).
- Gate: `/check-survey llms-for-coding` green + `citation-audit` clean.

## 8. Acceptance (definition of done)

- Appendix I exists with I.1–I.9, every section first-principles + math-rich + intuition-forward, matching §A/§C register.
- Every external citation traces to an acquired `local:` (or explicitly-tagged `web`) source; no load-bearing claim rests on a weak source; `check-citation-sources` clean.
- Renumber/link/validate `--check` all clean; equations sequential in `eq:I-*`; forward-links landed; `/cross-link` gaps cleared or tracked; `/check-survey` green.
- `todos/2026-07-01-mi-coverage-gaps.md` closed (or its P-items checked off as clusters land).

## 9. Risks

- **Scale.** Nine sections, ~40–60 new equations, ~20 sources. Sequenced P1→P3; each cluster is independently shippable.
- **Web-only canonical sources.** Superposition/monosemanticity/causal-scrubbing are transformer-circuits.pub. Mitigation: derive the math inline (it is first-principles), cite arXiv equivalents for load-bearing values, tag the rest `web`.
- **Charter creep.** Keep it an *architecture-anchored* MI appendix (tie every method to the toy/GPT-2/Llama models), not a standalone interpretability survey.
- **Cascade risk.** Mitigated by the new-appendix placement + append-at-end equation discipline.
