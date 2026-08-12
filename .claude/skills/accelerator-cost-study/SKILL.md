---
name: accelerator-cost-study
description: Take an equivalence-proven kernel (or a validated reference implementation) through a real measurement flow on named hardware and produce flow-measured ABSOLUTE cost — latency and its distribution, achieved FLOP/s against the device's peak, HBM bandwidth utilization, arithmetic intensity against the roofline, memory footprint, and energy per token — gated by a pre-registered CONFIRM/REFUTE window against the analytic cost model and anchored to an external published datapoint. Use to convert a reference-implementation-study's RELATIVE cost ranking into absolute ms / TFLOP/s / GB/s / J-per-token on a named accelerator. Accelerator-realization family; consumes kernel-bringup (invoke it as Phase 1 if the kernel is not yet equivalence-proven).
---

# accelerator-cost-study — flow-measured absolute accelerator cost

## When to use

- A `reference-implementation-study` produced a **relative** ranking (this attention variant is
  ~2× cheaper in FLOPs; this quantization halves the KV cache) and you now need **absolute,
  measured** cost on a named device to make an engineering decision.
- A cost claim in a survey rests on a **FLOP or byte count** and has never been measured — the
  gap this skill closes, because FLOPs are not time and byte counts are not bandwidth.

Do NOT use for: a kernel whose correctness is unproven (run `kernel-bringup` first — a fast wrong
kernel measures nothing); a pure accuracy comparison (that is the study's Phase 3); a claim that
only needs the relative ranking the study already produced.

## Phase 1 — equivalence-proven kernel (prerequisite)

Cost is only meaningful for a kernel that computes the right thing. If the kernel is not yet proven
against a deterministic reference within a derived bound, run `kernel-bringup` first. A measured
speedup over a baseline that computes something *else* is the most common way this study produces a
confident wrong number.

## Environment — the part that costs hours if rediscovered

Pin and record, in the artifact, before any measurement:

- **Device**: exact accelerator and memory (`A100-SXM4-80GB`, `H100-PCIe-80GB`, `RTX 4090`), driver,
  CUDA/ROCm version, and the **clock state** — a thermally-throttled or power-capped device produces
  a reproducible wrong number. Record `nvidia-smi -q` power limit and the achieved clock during the
  run, not just the nominal boost clock.
- **Stack**: torch version, the kernel toolchain (Triton/CUTLASS/cuBLAS version), and whether TF32 /
  flash-attention backends are enabled. These change the baseline silently between releases.
- **Peak references**: the device's *dense* peak FLOP/s **for the dtype actually used** and its HBM
  peak bandwidth, both read from the vendor datasheet, never recalled (`.claude/rules/citation-integrity.md`).
  Quoting a bf16-sparse peak against a bf16-dense measurement inflates the "% of peak" figure by 2×.
- **Measurement protocol**: warmup iterations, measured iterations, CUDA-graph or not, and
  `torch.cuda.synchronize()` placement. A timing loop without synchronization measures queue-submit
  latency, which is fast and meaningless.

## Phases (2 onward)

2. **Latency — the load-bearing measurement.** Per (kernel × shape × dtype): warm up, then time N
   iterations with explicit synchronization and report the **distribution** (median, p90, min), never
   a single mean. Sweep the shape axis the decision turns on — sequence length, batch, head count,
   group size. Report each against its pre-registered window. Hold everything else fixed and say so.
3. **Achieved FLOP/s and bandwidth against the roofline.** Compute the kernel's *algorithmic* FLOPs
   and bytes analytically (the survey's cost model), divide by measured time, and place the point on
   a roofline for the named device. The load-bearing output is **which side of the ridge the kernel
   sits on**: a memory-bound kernel at 8% of peak FLOP/s is not underperforming, and "optimizing" its
   arithmetic is wasted work. Use a profiler (Nsight Compute, `torch.profiler`) to confirm the
   analytic byte count against measured DRAM traffic — a large gap is a cache-behavior finding, not a
   rounding error.
4. **Memory footprint.** Peak allocated and peak reserved (`torch.cuda.max_memory_allocated` /
   `_reserved`), plus the KV-cache footprint as a closed form in (batch, sequence, layers, KV heads,
   head dim, dtype) so it extrapolates. Reserved-vs-allocated is the allocator's fragmentation and
   belongs in the report — it is what actually OOMs a deployment.
5. **Energy.** Sample board power during a sustained run (`nvidia-smi --query-gpu=power.draw` at a
   stated interval, or NVML) and integrate over the measured window to get **joules per token** (or
   per sequence). Disclose that this is **board** power, not silicon; that it includes idle draw
   between kernels unless you subtract a measured floor; and the sampling interval, since a short
   kernel is invisible to a coarse sampler. State the worst-case nature explicitly.
6. **Verdict + external anchor.** Compute the ratios; apply the **pre-registered CONFIRM/REFUTE**
   windows. The **comparison basis matters** — compare on the cost model's own basis (a
   FLOP-count-derived prediction must be compared against a compute-bound measurement, not a
   memory-bound one), and report a **bracket, not a point**. Acquire ≥1 **external published**
   datapoint for the same kernel class on comparable hardware (`source-fetch`) and bracket your
   absolutes against it.

## Gotchas

- Say it explicitly: **"the ratios transfer across devices; the absolutes carry the
  this-device-this-stack caveat"** — the ranking is load-bearing, the absolute ms/J are estimates
  tied to one clock state and one library version.
- **The baseline is under test too** (`.claude/rules/sim-report-completeness.md` `[opt:SIM-BASELINE]`).
  A "3× faster than PyTorch" claim measured against an eager, unfused, fp32 baseline with TF32
  disabled is measuring the baseline's handicap. Run the baseline at *its* best available setting and
  say what that was.
- **Autotuning is part of the measurement.** A Triton kernel timed on its first (unautotuned) config
  is not the kernel anyone would ship. Record whether autotuning ran and whether its cache was warm.
- **Small shapes measure launch overhead.** Below a few tens of microseconds the kernel launch and
  Python dispatch dominate; report those points as overhead-dominated rather than as kernel cost, or
  use CUDA graphs and say so.
- Disclose every silent cap: shapes not swept, dtypes not measured, the single device, and the fact
  that a single-stream microbenchmark is not serving throughput under batching and preemption.

## Output / acceptance

`sim/<study>/perf/`: run scripts + `{latency,roofline,memory,energy}_<device>.json`, raw
per-iteration timings retained (not just summaries). **Acceptance:** the measured ratios + a
CONFIRM/REFUTE verdict against the pre-registered window, the roofline placement with the analytic
and profiled byte counts reconciled, the memory closed form, the energy absolutes with their
disclosed basis, and the external-anchor sanity check. Then fold into the study report (§6) + the
parent survey (§ cost-model / tradeoffs), and run **`results-reconciliation`** if the docs accreted
the results incrementally.

## Chaining

`reference-implementation-study` → [`kernel-bringup`] → **`accelerator-cost-study`** →
`results-reconciliation` (doc consistency) ; `citation-audit` on the external anchor.
