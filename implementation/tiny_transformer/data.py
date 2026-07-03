"""Synthetic tasks.

Induction (the canonical probe, Olsson et al. style): each sequence is a random
first half followed by an exact copy of that half. At a position t in the copied
region the correct next token is fully determined by the earlier occurrence — an
induction head (match the current token to its previous occurrence, copy what
followed) solves it; a 1-layer attention-only model cannot (H1). First-half
positions are unpredictable, so the in-context loss drops from the first to the
second half once the induction head forms (H2/H8).

Modular addition (the grokking task, H7): tokens [a, b, '='] -> target (a+b) mod p.
"""
from __future__ import annotations

import numpy as np

IGNORE = -1  # target id for positions not scored


def make_induction_batch(rng, batch: int, n_ctx: int, d_vocab: int,
                         vocab_lo: int = 0, vocab_hi: int | None = None,
                         min_prefix: int = 1):
    """Random-length prefix + a repeated random block, with a **variable offset
    per sequence** — so a fixed relative-offset positional head cannot solve it
    and genuine content-matching induction is required (a 1-layer attention-only
    model fails, H1; the fixed-offset version had a positional shortcut — bug
    2026-07-02-04).

    Returns tokens[B,T] int64, targets[B,T] (next-token, IGNORE at last pos),
    ind_mask[B,T] (True at induction query positions), attend_pos[B,T] (the
    position an induction head should attend to from each query, else -1).
    vocab_lo/vocab_hi restrict the sampled alphabet (held-out-symbol control).
    """
    if vocab_hi is None:
        vocab_hi = d_vocab
    T = n_ctx
    toks = rng.integers(vocab_lo, vocab_hi, size=(batch, T)).astype(np.int64)
    attend_pos = np.full((batch, T), -1, dtype=np.int64)
    for b in range(batch):
        # random prefix length -> the repeated block sits at a data-dependent
        # absolute position AND has a data-dependent offset (= block length).
        hi = max(min_prefix + 1, T // 2)
        p = int(rng.integers(min_prefix, hi))
        block = (T - p) // 2
        if block < 2:                       # degenerate; fall back to a safe split
            p, block = T // 4, (T - T // 4) // 2
        end = min(T, p + 2 * block)
        L = end - (p + block)
        toks[b, p + block:end] = toks[b, p:p + L]      # copy the block
        # induction queries t in [p+block, end-1): toks[t]==toks[t-block],
        # target toks[t+1]==toks[t-block+1]; the head should attend to t-block+1.
        idx = np.arange(p + block, end - 1)
        attend_pos[b, idx] = idx - block + 1

    targets = np.full((batch, T), IGNORE, dtype=np.int64)
    targets[:, :-1] = toks[:, 1:]
    ind_mask = attend_pos >= 0
    return toks, targets, ind_mask, attend_pos


def make_corrupt_batch(rng, toks, ind_mask, d_vocab: int):
    """Clean/corrupt pair for activation patching (H10).

    For each sequence, pick one induction query position q and overwrite toks[q]
    with a random token that differs from the original, breaking the prefix match
    so the induction prediction at q becomes wrong. Returns corrupted tokens and
    the chosen query index per sequence.
    """
    B, T = toks.shape
    corrupt = toks.copy()
    q_idx = np.empty(B, dtype=np.int64)
    for b in range(B):
        cand = np.flatnonzero(ind_mask[b])
        q = int(rng.choice(cand))
        q_idx[b] = q
        new = int(rng.integers(0, d_vocab))
        while new == corrupt[b, q]:
            new = int(rng.integers(0, d_vocab))
        corrupt[b, q] = new
    return corrupt, q_idx


def make_modadd_data(p: int):
    """All p*p pairs. tokens [a,b,'='] (|V|=p+1, '=' is id p); target = (a+b) mod p.
    Predicted at the final ('=') position. Returns tokens[N,3], targets[N]."""
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    a = a.ravel()
    b = b.ravel()
    c = (a + b) % p
    eq = np.full_like(a, p)
    toks = np.stack([a, b, eq], axis=1).astype(np.int64)
    return toks, c.astype(np.int64)


def modadd_split(toks, targets, frac_train: float, seed: int = 0):
    """Deterministic train/val split for grokking (delayed generalization needs
    a held-out set)."""
    rng = np.random.default_rng(seed)
    n = len(toks)
    perm = rng.permutation(n)
    n_tr = int(round(frac_train * n))
    tr, va = perm[:n_tr], perm[n_tr:]
    return (toks[tr], targets[tr]), (toks[va], targets[va])
