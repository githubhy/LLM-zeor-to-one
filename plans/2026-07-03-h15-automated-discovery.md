# Plan — H15 Automated Circuit Discovery (GPT-2-small induction)

**Filed:** 2026-07-03 · **Status:** executing (review gate waived per explicit user
"go end-to-end" instruction) · **Parent:** `docs/tiny-transformer-induction-study.md`
§11 (H15, DEFERRED), plan `plans/2026-06-30-tiny-transformer-induction-study.md:37,151`.

## Goal

Close **H15** ("automated discovery — ACDC/EAP/EAP-IG recover the manual §A.9
induction circuit, rank-consistent with the patching deltas") at the **GPT-2-small
rung**, now MPS-feasible. The toy rung deferred H15 because its distributed 4-head
circuit gives weak localization; GPT-2-small has sharply localized induction heads,
which is exactly where automated discovery can be validated.

## Design (one sentence)

Reuse the proven node-level EAP/EAP-IG attribution engine (`implementation/eap_ig/`,
read-only) to run automated circuit discovery on a **minimal-pair induction task**,
and test whether the discovered top heads recover the **known induction-head set** —
where "known" is a *computable* oracle (Olsson prefix-matching score per head), so no
citation-from-memory and no external download.

## Why this is honest about granularity

The engine scores **nodes (heads)**, not **edges**. So H15's pre-registered "recover
the §A.9 induction **K-edge**" is operationalized at node granularity as **induction-
*head* recovery**; the prev-token→induction *composition edge* is identified indirectly
(a companion previous-token-head score) and full **edge-level** K-composition recovery
is explicitly **deferred** (same node-vs-edge caveat the eap-ig study flags in its §7).

## Oracle (ground truth, computable — validated in smoke test)

- **Prefix-matching score** per head (Olsson 2022 App. "(3) Head activation evaluators",
  `download/olsson-induction-heads-2022.pdf`): repeated-random-token sequence; average
  attention from a token to the position following its previous occurrence.
- Smoke test (bf32, seed 0, L=50×2, batch 32) already reproduces the canonical cluster
  **5.5, 7.10, 6.9, 5.1, 7.2** (scores ~0.83–0.92) vs median 0.005 — 178× separation,
  and these are exactly the heads the parent study's Phase-4b named. Convergent validity.
- Companion **previous-token score** per head (attention i→i-1) for the feeder story.
- **Oracle induction-head set** = heads with mean prefix-match score ≥ **0.2** (pinned as
  a pre-registered threshold — decision `2026-07-03-01`; a >5σ outlier over the head median).

## Task (minimal-pair induction, single-token answers)

Random token block `s = [x_0..x_{L-1}]` (L=25, ids sampled excluding most/least common).
- **clean** = `s + s[:-1]`; last token `x_{L-2}`; induction answer `pos = x_{L-1}`.
- **corrupt** = same, but the first-copy follower `x_{L-1}` replaced by a foil `y`;
  induction answer becomes `neg = y`. Same shape, same query token — a minimal pair,
  directly analogous to IOI's one-token swap. Metric = `logit_diff(pos, neg)`.

## Methods & metrics

- Candidates (eap_ig registry): `random`, `eap`, `eap_ig` (m=5), `exact_patch` (ground-truth node effect).
- **Head recovery (headline):** Spearman ρ(method per-head |score|, oracle prefix-match),
  **AUROC**(method |score| vs oracle-binary), **recovery@k** (k = |oracle set|).
- **Rank-consistency with patching (pre-registered criterion):** Pearson/Spearman of
  method scores vs `exact_patch` (reproduces eap-ig's ρ=0.92 vs 0.46, on induction).
- **Faithfulness** curve over sizes (3,5,10,20,40,80,157); EAP-IG should dominate EAP.
- Seeds 0–4; bootstrap 95% CI on every cell (reuse `eap_ig.stats`); paired EAP-IG−EAP test.

## H15 verdict rubric (pre-registered)

- **PASS** iff EAP-IG (a) recovers the oracle induction-head set (AUROC ≥ 0.90) **and**
  (b) is rank-consistent with exact patching (Spearman ≥ 0.5) **and** (c) its faithfulness
  ≥ EAP's at the operating point (paired, significant). **INCONCLUSIVE** if head scores are
  indistinguishable from the random floor. **FAIL** otherwise.

## Deliverables

1. `implementation/induction_discovery/` — `oracle.py`, `task.py`, `discover.py`, `run.py`, `__init__.py` (imports `implementation.eap_ig` read-only).
2. `artifacts/induction-discovery/` — per-seed JSON + `scores.npz` + `study-manifest.json` + oracle head-set.
3. `tests/induction_discovery/test_core.py` — G1 gate (oracle recovers known heads; EAP-IG@m=1==EAP; faithfulness anchors 0/1; task minimal-pair invariant; determinism).
4. A figure (faithfulness-vs-size + head-recovery) with operating-conditions caption.
5. **Report:** standalone `docs/h15-automated-discovery-study.md` on the sim-report-completeness spine (decision `2026-07-03-01`), **and** update the parent report §6 H15 row (DEFERRED → resolved + pointer) and move the §11 item.
6. Verification: `sim-audit` + `citation-audit` + `check-report-completeness.py` before sign-off.

## Non-goals (deferred → todos)

Edge-level K-composition recovery; ACDC/AtP* (only EAP/EAP-IG here); the toy-rung H15;
Gemma-scale. File a `todos/` entry naming these at sign-off.
