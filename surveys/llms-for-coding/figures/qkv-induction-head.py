"""An induction head, constructed by hand from (M, W_OV) -- no training.

Appendix A, section A.9.  An induction head completes  ...[A][B]...[A] -> [B]
by (i) prefix matching: attend back to positions preceded by the current token,
and (ii) copying: write the attended token into the next-token logits
(Olsson et al. 2022; Elhage et al. 2021).  We build one explicitly to show the
whole head IS the pair (M, W_OV); the raw Q, K, V never appear.

Construction.  Give each position j a residual feature that concatenates two
one-hot blocks: its own token  e(tok_j)  and its predecessor  e(tok_{j-1})
(the predecessor block is what a "previous-token head" would have written one
layer earlier).  Then:

  * QK circuit  M  matches the query's OWN-token block against the key's
    PREDECESSOR block:  M = sum_a e_own(a) e_prev(a)^T.  So score(t,j) is high
    exactly when tok_t == tok_{j-1}, i.e. j follows an earlier copy of the
    current token -- prefix matching.

  * OV circuit  W_OV  reads the attended position's OWN-token block and writes
    it to the vocab-logit space:  W_OV = sum_a e_own(a) e_logit(a)^T.  So the
    head copies whatever token it attended to into the next-token logits.

Run on a random token stream with one planted repeat, the head at the final
occurrence of the trigger attends to the token that followed the FIRST
occurrence and boosts exactly that token's logit.  Deterministic (fixed seed).

Outputs:
  qkv-induction-head.svg
  qkv-induction-head.json
"""
import json
import pathlib

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent

# macOS Accelerate / NumPy 2.x raises spurious FP flags inside BLAS matmul;
# the printed results are exact (verified), so silence these non-errors.
np.seterr(divide="ignore", over="ignore", invalid="ignore")

V = 6          # vocabulary size
rng = np.random.default_rng(11)
vocab = ["A", "B", "C", "D", "E", "F"]

# Token stream with a planted induction pattern: a trigger token T appears
# twice; the first time it is followed by the "answer" token. The model sees
# the prefix up to (and including) the second trigger and must predict the
# answer at the next step.
tokens = [2, 0, 3, 1, 4, 5, 2, 3]   # C A D B E F C D ...
#          C  A  D  B  E  F  C  ?   -> first 'C'(idx0) is followed by 'A'(idx1);
# the second 'C' is at position 6; an induction head predicts 'A'.
trigger_pos = 6
answer_tok = tokens[tokens.index(2) + 1]   # token after the FIRST trigger = 'A' (0)
Tlen = len(tokens)

eye = np.eye(V)


def feature(j):
    own = eye[tokens[j]]
    prev = eye[tokens[j - 1]] if j > 0 else np.zeros(V)
    return np.concatenate([own, prev])      # dim 2V: [own | prev]


Xr = np.stack([feature(j) for j in range(Tlen)])   # (T, 2V)
own_blk = np.concatenate([np.eye(V), np.zeros((V, V))], axis=1)    # selects own
prev_blk = np.concatenate([np.zeros((V, V)), np.eye(V)], axis=1)   # selects prev

# QK circuit: own(query) matched to prev(key).  M is (2V x 2V).  The strength
# beta is the head's matching confidence (a trained induction head learns large
# match logits); it sets how sharply the softmax concentrates on the match.
beta = 10.0
M = beta * (own_blk.T @ prev_blk)   # beta * sum_a e_own(a) e_prev(a)^T
# OV circuit: own(value) copied to logit space.  W_OV is (2V x V).  The write
# strength gamma is the head's copy confidence (a trained head writes large
# logits); it sharpens the next-token distribution onto the copied token.
gamma = 4.0
W_OV = gamma * (own_blk.T @ np.eye(V))   # gamma * sum_a e_own(a) e_logit(a)^T

dk = V
scores = (Xr @ M @ Xr.T) / np.sqrt(dk)
# causal mask: position t attends to j <= t (here we read out the trigger row)
mask = np.tril(np.ones((Tlen, Tlen), dtype=bool))
scores = np.where(mask, scores, -np.inf)
scores = scores - np.nanmax(scores, axis=1, keepdims=True)
A = np.exp(scores)
A /= A.sum(axis=1, keepdims=True)

attn_row = A[trigger_pos]                       # where the final 'C' looks
logits = attn_row @ Xr @ W_OV                   # copied into vocab logits
probs = np.exp(logits - logits.max()); probs /= probs.sum()

data = {
    "vocab": vocab, "tokens": tokens, "token_str": [vocab[t] for t in tokens],
    "trigger_pos": trigger_pos, "trigger_tok": vocab[tokens[trigger_pos]],
    "answer_tok": vocab[answer_tok],
    "attention_row_at_trigger": [float(x) for x in attn_row],
    "argmax_attended_pos": int(attn_row.argmax()),
    "next_token_probs": {vocab[i]: float(probs[i]) for i in range(V)},
    "predicted_tok": vocab[int(probs.argmax())],
}
with open(HERE / "qkv-induction-head.json", "w") as f:
    json.dump(data, f, indent=1)

labels = [f"{j}:{vocab[t]}" for j, t in enumerate(tokens)]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.0))

bars = ax1.bar(range(Tlen), attn_row, color="#2563eb")
bars[attn_row.argmax()].set_color("#dc2626")
ax1.set_xticks(range(Tlen))
ax1.set_xticklabels(labels, fontsize=8)
ax1.set_xlabel("position : token")
ax1.set_ylabel(f"attention from the final trigger (pos {trigger_pos}: "
               f"'{vocab[tokens[trigger_pos]]}')")
ax1.set_title("Prefix matching: attend to the token AFTER the first 'C'",
              fontsize=10.0)
ax1.grid(True, axis="y", alpha=0.25)

pbars = ax2.bar(range(V), [probs[i] for i in range(V)], color="#9ca3af")
pbars[int(probs.argmax())].set_color("#16a34a")
ax2.set_xticks(range(V)); ax2.set_xticklabels(vocab)
ax2.set_xlabel("next-token vocabulary")
ax2.set_ylabel("predicted next-token probability")
ax2.set_title(f"Copying: logits peak at '{vocab[answer_tok]}' "
              f"(the token after the first 'C')", fontsize=10.0)
ax2.grid(True, axis="y", alpha=0.25)

fig.tight_layout()
fig.savefig(HERE / "qkv-induction-head.svg")
print("wrote qkv-induction-head.svg / .json")
print(f"  stream: {[vocab[t] for t in tokens]}, trigger at pos {trigger_pos} ('C')")
print(f"  attends to position {int(attn_row.argmax())} "
      f"('{vocab[tokens[int(attn_row.argmax())]]}'), weight {attn_row.max():.3f}")
print(f"  predicts '{vocab[int(probs.argmax())]}' "
      f"with p={probs.max():.3f} (answer = '{vocab[answer_tok]}')")
