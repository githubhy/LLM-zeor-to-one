# Plan — EAP-IG edge-level attribution (close the node-vs-edge divergence)

**Date:** 2026-07-04 · **Status:** proposed (awaiting review) ·
**Todo:** `todos/2026-07-02-eap-ig-followups.md` · **Study:** `docs/eap-ig-faithfulness-implementation-study.md` §7 ·
**Source:** `download/hanna-eap-ig-faithfulness-2024.pdf` (+ `syed-eap-2023.pdf`) · **Engine:** `implementation/eap_ig/`

## 0. Goal

The `eap-ig-faithfulness` study ran at **node granularity + top-n** and its §7 root-causes the
divergence from Hanna Fig 3 into {granularity, search, operating-point}. Close it: build
**edge-level EAP/EAP-IG (q/k/v-split, 32,491-edge parity) + greedy search**, re-run IOI + SVA,
and check the per-task ordering flips to Hanna's — **IOI: EAP≈EAP-IG both plateau ~0.6**;
**SVA: EAP catastrophic (pruned to nothing at small n) while EAP-IG faithful** — or document why
GPT-2-small cannot.

## 1. The math (verified against the PDFs, §-cited)

**Edge EAP** (Hanna Eq 1, p.4): `score(u→v) = (z'_u − z_u) · ∇_{v_input} L`, gradient w.r.t. the
**input** of the downstream node `v`; `z_u` = clean output, `z'_u` = corrupt output (direction
corrupt−clean); `L = −M`.

**Edge EAP-IG** (Hanna Eq 3, p.4): `(z'_u − z_u) · (1/m) Σ_{k=1..m} ∂L/∂z_v` at `m` points on the
straight line from corrupt→clean **in input-embedding space**; activation-diff identical to EAP,
only the gradient integrated; `m=5`.

**The efficiency trick** (Syed App F, p.12): because `v`'s input is a *linear sum* of incoming
edges, `∂L/∂edge = ∂L/∂(v_input)` — **one backward pass gives the gradient for every edge into
`v`**. So per destination slot I need one residual-input gradient; the edge score for each
upstream `u` is `⟨z'_u − z_u, g_slot⟩` summed over positions.

**q/k/v split** (Syed App F; mandatory for the 32,491 count): 157 sources (embed + 144 heads +
12 MLPs) × 445 destination slots (144×3 q/k/v + 12 MLP + 1 logits), connected iff `u` writes
strictly before `v` reads (intra-layer: attn writes before same-layer MLP; heads of a layer are
parallel). `Σ = 31320 + 1014 + 157 = 32491` ✓ (without the ×3 split it is 11,611 — wrong).

**Greedy search** (Hanna App E, p.18): ADD edges backward from logits. `C_V={logits}, C_E={}`;
for `n` steps: eligible `= {e : e.child ∈ C_V, e ∉ C_E}`; pick `argmax |score|`; add edge +
parent. Fixed edge-budget grid `n ∈ {30,40,…,100,200,…,1000(,2000)}`; report the smallest circuit
with normalized faithfulness ≥ 0.85. Post-prune childless/parentless nodes. (Greedy > top-n
because it never orphans an edge from the output — the exact SVA failure.)

**Edge ablation** (Hanna §2, p.2): `input(v) = Σ_{e=(u,v)} [ i_e·z_u + (1−i_e)·z'_u ]` — per
incoming edge, clean current-pass output if in-circuit else corrupt-run output; **recursive**
(corruption propagates; `z_u` is the current partially-corrupted output, not pure-clean).
**Normalized faithfulness** `= (m − b')/(b − b')`, baselines from the study's per-task b/b'.

## 2. Architecture (what to add — new `edge*` module, node engine reused read-only where possible)

1. **`edges.py` — the 32,491-edge graph.** Enumerate sources, destination slots, and the
   causal connectivity; expose `edges()`, `upstream_of(slot)`, index maps. Assert count == 32491.
