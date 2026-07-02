"""FastV vision-token pruning on SmolVLM-256M (Idefics3) — Track B1 (decision 2026-07-02-04).

Reproduces (Chen et al. ECCV 2024): (a) image-token attention efficiency collapses in deep layers,
(b) attention-ranked pruning of image tokens holds accuracy up to a knee, (c) attn-rank > random, and
(d) the Eq-5 FLOP-reduction closed form. Substrate: a real small early-fusion VLM + synthetic
ground-truth images (offline). Pruning is realised by masking the bottom-R% image tokens as keys
(a conservative all-layers approximation of FastV's after-layer-K removal; disclosed §2/§7)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from PIL import Image, ImageDraw
from transformers import AutoProcessor, Idefics3ForConditionalGeneration

REPO = "HuggingFaceTB/SmolVLM-256M-Instruct"
COLORS = {"red": (220, 30, 30), "green": (30, 180, 30), "blue": (30, 30, 220),
          "yellow": (230, 210, 30)}


def make_image(color, shape, size=224, seed=0):
    img = Image.new("RGB", (size, size), (250, 250, 250))
    d = ImageDraw.Draw(img)
    c = COLORS[color]
    m = size // 5
    if shape == "square":
        d.rectangle([m, m, size - m, size - m], fill=c)
    elif shape == "circle":
        d.ellipse([m, m, size - m, size - m], fill=c)
    else:  # triangle
        d.polygon([(size // 2, m), (m, size - m), (size - m, size - m)], fill=c)
    return img


@dataclass
class Example:
    image: Image.Image
    question: str
    answer: str


def synthetic_dataset(n_per=6):
    """Color-identification questions (the model's strongest axis)."""
    rng = np.random.default_rng(0)
    shapes = ["square", "circle", "triangle"]
    exs = []
    for color in COLORS:
        for i in range(n_per):
            shape = shapes[int(rng.integers(len(shapes)))]
            exs.append(Example(make_image(color, shape),
                               "What color is the shape? Answer in one word.", color))
    return exs


class FastVModel:
    def __init__(self, device="cpu"):
        self.device = device
        # longest_edge=768 -> 320 image tokens: enough redundancy for FastV's premise while
        # output_attentions over all 30 layers stays ~0.1 GB (full 1088-token split is ~42 GB;
        # 64-token no-split has too little redundancy — attention-ranked pruning then loses to random).
        self.proc = AutoProcessor.from_pretrained(REPO, do_image_splitting=True,
                                                  size={"longest_edge": 768})
        self.model = Idefics3ForConditionalGeneration.from_pretrained(
            REPO, torch_dtype=torch.float32).to(device).eval()
        self.image_token_id = self.model.config.image_token_id

    def _prep(self, ex: Example):
        msgs = [{"role": "user", "content": [{"type": "image"},
                {"type": "text", "text": ex.question}]}]
        prompt = self.proc.apply_chat_template(msgs, add_generation_prompt=True)
        inp = self.proc(text=prompt, images=[ex.image], return_tensors="pt").to(self.device)
        img_mask = (inp["input_ids"][0] == self.image_token_id)
        return inp, img_mask

    @torch.no_grad()
    def attention_efficiency(self, ex: Example):
        """Per-layer mean attention received by image tokens vs text tokens (Chen Eq 4)."""
        inp, img_mask = self._prep(ex)
        out = self.model(**inp, output_attentions=True)
        eff_img, eff_txt = [], []
        for att in out.attentions:                      # (1, H, T, T)
            a = att[0].mean(0)                           # (T,T) head-averaged; a[q,k]
            recv = a.sum(0)                              # (T,) total attention each key receives
            eff_img.append((recv[img_mask].sum() / img_mask.sum()).item())
            eff_txt.append((recv[~img_mask].sum() / (~img_mask).sum()).item())
        return np.array(eff_img), np.array(eff_txt), int(img_mask.sum())

    @torch.no_grad()
    def _rank_image_tokens(self, attentions, img_mask, layer_K):
        """Avg attention received by each image token at layer K (FastV phi_attn)."""
        a = attentions[layer_K][0].mean(0)               # (T,T)
        recv = a.sum(0)                                  # (T,)
        img_idx = img_mask.nonzero(as_tuple=True)[0]
        return img_idx, recv[img_idx]

    @torch.no_grad()
    def rank(self, ex: Example, K: int):
        """Return (inp, img_idx sorted by ASCENDING layer-K received attention). Cache per (ex,K)."""
        inp, img_mask = self._prep(ex)
        out = self.model(**inp, output_attentions=True)
        img_idx, scores = self._rank_image_tokens(out.attentions, img_mask, K)
        order = scores.argsort()                         # lowest attention first (pruned first)
        return inp, img_idx[order]

    @torch.no_grad()
    def answer(self, inp, drop_idx=None):
        """Single-forward greedy answer; drop_idx image tokens masked as keys. Explicit
        position_ids=arange keeps RoPE correct for the surviving tokens (no cumsum shift)."""
        T = inp["input_ids"].shape[1]
        attn_mask = inp["attention_mask"].clone()
        if drop_idx is not None and len(drop_idx) > 0:
            attn_mask[0, drop_idx] = 0
        pos = torch.arange(T, device=self.device).unsqueeze(0)
        out = self.model(input_ids=inp["input_ids"], attention_mask=attn_mask,
                         pixel_values=inp["pixel_values"], position_ids=pos)
        tok = out.logits[0, -1].argmax().item()
        return self.proc.tokenizer.decode([tok]).strip().lower()

    def predict(self, ex: Example, K=2, R=0.0, criterion="attn"):
        inp, ranked = self.rank(ex, K)
        n_prune = int(R * len(ranked))
        if n_prune == 0:
            return self.answer(inp)
        if criterion == "random":
            g = torch.Generator().manual_seed(0)
            ranked = ranked[torch.randperm(len(ranked), generator=g)]
        return self.answer(inp, ranked[:n_prune])


def flop_reduction(K, R, n_img, n_total, T_layers=30, d=576, m_ff=1536):
    """Chen Eq 5: FLOP reduction from pruning n_img -> (1-R)*n_img image tokens after layer K."""
    def layer_flops(n):
        return 4 * n * d * d + 2 * n * n * d + 2 * n * d * m_ff
    n = n_total
    n_hat = n_total - int(R * n_img)
    full = T_layers * layer_flops(n)
    kept = K * layer_flops(n) + (T_layers - K) * layer_flops(n_hat)
    return 1.0 - kept / full
