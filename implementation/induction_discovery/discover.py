"""H15 recovery metrics: does an automated method's per-head attribution recover the
oracle induction-head set?

Headline (threshold-free): Spearman rho of method |score| vs the continuous oracle
prefix-matching score, and AUROC of method |score| against the binary oracle set.
Also recovery@k and rank-consistency with exact patching (the pre-registered criterion).
"""
from __future__ import annotations

import numpy as np
from scipy import stats as _ss

HEAD = "a"   # attention-head node names start with 'a{l}.h{h}'


def head_abs_scores(scores: dict) -> dict:
    """Restrict a node-score dict to attention heads; return |score|."""
    return {u: abs(v) for u, v in scores.items() if u.startswith(HEAD) and ".h" in u}


def _auroc(scores: dict, positives: set) -> float:
    """AUROC of `scores` (higher = predicted positive) against the binary `positives` set,
    over the shared head keys. Mann-Whitney U / (n_pos*n_neg). Ties -> 0.5 credit."""
    keys = list(scores)
    pos = np.array([scores[k] for k in keys if k in positives], dtype=float)
    neg = np.array([scores[k] for k in keys if k not in positives], dtype=float)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # U statistic via rank-sum
    gt = sum((pos[:, None] > neg[None, :]).sum() for _ in [0])
    eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


def recovery_metrics(method_scores: dict, oracle_prefix: dict, oracle_set: list,
                     exact_scores: dict) -> dict:
    """method_scores/exact_scores: full node-score dicts. oracle_prefix: per-head prefix score."""
    mh = head_abs_scores(method_scores)             # |score| per head
    eh = head_abs_scores(exact_scores)
    keys = [k for k in mh if k in oracle_prefix]
    mv = np.array([mh[k] for k in keys])
    ov = np.array([oracle_prefix[k] for k in keys])
    sp = _ss.spearmanr(mv, ov)
    # rank-consistency with exact patching, over heads and over all nodes
    ek = [k for k in mh if k in eh]
    sp_exact = _ss.spearmanr([mh[k] for k in ek], [eh[k] for k in ek])
    allk = [k for k in method_scores if k in exact_scores]
    pe_all = _ss.pearsonr([abs(method_scores[k]) for k in allk],
                          [abs(exact_scores[k]) for k in allk])
    # recovery@k: of the top-k method heads (k=|oracle set|), fraction in the oracle set
    k = max(1, len(oracle_set))
    top_k = set(sorted(mh, key=lambda u: mh[u], reverse=True)[:k])
    rec_at_k = len(top_k & set(oracle_set)) / k
    return {
        "spearman_vs_oracle": float(sp.statistic),
        "spearman_vs_oracle_p": float(sp.pvalue),
        "auroc_vs_oracle_set": _auroc(mh, set(oracle_set)),
        "recovery_at_k": float(rec_at_k),
        "k": k,
        "spearman_vs_exact_heads": float(sp_exact.statistic),
        "pearson_vs_exact_allnodes": float(pe_all.statistic),
        "top_heads": sorted(mh, key=lambda u: mh[u], reverse=True)[:8],
    }
