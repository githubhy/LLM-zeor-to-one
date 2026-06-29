"""Two layers stacked, traced through with numbers (Appendix A, A.20).

The minimal induction example: stream [A, B, A] -> predict B. A previous-token
head (layer 1) writes each position's predecessor into a *prev* block; the
induction head (layer 2) keys its own token against those prev blocks, attends to
the token that FOLLOWED the earlier copy of the current token, and copies it to
the logits. Every number is computed from the hand-built (M, W_OV) of A.9 Eq (9),
applied to this stream -- so the section's trace is real, not illustrative.

Three panels:
  (1) the residual stream after layer 1: [own | prev] one-hot blocks per position;
  (2) the layer-2 attention from the query (position 3, own = A);
  (3) the predicted next-token logits -> B.

Deterministic (no RNG). Outputs:
  qkv-two-layer-trace.svg
  qkv-two-layer-trace.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = pathlib.Path(__file__).resolve().parent

# =============================== THE COMPUTATION ===========================
vocab = ["A", "B"]
V = len(vocab)
stream = [0, 1, 0]                      # A B A
toks = [vocab[t] for t in stream]
T = len(stream)
beta, gamma = 4.0, 4.0
d_k = V                                  # rank of the bilinear comparison

def onehot(idx):
    e = np.zeros(V); e[idx] = 1.0; return e

own = [onehot(t) for t in stream]                      # own(tok_j)
prev = [np.zeros(V)] + [onehot(stream[j - 1]) for j in range(1, T)]  # prev(tok_{j-1}); pos1 has none

query = T - 1                            # position 3 (0-indexed 2): own = A
# layer-2 scores: s_ij = beta * (own(tok_i) . prev(tok_{j-1})), scaled by 1/sqrt(d_k)
raw = np.array([beta * float(own[query] @ prev[j]) for j in range(T)])
scaled = raw / np.sqrt(d_k)
# causal mask j <= query (all j here, query is last)
e = np.exp(scaled - scaled.max())
attn = e / e.sum()
# copy: logits ~ gamma * sum_j attn_j * own(tok_j)
logit_vec = gamma * sum(attn[j] * own[j] for j in range(T))
p_next = np.exp(logit_vec - logit_vec.max()); p_next = p_next / p_next.sum()
pred = vocab[int(np.argmax(p_next))]

data = {
    "stream": toks, "beta": beta, "gamma": gamma, "d_k": d_k,
    "own": [o.tolist() for o in own], "prev": [p.tolist() for p in prev],
    "query_pos": query + 1, "raw_scores": raw.tolist(),
    "scaled_scores": np.round(scaled, 4).tolist(),
    "attention": np.round(attn, 4).tolist(),
    "logits": np.round(logit_vec, 4).tolist(),
    "p_next": np.round(p_next, 4).tolist(), "prediction": pred,
}
with open(HERE / "qkv-two-layer-trace.json", "w") as f:
    json.dump(data, f, indent=1)
print("attn =", np.round(attn, 3), " logits =", np.round(logit_vec, 3),
      " p_next =", np.round(p_next, 3), " pred =", pred)

# =============================== STYLE =====================================
BG    = "#fbfcfe"
INK   = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
QK_E  = "#6366f1"; QK_D = "#4338ca"        # indigo: own / query
PV_E  = "#f59e0b"; PV_D = "#b45309"        # amber: prev
OV_E  = "#10b981"; OV_D = "#047857"        # emerald: copy / logits
HL    = "#16a34a"; HL_F = "#dcfce7"
OFF_E = "#cbd5e1"

SLOT = 0.5

def strip(ax, cx, top, lit_idx, ec, lit_fc, *, hl=None):
    for r in range(V):
        cy = top - r * SLOT
        on = (r == lit_idx)
        is_hl = (hl is not None and r == hl and on)
        fc = (HL_F if is_hl else lit_fc) if on else "white"
        ed = HL if is_hl else (ec if on else OFF_E)
        ax.add_patch(Rectangle((cx - 0.42, cy - SLOT / 2), 0.84, SLOT,
                     fc=fc, ec=ed, lw=2.0 if on else 0.9, zorder=4))
        ax.text(cx, cy, vocab[r], ha="center", va="center",
                fontsize=10 if on else 8,
                color=(HL if is_hl else ec) if on else FAINT,
                fontweight="bold" if on else "normal", zorder=5)

# =============================== FIGURE ====================================
fig = plt.figure(figsize=(12.6, 4.9))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(1, 3, width_ratios=[1.7, 1.05, 1.0], wspace=0.22)
ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1]); ax3 = fig.add_subplot(gs[0, 2])
for ax in (ax1, ax2, ax3):
    ax.set_facecolor(BG)

# ---- panel 1: residual stream after layer 1 -------------------------------
ax1.set_xlim(0, 6.2); ax1.set_ylim(0, 5.0); ax1.axis("off")
ax1.text(0.1, 4.72, "After layer 1 (previous-token head)",
         fontsize=11.2, color=INK, fontweight="bold", ha="left")
ax1.text(0.1, 4.36, r"each position carries [ own $\mid$ prev ];  stream $=$ A B A",
         fontsize=8.6, color=MUTE, ha="left")
own_top, prev_top = 3.4, 1.55
xs = [1.3, 3.0, 4.7]
match_idx = int(np.argmax(own[query]))      # A -> row 0; the matched slot
for j, cx in enumerate(xs):
    is_q = (j == query)
    ax1.text(cx, 4.0, f"pos {j+1}: {toks[j]}", ha="center", va="center",
             fontsize=8.8, color=(QK_D if is_q else INK),
             fontweight="bold" if is_q else "normal")
    lit_own = int(np.argmax(own[j]))
    lit_prev = int(np.argmax(prev[j])) if prev[j].any() else -1
    # highlight: the query's own slot, and the key whose prev matches it (pos 2)
    hl_own = match_idx if is_q else None
    hl_prev = match_idx if (prev[j].any() and lit_prev == match_idx) else None
    strip(ax1, cx, own_top, lit_own, QK_E, "#eef0fe", hl=hl_own)
    strip(ax1, cx, prev_top, lit_prev, PV_E, "#fef3c7", hl=hl_prev)
ax1.text(0.55, own_top - SLOT / 2, "own", ha="right", va="center",
         fontsize=8.4, color=QK_D, fontweight="bold")
ax1.text(0.55, prev_top - SLOT / 2, "prev", ha="right", va="center",
         fontsize=8.4, color=PV_D, fontweight="bold")
ax1.annotate("", xy=(xs[1] + 0.1, prev_top + SLOT * 0.55), xytext=(xs[query] - 0.1, own_top - SLOT * 0.55),
             arrowprops=dict(arrowstyle="-|>", color=HL, lw=2.0,
                             connectionstyle="arc3,rad=0.35"), zorder=6)
ax1.text(3.0, 0.42, "match:  query own A   =   key (pos 2) prev A",
         ha="center", va="center", fontsize=8.0, color=HL,
         fontweight="bold", fontstyle="italic")

# ---- panel 2: layer-2 attention from the query ----------------------------
ax2.set_xlim(0, 1.0); ax2.set_ylim(-0.6, T - 0.2); ax2.axis("off")
ax2.text(0.5, T - 0.32, "Layer-2 attention", fontsize=10.8,
         color=INK, fontweight="bold", ha="center")
ax2.text(0.5, T - 0.62, r"from query (pos 3, own = A)", fontsize=8.2,
         color=MUTE, ha="center")
for j in range(T):
    yy = T - 1 - j - 0.5
    w = attn[j]
    top = (j == int(np.argmax(attn)))
    ax2.add_patch(Rectangle((0.0, yy - 0.18), max(w, 0.001), 0.36,
                  fc=(QK_E if top else "#c7d2fe"), ec=QK_D, lw=1.0, zorder=3))
    ax2.text(-0.03, yy, f"$j={j+1}$", ha="right", va="center", fontsize=8.2, color=MUTE)
    ax2.text(min(w + 0.03, 0.86), yy, f"{w:.2f}", ha="left", va="center",
             fontsize=8.6, color=INK, fontweight="bold" if top else "normal")
ax2.text(0.5, -0.5, "attends the token after\nthe earlier A  (pos 2 = B)",
         ha="center", va="center", fontsize=7.6, color=MUTE, fontstyle="italic")

# ---- panel 3: predicted next-token logits ---------------------------------
ax3.set_xlim(-0.7, V - 0.3); ax3.set_ylim(0, 1.42); ax3.axis("off")
ax3.text((V - 1) / 2.0, 1.36, "Predicted next token", fontsize=10.8,
         color=INK, fontweight="bold", ha="center")
ax3.text((V - 1) / 2.0, 1.20, "OV copies own(pos 2) = B", fontsize=8.2,
         color=OV_D, ha="center")
for a in range(V):
    p = p_next[a]
    top = (a == int(np.argmax(p_next)))
    ax3.add_patch(Rectangle((a - 0.32, 0.0), 0.64, p,
                  fc=(OV_E if top else "#cbd5e1"), ec=OV_D if top else "#94a3b8",
                  lw=1.2, zorder=3))
    ax3.text(a, p + 0.04, f"{p:.2f}", ha="center", va="bottom",
             fontsize=9.2, color=INK, fontweight="bold" if top else "normal")
    ax3.text(a, -0.07, vocab[a], ha="center", va="center",
             fontsize=10, color=(OV_D if top else MUTE), fontweight="bold")

fig.suptitle(r"Two layers stacked: induction on  A B A $\rightarrow$ B   "
             r"($\beta=4$, $\gamma=4$; hand-built, no training)",
             fontsize=12.4, color=INK, fontweight="bold", y=1.02, x=0.5)
fig.savefig(HERE / "qkv-two-layer-trace.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-two-layer-trace.svg / .json")
