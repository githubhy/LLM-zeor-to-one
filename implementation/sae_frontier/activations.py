"""S2 real-model substrate: harvest GPT-2-small residual-stream activations and
compute the cross-entropy loss-recovered metric (survey Section 10.3, Eq 6-3).

`transformers`/`datasets` are imported lazily inside the functions, so this module
imports fine (and G1 unit tests pass) on a box without the model downloaded.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class ActivationConfig:
    model_name: str = "gpt2"          # GPT-2-small, 124M, ungated
    layer: int = 6                    # residual-stream site (resid_post of block `layer`)
    n_sequences: int = 256
    seq_len: int = 128
    seed: int = 0
    device: str = "cpu"


def _resid_hookpoint(model, layer: int):
    # GPT-2: hidden states after block `layer`; captured via output_hidden_states.
    return layer


def harvest_activations(cfg: ActivationConfig):
    """Return (X, meta): residual-stream activations (n_tokens, d_model) from wikitext."""
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast  # lazy
    from datasets import load_dataset  # lazy

    torch.manual_seed(cfg.seed)
    tok = GPT2TokenizerFast.from_pretrained(cfg.model_name)
    tok.pad_token = tok.eos_token  # GPT-2 has no pad token; reuse eos (masked out via attention_mask)
    model = GPT2LMHeadModel.from_pretrained(cfg.model_name).to(cfg.device).eval()
    ds = load_dataset("wikitext", "wikitext-103-raw-v1", split="train", streaming=True)
    texts, acts = [], []
    it = iter(ds)
    while len(texts) < cfg.n_sequences:
        row = next(it)
        t = row["text"].strip()
        if len(t) > 200:
            texts.append(t)
    with torch.no_grad():
        for i in range(0, len(texts), 16):
            batch = texts[i:i + 16]
            enc = tok(batch, return_tensors="pt", truncation=True, max_length=cfg.seq_len,
                      padding="max_length")
            enc = {k: v.to(cfg.device) for k, v in enc.items()}
            out = model(**enc, output_hidden_states=True)
            h = out.hidden_states[cfg.layer + 1]  # +1: hidden_states[0] is the embedding
            mask = enc["attention_mask"].bool()
            acts.append(h[mask].float().cpu())
    X = torch.cat(acts, dim=0)
    return X, {"model": cfg.model_name, "layer": cfg.layer, "d_model": X.shape[1],
               "n_tokens": X.shape[0]}


@torch.no_grad()
def loss_recovered_on_model(sae, cfg: ActivationConfig, n_eval_seqs: int = 64) -> dict:
    """Splice the SAE reconstruction into GPT-2 at `layer` and measure CE loss recovered."""
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast  # lazy
    from datasets import load_dataset  # lazy

    tok = GPT2TokenizerFast.from_pretrained(cfg.model_name)
    tok.pad_token = tok.eos_token  # GPT-2 has no pad token; reuse eos (masked out via attention_mask)
    model = GPT2LMHeadModel.from_pretrained(cfg.model_name).to(cfg.device).eval()
    ds = load_dataset("wikitext", "wikitext-103-raw-v1", split="validation", streaming=True)
    texts = []
    for row in ds:
        if len(row["text"].strip()) > 200:
            texts.append(row["text"].strip())
        if len(texts) >= n_eval_seqs:
            break

    block = model.transformer.h[cfg.layer]
    mode = {"m": "orig"}

    def hook(module, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        if mode["m"] == "recon":
            xh, _ = sae(h.float())
            h = xh.to(h.dtype)
        elif mode["m"] == "zero":
            h = torch.zeros_like(h)
        return (h,) + out[1:] if isinstance(out, tuple) else h

    handle = block.register_forward_hook(hook)
    losses = {"orig": [], "recon": [], "zero": []}
    try:
        for i in range(0, len(texts), 8):
            enc = tok(texts[i:i + 8], return_tensors="pt", truncation=True,
                      max_length=cfg.seq_len, padding="max_length")
            enc = {k: v.to(cfg.device) for k, v in enc.items()}
            labels = enc["input_ids"].clone()
            labels[enc["attention_mask"] == 0] = -100
            for m in ("orig", "recon", "zero"):
                mode["m"] = m
                out = model(**enc, labels=labels)
                losses[m].append(float(out.loss.item()))
    finally:
        handle.remove()
    avg = {m: sum(v) / len(v) for m, v in losses.items()}
    from .metrics import loss_recovered
    return {"ce": avg, "loss_recovered": loss_recovered(avg["orig"], avg["recon"], avg["zero"])}
