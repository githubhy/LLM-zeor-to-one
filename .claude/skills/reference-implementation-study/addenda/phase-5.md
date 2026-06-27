# Proposed-mode addendum — Phase 5 (load on demand)

Apply iff `proposed` is set OR `P2-3` is in the active `flags` set.

**[P2-3] Reduced-precision design-of-experiments (not a single bit-width knob).** The baseline
sweeps one precision knob; that cannot answer "which quantization scheme degrades most
gracefully." Instead run a precision DoE: sweep **bit-width x quantization-structure** (>=2
structures from the domain list — e.g. per-tensor vs per-channel vs per-group/block scaling;
symmetric vs asymmetric; weight-only vs weight+activation quantization; or, for a quantized
attention / FFN block, round-to-nearest vs GPTQ vs AWQ) with saturation-aware (clipping-aware)
quantization, and quantify graceful-degradation (e.g. accuracy or perplexity vs bit-width slope
per structure). Where the candidate trains, contrast quantization-aware training (QAT) vs
post-training quantization (PTQ). Persist the full sweep grid as an artifact; flag any saturation
(clipping/overflow) events.
