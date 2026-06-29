"""The two-layer induction circuit: K-composition across depth (Appendix A, A.9).

A structural schematic (no randomness in the layout), with the attention weight
and prediction annotated from the SAME hand-built head as Figure A.7 so the
numbers are real, not illustrative.

The point the figure makes is what "one layer earlier" means in A.9: an induction
head is a TWO-LAYER circuit and cannot run in a single block.

  * Layer L-1  ·  previous-token head.  At each position j it attends to j-1 and
    writes the predecessor token tok_{j-1} into position j's residual stream --
    the "prev" block.  (This is the block the A.9 construction ASSUMES is already
    present in x_j.)
  * Residual stream.  After layer L-1 each position carries [ own(tok_j) |
    prev(tok_{j-1}) ].
  * Layer L  ·  induction head.  At the trigger (the 2nd 'C') it forms a query
    from its OWN token (C) and, via the QK circuit M, matches the key whose PREV
    block equals C -- that is position 1, whose predecessor is the FIRST 'C'.  It
    attends there and the OV circuit W_OV copies that position's OWN token (A)
    into the next-token logits.

The arrow from the prev block (written at L-1) into the induction head's key (read
at L) is the K-composition the caption names.

Deterministic.  Outputs:
  qkv-induction-two-layer.svg
  qkv-induction-two-layer.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = pathlib.Path(__file__).resolve().parent
np.seterr(divide="ignore", over="ignore", invalid="ignore")

# --------------------------------------------------------------------------
# The hand-built head (same construction as qkv-induction-head.py / Fig A.7),
# run here so the annotated weight and prediction are computed, not asserted.
# --------------------------------------------------------------------------
vocab = ["A", "B", "C", "D", "E", "F"]
V = len(vocab)
tokens = [2, 0, 3, 1, 4, 5, 2]          # C A D B E F C   (trigger = 2nd C at pos 6)
toks = [vocab[t] for t in tokens]
Tlen = len(tokens)
trigger_pos = 6
first_C = tokens.index(2)                # 0
answer_pos = first_C + 1                 # 1  -> 'A'
answer_tok = vocab[tokens[answer_pos]]

eye = np.eye(V)
def feature(j):
    own = eye[tokens[j]]
    prev = eye[tokens[j - 1]] if j > 0 else np.zeros(V)
    return np.concatenate([own, prev])
Xr = np.stack([feature(j) for j in range(Tlen)])
own_blk = np.concatenate([np.eye(V), np.zeros((V, V))], axis=1)
prev_blk = np.concatenate([np.zeros((V, V)), np.eye(V)], axis=1)
beta, gamma = 10.0, 4.0
M = beta * (own_blk.T @ prev_blk)
W_OV = gamma * (own_blk.T @ np.eye(V))
dk = V
scores = (Xr @ M @ Xr.T) / np.sqrt(dk)
mask = np.tril(np.ones((Tlen, Tlen), dtype=bool))
scores = np.where(mask, scores, -np.inf)
scores = scores - np.nanmax(scores, axis=1, keepdims=True)
A = np.exp(scores); A /= A.sum(axis=1, keepdims=True)
attn_row = A[trigger_pos]
logits = attn_row @ Xr @ W_OV
probs = np.exp(logits - logits.max()); probs /= probs.sum()
match_pos = int(attn_row.argmax())
match_w = float(attn_row.max())
pred_tok = vocab[int(probs.argmax())]
pred_p = float(probs.max())

data = {
    "vocab": vocab, "tokens": tokens, "token_str": toks,
    "trigger_pos": trigger_pos, "first_occurrence_pos": first_C,
    "matched_pos": match_pos, "match_weight": match_w,
    "predicted_tok": pred_tok, "predicted_prob": pred_p, "answer_tok": answer_tok,
    "beta": beta, "gamma": gamma,
    "circuits": {"M": "beta * sum_a e_own(a) e_prev(a)^T (QK)",
                 "W_OV": "gamma * sum_a e_logit(a) e_own(a)^T (OV)"},
    "note": "two-layer: prev block written by a previous-token head at layer L-1; "
            "induction head reads it at layer L (K-composition).",
}
with open(HERE / "qkv-induction-two-layer.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== STYLE =====================================
BG    = "#fbfcfe"
INK   = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
QK_F  = "#eef0fe"; QK_E = "#6366f1"; QK_D = "#4338ca"      # indigo: QK / match / own
OV_F  = "#e9f9f1"; OV_E = "#10b981"; OV_D = "#047857"      # emerald: OV / copy
PV_F  = "#fef3c7"; PV_E = "#f59e0b"; PV_D = "#b45309"      # amber: prev block / layer L-1
HL    = "#16a34a"                                          # green: the match / answer
DIM_E = "#cbd5e1"

xs = [2.3 + i * 1.95 for i in range(Tlen)]                 # position x-centres


def cell(ax, cx, cy, w, h, text, fc, ec, *, tc=INK, fs=12, lw=1.6, bold=True, shadow=False):
    box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                         boxstyle="round,pad=0.02,rounding_size=0.10",
                         fc=fc, ec=ec, lw=lw, zorder=4)
    if shadow:
        box.set_path_effects([pe.withSimplePatchShadow(offset=(2, -2),
                              shadow_rgbFace=FAINT, alpha=0.25)])
    ax.add_patch(box)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", zorder=5)


def arrow(ax, p0, p1, *, color=INK, lw=1.7, rad=0.0, ls="-", mut=14, z=3):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=mut,
                 lw=lw, color=color, linestyle=ls, shrinkA=3, shrinkB=3,
                 connectionstyle=f"arc3,rad={rad}", zorder=z))


def lbl(ax, x, y, s, *, color=MUTE, fs=8.4, ha="center", style="normal", weight="normal"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color,
            fontstyle=style, fontweight=weight, zorder=6)


def band(ax, y, h, fc, ec, label, lblc):
    ax.add_patch(FancyBboxPatch((0.5, y), 15.4, h,
                 boxstyle="round,pad=0.02,rounding_size=0.18",
                 fc=fc, ec=ec, lw=1.2, alpha=0.45, zorder=0))
    ax.text(0.85, y + h - 0.30, label, ha="left", va="top", fontsize=10,
            color=lblc, fontweight="bold", zorder=6)


# =============================== FIGURE ====================================
fig, ax = plt.subplots(figsize=(13.0, 7.6))
fig.patch.set_facecolor("white")
ax.set_facecolor(BG)
ax.set_xlim(0, 16.0); ax.set_ylim(0, 11.3); ax.axis("off")

ax.text(0.3, 10.95, "The two-layer induction circuit",
        fontsize=14, color=INK, fontweight="bold", ha="left")
ax.text(0.3, 10.52, r"an induction head is a composition across depth: a "
        r"previous-token head one layer below writes the key the induction head reads",
        fontsize=9.5, color=MUTE, ha="left")

y_emb, y_l1, y_stream, y_head, y_logit = 1.05, 2.5, 4.35, 7.4, 9.85

# --- background bands for the two layers ----------------------------------
band(ax, 1.95, 1.05, PV_F, PV_E, r"Layer $\ell-1$  ·  previous-token head", PV_D)
band(ax, 5.85, 2.55, QK_F, QK_E, r"Layer $\ell$  ·  induction head", QK_D)

# --- token embeddings (bottom) --------------------------------------------
lbl(ax, 0.85, y_emb, "tokens", color=INK, fs=8.6, ha="left", weight="bold")
for i, t in enumerate(toks):
    hl = i in (first_C, answer_pos, trigger_pos)
    cell(ax, xs[i], y_emb, 1.05, 0.74, f"{i}:{t}",
         "white", QK_E if hl else DIM_E, tc=QK_D if hl else MUTE, fs=11)

# --- layer L-1: previous-token head writes prev block ---------------------
# each position j copies token j-1 into its prev cell; highlight 0 -> 1.
for j in range(1, Tlen):
    strong = (j == answer_pos)
    arrow(ax, (xs[j - 1], y_emb + 0.40), (xs[j] - 0.05, y_stream - 0.62),
          color=PV_D if strong else PV_E, lw=2.1 if strong else 1.1,
          rad=-0.30, mut=12 if strong else 9, z=2 if strong else 1)
lbl(ax, 8.2, 3.32, r"attends $j\!\to\!j\!-\!1$, writes $\mathrm{tok}_{j-1}$ into the prev block",
    color=PV_D, fs=8.4, style="italic")

# --- residual stream: [ own | prev ] per position -------------------------
lbl(ax, 0.85, y_stream, "residual\nstream", color=INK, fs=8.4, ha="left", weight="bold")
for i in range(Tlen):
    own = toks[i]
    prev = toks[i - 1] if i > 0 else "·"
    hl_own = i in (answer_pos, trigger_pos)
    hl_prev = i == answer_pos
    cell(ax, xs[i], y_stream + 0.40, 1.05, 0.62, own,
         QK_F if hl_own else "white", QK_E if hl_own else DIM_E,
         tc=QK_D if hl_own else MUTE, fs=11, shadow=hl_own)
    cell(ax, xs[i], y_stream - 0.30, 1.05, 0.62, prev,
         "#dcfce7" if hl_prev else PV_F, HL if hl_prev else PV_E,
         tc=HL if hl_prev else PV_D, fs=11, shadow=hl_prev)
lbl(ax, xs[-1] + 0.95, y_stream + 0.40, "own", color=QK_D, fs=7.8, ha="left")
lbl(ax, xs[-1] + 0.95, y_stream - 0.30, "prev", color=PV_D, fs=7.8, ha="left")

# K-composition: the prev cell written at L-1 is the key read at L.
arrow(ax, (xs[answer_pos] - 0.55, y_stream - 0.30), (xs[answer_pos] - 1.15, y_stream + 1.7),
      color=HL, lw=1.8, rad=0.25, ls=(0, (4, 2)))
lbl(ax, xs[answer_pos] - 2.35, y_stream + 1.15,
    "K-composition:\nprev block (written\nat $\\ell-1$) is the key\nread at $\\ell$",
    color=HL, fs=7.8, ha="center", weight="bold")

# --- layer L: induction head box + the three operations -------------------
head_cx = 11.3
cell(ax, head_cx, y_head, 4.6, 1.5, "", QK_F, QK_E, lw=1.7)
ax.text(head_cx, y_head + 0.46, "induction head", ha="center", va="center",
        fontsize=11, color=QK_D, fontweight="bold", zorder=5)
ax.text(head_cx, y_head - 0.02, r"query $=$ own$(\mathrm{C})$;  match key whose prev $=\mathrm{C}$",
        ha="center", va="center", fontsize=8.6, color=INK, zorder=5)
ax.text(head_cx, y_head - 0.45, r"$M=\beta\sum_a \mathbf{e}_{\mathrm{own}}(a)\,"
        r"\mathbf{e}_{\mathrm{prev}}(a)^{\top}$",
        ha="center", va="center", fontsize=8.4, color=QK_D, zorder=5)

# (1) query: trigger own(C) -> head
arrow(ax, (xs[trigger_pos], y_stream + 0.71), (head_cx + 1.4, y_head - 0.75),
      color=QK_E, lw=1.8, rad=-0.15)
lbl(ax, 14.1, 6.0, r"query: own$(\mathrm{C})$", color=QK_D, fs=8.2, ha="center")

# (2) prefix match: head -> matched position's prev cell (the green key)
arrow(ax, (head_cx - 2.3, y_head - 0.55), (xs[answer_pos] + 0.10, y_stream + 1.0),
      color=HL, lw=2.1, rad=0.22)
lbl(ax, 6.4, 6.35, r"prefix match $\Rightarrow$ attend pos %d  ($a=%.2f$)" % (match_pos, match_w),
    color=HL, fs=8.4, ha="center", weight="bold")

# (3) copy: matched own(A) -> logits, via OV
arrow(ax, (xs[answer_pos], y_stream + 0.71), (xs[answer_pos], y_logit - 0.45),
      color=OV_E, lw=2.1, rad=0.0)
lbl(ax, 5.95, 8.95, r"copy own$(\mathrm{%s})$" % answer_tok,
    color=OV_D, fs=8.2, ha="center", weight="bold")
lbl(ax, 5.95, 8.55, r"$W_{OV}=\gamma\sum_a \mathbf{e}_{\mathrm{logit}}(a)\,"
    r"\mathbf{e}_{\mathrm{own}}(a)^{\top}$", color=OV_D, fs=7.6, ha="center")

# --- next-token logits / prediction (top) ---------------------------------
cell(ax, xs[answer_pos], y_logit, 2.6, 0.86,
     r"predict  $\mathrm{%s}$   ($p=%.2f$)" % (pred_tok, pred_p),
     OV_F, OV_E, tc=OV_D, fs=11, shadow=True)
lbl(ax, 0.85, y_logit, "next-token\nlogits", color=INK, fs=8.4, ha="left", weight="bold")

# --- "one layer earlier" depth bracket on the right ------------------------
ax.annotate("", xy=(15.6, 5.85), xytext=(15.6, 3.0),
            arrowprops=dict(arrowstyle="<->", color=FAINT, lw=1.4))
lbl(ax, 15.75, 4.45, "one layer\nearlier", color=MUTE, fs=8.0, ha="left", style="italic")

fig.savefig(HERE / "qkv-induction-two-layer.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-induction-two-layer.svg / .json")
print(f"  stream {toks}; trigger pos {trigger_pos} -> attends pos {match_pos} "
      f"(w={match_w:.3f}); predicts {pred_tok} (p={pred_p:.3f}); answer {answer_tok}")