2. **`model.py` extension — `forward_grad_edges`** (or a new `edge_model.py`): one fwd+bwd (× m
   for IG) capturing, per destination slot, the **residual-input gradient**:
   - attn head `h`, slot `s∈{q,k,v}`: hook `∂L/∂(c_attn output)`, split to `∂L/∂s_h`, project
     back through the `W_s` head-slice → `g_{h.s}` (B,T,d). (c_attn is one Conv1D → q,k,v; the
     three slots share the residual read but differ by weight slice, so the three gradients
     differ — this is the crux.)
   - MLP `l`: gradient at the MLP input (c_fc pre-hook grad) → `g_{m l}`.
   - logits: gradient at `ln_f` input (final residual) → `g_logits`.
   Reuse the existing clean/corrupt node-output cache (`forward_cache`) for `z'_u − z_u`.
3. **`edge_attribution.py` — `score_edges(method ∈ {eap, eap_ig, random})`**: for each
   destination slot gradient `g`, score all causally-upstream `u` as `⟨Δz_u, g⟩`. Returns a
   dict keyed by edge id. (exact-patch at edge level is out of MVP — 32,491 patches is
   intractable; keep node-level exact as the anchor.)
4. **`edge_greedy.py`** — the App-E greedy builder + post-prune.
5. **`edge_faithfulness.py`** — recursive edge-ablation forward (reconstruct each destination's
   input from per-edge in/out choices) + normalized faithfulness. This is the highest-risk
   component; verified hardest (§4).

## 3. Verification (the correctness gates — this is where the risk is)

- **Edge count == 32,491** (and 11,611 without the split) — a structural unit test.
- **Edge→node consistency:** summing all edge scores into a destination node's slots should
  relate to the node-level score under the linear-sum identity; a 2-layer toy exact check.
- **m=1 EAP-IG == EAP** at edge level (as node-level, G1).
- **All-edges-in == clean, all-edges-out == corrupt** faithfulness (Hanna p.2 boundary) — exact.
- **Gradient-projection check:** the q/k/v residual-input gradients recompose to the total
  residual gradient (`Σ_s g_{h.s}·(read) == ∂L/∂residual through head h`) — a finite-difference
  or autograd cross-check on a tiny input.
- **Reproduce-the-ordering acceptance:** edge+greedy IOI shows EAP≈EAP-IG (~0.6 plateau); SVA
  shows EAP≪EAP-IG at small n (EAP pruned near-zero). The SVA smoking gun: EAP misses the
  `input→MLP0` edge (Hanna p.7) — assert EAP-IG ranks it high and EAP does not.
- **`sim-audit`** before sign-off (independent re-derivation of the edge score + the recursive
  ablation; this is exactly the error-prone class it guards).

## 4. MVP scope (recommended) vs deferred

**MVP (this pass):** edge graph + edge EAP/EAP-IG scorer + greedy + recursive edge-ablation
faithfulness + **IOI and SVA** re-run (the two Fig-3 anchors) + the verification gates + a report
(`docs/eap-ig-edge-level-study.md`, or a §-extension of the existing study) + `sim-audit`.

**Deferred → keep in `todos/2026-07-02-eap-ig-followups.md`** (out of MVP): the 3 omitted tasks
(Gender-Bias, Capital-Country, Hypernymy — need word-list generators); **EAP-IG-KL**;
**TransformerLens cross-check** (needs network/pip — likely unavailable offline);
**reduced-precision compute** (CUDA host); Greater-Than edge re-run (node-level already saturated).

## 5. Compute & risk

- **Compute:** edge scoring is one fwd+bwd (×5 for IG) per task — cheap (like the node study,
  which ran here on CPU). Greedy over ≤2000 edges × a faithfulness forward each is the cost;
  bounded and CPU-feasible. **No training.** MPS optional; CPU is the safe default (the node
  study's lesson).
- **Risk:** the recursive edge-ablation forward (§2.5) is the hard, error-prone core — a wrong
  input reconstruction silently corrupts every faithfulness number. Mitigated by the boundary
  checks (all-in==clean, all-out==corrupt) + the sim-audit. Estimate: a multi-hour build with
  heavy verification; the single biggest of the three queued items (1→2→3).

## 6. Deliverables

Edge module under `implementation/eap_ig/` (or `implementation/eap_ig_edge/`); G1 edge tests;
report closing the §7 divergence (or documenting the GPT-2-small limit); decision (MVP scope);
`sim-audit`; update `docs/eap-ig-faithfulness-implementation-study.md` §7 with the resolution;
update `todos/2026-07-02-eap-ig-followups.md` (edge+greedy closed, rest deferred). Commit.
