"""Anatomy of the hand-built head: M and W_OV as one-hot matchers (Appendix A, A.9).

A structural schematic (no randomness) that draws Equation (9) literally, so a
reader can see WHY the two one-hot circuits implement prefix matching and copying.

Each position carries a residual feature that stacks two one-hot blocks:
    x_j = [ own(tok_j) | prev(tok_{j-1}) ]          (dim 2V)
drawn here as two vertical strips of V=6 vocab slots, with the active slot lit.

  * QK circuit  M = beta * sum_a e_own(a) e_prev(a)^T  connects the QUERY's OWN
    block to the KEY's PREV block.  The bilinear score x_i^T M x_j is large iff
    own(tok_i) == prev(tok_{j-1}), i.e. tok_i == tok_{j-1}: position j follows an
    earlier copy of the current token.  Shown for query i = trigger (own = C) and
    key j = 1 (prev = C): the blocks line up on 'C' -> match (green).

  * OV circuit  W_OV = gamma * sum_a e_logit(a) e_own(a)^T  reads the ATTENDED
    position's OWN block and writes it to the vocab-logit axis: it copies token A
    (the own block of the matched position) into the next-token logits.

Outputs:
  qkv-induction-anatomy.svg
  qkv-induction-anatomy.json
"""
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

HERE = pathlib.Path(__file__).resolve().parent

vocab = ["A", "B", "C", "D", "E", "F"]
V = len(vocab)
# query i = trigger 'C' with predecessor 'F'; key j = position 1, own 'A', prev 'C'.
query = {"pos": 6, "own": "C", "prev": "F"}
key = {"pos": 1, "own": "A", "prev": "C"}
matched_on = "C"            # own(query) == prev(key) == C  -> prefix match
copied_tok = key["own"]     # 'A' copied to the logits

data = {
    "vocab": vocab, "query": query, "key": key,
    "match_slot": matched_on, "copied_token": copied_tok,
    "M": "beta * sum_a e_own(a) e_prev(a)^T  (own[query] <-> prev[key])",
    "W_OV": "gamma * sum_a e_logit(a) e_own(a)^T  (own[attended] -> logit)",
    "rule": "score high iff own(tok_i) == prev(tok_{j-1}); copy own(attended).",
}
with open(HERE / "qkv-induction-anatomy.json", "w") as f:
    json.dump(data, f, indent=1)

# =============================== STYLE =====================================
BG    = "#fbfcfe"
INK   = "#1e293b"; MUTE = "#64748b"; FAINT = "#94a3b8"
QK_E  = "#6366f1"; QK_D = "#4338ca"        # indigo: own block / QK
PV_E  = "#f59e0b"; PV_D = "#b45309"        # amber: prev block
OV_E  = "#10b981"; OV_D = "#047857"        # emerald: OV / copy
HL    = "#16a34a"; HL_F = "#dcfce7"        # green: the match
OFF_E = "#cbd5e1"                          # unlit slot edge

SLOT = 0.46                                # vocab-slot height
W    = 0.92                                # slot width
OWN_TOP  = 7.0                             # centre of top (A) slot, own block
PREV_TOP = 3.85                            # centre of top (A) slot, prev block
QX, KX, OX = 2.3, 6.6, 11.5               # column x-centres: query, key, logits


def row_y(top, sym):
    return top - vocab.index(sym) * SLOT


def onehot(ax, cx, top, lit, ec, lit_fc, *, hl_slot=None):
    """Vertical one-hot strip A..F top-down; `lit` slot filled, `hl_slot` greened."""
    for r, sym in enumerate(vocab):
        cy = top - r * SLOT
        on = (sym == lit)
        is_hl = (sym == hl_slot) and on
        fc = (HL_F if is_hl else lit_fc) if on else "white"
        ed = HL if is_hl else (ec if on else OFF_E)
        ax.add_patch(Rectangle((cx - W / 2, cy - SLOT / 2), W, SLOT,
                     fc=fc, ec=ed, lw=2.0 if on else 0.9, zorder=4))
        ax.text(cx, cy, sym, ha="center", va="center",
                fontsize=10.5 if on else 8.6,
                color=(HL if is_hl else ec) if on else FAINT,
                fontweight="bold" if on else "normal", zorder=5)


def tag(ax, cx, y, text, color, *, fs=9, weight="bold"):
    ax.text(cx, y, text, ha="center", va="center", fontsize=fs,
            color=color, fontweight=weight, zorder=6)


def feature_col(ax, cx, own, prev, title, *, hl_own=None, hl_prev=None):
    tag(ax, cx, OWN_TOP + 0.62, title, INK, fs=9.5)
    tag(ax, cx, OWN_TOP + 0.31, "own", QK_D, fs=8.4)
    onehot(ax, cx, OWN_TOP, own, QK_E, "#eef0fe", hl_slot=hl_own)
    tag(ax, cx, PREV_TOP + 0.31, "prev", PV_D, fs=8.4)
    onehot(ax, cx, PREV_TOP, prev, PV_E, "#fef3c7", hl_slot=hl_prev)


