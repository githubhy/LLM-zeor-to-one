"""Edge-level gradient surface: per-(head, q/k/v)-slot residual-input gradients via autograd.

Hanna Eq 1/3 take the gradient w.r.t. the INPUT of the downstream node. For an attention head's
q/k/v the "input" is the residual stream read by that projection; the three slots share the
residual but differ by weight slice, so the three gradients differ. TransformerLens gets these
with `split_qkv_input` (a per-head residual copy per slot); we replicate it on raw `transformers`
GPT-2 by reimplementing ONLY the attention q/k/v-from-copies path (reusing the model's ln_1 /
ln_2 / ln_f / mlp / c_proj / lm_head modules, so the forward reproduces the real model's logits —
verified by `logits_match`). Each destination slot reads a grad-retained copy of the residual, so
autograd yields the residual-space gradient (LayerNorm included) with one backward pass.

Direction & sign follow the node engine: L = sign * metric (sign=-1 -> loss); edge activation
difference is (z'_u - z_u) = corrupt - clean from Model.forward_cache. IG integrates the gradient
over m straight-line points between corrupt and clean INPUT-embedding endpoints (Hanna Eq 3);
the activation difference is the endpoint difference, not interpolated.
"""
from __future__ import annotations

import math

import torch

from .edges import dest_slots, SLOTS


