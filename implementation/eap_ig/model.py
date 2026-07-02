"""GPT-2 residual-stream node harness (no TransformerLens; raw `transformers` + hooks).

Node granularity: `embed`, each attention head `a{l}.h{head}`, each MLP `m{l}` — the additive
contributions to the residual stream (Elhage et al. 2021). Three services:

  forward_cache : per-node output contributions z_u  (B,T,d)   [clean or corrupt run]
  forward_grad  : per-node output-point gradients g_u = dL/dz_u  (B,T,d), optional IG path
  patched_logits: single-pass circuit intervention — out-of-circuit node outputs -> corrupt

Correctness key: a node's OUTPUT gradient equals the residual gradient where it writes, so all
heads of a layer share dL/d(attn_out[l]); per-head discrimination lives in Δz_u (the head's
contribution), not the gradient. Verified by the G1 decomposition-invariant test.
"""
from __future__ import annotations

import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

from .config import ModelConfig


def node_names(n_layer: int, n_head: int) -> list[str]:
    names = ["embed"]
    for l in range(n_layer):
        names += [f"a{l}.h{h}" for h in range(n_head)]
        names.append(f"m{l}")
    return names


class Model:
    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        self.tok = GPT2TokenizerFast.from_pretrained(cfg.name)
        self.tok.pad_token = self.tok.eos_token
        dtype = {"float32": torch.float32, "float16": torch.float16,
                 "bfloat16": torch.bfloat16}[cfg.dtype]
        self.model = GPT2LMHeadModel.from_pretrained(cfg.name, torch_dtype=dtype).to(cfg.device).eval()
        c = self.model.config
        self.n_layer, self.n_head, self.d_model = c.n_layer, c.n_head, c.n_embd
        self.d_head = self.d_model // self.n_head
        self.names = node_names(self.n_layer, self.n_head)
        self.blocks = self.model.transformer.h

    # ---- per-head decomposition of an attention output --------------------------
    def _split_heads(self, merged: torch.Tensor, block) -> torch.Tensor:
        """merged (B,T,d) = c_proj input -> per-head residual contributions (B,T,H,d)."""
        W = block.attn.c_proj.weight            # (d, d) Conv1D: y = x @ W + b
        B, T, d = merged.shape
        mh = merged.view(B, T, self.n_head, self.d_head)          # (B,T,H,dh)
        Wh = W.view(self.n_head, self.d_head, d)                  # (H, dh, d)
        # contribution_h = mh[...,h,:] @ Wh[h]  -> (B,T,H,d)
        return torch.einsum("bthk,hkd->bthd", mh, Wh)

    # ---- clean/corrupt cache of node output contributions -----------------------
    @torch.no_grad()
    def forward_cache(self, ids, mask):
        contribs: dict[str, torch.Tensor] = {}
        merged: dict[int, torch.Tensor] = {}
        handles = []

        def cproj_pre(l):
            def hook(mod, inp):
                merged[l] = inp[0].detach()
            return hook

        def mlp_out(l):
            def hook(mod, inp, out):
                contribs[f"m{l}"] = out.detach()
            return hook

        def embed_out(mod, inp, out):
            contribs["embed"] = out.detach()

        handles.append(self.model.transformer.drop.register_forward_hook(embed_out))
        for l, blk in enumerate(self.blocks):
            handles.append(blk.attn.c_proj.register_forward_pre_hook(cproj_pre(l)))
            handles.append(blk.mlp.register_forward_hook(mlp_out(l)))
        try:
            logits = self.model(ids, attention_mask=mask).logits
        finally:
            for h in handles:
                h.remove()
        for l, blk in enumerate(self.blocks):
            heads = self._split_heads(merged[l], blk)   # (B,T,H,d)
            for h in range(self.n_head):
                contribs[f"a{l}.h{h}"] = heads[:, :, h, :].contiguous()
        return logits, contribs

    # ---- output-point gradients dL/dz_u (single pass or IG path) ----------------
    def forward_grad(self, ids, mask, metric_fn, sign=-1.0,
                     ig_steps=1, corrupt_embed=None, clean_embed=None):
        """Return {node: dL/d(output point)} averaged over ig_steps interp points.

        L = sign * metric (sign=-1 -> loss). For EAP (ig_steps=1) uses the clean token
        embeddings. For EAP-IG pass ig_steps=m, corrupt_embed=z', clean_embed=z (INPUT token
        embeddings); the gradient is captured at the embed node (drop output = wte+wpe),
        attn_out[l], and mlp_out[l], and averaged over the m straight-line interp points.

        Endpoints are detached (constants): IG interpolates embedding VALUES, and we want the
        gradient w.r.t. the running residual, not w.r.t. the embedding matrix."""
        acc: dict[str, torch.Tensor] = {}
        wte = self.model.transformer.wte
        z_clean = (clean_embed if clean_embed is not None else wte(ids)).detach()
        z_corrupt = corrupt_embed.detach() if corrupt_embed is not None else None

        for k in range(1, ig_steps + 1):
            if ig_steps == 1 or z_corrupt is None:
                inp_embed = z_clean.clone()
            else:
                alpha = k / ig_steps
                inp_embed = (z_corrupt + alpha * (z_clean - z_corrupt)).clone()
            inp_embed = inp_embed.requires_grad_(True)   # leaf token embeddings
            grads: dict[str, torch.Tensor] = {}
            handles = []

            def grab(name):
                def fwd(mod, inp, out):
                    o = out[0] if isinstance(out, tuple) else out
                    o.retain_grad()
                    grads[name] = o
                return fwd
            # embed-node output = drop(wte+wpe); its grad is dL/d(h_0)
            handles.append(self.model.transformer.drop.register_forward_hook(grab("embed")))
            for l, blk in enumerate(self.blocks):
                handles.append(blk.attn.register_forward_hook(grab(f"attn{l}")))
                handles.append(blk.mlp.register_forward_hook(grab(f"m{l}")))
            try:
                out = self.model(inputs_embeds=inp_embed, attention_mask=mask)
                loss = sign * metric_fn(out.logits).mean()
                self.model.zero_grad(set_to_none=True)
                loss.backward()
            finally:
                for h in handles:
                    h.remove()
            step = {"embed": grads["embed"].grad.detach()}
            for l in range(self.n_layer):
                ga = grads[f"attn{l}"].grad.detach()   # shared across heads of layer l
                for h in range(self.n_head):
                    step[f"a{l}.h{h}"] = ga
                step[f"m{l}"] = grads[f"m{l}"].grad.detach()
            for name, g in step.items():
                acc[name] = g if name not in acc else acc[name] + g
        return {k: v / ig_steps for k, v in acc.items()}, z_clean

    # ---- circuit intervention: out-of-circuit node outputs -> corrupt -----------
    @torch.no_grad()
    def patched_logits(self, ids, mask, corrupt_contribs, in_circuit):
        """Single forward pass; out-of-circuit node outputs replaced by corrupt cache."""
        handles = []
        merged: dict[int, torch.Tensor] = {}

        def embed_hook(mod, inp, out):
            return out if "embed" in in_circuit else corrupt_contribs["embed"].to(out.dtype)

        def cproj_pre(l):
            def hook(mod, inp):
                merged[l] = inp[0]
            return hook

        def attn_hook(l):
            def hook(mod, inp, out):
                blk = self.blocks[l]
                heads = self._split_heads(merged[l], blk)         # (B,T,H,d) live/clean
                rebuilt = out[0].clone()
                # attn_out = sum_h contrib_h + bias; rebuild sum with per-head choice
                total = torch.zeros_like(rebuilt)
                for h in range(self.n_head):
                    name = f"a{l}.h{h}"
                    ch = heads[:, :, h, :] if name in in_circuit else corrupt_contribs[name].to(rebuilt.dtype)
                    total = total + ch
                bias = blk.attn.c_proj.bias
                new_out = total + bias
                return (new_out,) + tuple(out[1:])
            return hook

        def mlp_hook(l):
            def hook(mod, inp, out):
                name = f"m{l}"
                return out if name in in_circuit else corrupt_contribs[name].to(out.dtype)
            return hook

        handles.append(self.model.transformer.drop.register_forward_hook(embed_hook))
        for l, blk in enumerate(self.blocks):
            handles.append(blk.attn.c_proj.register_forward_pre_hook(cproj_pre(l)))
            handles.append(blk.attn.register_forward_hook(attn_hook(l)))
            handles.append(blk.mlp.register_forward_hook(mlp_hook(l)))
        try:
            logits = self.model(ids, attention_mask=mask).logits
        finally:
            for h in handles:
                h.remove()
        return logits
