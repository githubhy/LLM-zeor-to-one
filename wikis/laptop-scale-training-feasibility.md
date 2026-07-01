# Laptop-Scale Training Feasibility — How Big a Transformer Can a 16 GB Laptop Train From Scratch?

*Reference note · 2026-07-01 · supports [`plans/2026-06-30-tiny-transformer-induction-study.md`](../plans/2026-06-30-tiny-transformer-induction-study.md)*

## TL;DR

- **Memory is almost never the limit; compute time is.** A 16 GB laptop can *hold* a GPT-2-small (124M-param) training run in ~2 GB, but cannot *finish* one in under weeks.
- **Practical from-scratch ceiling on a 16 GB laptop: ~10M params** (up to ~30M if you are patient), **and only with a small vocabulary.** That trains in minutes-to-~1 hour and stays iterable across seeds and ablations.
- **For real GPT-2 (124M and up): load the pretrained weights, do not train them.** Interpretability and circuit verification need the weights, not the training run.
- The compute-feasible size (~10M) is **~30–50× smaller** than the memory-feasible size (~several hundred M). That gap is the whole story.

## 1. The two limits are not the same limit

Training has two independent resource walls. On a laptop they sit at very different places, and confusing them is the usual mistake.

**Memory** — can the model, its gradients, the optimizer state, and one forward/backward pass of activations fit in RAM (or unified memory)?

**Compute** — can the machine execute enough floating-point operations to reach a *trained* state in a wall-clock time you are willing to wait?

For a laptop, compute is the binding wall, by roughly an order of magnitude. You can hold a far bigger model than you can afford to actually optimize.

## 2. Memory accounting

With AdamW in fp32, each parameter drags along four fp32 words of state:

- parameter: 4 bytes
- gradient: 4 bytes
- Adam first moment $m$: 4 bytes
- Adam second moment $v$: 4 bytes

That is **16 bytes/param** for the model + optimizer state, plus activations (which scale with batch size × sequence length × width × depth, and can be traded down with a small batch or gradient checkpointing).

| Model | Params | Training state at 16 bytes/param |
|---|---|---|
| Toy (induction) | ~0.17M | ~3 MB |
| Mini-GPT-2 | ~10M | ~0.16 GB |
| GPT-2 small | 124M | ~2 GB |
| GPT-2 medium | 355M | ~5.7 GB |
| GPT-2 large | 774M | ~12.4 GB |

So a 16 GB budget *holds* the training state of models up to roughly **several hundred M params** (mixed precision pushes this higher; activations and framework overhead pull it back). Memory would let you train GPT-2-large. The clock will not.

## 3. Compute accounting — the wall that actually stops you

A full training run costs, to a good approximation,

$$
C_{\text{train}} \approx 6 N D \tag{1}
$$

where $N$ is the parameter count and $D$ the number of tokens seen (2 FLOPs/param for the forward pass, ~4 for the backward). For a *reasonably trained* language model the compute-optimal token budget is about $D \approx 20 N$ (the Chinchilla ratio).

A 16 GB laptop GPU — Apple-Silicon MPS is the typical case — sustains on the order of **1–3 TFLOP/s of *effective* training throughput**. Use **1e12 FLOP/s** as a conservative planning number (a high-end M-series or a discrete laptop GPU does more; CPU-only is ~10–50× *worse*).

Worked examples at $D \approx 20N$ and 1 TFLOP/s effective:

- **GPT-2 small (124M):** $6 \times 124\text{M} \times 2.5\text{B} \approx 1.9\text{e}18$ FLOPs → ~520 hours ≈ **3 weeks** (~4 days on a fast M-series GPU).
- **Mini-GPT-2 (10M):** $6 \times 10\text{M} \times 200\text{M} \approx 1.2\text{e}16$ FLOPs → ~3 hours at the Chinchilla budget, and **minutes-to-tens-of-minutes** in practice because interpretability studies converge on a small or synthetic corpus long before $20N$ tokens.

## 4. Feasibility by size