class EdgeModel:
    def __init__(self, model):
        self.M = model
        m = model.model
        self.wte = m.transformer.wte
        self.wpe = m.transformer.wpe
        self.blocks = m.transformer.h
        self.ln_f = m.transformer.ln_f
        self.lm_head = m.lm_head
        self.L, self.H, self.d = model.n_layer, model.n_head, model.d_model
        self.dh = self.d // self.H
        self.device = model.cfg.device

    # ---- reimplemented forward with per-slot residual copies --------------------
    def _forward(self, inp_embed, mask, retain=True):
        """inp_embed (B,T,d) token embeddings (leaf). Returns (logits, copies) where copies maps
        each dest slot -> the grad-retained residual copy it reads. If retain=False, no copies are
        made (used by logits_match to check faithfulness of the reimplementation)."""
        B, T, d = inp_embed.shape
        pos = torch.arange(T, device=inp_embed.device)
        h = inp_embed + self.wpe(pos)[None]          # drop is identity in eval
        copies: dict[str, torch.Tensor] = {}
        # additive masks
        neg = torch.finfo(h.dtype).min
        causal = torch.tril(torch.ones(T, T, dtype=torch.bool, device=h.device))
        pad = None if mask is None else (1.0 - mask[:, None, None, :].to(h.dtype)) * neg

        for l, blk in enumerate(self.blocks):
            attn = blk.attn
            Wq, Wk, Wv = attn.c_attn.weight.split(d, dim=1)     # each (d, d)
            bq, bk, bv = attn.c_attn.bias.split(d, dim=0)       # each (d,)
            qkv = []
            for name, W, b in (("q", Wq, bq), ("k", Wk, bk), ("v", Wv, bv)):
                if retain:
                    # ci is derived from h (which requires grad) -> a NON-LEAF; retain_grad()
                    # to populate .grad = dL/d(residual read by this slot). Per-head grad is
                    # sliced from the (B,T,H,d) tensor later.
                    ci = h[:, :, None, :].expand(B, T, self.H, d).clone()
                    ci.retain_grad()
                    copies[f"__{name}{l}"] = ci
                else:
                    ci = h[:, :, None, :].expand(B, T, self.H, d)
                cn = blk.ln_1(ci)                                # (B,T,H,d) LN over last dim
                Wh = W.view(d, self.H, self.dh)                  # columns -> (head, head_dim)
                x = torch.einsum("bthd,dhe->bthe", cn, Wh) + b.view(self.H, self.dh)
                qkv.append(x.permute(0, 2, 1, 3))                # (B,H,T,dh)
            q, k, v = qkv
            scores = (q @ k.transpose(-1, -2)) / math.sqrt(self.dh)
            scores = torch.where(causal, scores, torch.full_like(scores, neg))
            if pad is not None:
                scores = scores + pad
            a = torch.softmax(scores, dim=-1) @ v                # (B,H,T,dh)
            a = a.permute(0, 2, 1, 3).reshape(B, T, d)
            attn_out = attn.c_proj(a)
            h = attn_out + h                                     # post-attn residual

            if retain:
                mi = h.clone(); mi.retain_grad()
                copies[f"m{l}.in"] = mi
                h = h + blk.mlp(blk.ln_2(mi))
            else:
                h = h + blk.mlp(blk.ln_2(h))

        if retain:
            li = h.clone(); li.retain_grad()
            copies["logits"] = li
            logits = self.lm_head(self.ln_f(li))
        else:
            logits = self.lm_head(self.ln_f(h))
        return logits, copies

    @torch.no_grad()
    def logits_match(self, ids, mask):
        """Max abs diff between the reimplemented forward and the real model (faithfulness gate)."""
        emb = self.wte(ids)
        mine, _ = self._forward(emb, mask, retain=False)
        real = self.M.model(ids, attention_mask=mask).logits
        return (mine - real).abs().max().item()

    # ---- recursive edge-ablation forward (Hanna 2024 §2) ------------------------
    @torch.no_grad()
    def patched_logits_edges(self, batch, circuit_edges):
        """Edge-level circuit intervention. input(v) = Σ_e [i_e z_u + (1-i_e) z'_u]; equivalently
        base_residual + Σ_{(u,v) out-of-circuit} (z'_u - z_u_current). z'_u = corrupt-run output
        (cached); z_u_current = this-forward output (recursive corruption). circuit_edges = set of
        (u, v) in-circuit. All-in == clean; all-out == corrupt (verified)."""
        from .edges import upstream_sources, SLOTS as _S
        M = self.M
        _, zc = M.forward_cache(batch.corrupt_ids, batch.attn_mask)     # z'_u corrupt outputs
        ids, mask = batch.clean_ids, batch.attn_mask
        circ = circuit_edges if isinstance(circuit_edges, set) else set(circuit_edges)
        B, T = ids.shape
        d, Hh, dh = self.d, self.H, self.dh
        emb = self.wte(ids)
        pos = torch.arange(T, device=ids.device)
        h = emb + self.wpe(pos)[None]
        zcur = {"embed": h}                                            # current source outputs
        neg = torch.finfo(h.dtype).min
        causal = torch.tril(torch.ones(T, T, dtype=torch.bool, device=h.device))
        pad = None if mask is None else (1.0 - mask[:, None, None, :].to(h.dtype)) * neg

        def correction(v, ups):
            """Σ_{u in ups : (u,v) out-of-circuit} (z'_u - z_u_current)."""
            c = torch.zeros_like(h)
            for u in ups:
                if (u, v) not in circ:
                    c = c + (zc[u] - zcur[u])
            return c

        for l, blk in enumerate(self.blocks):
            attn = blk.attn
            ups = upstream_sources(f"a{l}.h0.q", self.L, self.H)       # shared across heads/slots
            Wsplit = attn.c_attn.weight.split(d, dim=1)
            bsplit = attn.c_attn.bias.split(d, dim=0)
            qkv = []
            for si, name in enumerate(_S):
                W, b = Wsplit[si], bsplit[si]
                ci = h[:, :, None, :].expand(B, T, Hh, d).clone()
                for hd in range(Hh):
                    ci[:, :, hd, :] = h + correction(f"a{l}.h{hd}.{name}", ups)
                cn = blk.ln_1(ci)
                x = torch.einsum("bthd,dhe->bthe", cn, W.view(d, Hh, dh)) + b.view(Hh, dh)
                qkv.append(x.permute(0, 2, 1, 3))
            q, k, v = qkv
            scores = (q @ k.transpose(-1, -2)) / math.sqrt(dh)
            scores = torch.where(causal, scores, torch.full_like(scores, neg))
            if pad is not None:
                scores = scores + pad
            a = torch.softmax(scores, dim=-1) @ v
            a = a.permute(0, 2, 1, 3).reshape(B, T, d)
            attn_out = attn.c_proj(a)
            # per-head current contributions (before adding bias, matching forward_cache split)
            heads = M._split_heads(a, blk)                              # (B,T,H,d)
            for hd in range(Hh):
                zcur[f"a{l}.h{hd}"] = heads[:, :, hd, :].contiguous()
            h = attn_out + h
            ups_m = upstream_sources(f"m{l}.in", self.L, self.H)
            mi = h + correction(f"m{l}.in", ups_m)
            mlp_out = blk.mlp(blk.ln_2(mi))
            zcur[f"m{l}"] = mlp_out
            h = h + mlp_out
        ups_lg = upstream_sources("logits", self.L, self.H)
        li = h + correction("logits", ups_lg)
        return self.lm_head(self.ln_f(li))

    # ---- per-slot residual-input gradients (one bwd, IG-averaged) ---------------
    def forward_grad_edges(self, ids, mask, metric_fn, sign=-1.0, ig_steps=1,
                           corrupt_embed=None, clean_embed=None):
        """Returns {dest_slot: g (B,T,d)} = mean over IG points of dL/d(residual read by slot)."""
        z_clean = (clean_embed if clean_embed is not None else self.wte(ids)).detach()
        z_corrupt = corrupt_embed.detach() if corrupt_embed is not None else None
        acc: dict[str, torch.Tensor] = {}
        for kstep in range(1, ig_steps + 1):
            if ig_steps == 1 or z_corrupt is None:
                inp = z_clean.clone()
            else:
                alpha = kstep / ig_steps
                inp = (z_corrupt + alpha * (z_clean - z_corrupt)).clone()
            inp = inp.requires_grad_(True)
            logits, copies = self._forward(inp, mask, retain=True)
            loss = sign * metric_fn(logits).mean()
            self.M.model.zero_grad(set_to_none=True)
            loss.backward()
            step = {}
            for v in dest_slots(self.L, self.H):
                if v.endswith((".q", ".k", ".v")):
                    body, s = v.rsplit(".", 1)
                    l = int(body[1:].split(".")[0]); hd = int(body.split(".h")[1])
                    step[v] = copies[f"__{s}{l}"].grad[:, :, hd, :].detach()
                else:
                    step[v] = copies[v].grad.detach()
            for name, g in step.items():
                acc[name] = g if name not in acc else acc[name] + g
        return {k: v / ig_steps for k, v in acc.items()}
