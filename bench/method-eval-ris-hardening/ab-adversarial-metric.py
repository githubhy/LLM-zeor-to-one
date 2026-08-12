"""A/B confirmation for [opt:ME-ADVERSARIAL-METRIC] (method-eval hardening).

Planted case modelling the floor-gate triviality class: a *confidence*-style tuning
metric that a DEGENERATE decoder satisfies WITHOUT actually predicting anything.

A `decoder` applies a logit bias `b` toward one fixed token; the tuning METRIC rewards a
large mean |logit margin| (the "the model is confident / the distribution is peaked"
proxy that decoding-parameter sweeps routinely optimise). A huge bias saturates every
next-token decision to the same token -> huge mean |margin| -> the metric scores it BEST,
while the true quality (mutual information the emitted tokens carry about the targets)
COLLAPSES to ~0. This is the degenerate-repetition failure in miniature: peaked and
confident, and carrying no information.

A = un-toggled rubric: adopt argmax(metric).            -> picks the trivial candidate (WRONG)
B = ME-ADVERSARIAL-METRIC: construct the degenerate case, require the metric to REJECT it.
    The metric does NOT reject it -> the metric is disqualified -> the trivial win is caught.
Deterministic (seeded).

Run:  python bench/method-eval-ris-hardening/ab-adversarial-metric.py
"""
import numpy as np

rng = np.random.default_rng(0)
N = 200_000
targets = rng.integers(0, 2, N)           # the correct next token, of two candidates (0/1)
# Logit margin for token 0 over token 1, under a mildly-informative model.
true_margin = (1 - 2 * targets) * 1.2 + rng.standard_normal(N) * 1.0


def decode(bias):
    """A 1-parameter 'decoder': add a fixed logit bias toward token 0. bias=0 is the honest
    decoder; a huge |bias| saturates every decision to one token (degenerate repetition)."""
    return true_margin + bias


def tuning_metric(margin):
    """The FLAWED tuning objective: reward a large mean |logit margin| -- 'confident /
    low-entropy / peaked'. A saturating bias maximises it without predicting anything."""
    return float(np.mean(np.abs(margin)))


def true_quality(margin):
    """Ground truth the metric is a proxy FOR: mutual information the emitted tokens carry
    about the targets (a decoder that ignores the context scores ~0)."""
    emitted = (margin < 0).astype(int)       # margin<0 -> token 1
    p = np.mean(emitted == targets)          # next-token accuracy
    p = min(max(p, 1e-9), 1 - 1e-9)
    return 1 + p * np.log2(p) + (1 - p) * np.log2(1 - p)   # 1 - H(p): 1 bit if perfect, 0 if chance


# Candidate set: an honest decoder (bias 0) and a "trivial" one (huge bias) plus a few.
candidates = {"honest(b=0)": 0.0, "mild(b=2)": 2.0, "trivial(b=60)": 60.0, "trivial(b=200)": 200.0}
metric = {k: tuning_metric(decode(b)) for k, b in candidates.items()}
quality = {k: true_quality(decode(b)) for k, b in candidates.items()}

print("candidate        tuning_metric   true_quality(bits)")
for k in candidates:
    print(f"  {k:14s}  {metric[k]:10.3f}     {quality[k]:.4f}")

# --- A: un-toggled rubric -> adopt argmax(metric) ---------------------------
winner_A = max(metric, key=metric.get)
print(f"\n[A - ME-ADVERSARIAL-METRIC OFF] adopt argmax(metric) -> {winner_A!r} "
      f"(metric={metric[winner_A]:.1f}, true_quality={quality[winner_A]:.4f})")

# --- B: ME-ADVERSARIAL-METRIC -> construct the degenerate case, require rejection ---
# The named trivial solution: a saturating bias that annihilates the token's information.
degenerate = decode(200.0)
deg_metric = tuning_metric(degenerate)
deg_quality = true_quality(degenerate)
# The discipline: does the metric REJECT the degenerate solution?
best_metric = max(metric.values())
metric_rejects_degenerate = deg_metric < best_metric   # is the trivial NOT the best?
print(f"[B - ME-ADVERSARIAL-METRIC ON ] degenerate (saturating bias) scores metric="
      f"{deg_metric:.1f} (best={best_metric:.1f}), true_quality={deg_quality:.4f}")
print(f"    metric REJECTS the degenerate case? {metric_rejects_degenerate}  "
      f"-> {'metric OK' if metric_rejects_degenerate else 'METRIC DISQUALIFIED: rewards triviality; do not adopt on it'}")

caught_A = quality[winner_A] < 0.5          # A adopted a low-true-quality (trivial) candidate
print("\nRESULT:")
print(f"  A (OFF) adopted a trivial candidate that clears the metric by triviality: {caught_A}")
print(f"  B (ON)  flags the metric as satisfiable-by-triviality: {not metric_rejects_degenerate}")
ok = caught_A and (not metric_rejects_degenerate)
print("\nA/B VERDICT:", "PASS -- ME-ADVERSARIAL-METRIC catches the planted degenerate-metric case that the un-toggled rubric adopts"
      if ok else "INCONCLUSIVE")
