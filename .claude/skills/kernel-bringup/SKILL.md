---
name: kernel-bringup
description: Turn a validated reference implementation of an LLM operator into an optimized/fused kernel (Triton, CUDA, torch.compile, a custom attention or quantized matmul) proven numerically equivalent to a deterministic golden reference — a stated, derived error bound over seeded golden vectors, not an eyeballed `allclose`. Use after a reference-implementation-study (or any validated numerical model) when you need a fast kernel whose equivalence to the *studied algorithm* is provable. Accelerator-realization family; also the first phase of accelerator-cost-study — invoke it directly when you only need the kernel + equivalence, not the measurement flow.
---

# kernel-bringup — a fast kernel proven equivalent to its reference

## When to use

- A reference implementation is validated (its accuracy/eval battery passes) and you now need an
  **optimized kernel** of it — a fused attention, a quantized matmul, a custom sampler, a paged
  KV-cache read.
- You must be able to **prove** the kernel computes the studied algorithm — a golden-vector
  equivalence within a *derived* bound, not a "looks right" eyeball or a default `allclose`.

Do NOT use for: an unvalidated algorithm (validate first); a kernel with no reference oracle to
check against; pure latency/throughput exploration (that is `accelerator-cost-study`).

## The core idea — the deterministic reference IS the spec

Floating-point addition is not associative, so a fast kernel and its reference disagree *by
construction*: a tiled/split-K reduction sums in a different order than a sequential one, and on
GPUs the order is not even fixed run-to-run (atomics, split-K scheduling, cuBLAS algorithm
selection). This is why a bare `torch.allclose(fast, ref)` with library-default tolerances proves
almost nothing — it passes for a kernel that is wrong in a way smaller than the slop, and it fails
for a kernel that is right.

The fix is the same move the integer-golden trick makes in fixed-point hardware: **remove the
ambiguity from the reference.** Build a *deterministic* golden — fixed reduction order, fixed
dtype (accumulate in float64, or in float32 with an explicitly sequential reduction), no
nondeterministic kernels, no TF32 — that mirrors the algorithm operation-for-operation. That
reference has exactly one answer for a given input, so it **becomes the equivalence spec**, and the
tolerance you compare against stops being a library default and becomes a **derived bound**: for a
reduction of length $n$ in precision with unit roundoff $u$, the worst-case relative error grows
like $n u$ (and like $\sqrt{n}\,u$ under a random-walk model), so a tolerance is *computed from the
shape*, not guessed. Cross-checking the deterministic reference against the validated model ties it
back to the studied algorithm; the fast kernel then has an unambiguous, machine-checkable oracle.

## Workflow

1. **Pin the numerical contract** and write it to a `formats.json` the kernel and golden share:
   input/output dtypes (bf16 / fp16 / fp8-e4m3 / int4 group size), the **accumulator** dtype, the
   reduction order and tile shape, whether TF32 is permitted, the softmax scaling and max-subtraction
   convention, any denormal/clamping rule, and the RNG contract for a stochastic kernel. This is the
   contract between the reference and the kernel.
2. **Build the deterministic reference** (float64 accumulation, sequential reduction, deterministic
   algorithms enabled) and VALIDATE it three ways: (a) cross-check against the validated model on a
   large seeded set; (b) re-run the algorithm's accuracy/eval battery on the reference's output
   stream; (c) confirm the structural extremes hit their closed form exactly — a fully-masked
   attention row is exactly the mask value, a one-hot softmax is exactly 1, an all-equal-logits
   softmax is exactly uniform, a zero-length sequence does not NaN.
3. **Derive the tolerance before running anything.** State it as a formula in the shape
   (sequence length, head dim, group size, tile width) and the dtype's unit roundoff, and record the
   derivation. A tolerance chosen *after* seeing the mismatch is a fitted parameter, not a bound.
4. **Emit the artifacts** the kernel consumes: seeded golden input/output tensors (saved, not
   regenerated), any quantization scales/zero-points, and key per-stage intermediates (pre-softmax
   scores, row max, row sum) so a future mismatch is localisable to a stage rather than to "the
   kernel".
5. **Equivalence harness**: replay the golden vectors through the kernel and assert the output is
   within the derived bound, elementwise **and** in the aggregate statistic the algorithm actually
   cares about (max abs error, max rel error, and the downstream metric — logit ranking, top-k
   membership, sampled-token agreement under a fixed seed). Include the structural-extreme probes.
   Report the measured max error against the bound, never a bare pass/fail.

## Gotchas

- **The float-order identity holds only while the accumulator has headroom.** bf16 accumulation over
  a long reduction loses low-order bits catastrophically; the derived bound must use the *accumulator*
  dtype, not the storage dtype, and a kernel that accumulates in the storage dtype is a different
  algorithm, not a faster one. Cap and disclose the shapes the bound covers.
- **Determinism is not the default.** Set `torch.use_deterministic_algorithms(True)`, disable TF32
  (`torch.backends.cuda.matmul.allow_tf32 = False`), and pin the cuBLAS workspace before believing
  any repeat comparison. Two runs of the *same* kernel differing is a rig problem, and if you have
  not proven repeats are identical you cannot attribute a reference mismatch to the kernel.
- **Keep the kernel unfused for the equivalence gate where you can.** Equivalence is *arithmetic*;
  fusion, pipelining, and autotuning are `accelerator-cost-study`'s job. Prove the math first, then
  optimize against a green gate.
- **Validate indexing over all inputs including measure-zero edges** — a causal mask at the diagonal,
  a sequence length exactly equal to the tile width, the last partial tile, a group-size boundary in
  a quantized matmul, an empty KV page. Random inputs miss exactly these.
- **A quantized kernel has two oracles, not one**: the dequantized-reference result (does the kernel
  match the quantization scheme it claims?) and the full-precision result (how much did quantization
  cost?). Do not let the second stand in for the first — a kernel with a wrong scale can still look
  "close to fp16" on an easy input.

## Output / acceptance

A kernel source tree (kernel + shared primitives + the equivalence harness + a run script) and a
`golden/` directory (`formats.json`, seeded golden tensors, quantization parameters, a
`crosscheck.json` recording reference-vs-model agreement and the **derived tolerance with its
derivation**). **Acceptance:** measured max error is within the derived bound over the full vector
set including the extremes, repeats are bit-identical under the determinism settings, the
deterministic reference is cross-checked to the validated model, and the accuracy/eval battery is
preserved on the kernel's output stream.

## Chaining

`deep-research-survey` → `reference-implementation-study` → **`kernel-bringup`** →
`accelerator-cost-study`.
