"""Why the KV cache makes generation O(T), not O(T^2) (§3.5 / §3.5.1).

Two panels, deterministic. The figure illustrates the MECHANISM behind the
O(T^2) -> O(T) collapse (Figure 3.5's right panel shows the cost magnitude; this
shows where the quadratic comes from and why caching is lossless).

(left, SCHEMATIC) The work tableau. Rows are sequence positions p, columns are
decode steps s; a cell (p, s) with p <= s is "touched" at step s. WITHOUT a
cache, step s reprocesses the whole length-s prefix, so every cell in the
lower-triangular region is (re)computed — the green diagonal PLUS the grey
sub-diagonal — and the total is the triangle's area, sum_{s=1}^T s = T(T+1)/2 =
O(T^2). WITH a KV cache, the grey cells are read from the cache (the past keys
and values, already computed) and only the green diagonal — one new block pass
per step — is computed, for a total of T = O(T). The grey region is exactly the
redundant recomputation the cache removes.

(right, COMPUTED) Causal invariance — why the grey cells may be reused. Through a
2-layer causal self-attention stack (fixed random weights), the layer-2 key
vector at position j is computed for a length-6 prefix and again inside a length-7
sequence (same first 6 tokens + 1 appended). Because the causal mask lets
position j attend only to positions <= j, appending token 7 cannot change any
key at j <= 6: the recomputed prefix keys are bit-identical to the cached ones
(max ||Delta K_j|| = 0, exactly). The paired bars (||K_j|| under each sequence
length) coincide on the shared prefix; only position 7 is new. Caching is
therefore lossless, not an approximation.

CAVEAT (kept faithful to §3.5): the per-token attention SCAN over the cached keys
is O(t) with or without the cache; the cache removes the prefix RECOMPUTATION
(the projection/FFN work the block-pass count tracks), which is the O(T^2) term.

Outputs:
  kv-cache-mechanism.svg
  kv-cache-mechanism.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

HERE = pathlib.Path(__file__).resolve().parent
np.seterr(divide="ignore", over="ignore", invalid="ignore")

# ---------------------------------------------------------------------------
# Panel A data: the work tableau counts (schematic, exact arithmetic).
# ---------------------------------------------------------------------------
Tg = 8
M = np.zeros((Tg, Tg))                 # M[p, s]: 0 empty, 1 prefix (grey), 2 new (green)
for s in range(Tg):
    for p in range(Tg):
        if p < s:
            M[p, s] = 1
        elif p == s:
            M[p, s] = 2
tri = Tg * (Tg + 1) // 2               # 36 = no-cache total block-passes
diag = Tg                              # 8  = cache total block-passes

# ---------------------------------------------------------------------------
# Panel B data: causal invariance through a 2-layer causal self-attention stack.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(0)
d, dk, T2 = 16, 8, 7
X = rng.standard_normal((T2, d)) * 0.5
WQ1 = rng.standard_normal((d, dk)); WK1 = rng.standard_normal((d, dk))
WV1 = rng.standard_normal((d, dk)); WO1 = rng.standard_normal((dk, d))
WK2 = rng.standard_normal((d, dk))


def layer2_keys(Xin):
    """Layer-2 keys after one causal self-attention layer (residual) — the K a
    cache would store. Causal mask ⇒ position j depends only on tokens ≤ j."""
    n = Xin.shape[0]
    Q1, K1, V1 = Xin @ WQ1, Xin @ WK1, Xin @ WV1
    S = (Q1 @ K1.T) / np.sqrt(dk)
    mask = np.tril(np.ones((n, n), dtype=bool))
    S = np.where(mask, S, -np.inf)
    S = S - S.max(axis=1, keepdims=True)
    A = np.where(mask, np.exp(S), 0.0)
    A = A / A.sum(axis=1, keepdims=True)
    H1 = Xin + (A @ V1) @ WO1
    return H1 @ WK2


K2_6 = layer2_keys(X[:6])
K2_7 = layer2_keys(X[:7])
delta = np.linalg.norm(K2_7[:6] - K2_6, axis=1)        # per-position change, prefix
max_delta = float(delta.max())                          # = 0.0 exactly
norms6 = np.linalg.norm(K2_6, axis=1)
norms7 = np.linalg.norm(K2_7, axis=1)

data = {
    "panel_a": {"T": Tg, "no_cache_blockpasses": tri, "cache_blockpasses": diag,
                "no_cache_formula": "T(T+1)/2", "cache_formula": "T"},
    "panel_b": {"layers": 2, "d": d, "d_k": dk,
                "prefix_len": 6, "appended_len": 7,
                "max_prefix_key_change": max_delta,
                "key_norms_len6": [round(float(x), 3) for x in norms6],
                "key_norms_len7": [round(float(x), 3) for x in norms7]},
}
with open(HERE / "kv-cache-mechanism.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== FIGURE ====================================
GREY, GREEN, NEW_C, OLD_C, EDGE = "#d1d5db", "#16a34a", "#16a34a", "#9ca3af", "#374151"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 5.0))

# ---- Panel A: the work tableau --------------------------------------------
cmap = ListedColormap(["white", GREY, GREEN])
ax1.imshow(M, cmap=cmap, origin="lower", vmin=0, vmax=2, aspect="equal")
ax1.set_xticks(np.arange(-0.5, Tg, 1), minor=True)
ax1.set_yticks(np.arange(-0.5, Tg, 1), minor=True)
ax1.grid(which="minor", color="white", lw=2)
ax1.tick_params(which="minor", length=0)
ax1.set_xticks(range(Tg)); ax1.set_xticklabels(range(1, Tg + 1), fontsize=8)
ax1.set_yticks(range(Tg)); ax1.set_yticklabels(range(1, Tg + 1), fontsize=8)
ax1.set_xlabel(r"decode step  $s$", fontsize=9)
ax1.set_ylabel(r"sequence position  $p$", fontsize=9)
ax1.set_title(r"Where $O(T^2)$ comes from: the recomputed prefix", fontsize=10.0)
ax1.legend(handles=[
    Patch(facecolor=GREEN, edgecolor=EDGE, label="computed this step (1 block-pass)"),
    Patch(facecolor=GREY, edgecolor=EDGE, label="prefix: cached & reused (KV) /\nrecomputed every step (no cache)"),
], loc="upper left", fontsize=7.0, framealpha=0.95)
ax1.text(0.5, -2.15,
         rf"no cache: green $+$ grey $= \sum_{{s=1}}^{{T}} s = T(T{{+}}1)/2 = {tri}$  block-passes" "\n"
         rf"KV cache: green only $= T = {diag}$  ($T={Tg}$ shown)",
         transform=ax1.get_xaxis_transform(), ha="left", va="top", fontsize=7.8, color=EDGE)

# ---- Panel B: causal invariance (computed) --------------------------------
pos = np.arange(1, T2 + 1)
w = 0.4
ax2.bar(pos[:6] - w / 2, norms6, width=w, color=OLD_C, edgecolor=EDGE, lw=0.5,
        label="recompute prefix alone (length 6)")
ax2.bar(pos - w / 2 + w, norms7, width=w, color=NEW_C, alpha=0.85, edgecolor=EDGE, lw=0.5,
        label="inside the length-7 sequence")
ax2.scatter(pos[:6], norms6, marker="_", s=140, color=EDGE, zorder=5,
            label=r"prefix keys coincide: $\max_j\,\|\Delta K_j\| = 0$ (exact)")
# mark position 7 as the only new key
ax2.annotate("only position 7\nis newly computed", (7, norms7[6]),
             xytext=(5.1, norms7[6] + 0.6), fontsize=7.2, color=GREEN,
             arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.0))
ax2.set_xticks(pos); ax2.set_xticklabels(pos, fontsize=8)
ax2.set_xlabel(r"key position  $j$", fontsize=9)
ax2.set_ylabel(r"layer-2 key norm  $\| K_j\|$", fontsize=9)
ax2.set_title(r"Causal invariance: appending a token freezes the past keys", fontsize=10.0)
ax2.grid(True, axis="y", alpha=0.25)
ax2.legend(fontsize=6.9, loc="upper right", framealpha=0.95)
ax2.text(0.02, -0.20,
         "causal mask $\\Rightarrow$ key $j$ depends only on tokens $\\leq j$, so the cached prefix keys are\n"
         "bit-identical to a recompute — caching is lossless, not an approximation.",
         transform=ax2.transAxes, ha="left", va="top", fontsize=7.2, color=EDGE)

fig.subplots_adjust(left=0.06, right=0.98, top=0.92, bottom=0.20, wspace=0.24)
fig.savefig(HERE / "kv-cache-mechanism.svg", bbox_inches="tight")
print("wrote kv-cache-mechanism.svg / .json")
print(f"  Panel A: no-cache {tri} block-passes (T(T+1)/2), cache {diag} (T), T={Tg}")
print(f"  Panel B: max prefix key change = {max_delta:.3e}  (should be 0.0)")
