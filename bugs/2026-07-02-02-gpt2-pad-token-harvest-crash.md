---
id: 2026-07-02-02
title: S2 GPT-2 activation harvest crashes — tokenizer has no pad token
severity: med
status: fixed
date: 2026-07-02
component: implementation/sae_frontier/activations.py
---

## Symptom
`run_s2` (GPT-2 realism substrate) crashed at harvest with
`ValueError: Asking to pad but the tokenizer does not have a padding token`.

## Root cause
`activations.harvest_activations` / `loss_recovered_on_model` call the tokenizer with
`padding="max_length"`, but GPT-2's `GPT2TokenizerFast` ships **no pad token** (GPT-2 was trained
without padding). HuggingFace raises rather than guessing.

## Fix
Set `tok.pad_token = tok.eos_token` after loading the tokenizer (both functions); padded positions
are masked out via `attention_mask`, so reusing eos is correct. Commit SHA on landing.

## Regression test
none — an integration path requiring the GPT-2 download; covered by S2 now completing. The unit
suite (S1 substrate) does not touch `transformers`.

## Refs
- Report `docs/sae-frontier-implementation-study.md` Sec. 6.1 (S2). Field note: session `sae-frontier`.
