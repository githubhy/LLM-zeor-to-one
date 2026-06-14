"""More context lowers next-token uncertainty -- and deeper memory keeps
paying off longer (why an AR(infinity) model wants the whole past).

Section 3.1.  A language model is an AR(infinity) predictor: x_t may depend
on the entire history.  How much does conditioning on more of the past
actually buy?  For a source with memory depth K (an order-K Markov chain),
the conditional entropy

  H(X_t | last k symbols)

falls as k grows and then plateaus once k reaches the true memory depth K
(no finite amount of further context helps).  Plotted for three sources of
increasing memory depth K in {1, 2, 4}: the deeper the memory, the longer
the curve keeps dropping.  Natural language has very deep, long-range
structure, so a model that conditions on the whole past (AR-infinity) keeps
extracting reductions a short-context AR(p) leaves on the table.

Everything is computed EXACTLY (no sampling): each source's order-K
transition is drawn once from a fixed-seed peaked Dirichlet, its stationary
k-gram distribution is the dominant left eigenvector, and every conditional
entropy is read off the exact stationary joint.

Outputs:
  context-reduces-uncertainty.svg
  context-reduces-uncertainty.json
"""
import json
import itertools
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

A = 3          # alphabet size
ALPHA = 0.4    # Dirichlet concentration (<1 => peaked => predictable source)
ORDERS = [1, 2, 3]
KMAX = 5


def H(dist):
    d = np.asarray(dist).ravel()
    d = d[d > 1e-15]
    return float(-np.sum(d * np.log2(d)))


def build_transition(K, seed):
    """P[context] = categorical over A, context in A^K, from peaked Dirichlet."""
    rng = np.random.default_rng(seed)
    contexts = list(itertools.product(range(A), repeat=K))
    return contexts, {c: rng.dirichlet(np.full(A, ALPHA)) for c in contexts}


def stationary(K, contexts, P):
    """Stationary distribution over A^K states of the K-gram Markov chain.

    Found by power iteration (robust; the chain is irreducible and aperiodic
    because every Dirichlet transition probability is strictly positive)."""
    idx = {c: i for i, c in enumerate(contexts)}
    n = len(contexts)
    M = np.zeros((n, n))
    for c in contexts:
        for x in range(A):
            M[idx[c], idx[c[1:] + (x,)]] += P[c][x]
    pi = np.full(n, 1.0 / n)
    for _ in range(100000):
        nxt = pi @ M
        nxt /= nxt.sum()
        if np.max(np.abs(nxt - pi)) < 1e-14:
            pi = nxt
            break
        pi = nxt
    return idx, pi


def joint_Kplus1(K, contexts, P, idx, pi):
    """Exact stationary joint over (X_{t-K}, ..., X_t), shape A^(K+1)."""
    J = np.zeros([A] * (K + 1))
    for c in contexts:
        for x in range(A):
            J[c + (x,)] += pi[idx[c]] * P[c][x]
    return J


def cond_entropy_given_k(J, K, k):
    """H(X_t | last k symbols) from the (K+1)-gram joint J (valid k <= K)."""
    Jk = J.sum(axis=tuple(range(0, K - k))) if k < K else J  # keep last k+1 axes
    return H(Jk) - H(Jk.sum(axis=-1))                        # H(joint) - H(context)


curves = {}
for K in ORDERS:
    contexts, P = build_transition(K, seed=100 + K)
    idx, pi = stationary(K, contexts, P)
    J = joint_Kplus1(K, contexts, P, idx, pi)
    rate = cond_entropy_given_k(J, K, K)                    # entropy rate
    vals = [cond_entropy_given_k(J, K, k) if k <= K else rate for k in range(KMAX + 1)]
    curves[K] = vals

data = {"alphabet_size": A, "dirichlet_alpha": ALPHA, "orders": ORDERS,
        "kmax": KMAX, "conditional_entropy_bits": {str(K): v for K, v in curves.items()}}
with open(HERE / "context-reduces-uncertainty.json", "w") as f:
    json.dump(data, f, indent=1)

colors = {1: "#dc2626", 2: "#d97706", 3: "#16a34a"}
ks = np.arange(KMAX + 1)
fig, ax = plt.subplots(figsize=(6.2, 4.0))
for K in ORDERS:
    ax.plot(ks, curves[K], "-o", color=colors[K], lw=2.0, ms=4.5,
            label=f"source with memory depth K = {K}")
    ax.axvline(K, color=colors[K], lw=0.8, ls=":", alpha=0.5)

ax.set_xlabel("context length used by the predictor,  k  (symbols of past)")
ax.set_ylabel(r"next-token uncertainty  $H(X_t \mid \mathrm{last}\ k)$  (bits)")
ax.set_title("More context lowers uncertainty; deeper memory pays off longer",
             fontsize=10.5)
ax.set_xticks(ks)
ax.set_xlim(-0.2, KMAX + 0.2)
ax.grid(True, alpha=0.25)
ax.legend(fontsize=8.5, loc="upper right")
fig.tight_layout()
fig.savefig(HERE / "context-reduces-uncertainty.svg")
print("wrote context-reduces-uncertainty.svg / .json")
for K in ORDERS:
    print(f"  K={K}: H(X_t|last k) = {[round(v, 3) for v in curves[K]]}")
