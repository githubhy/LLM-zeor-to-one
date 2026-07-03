"""Weight-space circuit extraction (numpy; operates on extracted weight arrays).

Code (row) convention, per the package docstring: for one head with W_Q, W_K, W_V
of shape (d, d_k) and W_O of shape (d_k, d),
  - the QK bilinear form on residual embeddings is  M = W_Q W_Kᵀ  (d×d, rank ≤ d_k)
    with score(query h_i, key h_j) = h_i M h_jᵀ  (§A.2/§A.8);
  - the OV map on the residual stream is  W_OV = W_V W_O  (d×d)  (§A.4/§A.8).
These are the survey's circuits up to the row/column-convention transpose.
"""
from __future__ import annotations

import numpy as np


def qk_circuit(W_Q_h, W_K_h):
    """One head. W_Q_h,(d,d_k); W_K_h,(d,d_k). Returns (M,(d,d), singular_values)."""
    M = W_Q_h @ W_K_h.T
    s = np.linalg.svd(M, compute_uv=False)
    return M, s


def ov_circuit(W_V_h, W_O_h):
    """One head. W_V_h,(d,d_k); W_O_h,(d_k,d). Returns (W_OV,(d,d), eigenvalues)."""
    W_OV = W_V_h @ W_O_h
    eig = np.linalg.eigvals(W_OV)
    return W_OV, eig


def copying_score(eig):
    """Elhage-style OV copying score: mass of the eigenspectrum on the positive
    real axis. Returns (frac_positive_count, positive_real_mass_fraction).

    A pure copy head has predominantly positive real eigenvalues (§A.9, H3)."""
    re = np.real(eig)
    frac_pos = float((re > 0).mean())
    mass = float(re[re > 0].sum() / (np.abs(re).sum() + 1e-12))
    return frac_pos, mass


def effective_rank(s, thresh=0.99):
    """Number of singular values needed to capture `thresh` of the spectral energy
    (participation-style rank). Backs the rank-≤d_k cliff of §A.8 (H_theory)."""
    s = np.asarray(s, float)
    if s.sum() == 0:
        return 0
    csum = np.cumsum(s ** 2) / (s ** 2).sum()
    return int(np.searchsorted(csum, thresh) + 1)


def composition_score(W_ov_A, read_B):
    """Normalized Frobenius composition score (Elhage et al.): how much head B's
    read matrix (read_B, (d,d_k): W_Q/W_K/W_V of the later head) reads from what
    head A writes (W_ov_A, (d,d)). K-composition -> read_B = W_K_B.  (§A.3/§A.18)"""
    num = np.linalg.norm(read_B.T @ W_ov_A, ord="fro")
    den = np.linalg.norm(read_B, ord="fro") * np.linalg.norm(W_ov_A, ord="fro") + 1e-12
    return float(num / den)


def qk_token_table(W_E, M):
    """QK bigram table in vocab×vocab coords: B[a,b] = e_a M e_bᵀ — 'which key
    token b does query token a prefer'. W_E,(V,d); M,(d,d). Returns (V,V)."""
    return W_E @ M @ W_E.T


def ov_logit_table(W_U, W_OV, W_E):
    """OV 'effect on logits' table: L[a,c] = contribution to logit(c) when the head
    fires on source token a = e_a W_OV W_U[:,c].  W_E,(V,d); W_OV,(d,d); W_U,(d,V).
    Returns (V,V) — the head-dump 'Effect on logits' block (§A.9 head dump)."""
    return W_E @ W_OV @ W_U


def copying_score_diag(W_E, W_OV, W_U):
    """Direct copy signature (more robust than residual-basis eigenvalues for a
    distributed circuit): L = E W_OV U (source-token a x predicted-token c). A copy
    head, when attending to token a, should most boost logit a. Returns the fraction
    of source tokens whose top-predicted token is themselves, the mean self-rank,
    and the positive-diagonal fraction."""
    L = W_E @ W_OV @ W_U
    V = L.shape[0]
    order = np.argsort(-L, axis=1)
    ranks = np.array([int(np.where(order[a] == a)[0][0]) for a in range(V)])
    return dict(frac_top1_self=float((ranks == 0).mean()),
                mean_self_rank=float(ranks.mean()),
                diag_positive_frac=float((np.diag(L) > 0).mean()))


def head_dump(W_E, W_U, W_Q_h, W_K_h, W_V_h, W_O_h, topk=5):
    """Reproduce the small_a-style head dump for one head:
    'Queries that prefer key' (top QK bigram pairs) and 'Effect on logits'
    (top source->predicted pairs). Returns a dict."""
    M, s = qk_circuit(W_Q_h, W_K_h)
    W_OV, eig = ov_circuit(W_V_h, W_O_h)
    qk = qk_token_table(W_E, M)
    ov = ov_logit_table(W_U, W_OV, W_E)
    fp, mass = copying_score(eig)

    def top_pairs(tab, k):
        flat = np.argsort(tab, axis=None)[::-1][:k]
        return [(int(i // tab.shape[1]), int(i % tab.shape[1]), float(tab.flat[i]))
                for i in flat]

    return {
        "qk_singular_values": s.tolist(),
        "qk_effective_rank": effective_rank(s),
        "ov_copying_frac_positive": fp,
        "ov_copying_mass": mass,
        "queries_that_prefer_key": top_pairs(qk, topk),   # (query_tok, key_tok, score)
        "effect_on_logits": top_pairs(ov, topk),          # (source_tok, predicted_tok, score)
    }
