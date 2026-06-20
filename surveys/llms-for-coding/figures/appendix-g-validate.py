"""Appendix G validation engine — the MoE router + gating, proven correct.

The frontier block replaces the single SwiGLU MLP (Appendix E) with a router and
many expert MLPs; each token is routed to its top-K_r experts and a shared expert,
the outputs combined by normalized gating values. The genuinely new piece is the
ROUTER backward: gradient flows through the gate values g_i (a softmax-like
normalization over the SELECTED experts) back to the router centroids e_i, while
top-k itself is a non-differentiable mask. This engine implements that backward
analytically and checks it against central finite differences, following the
DeepSeek-V3 gating of Eqs (12)-(15) [64]: sigmoid affinity, top-k selection,
normalization over the selected set.

Run:  python appendix-g-validate.py   (asserts every gradient; writes JSON)
Experts here are plain ReLU MLPs (SwiGLU was already validated in Appendix E);
the target of this check is the router/gating, not the expert internals.
"""
import json
import pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
rng = np.random.default_rng(0)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def expert_fwd(u, W1, W2):
    pre = u @ W1
    hid = np.maximum(pre, 0.0)
    return hid @ W2, (u, W1, W2, pre, hid)


def expert_bwd(do, cache):
    u, W1, W2, pre, hid = cache
    dhid = do @ W2.T
    dW2 = np.outer(hid, do)
    dpre = dhid * (pre > 0)
    dW1 = np.outer(u, dpre)
    du = dpre @ W1.T
    return du, dW1, dW2


# ---- MoE layer: sigmoid router, top-Kr, normalized gating over selected -----
def moe_fwd(u, E, Wr1, Wr2, Ws1, Ws2, Kr):
    Nr = E.shape[0]
    a = E @ u                              # affinity logits a_i = e_i . u
    s = sigmoid(a)                         # s_i = sigmoid(a_i)  (Eq 15)
    S = np.argsort(-s)[:Kr]               # top-Kr selected set
    Z = s[S].sum()
    g = np.zeros(Nr)
    g[S] = s[S] / Z                        # gating g_i = s_i / Z  (Eqs 13-14)
    o = np.zeros_like(u)
    ecache = {}
    for i in S:
        ei, c = expert_fwd(u, Wr1[i], Wr2[i])
        o += g[i] * ei
        ecache[i] = (ei, c)
    scache = []
    for j in range(Ws1.shape[0]):          # shared experts (always on)
        ej, c = expert_fwd(u, Ws1[j], Ws2[j])
        o += ej
        scache.append((ej, c))
    return o, (u, E, s, S, Z, g, ecache, scache, Wr1, Wr2, Ws1, Ws2)


def moe_bwd(do, cache):
    u, E, s, S, Z, g, ecache, scache, Wr1, Wr2, Ws1, Ws2 = cache
    du = np.zeros_like(u)
    dE = np.zeros_like(E)
    dWr1 = np.zeros_like(Wr1); dWr2 = np.zeros_like(Wr2)
    dWs1 = np.zeros_like(Ws1); dWs2 = np.zeros_like(Ws2)
    # 1) gradient to the gate values: dg_i = <do, E_i(u)>
    dg = {i: float(do @ ecache[i][0]) for i in S}
    # 2) expert backward with upstream g_i * do
    for i in S:
        dui, dW1i, dW2i = expert_bwd(g[i] * do, ecache[i][1])
        du += dui; dWr1[i] += dW1i; dWr2[i] += dW2i
    for j, (ej, c) in enumerate(scache):
        duj, dW1j, dW2j = expert_bwd(do, c)
        du += duj; dWs1[j] += dW1j; dWs2[j] += dW2j
    # 3) gating backward: g_i = s_i / Z over selected -> ds_k = (1/Z)[dg_k - sum_i g_i dg_i]
    gw = sum(g[i] * dg[i] for i in S)
    ds = {k: (dg[k] - gw) / Z for k in S}
    # 4) ds_k -> a_k = e_k . u -> e_k, u
    for k in S:
        da = ds[k] * s[k] * (1 - s[k])     # sigmoid'
        dE[k] += da * u
        du += da * E[k]
    return du, dE, dWr1, dWr2, dWs1, dWs2


# ----------------------------- gradient check --------------------------------
def fd(f, x, eps=1e-6):
    g = np.zeros_like(x)
    it = np.nditer(x, flags=["multi_index"])
    while not it.finished:
        i = it.multi_index
        o = x[i]
        x[i] = o + eps; fp = f()
        x[i] = o - eps; fm = f()
        x[i] = o
        g[i] = (fp - fm) / (2 * eps)
        it.iternext()
    return g


d, dff, Nr, Kr, Ns = 6, 8, 5, 2, 1
u = rng.standard_normal(d)
E = rng.standard_normal((Nr, d)) * 0.6                 # router centroids
Wr1 = rng.standard_normal((Nr, d, dff)) * 0.3
Wr2 = rng.standard_normal((Nr, dff, d)) * 0.3
Ws1 = rng.standard_normal((Ns, d, dff)) * 0.3
Ws2 = rng.standard_normal((Ns, dff, d)) * 0.3
tgt = rng.standard_normal(d)


def loss():
    o, _ = moe_fwd(u, E, Wr1, Wr2, Ws1, Ws2, Kr)
    return 0.5 * np.sum((o - tgt) ** 2)


o, cache = moe_fwd(u, E, Wr1, Wr2, Ws1, Ws2, Kr)
do = o - tgt
du, dE, dWr1, dWr2, dWs1, dWs2 = moe_bwd(do, cache)

results = {}
for name, an, var in [("du", du, u), ("dE_router", dE, E),
                      ("dWr1", dWr1, Wr1), ("dWr2", dWr2, Wr2),
                      ("dWs1_shared", dWs1, Ws1), ("dWs2_shared", dWs2, Ws2)]:
    num = fd(loss, var)
    e = np.max(np.abs(an - num)) / (np.max(np.abs(num)) + 1e-12)
    assert e < 1e-6, (name, e)
    results[name + "_relerr"] = float(e)

# --- the decoupling, sourced DeepSeek-V3 [64]: total vs active per token ---
results["deepseek_v3_total_B"] = 671
results["deepseek_v3_active_B"] = 37
results["deepseek_v3_active_fraction"] = round(37 / 671, 4)
results["routed_experts"] = 256
results["shared_experts"] = 1
results["activated_routed"] = 8

with open(HERE / "appendix-g-validate.json", "w") as f:
    json.dump(results, f, indent=1)

print("All Appendix G MoE-router checks passed.")
for k, v in results.items():
    print(f"  {k}: {v}")