def arrow(ax, p0, p1, *, color=INK, lw=1.8, rad=0.0, ls="-", mut=14, z=6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=mut,
                 lw=lw, color=color, linestyle=ls, shrinkA=3, shrinkB=3,
                 connectionstyle=f"arc3,rad={rad}", zorder=z))


def lbl(ax, x, y, s, *, color=MUTE, fs=8.6, ha="center", style="normal", weight="normal"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color,
            fontstyle=style, fontweight=weight, zorder=7)


# =============================== FIGURE ====================================
fig, ax = plt.subplots(figsize=(12.2, 6.2))
fig.patch.set_facecolor("white")
ax.set_facecolor(BG)
ax.set_xlim(0, 13.4); ax.set_ylim(0, 9.0); ax.axis("off")

ax.text(0.3, 8.62, r"Anatomy of the hand-built head: $M$ and $W_{OV}$ as one-hot matchers",
        fontsize=13.5, color=INK, fontweight="bold", ha="left")
ax.text(0.3, 8.18, r"Equation (9) drawn literally — the QK circuit matches "
        r"own$\leftrightarrow$prev; the OV circuit copies own$\rightarrow$logit",
        fontsize=9.3, color=MUTE, ha="left")

feature_col(ax, QX, query["own"], query["prev"],
            r"query $i$  (trigger, pos %d)" % query["pos"], hl_own=matched_on)
feature_col(ax, KX, key["own"], key["prev"],
            r"key $j$  (pos %d)" % key["pos"], hl_prev=matched_on, hl_own=copied_tok)

# --- M: own(query) -> prev(key), the prefix match on slot 'C' --------------
arrow(ax, (QX + 0.52, row_y(OWN_TOP, matched_on)),
      (KX - 0.52, row_y(PREV_TOP, matched_on)), color=HL, lw=2.4, rad=-0.18)
lbl(ax, 4.45, 6.45, r"$M=\beta\sum_a \mathbf{e}_{\mathrm{own}}(a)\,"
    r"\mathbf{e}_{\mathrm{prev}}(a)^{\top}$", color=QK_D, fs=9.4)
lbl(ax, 4.45, 6.02, r"score high $\Leftrightarrow$ own$(\mathrm{tok}_i)=$prev$(\mathrm{tok}_{j-1})$",
    color=HL, fs=8.4, weight="bold")
lbl(ax, 4.55, 2.55, r"both blocks lit on $\mathrm{C}$ $\Rightarrow$ prefix match",
    color=HL, fs=8.6, style="italic", weight="bold")

# --- softmax / attend node (consequence of the match) ----------------------
nx, ny = 9.05, row_y(PREV_TOP, matched_on)
ax.add_patch(FancyBboxPatch((nx - 0.95, ny - 0.45), 1.9, 0.9,
             boxstyle="round,pad=0.02,rounding_size=0.12",
             fc="white", ec=QK_E, lw=1.5, zorder=4))
tag(ax, nx, ny + 0.14, "softmax", INK, fs=9.5)
lbl(ax, nx, ny - 0.20, r"attend pos %d" % key["pos"], color=QK_D, fs=8.4)
arrow(ax, (KX + 0.52, ny), (nx - 0.95, ny), color=QK_E, lw=1.7)

# --- W_OV: own(attended) -> logit axis (copy 'A') --------------------------
tag(ax, OX, OWN_TOP + 0.31, "logits", OV_D, fs=8.4)
onehot(ax, OX, OWN_TOP, copied_tok, OV_E, "#e9f9f1", hl_slot=copied_tok)
arrow(ax, (KX + 0.52, row_y(OWN_TOP, key["own"])),
      (OX - 0.52, row_y(OWN_TOP, copied_tok)), color=OV_E, lw=2.2, rad=-0.22)
lbl(ax, 9.05, OWN_TOP + 1.00, r"$W_{OV}=\gamma\sum_a \mathbf{e}_{\mathrm{logit}}(a)\,"
    r"\mathbf{e}_{\mathrm{own}}(a)^{\top}$", color=OV_D, fs=9.2)
lbl(ax, 9.05, OWN_TOP + 0.60, r"copy own$(\mathrm{%s})\rightarrow$ logit" % copied_tok,
    color=OV_D, fs=8.4, weight="bold")

fig.savefig(HERE / "qkv-induction-anatomy.svg", bbox_inches="tight", facecolor="white")
print("wrote qkv-induction-anatomy.svg / .json")
print(f"  query own={query['own']} prev={query['prev']}; key own={key['own']} "
      f"prev={key['prev']}; match on {matched_on}; copy {copied_tok}")
