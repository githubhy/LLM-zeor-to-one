"""Activation-steering head-to-head on GPT-2-small (Track A3, scaled reproduction of the
AxBench steering-method ranking; decision 2026-07-02-04).

Three steering methods, one shared success/coherence metric (P2-1):
  - prompting        : prepend a natural-language instruction
  - diff_in_means    : add alpha * (mean_pos - mean_neg) residual vector at layer L (CAA / ActAdd)
  - sae_clamp        : train an SAE on layer-L activations, clamp the most concept-selective feature

Concept = sentiment (positive vs negative), self-generated (offline). Success = how much steering
raises target-sentiment token log-prob over the opposite; coherence cost = KL(steered || base).
GPT-2 is cached; the SAE reuses implementation/sae_frontier (build_sae/train_sae)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

POS = [" good", " great", " wonderful", " happy", " love", " excellent", " beautiful",
       " amazing", " joy", " nice", " perfect", " best", " delightful", " fantastic"]
NEG = [" bad", " terrible", " awful", " sad", " hate", " horrible", " ugly", " disgusting",
       " misery", " worst", " nasty", " painful", " gross", " dreadful"]
POS_SENT = ["I feel", "This is", "It was", "The day was", "She looked", "Everything seemed",
            "The news is", "My mood is", "The food tasted", "Life feels"]
NEUTRAL = ["The weather today is", "My opinion of this is", "I think that it is",
           "The situation right now is", "When I woke up I felt", "The report says it is",
           "Overall the experience was", "People say the city is", "The meeting today was",
           "Looking back, it all seems"]


@dataclass
class SteerConfig:
    layer: int = 6
    device: str = "cpu"
    seed: int = 0


class Steerer:
    def __init__(self, cfg: SteerConfig):
        self.cfg = cfg
        self.tok = GPT2TokenizerFast.from_pretrained("gpt2")
        self.tok.pad_token = self.tok.eos_token
        self.model = GPT2LMHeadModel.from_pretrained("gpt2").to(cfg.device).eval()
        self.pos_ids = [self.tok.encode(w)[0] for w in POS if len(self.tok.encode(w)) == 1]
        self.neg_ids = [self.tok.encode(w)[0] for w in NEG if len(self.tok.encode(w)) == 1]

    # ---- activation capture / injection at layer L residual (post-block) ----
    @torch.no_grad()
    def _resid(self, prompts):
        enc = self.tok(prompts, return_tensors="pt", padding=True).to(self.cfg.device)
        out = self.model(**enc, output_hidden_states=True)
        h = out.hidden_states[self.cfg.layer + 1]        # (B,T,d)
        last = enc["attention_mask"].sum(1) - 1
        return h[torch.arange(h.shape[0]), last], enc     # (B,d) last-token resid

    @torch.no_grad()
    def _logits_with_vector(self, prompts, vec=None, alpha=0.0, clamp=None):
        """Run prompts; optionally add alpha*vec (broadcast) at layer L, or clamp an SAE feature.
        Returns next-token logits at the last position (B,V)."""
        enc = self.tok(prompts, return_tensors="pt", padding=True).to(self.cfg.device)
        handle = None
        blk = self.model.transformer.h[self.cfg.layer]
        if vec is not None or clamp is not None:
            def hook(mod, inp, out):
                h = out[0]
                if vec is not None:
                    h = h + alpha * vec.to(h.dtype)
                if clamp is not None:
                    sae, fidx, val = clamp
                    f = sae.encode(h.reshape(-1, h.shape[-1]))
                    f[:, fidx] = val
                    h = sae.decode(f).reshape(h.shape)
                return (h,) + tuple(out[1:])
            handle = blk.register_forward_hook(hook)
        try:
            out = self.model(**enc)
        finally:
            if handle:
                handle.remove()
        last = enc["attention_mask"].sum(1) - 1
        return out.logits[torch.arange(out.logits.shape[0]), last]   # (B,V)

    def diff_in_means_vector(self):
        pos = [f"{s}{w}." for s in POS_SENT for w in POS]
        neg = [f"{s}{w}." for s in POS_SENT for w in NEG]
        hp, _ = self._resid(pos)
        hn, _ = self._resid(neg)
        return (hp.mean(0) - hn.mean(0))               # (d,)

    def sae_clamp_setup(self, steps: int = 1500):
        """Train an SAE on layer-L activations; return (sae, concept_feature_idx). The concept
        feature is the latent whose mean activation most separates positive from negative text."""
        from implementation.sae_frontier.config import SAEConfig, TrainConfig
        from implementation.sae_frontier.saes import build_sae
        from implementation.sae_frontier.train import train_sae
        pos = [f"{s}{w}." for s in POS_SENT for w in POS]
        neg = [f"{s}{w}." for s in POS_SENT for w in NEG]
        hp, _ = self._resid(pos)
        hn, _ = self._resid(neg)
        X = torch.cat([hp, hn], 0).detach()
        sae = build_sae(SAEConfig(variant="topk", d_model=X.shape[1], expansion=4,
                                  seed=self.cfg.seed, k=32))
        train_sae(sae, X, TrainConfig(steps=steps, seed=self.cfg.seed))
        with torch.no_grad():
            fp = sae.encode(hp).mean(0)
            fn = sae.encode(hn).mean(0)
            fidx = int((fp - fn).abs().argmax().item())     # most concept-selective latent
        return sae, fidx

    # ---- metric: sentiment success + coherence cost (KL vs base) ----
    def _sentiment_score(self, logits):
        lp = torch.log_softmax(logits.float(), dim=-1)
        return (lp[:, self.pos_ids].logsumexp(1) - lp[:, self.neg_ids].logsumexp(1))  # (B,)

    @torch.no_grad()
    def evaluate(self, method, strength, sae_clamp=None, vec=None):
        base = self._logits_with_vector(NEUTRAL)
        base_score = self._sentiment_score(base)
        if method == "prompting":
            steered = self._logits_with_vector([f"Write something very positive and cheerful. {p}"
                                                for p in NEUTRAL])
        elif method == "diff_in_means":
            steered = self._logits_with_vector(NEUTRAL, vec=vec, alpha=strength)
        elif method == "sae_clamp":
            steered = self._logits_with_vector(NEUTRAL, clamp=(sae_clamp[0], sae_clamp[1], strength))
        else:
            raise KeyError(method)
        success_per = (self._sentiment_score(steered) - base_score)            # (B,)
        # coherence cost = mean KL(steered || base) over vocab (higher = more disruption)
        pb = torch.log_softmax(base.float(), -1)
        ps = torch.log_softmax(steered.float(), -1)
        kl = (ps.exp() * (ps - pb)).sum(-1).mean().item()
        return {"success": success_per.mean().item(),
                "success_per": success_per.tolist(), "kl": kl}
