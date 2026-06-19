"""A toy decoder transformer, end-to-end: forward, full backward, one Adam step.

Appendix C (calibration chapter). A deliberately tiny model so every number is
hand-checkable and the analytic gradients can be verified against finite
differences. One decoder block, pre-LayerNorm, a single attention head, a ReLU
MLP, learned token+position embeddings, an untied unembedding. Causal, teacher-
forced next-token cross-entropy on one fixed sequence.

Config (tiny on purpose):
  vocab V=3, model width d=4, context T=3, 1 head (d_k=d_v=4), FFN hidden d_ff=8.
  input x=[0,1,2], targets y=[1,2,0] (predict the next symbol in a 3-cycle).

This script is the correctness backbone of the chapter: it implements the exact
forward and backward equations the prose derives, runs a CENTRAL finite-
difference gradient check on every parameter tensor (max relative error printed
and asserted < 1e-5), takes one Adam step, and writes all verified numbers to a
JSON sidecar plus a validation figure (analytic vs numerical gradients; loss over
a few Adam steps). If the chapter's derivations were wrong, the gradient check
here would fail.

Outputs:
  appendix-c-gradcheck.svg
  appendix-c-toy.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
np.seterr(divide="ignore", over="ignore", invalid="ignore")

V, d, T, dk, dff = 3, 4, 3, 4, 8
EPS = 1e-5
x = np.array([0, 1, 2])          # input token ids
y = np.array([1, 2, 0])          # next-token targets (a 3-cycle)
CAUSAL = np.tril(np.ones((T, T), dtype=bool))


def init_params(seed=0):
    r = np.random.default_rng(seed)
    s = 0.3
    return {
        "E":  r.standard_normal((V, d)) * s,
        "P":  r.standard_normal((T, d)) * s,
        "WQ": r.standard_normal((d, dk)) * s, "WK": r.standard_normal((d, dk)) * s,
        "WV": r.standard_normal((d, dk)) * s, "WO": r.standard_normal((dk, d)) * s,
        "g1": np.ones(d), "b1": np.zeros(d),                     # LayerNorm 1 (pre-attn)
        "W1": r.standard_normal((d, dff)) * s, "bff1": np.zeros(dff),
        "W2": r.standard_normal((dff, d)) * s, "bff2": np.zeros(d),
        "g2": np.ones(d), "b2": np.zeros(d),                     # LayerNorm 2 (pre-ffn)
        "gf": np.ones(d), "bf": np.zeros(d),                     # final LayerNorm
        "WU": r.standard_normal((d, V)) * s, "bU": np.zeros(V),
    }


def layernorm_fwd(H, g, b, eps=1e-5):
    mu = H.mean(axis=1, keepdims=True)
    xc = H - mu
    var = (xc ** 2).mean(axis=1, keepdims=True)
    inv = 1.0 / np.sqrt(var + eps)
    xhat = xc * inv
    return g * xhat + b, (xhat, inv, g)


def layernorm_bwd(dY, cache):
    xhat, inv, g = cache
    n = xhat.shape[1]
    dg = (dY * xhat).sum(axis=0)
    db = dY.sum(axis=0)
    dxhat = dY * g
    # dH = inv/n * (n*dxhat - sum(dxhat) - xhat*sum(dxhat*xhat))   (per row)
    dH = (inv / n) * (n * dxhat
                      - dxhat.sum(axis=1, keepdims=True)
                      - xhat * (dxhat * xhat).sum(axis=1, keepdims=True))
    return dH, dg, db


def softmax_rows_causal(S):
    Sm = np.where(CAUSAL, S, -np.inf)
    Sm = Sm - np.nanmax(np.where(CAUSAL, Sm, -np.inf), axis=1, keepdims=True)
    Ex = np.where(CAUSAL, np.exp(Sm), 0.0)
    return Ex / Ex.sum(axis=1, keepdims=True)


def forward(p, need_cache=False):
    H0 = p["E"][x] + p["P"]                                  # (T,d) embedding
    # --- attention sublayer (pre-norm) ---
    A1, c_ln1 = layernorm_fwd(H0, p["g1"], p["b1"])
    Q, K, Vv = A1 @ p["WQ"], A1 @ p["WK"], A1 @ p["WV"]      # (T,dk)
    S = (Q @ K.T) / np.sqrt(dk)
    Aw = softmax_rows_causal(S)                              # (T,T)
    Ctx = Aw @ Vv                                            # (T,dk)
    attn = Ctx @ p["WO"]                                     # (T,d)
    H1 = H0 + attn
    # --- FFN sublayer (pre-norm) ---
    A2, c_ln2 = layernorm_fwd(H1, p["g2"], p["b2"])
    Z = A2 @ p["W1"] + p["bff1"]                             # (T,dff) pre-activation
    G = np.maximum(Z, 0.0)                                   # ReLU
    ffn = G @ p["W2"] + p["bff2"]                            # (T,d)
    H2 = H1 + ffn
    # --- final norm + unembedding + loss ---
    HF, c_lnf = layernorm_fwd(H2, p["gf"], p["bf"])
    logits = HF @ p["WU"] + p["bU"]                          # (T,V)
    logits = logits - logits.max(axis=1, keepdims=True)
    Pr = np.exp(logits); Pr = Pr / Pr.sum(axis=1, keepdims=True)
    loss = -np.log(Pr[np.arange(T), y] + 1e-12).mean()
    if not need_cache:
        return loss
    cache = dict(H0=H0, A1=A1, c_ln1=c_ln1, Q=Q, K=K, Vv=Vv, S=S, Aw=Aw, Ctx=Ctx,
                 H1=H1, A2=A2, c_ln2=c_ln2, Z=Z, G=G, H2=H2, HF=HF, c_lnf=c_lnf, Pr=Pr)
    return loss, cache


def backward(p, cache):
    g = {}
    c = cache
    # loss -> logits:  dlogits = (Pr - onehot(y)) / T   (softmax + CE, mean over T)
    dlogits = c["Pr"].copy()
    dlogits[np.arange(T), y] -= 1.0
    dlogits /= T
    # unembedding
    g["WU"] = c["HF"].T @ dlogits
    g["bU"] = dlogits.sum(axis=0)
    dHF = dlogits @ p["WU"].T
    # final LayerNorm
    dH2, g["gf"], g["bf"] = layernorm_bwd(dHF, c["c_lnf"])
    # FFN residual: H2 = H1 + ffn
    dH1 = dH2.copy()
    dffn = dH2
    g["W2"] = c["G"].T @ dffn
    g["bff2"] = dffn.sum(axis=0)
    dG = dffn @ p["W2"].T
    dZ = dG * (c["Z"] > 0)                                   # ReLU'
    g["W1"] = c["A2"].T @ dZ
    g["bff1"] = dZ.sum(axis=0)
    dA2 = dZ @ p["W1"].T
    dH1b, g["g2"], g["b2"] = layernorm_bwd(dA2, c["c_ln2"])
    dH1 += dH1b
    # attention residual: H1 = H0 + attn
    dH0 = dH1.copy()
    dattn = dH1
    g["WO"] = c["Ctx"].T @ dattn
    dCtx = dattn @ p["WO"].T
    g_Vv = c["Aw"].T @ dCtx                                  # dV from Ctx=Aw@Vv
    dAw = dCtx @ c["Vv"].T
    # softmax (per causal row) backward:  dS_i = Aw_i * (dAw_i - sum_j Aw_ij dAw_ij)
    dS = c["Aw"] * (dAw - (dAw * c["Aw"]).sum(axis=1, keepdims=True))
    dS = np.where(CAUSAL, dS, 0.0) / np.sqrt(dk)
    dQ = dS @ c["K"]
    dK = dS.T @ c["Q"]
    dVv = g_Vv
    g["WQ"] = c["A1"].T @ dQ
    g["WK"] = c["A1"].T @ dK
    g["WV"] = c["A1"].T @ dVv
    dA1 = dQ @ p["WQ"].T + dK @ p["WK"].T + dVv @ p["WV"].T
    dH0b, g["g1"], g["b1"] = layernorm_bwd(dA1, c["c_ln1"])
    dH0 += dH0b
    # embedding
    g["P"] = dH0.copy()
    g["E"] = np.zeros_like(p["E"])
    for t in range(T):
        g["E"][x[t]] += dH0[t]
    return g


def gradient_check(p):
    _, cache = forward(p, need_cache=True)
    ga = backward(p, cache)
    worst = 0.0
    for name, P in p.items():
        gn = np.zeros_like(P)
        it = np.nditer(P, flags=["multi_index"])
        while not it.finished:
            idx = it.multi_index
            old = P[idx]
            P[idx] = old + EPS; lp = forward(p)
            P[idx] = old - EPS; lm = forward(p)
            P[idx] = old
            gn[idx] = (lp - lm) / (2 * EPS)
            it.iternext()
        num = np.linalg.norm(ga[name] - gn)
        den = np.linalg.norm(ga[name]) + np.linalg.norm(gn) + 1e-12
        worst = max(worst, num / den)
    return worst


def adam_train(p, steps=40, lr=0.1, b1=0.9, b2=0.999, eps=1e-8):
    m = {k: np.zeros_like(v) for k, v in p.items()}
    v = {k: np.zeros_like(v) for k, v in p.items()}
    losses = []
    for t in range(1, steps + 1):
        loss, cache = forward(p, need_cache=True)
        losses.append(loss)
        gr = backward(p, cache)
        for k in p:
            m[k] = b1 * m[k] + (1 - b1) * gr[k]
            v[k] = b2 * v[k] + (1 - b2) * gr[k] ** 2
            mh = m[k] / (1 - b1 ** t)
            vh = v[k] / (1 - b2 ** t)
            p[k] = p[k] - lr * mh / (np.sqrt(vh) + eps)
    losses.append(forward(p))
    return losses


# ----- run: gradient check, then a short Adam run -----------------------------
p = init_params()
rel_err = gradient_check(init_params())
# collect analytic vs numerical for the figure (flattened, a fresh copy)
pq = init_params()
_, cq = forward(pq, need_cache=True)
gaq = backward(pq, cq)
ana, num = [], []
for name, P in pq.items():
    it = np.nditer(P, flags=["multi_index"])
    while not it.finished:
        idx = it.multi_index
        old = P[idx]
        P[idx] = old + EPS; lp = forward(pq)
        P[idx] = old - EPS; lm = forward(pq)
        P[idx] = old
        num.append((lp - lm) / (2 * EPS)); ana.append(gaq[name][idx])
        it.iternext()
ana, num = np.array(ana), np.array(num)

ADAM_LR, ADAM_STEPS = 0.02, 60
losses = adam_train(init_params(), steps=ADAM_STEPS, lr=ADAM_LR)
loss0, loss1 = losses[0], losses[1]

assert rel_err < 1e-5, f"gradient check failed: rel_err={rel_err}"

data = {
    "config": {"V": V, "d": d, "T": T, "d_k": dk, "d_ff": dff,
               "input_x": x.tolist(), "target_y": y.tolist(),
               "block": "pre-LayerNorm, 1 head, ReLU MLP, learned pos, untied unembedding"},
    "n_params": int(sum(P.size for P in p.values())),
    "gradient_check_max_rel_error": float(rel_err),
    "adam_lr": ADAM_LR, "adam_steps": ADAM_STEPS,
    "loss_initial": float(losses[0]),
    "loss_after_1_adam_step": float(loss1),
    "loss_final": float(losses[-1]),
    "uniform_guess_loss_lnV": float(np.log(V)),
}
with open(HERE / "appendix-c-toy.json", "w") as f:
    json.dump(data, f, indent=1)

# ----- validation figure ------------------------------------------------------
EDGE, OK_C, LINE_C = "#374151", "#16a34a", "#7c3aed"
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6))

lim = max(np.abs(ana).max(), np.abs(num).max()) * 1.1
ax1.plot([-lim, lim], [-lim, lim], color=EDGE, lw=1.0, ls="--", zorder=1)
ax1.scatter(num, ana, s=22, color=OK_C, edgecolor=EDGE, lw=0.4, zorder=3, alpha=0.85)
ax1.set_xlim(-lim, lim); ax1.set_ylim(-lim, lim); ax1.set_aspect("equal")
ax1.set_xlabel("numerical gradient (central difference)", fontsize=9)
ax1.set_ylabel("analytic gradient (backprop)", fontsize=9)
ax1.set_title(rf"Backprop matches finite differences (max rel. error ${rel_err:.1e}$)",
              fontsize=10.0)
ax1.grid(alpha=0.25)
ax1.text(0.04, 0.96, f"all {len(ana)} parameter\ngradients on $y=x$",
         transform=ax1.transAxes, va="top", fontsize=8, color=EDGE,
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=EDGE, alpha=0.9))

ax2.plot(range(len(losses)), losses, "o-", color=LINE_C, lw=1.6, ms=3)
ax2.axhline(np.log(V), color=EDGE, ls=":", lw=1.0, label=fr"uniform-guess loss $\ln V={np.log(V):.2f}$")
ax2.annotate(rf"one Adam step: {loss0:.2f} $\to$ {loss1:.2f}",
             xy=(1, loss1), xytext=(8, np.log(V) * 0.82), fontsize=8, color=EDGE,
             arrowprops=dict(arrowstyle="-|>", color=EDGE, lw=1.0))
ax2.annotate(rf"converges to ${losses[-1]:.1e}$" "\n(3-cycle learned)",
             xy=(len(losses) - 1, losses[-1]), xytext=(len(losses) * 0.45, np.log(V) * 0.45),
             fontsize=8, color=EDGE, arrowprops=dict(arrowstyle="-|>", color=EDGE, lw=1.0))
ax2.set_xlabel("Adam step", fontsize=9)
ax2.set_ylabel("cross-entropy loss (nats)", fontsize=9)
ax2.set_title(rf"The toy model learns the 3-cycle (Adam, lr {ADAM_LR})", fontsize=10.0)
ax2.grid(alpha=0.25); ax2.legend(fontsize=8, loc="center right")

fig.tight_layout()
fig.savefig(HERE / "appendix-c-gradcheck.svg", bbox_inches="tight")
print("wrote appendix-c-gradcheck.svg / appendix-c-toy.json")
print(f"  params={data['n_params']}, gradcheck max rel err={rel_err:.3e}")
print(f"  loss {losses[0]:.4f} -> (1 step) {loss1:.4f} -> (40 steps) {losses[-1]:.4f}")