| Model | Params | Training state | From-scratch time on a 16 GB laptop | Verdict |
|---|---|---|---|---|
| Toy (the plan's) | ~0.17M | ~3 MB | seconds–minutes | trivial |
| **Mini-GPT-2** | **~5–15M** | ~0.1–0.24 GB | **minutes–~1 hr** | **sweet spot, iterable** |
| Small mini | ~30M | ~0.5 GB | hours–overnight | feasible, slow to iterate |
| **GPT-2 small** | **124M** | ~2 GB | **~3 weeks** | **load pretrained instead** |
| GPT-2 medium | 355M | ~5.7 GB | months | no |

The practical from-scratch ceiling is **~10M params (up to ~30M if patient)**. Above ~50M you are no longer training on a laptop; you are waiting on one.

## 5. The gotcha at small scale: the embedding table dominates

If you shrink the transformer but keep GPT-2's **50,257-token BPE vocabulary**, the token-embedding matrix (of shape vocabulary × width) swallows the parameter budget:

- GPT-2 small spends ~38M of its 124M params (~31%) on the embedding table alone.
- Scale the width down to 384 but keep the 50,257 vocab and the embedding table is still ~19M params — most of a nominal "10M model," leaving almost nothing for the attention circuits you actually want to study.

**Fix: shrink the vocabulary too.** Char-level (vocabulary ~65–256) or a small BPE (~1–8k). Otherwise a small model is mostly an embedding lookup table wearing a transformer costume, and you learn little about attention.

The canonical laptop config is nanoGPT's character-level Shakespeare model (~6 layers, ~6 heads, width ~384, block ~256, vocabulary ~65 → ~10M params, trains in minutes on a GPU). Treat it as the reference point for "the biggest thing you can train from scratch and still iterate on."

## 6. The consequence: a three-rung toy → real ladder

The feasibility math resolves the "should we train GPT-2?" question cleanly. You do not have to. A three-rung ladder gives you the from-scratch *emergence* story where training is cheap, and the real GPT-2 where training is not:

1. **Toy (~0.17M), from scratch** — closed-form ground truth; watch the induction circuit emerge (phase change, seed-permuted head roles). Seconds to train.
2. **Mini-GPT-2 (~10M, small vocab), from scratch** — a real-ish language model on tiny-shakespeare; watch emergence at a more GPT-2-like architecture; minutes-to-~1 hour, still iterable across seeds. This is the middle rung that "understand GPT-2" wants, and it is laptop-native.
3. **GPT-2 small (124M), pretrained** — no training; load the released weights and verify the QK/OV circuit structure (previous-token QK matching, positive-eigenvalue OV copying score, reproduced head dump) on a real model.

Training reproduction of the full 124M model (rented multi-GPU, hours, on the order of tens of dollars of compute) is explicitly *out of scope* — rungs 1–2 supply emergence-from-scratch and rung 3 supplies real GPT-2, all inside 16 GB.

## 7. Assumptions and caveats

- The throughput figure (~1 TFLOP/s effective) is an order-of-magnitude planning estimate for a mid-range 16 GB Apple-Silicon laptop under MPS. A discrete NVIDIA laptop GPU or a high-end M-series does better; CPU-only does much worse. Re-run the $6ND$ arithmetic with your measured tokens/second before committing to a size.
- $D \approx 20N$ is the compute-*optimal* budget for a natural-language LM. Interpretability studies on synthetic or tiny corpora converge with far fewer tokens, so the wall-clock estimates in §3–§4 are conservative upper bounds for that use case.
- Mixed precision (bf16/fp16) roughly halves the memory state and raises throughput, but does not change the conclusion: 124M from scratch is still weeks on a laptop.
- Memory estimates count model + optimizer state only. Activation memory depends on batch × sequence length and is controllable (small batch, gradient checkpointing), so it rarely becomes the binding constraint at these sizes.

## 8. Sources and further reading

These are pointers for the reader to consult, not values verified from source in this note; the accounting in §2–§4 stands on first principles.

- The $6ND$ training-FLOP heuristic — commonly attributed to the scaling-laws work of Kaplan et al. (2020).
- The $D \approx 20N$ compute-optimal token-to-parameter ratio — the Chinchilla result (Hoffmann et al., 2022). (Note: this ratio is Hoffmann et al., *not* Kaplan et al. — the two scaling-law papers reach different optima.)
- nanoGPT (Karpathy) — the canonical laptop-scale from-scratch training recipe and the character-level Shakespeare config referenced in §5.
- GPT-2 architecture and sizes (Radford et al., 2019) — the 124M / 355M / 774M / 1.5B family and the 50,257-token BPE vocabulary.
