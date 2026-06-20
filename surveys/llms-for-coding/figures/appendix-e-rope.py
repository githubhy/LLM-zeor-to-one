"""Figure E.2 — RoPE: rotation by position, and why the score is relative.

Left: a query/key 2-D sub-pair rotated by position; the angle is p*theta. Right:
the attention score <R_m q, R_n k> as a function of the offset (m-n) only — three
curves at different (m,n) but equal offset coincide exactly, the relative-position
property. Computed with the same rope() used in the validation engine, so the
right panel IS the numerical proof of the identity (spread ~1e-15).

RoPE: Su et al. (RoFormer) [66]; used per-layer in Llama [65, Sec 2.2].

Output: appendix-e-rope.svg / .json
"""
import json
import pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
Q_C, K_C, ACC = "#2563eb", "#dc2626", "#16a34a"
EDGE = "#374151"


def rope(x, pos, base=10000.0):
    d = x.shape[-1]
    j = np.arange(d // 2)
    theta = base ** (-2.0 * j / d)
    ang = pos * theta
    c, s = np.cos(ang), np.sin(ang)
    xe, xo = x[..., 0::2], x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = xe * c - xo * s
    out[..., 1::2] = xe * s + xo * c
    return out


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.7))

# --- left: a single 2-D pair rotated by position ---
q2 = np.array([1.0, 0.35]); k2 = np.array([0.55, 0.95])
ax1.set_aspect("equal"); ax1.set_xlim(-1.3, 1.4); ax1.set_ylim(-1.3, 1.4)
ax1.axhline(0, color="#cbd5e1", lw=0.8); ax1.axvline(0, color="#cbd5e1", lw=0.8)
theta0 = 0.6   # one frequency, for illustration
for p, alpha in [(0, 1.0), (1, 0.6), (2, 0.32)]:
    rq = np.array([q2[0] * np.cos(p * theta0) - q2[1] * np.sin(p * theta0),
                   q2[0] * np.sin(p * theta0) + q2[1] * np.cos(p * theta0)])
    ax1.annotate("", xy=rq, xytext=(0, 0),
                 arrowprops=dict(arrowstyle="-|>", color=Q_C, lw=2.0, alpha=alpha,
                                 mutation_scale=14))
    ax1.text(rq[0] * 1.12, rq[1] * 1.12, f"$\\mathbf{{q}}$@{p}", color=Q_C,
             fontsize=8.2, alpha=max(alpha, 0.5), ha="center")
ax1.annotate("", xy=k2, xytext=(0, 0),
             arrowprops=dict(arrowstyle="-|>", color=K_C, lw=2.0, mutation_scale=14))
ax1.text(k2[0] * 1.12, k2[1] * 1.15, "$\\mathbf{k}$@0", color=K_C, fontsize=8.2)
ax1.set_title("A 2-D (Q,K) pair is rotated by angle $p\\,\\theta$ at position $p$",
              fontsize=9.4)
ax1.set_xlabel("dim $2j$", fontsize=8.5); ax1.set_ylabel("dim $2j{+}1$", fontsize=8.5)

# --- right: score depends only on the offset (m-n) ---
rng = np.random.default_rng(1)
dh = 32
q = rng.standard_normal(dh); k = rng.standard_normal(dh)
offsets = np.arange(-12, 13)
# three different anchor positions n, same offset axis -> identical curves
for n, mk, lab in [(0, "o", "$n=0$"), (4, "s", "$n=4$"), (9, "^", "$n=9$")]:
    score = [rope(q, n + off) @ rope(k, n) for off in offsets]
    ax2.plot(offsets, score, mk, ms=4.2, mfc="none",
             color={0: ACC, 4: Q_C, 9: K_C}[n], label=lab, lw=0)
# reference line: single rotation by offset
ref = [rope(q, off) @ rope(k, 0) for off in offsets]
ax2.plot(offsets, ref, "-", color=EDGE, lw=1.3, alpha=0.8,
         label=r"$\langle R_{m-n}\mathbf{q},\,\mathbf{k}\rangle$")
ax2.axvline(0, color="#cbd5e1", lw=0.8)
ax2.set_xlabel("offset  $m - n$ (query pos $-$ key pos)", fontsize=8.8)
ax2.set_ylabel(r"score $\langle R_m\mathbf{q},\,R_n\mathbf{k}\rangle$", fontsize=8.8)
ax2.set_title("Score depends on the offset only — all anchors $n$ coincide", fontsize=9.4)
ax2.grid(alpha=0.25); ax2.legend(fontsize=7.8, ncol=2, loc="upper right")

# numeric residual annotation
spread = max(abs(np.array([rope(q, 0 + 5) @ rope(k, 0),
                           rope(q, 4 + 5) @ rope(k, 4),
                           rope(q, 9 + 5) @ rope(k, 9)]) - (rope(q, 5) @ rope(k, 0))))
ax2.text(0.02, 0.04, f"max anchor spread $= {spread:.0e}$", transform=ax2.transAxes,
         fontsize=7.4, color=EDGE)

with open(HERE / "appendix-e-rope.json", "w") as f:
    json.dump({"anchor_spread": float(spread)}, f, indent=1)

fig.tight_layout()
fig.savefig(HERE / "appendix-e-rope.svg", bbox_inches="tight")
print(f"wrote appendix-e-rope.svg  (anchor spread {spread:.1e})")
