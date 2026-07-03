"""Minimal-pair induction task as an eap_ig TaskBatch (single-token answers, logit-diff).

Construction (BOS at index 0, block length L, distinct random ids):
  block   = [x_0, ..., x_{L-1}]
  clean   = [BOS] + block + block[:-1]          # length 2L; last token = x_{L-2}
  corrupt = [BOS] + block[:-1] + [y] + block[:-1]  # first-copy follower x_{L-1} -> foil y

At the final position (token x_{L-2}) induction attends to the position holding x_{L-1}
(index L). In clean that is x_{L-1} (pos answer); in corrupt it is y (neg answer). Same
shape, same query token — a minimal pair, analogous to IOI's one-token swap. The engine's
attribution then localizes exactly the heads that move info from index L to the last token,
which are the induction heads. metric = logit_diff(x_{L-1}, y).
"""
from __future__ import annotations

import numpy as np
import torch

from implementation.eap_ig.tasks import TaskBatch


def build_induction(tok, *, n_examples=64, seed=0, block_len=25, id_lo=1000, id_hi=40000,
                    jitter=None):
    """Minimal-pair induction TaskBatch.

    jitter=None -> fixed block_len (query->target offset constant across examples).
    jitter=(lo,hi) -> per-example block length ~ Uniform[lo,hi), so the offset VARIES per
    example; a fixed-offset positional-copy head cannot exploit it (positional-shortcut
    robustness control, cf. parent bug 2026-07-02-05). Variable-length rows are right-padded
    with eos and carry per-example attn_mask + last_idx.
    """
    rng = np.random.default_rng(seed)
    bos = tok.eos_token_id
    pool = np.arange(id_lo, id_hi)
    clean_seqs, corrupt_seqs, pos_ids, neg_ids = [], [], [], []
    for _ in range(n_examples):
        L = block_len if jitter is None else int(rng.integers(jitter[0], jitter[1]))
        picks = rng.choice(pool, size=L + 1, replace=False)   # L distinct block ids + 1 foil
        block, y = picks[:L].tolist(), int(picks[L])
        second_copy = block[:L - 1]                            # [x_0 .. x_{L-2}] (query = x_{L-2})
        clean_seqs.append([bos] + block + second_copy)         # follower x_{L-1}
        corrupt_seqs.append([bos] + block[:L - 1] + [y] + second_copy)  # follower -> y
        pos_ids.append(block[L - 1])                           # correct = induction continuation
        neg_ids.append(y)                                      # foil = corrupt continuation
    T = max(len(s) for s in clean_seqs)
    pad = tok.eos_token_id
    cids, xids, mask, last = [], [], [], []
    for cs, xs in zip(clean_seqs, corrupt_seqs):
        n = len(cs)                                            # clean & corrupt share length
        last.append(n - 1)
        mask.append([1] * n + [0] * (T - n))
        cids.append(cs + [pad] * (T - n))
        xids.append(xs + [pad] * (T - n))
    return TaskBatch(torch.tensor(cids), torch.tensor(xids), torch.tensor(mask),
                     torch.tensor(last), "logit_diff",
                     pos_ids=torch.tensor(pos_ids), neg_ids=torch.tensor(neg_ids))
