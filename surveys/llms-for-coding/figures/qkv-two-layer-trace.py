"""Two layers stacked, traced through with numbers (Appendix A, A.20).

The minimal induction example: stream [A, B, A] -> predict B, presented in the
SAME column convention and explicit-matrix style as A.19 (tokens are columns;
d = 2V = 4, head dim d_k = V = 2, T = 3). A previous-token head (layer 1) writes
each position's predecessor into a *prev* block; the induction head (layer 2)
scores own-against-prev through the QK circuit M of Eq (9), attends, and copies
via the OV circuit W_OV. Every number is computed, not illustrative.

Three panels (parallel to Figure A.12):
  (1) the residual stream after layer 1, X^(2) in R^{d x T}: [own | prev] blocks;
  (2) the full causal attention matrix A = softmax(mask((X^(2))^T M X^(2)/sqrt(d_k)));
  (3) the predicted next-token logits at the induction query (pos 3) -> B.

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
from matplotlib.patches import Rectangle

HERE = pathlib.Path(__file__).resolve().parent

# =============================== THE COMPUTATION ===========================
# basis order: [own_A, own_B, prev_A, prev_B];  V=2, d=2V=4, d_k=V=2, T=3, stream A B A
vocab = ["A", "B"]
V = len(vocab)
d, d_k, T = 2 * V, V, 3
beta, gamma = 4.0, 4.0
toks = ["A", "B", "A"]
# residual stream AFTER layer 1 (previous-token head): columns = positions
X2 = np.array([[1, 0, 1],     # own_A
               [0, 1, 0],     # own_B
               [0, 1, 0],     # prev_A
               [0, 0, 1]], dtype=float)   # prev_B  -> p1=[1,0,0,0], p2=[0,1,1,0], p3=[1,0,0,1]
# induction QK circuit M = beta * sum_a e_own(a) e_prev(a)^T  (own rows 0,1 -> prev cols 2,3)
M = beta * np.array([[0, 0, 1, 0],
                     [0, 0, 0, 1],
                     [0, 0, 0, 0],
                     [0, 0, 0, 0]], dtype=float)
# OV circuit W_OV = gamma * sum_a e_logit(a) e_own(a)^T  (logit rows -> own cols 0,1)
W_OV = gamma * np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0]], dtype=float)      # 2x4 -> logits [A,B]

S = (X2.T @ M @ X2) / np.sqrt(d_k)                        # T x T, S_ij = x_i^T M x_j / sqrt(d_k)
mask = np.triu(np.ones((T, T), dtype=bool), k=1)
Sm = np.where(mask, -np.inf, S)
A = np.exp(Sm - np.nanmax(Sm, axis=1, keepdims=True))
A = np.where(mask, 0.0, A)
A = A / A.sum(axis=1, keepdims=True)                      # T x T causal attention
O_feat = X2 @ A.T                                         # d x T, column i = attention-weighted residual
logits = W_OV @ O_feat                                    # 2 x T, columns = per-query logits
P = np.exp(logits - logits.max(axis=0)); P = P / P.sum(axis=0)
q = T - 1                                                 # induction query = position 3
pred = vocab[int(np.argmax(P[:, q]))]

data = {
    "convention": "A.1 column form; d=2V=4, d_k=V=2, T=3, stream A B A.",
    "X2": X2.tolist(), "M": M.tolist(), "W_OV": W_OV.tolist(),
    "S_scaled": np.round(S, 4).tolist(), "A": np.round(A, 4).tolist(),
    "logits_query3": np.round(logits[:, q], 4).tolist(),
    "p_query3": np.round(P[:, q], 4).tolist(), "prediction": pred,
    "beta": beta, "gamma": gamma,
}
with open(HERE / "qkv-two-layer-trace.json", "w") as f:
    json.dump(data, f, indent=1)
print("A=\n", np.round(A, 3), "\nlogits(pos3)=", np.round(logits[:, q], 3),
      " p=", np.round(P[:, q], 3), " pred=", pred)

# =============================== STYLE =====================================
BG   = "#fbfcfe"
INK  = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
QK_E = "#6366f1"; QK_D = "#4338ca"        # indigo: own / query
PV_E = "#f59e0b"; PV_D = "#b45309"        # amber: prev
OV_E = "#10b981"; OV_D = "#047857"        # emerald: copy / logits
HL   = "#16a34a"; HL_F = "#dcfce7"
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
fig = plt.figure(figsize=(12.8, 4.9))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 1.25, 1.0], wspace=0.26)
ax1 = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1]); ax3 = fig.add_subplot(gs[0, 2])
for ax in (ax1, ax2, ax3):
    ax.set_facecolor(BG)

# ---- panel 1: residual stream after layer 1, X^(2) ------------------------
ax1.set_xlim(0, 6.2); ax1.set_ylim(0, 5.0); ax1.axis("off")
ax1.text(0.1, 4.72, r"$X^{(2)}$: residual after layer 1", fontsize=11.0,
         color=INK, fontweight="bold", ha="left")
ax1.text(0.1, 4.36, r"columns = positions; rows = [ own $\mid$ prev ]; stream A B A",
         fontsize=8.4, color=MUTE, ha="left")
own_top, prev_top = 3.4, 1.55
xs = [1.3, 3.0, 4.7]
own = [0, 1, 0]; prev = [-1, 0, 1]            # own/prev row indices per position (-1 = none)
for j, cx in enumerate(xs):
    is_q = (j == q)
    ax1.text(cx, 4.0, f"pos {j+1}: {toks[j]}", ha="center", va="center",
             fontsize=8.8, color=(QK_D if is_q else INK),
             fontweight="bold" if is_q else "normal")
    hl_own = own[j] if is_q else None
    hl_prev = prev[j] if (prev[j] >= 0 and prev[j] == own[q]) else None
    strip(ax1, cx, own_top, own[j], QK_E, "#eef0fe", hl=hl_own)
    strip(ax1, cx, prev_top, prev[j], PV_E, "#fef3c7", hl=hl_prev)
ax1.text(0.55, own_top - SLOT / 2, "own", ha="right", va="center",
         fontsize=8.4, color=QK_D, fontweight="bold")
ax1.text(0.55, prev_top - SLOT / 2, "prev", ha="right", va="center",
         fontsize=8.4, color=PV_D, fontweight="bold")
ax1.annotate("", xy=(xs[1] + 0.1, prev_top + SLOT * 0.55),
             xytext=(xs[q] - 0.1, own_top - SLOT * 0.55),
             arrowprops=dict(arrowstyle="-|>", color=HL, lw=2.0,
                             connectionstyle="arc3,rad=0.35"), zorder=6)
ax1.text(3.0, 0.42, "match:  query own A   =   key (pos 2) prev A",
         ha="center", va="center", fontsize=8.0, color=HL,
         fontweight="bold", fontstyle="italic")

# ---- panel 2: full causal attention matrix A ------------------------------
ax2.set_xlim(-0.8, T + 0.1); ax2.set_ylim(-1.0, T + 0.8); ax2.axis("off")
ax2.text((T - 1) / 2.0, T + 0.5, r"causal attention $A$ (layer 2)",
         fontsize=10.8, color=INK, fontweight="bold", ha="center")
ax2.text((T - 1) / 2.0, T + 0.1, r"$A=\mathrm{softmax}\;\mathrm{mask}((X^{(2)})^{\top} M X^{(2)}/\sqrt{d_k})$",
         fontsize=8.2, color=MUTE, ha="center")
for i in range(T):
    yy = T - 1 - i
    for j in range(T):
        masked = j > i
        val = A[i, j]
        is_ind = (i == q and j == int(np.argmax(A[q])))
        fc = "#f1f5f9" if masked else (HL_F if is_ind else plt.cm.Blues(0.16 + 0.7 * val))
        ec = HL if is_ind else "#cbd5e1"
        ax2.add_patch(Rectangle((j - 0.5, yy - 0.5), 1, 1, fc=fc, ec=ec,
                      lw=2.0 if is_ind else 1.0, zorder=2))
        if masked:
            ax2.text(j, yy, "·", ha="center", va="center", fontsize=12, color=FAINT, zorder=3)
        else:
            ax2.text(j, yy, f"{val:.2f}", ha="center", va="center", fontsize=9.2,
                     color=(HL if is_ind else (INK if val < 0.6 else "white")),
                     fontweight="bold" if (is_ind or val >= 0.6) else "normal", zorder=3)
    lbl = f"$i={i+1}$" + ("  (query)" if i == q else "")
    ax2.text(-0.62, yy, lbl, ha="right", va="center", fontsize=8.0,
             color=(QK_D if i == q else MUTE), fontweight="bold" if i == q else "normal")
for j in range(T):
    ax2.text(j, -0.66, f"$j={j+1}$", ha="center", va="center", fontsize=8.0, color=MUTE)
ax2.text((T - 1) / 2.0, -1.0, "row 3 is the induction query: it attends pos 2",
         fontsize=7.4, color=FAINT, ha="center", fontstyle="italic")

# ---- panel 3: predicted next-token logits at the query --------------------
ax3.set_xlim(-0.7, V - 0.3); ax3.set_ylim(0, 1.42); ax3.axis("off")
ax3.text((V - 1) / 2.0, 1.36, "Predicted next token", fontsize=10.6,
         color=INK, fontweight="bold", ha="center")
ax3.text((V - 1) / 2.0, 1.20, "OV copies own(pos 2) = B", fontsize=8.0,
         color=OV_D, ha="center")
for a in range(V):
    p = P[a, q]
    top = (a == int(np.argmax(P[:, q])))
    ax3.add_patch(Rectangle((a - 0.32, 0.0), 0.64, p,
                  fc=(OV_E if top else "#cbd5e1"), ec=OV_D if top else "#94a3b8",
                  lw=1.2, zorder=3))
    ax3.text(a, p + 0.04, f"{p:.2f}", ha="center", va="bottom",
             fontsize=9.2, color=INK, fontweight="bold" if top else "normal")
    ax3.text(a, -0.07, vocab[a], ha="center", va="center",
             fontsize=10, color=(OV_D if top else MUTE), fontweight="bold")

fig.suptitle(r"Two layers stacked: induction on  A B A $\rightarrow$ B   "
             r"(column convention; $d=2|\mathcal{V}|=4$, $d_k=2$, $T=3$; $\beta=4$, $\gamma=4$; hand-built)",
             fontsize=11.8, color=INK, fontweight="bold", y=1.03, x=0.5)
fig.savefig(HERE / "qkv-two-layer-trace.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-two-layer-trace.svg / .json")
