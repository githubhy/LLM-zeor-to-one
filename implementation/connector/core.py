"""Connector ablation (Track B2): MLP-projector vs Q-Former bridge at matched token budget `q`,
on FROZEN SmolVLM-256M SigLIP patch features (1024×768). Task = classify a synthetic image's color
(coarse) and shape (detail-sensitive). Tests the survey §3.3 fidelity-vs-budget tradeoff at toy
scale (decision 2026-07-02-04): does the learned Q-Former pooling preserve fine detail at low q
better than avg-pool + MLP, and how does the detail axis (shape) scale with q vs the coarse axis
(color)?"""
from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageDraw
from transformers import AutoProcessor, Idefics3ForConditionalGeneration

REPO = "HuggingFaceTB/SmolVLM-256M-Instruct"
COLORS = {"red": (220, 30, 30), "green": (30, 180, 30), "blue": (30, 30, 220), "yellow": (230, 210, 30)}
SHAPES = ["square", "circle", "triangle"]


def _draw(d, box, color, shape):
    c = COLORS[color]
    cx = (box[0] + box[2]) // 2
    if shape == "square":
        d.rectangle(box, fill=c)
    elif shape == "circle":
        d.ellipse(box, fill=c)
    else:
        d.polygon([(cx, box[1]), (box[0], box[3]), (box[2], box[3])], fill=c)


def make_image(left_color, right_color, shape="circle", size=224, jitter=0):
    """TWO shapes: `left_color` in the left half, `right_color` in the right half. Recovering each
    side's colour is the spatial-BINDING label a global/raster pool cannot separate (left+right mix
    within each raster row-strip), but a 2D-aware learned Q-Former can."""
    img = Image.new("RGB", (size, size), (250, 250, 250))
    d = ImageDraw.Draw(img)
    s = size // 5
    ly = size // 2 + jitter
    _draw(d, [size // 4 - s, ly - s, size // 4 + s, ly + s], left_color, shape)
    _draw(d, [3 * size // 4 - s, ly - s, 3 * size // 4 + s, ly + s], right_color, shape)
    return img


def gen_dataset(n_per_combo, seed):
    """Label = (left_color, right_color) — both need spatial binding (which side is which colour)."""
    rng = np.random.default_rng(seed)
    colors = list(COLORS); imgs, cy, sy = [], [], []
    combos = [(lc, rc) for lc in range(len(colors)) for rc in range(len(colors))]
    for (lc, rc) in combos:
        for _ in range(n_per_combo):
            shape = SHAPES[int(rng.integers(len(SHAPES)))]
            imgs.append(make_image(colors[lc], colors[rc], shape, jitter=int(rng.integers(-6, 7))))
            cy.append(lc); sy.append(rc)
    return imgs, torch.tensor(cy), torch.tensor(sy)


@torch.no_grad()
def extract_features(imgs, device="cpu", batch=16):
    """Frozen SigLIP patch features (N_imgs, 1024, 768) from SmolVLM's vision tower."""
    proc = AutoProcessor.from_pretrained(REPO, do_image_splitting=False, size={"longest_edge": 384})
    model = Idefics3ForConditionalGeneration.from_pretrained(REPO, torch_dtype=torch.float32).to(device).eval()
    vm = model.model.vision_model
    feats = []
    for i in range(0, len(imgs), batch):
        pv = proc.image_processor(images=imgs[i:i + batch], return_tensors="pt")["pixel_values"]
        pv = pv.reshape(-1, *pv.shape[-3:]).to(device)
        feats.append(vm(pixel_values=pv).last_hidden_state.cpu())
    return torch.cat(feats, 0)


class MLPPoolConnector(nn.Module):
    """Avg-pool 1024 patches -> q tokens, then a 2-layer MLP projection (LLaVA-style projector)."""
    def __init__(self, d_vis, d_out, q):
        super().__init__()
        self.q = q
        self.mlp = nn.Sequential(nn.Linear(d_vis, d_out), nn.GELU(), nn.Linear(d_out, d_out))

    def forward(self, feat):                                  # (B,N,d_vis)
        pooled = F.adaptive_avg_pool1d(feat.transpose(1, 2), self.q).transpose(1, 2)
        return self.mlp(pooled)                              # (B,q,d_out)


class QFormerConnector(nn.Module):
    """q learnable queries cross-attend the patch features (BLIP-2-style bridge)."""
    def __init__(self, d_vis, d_out, q, n_heads=4):
        super().__init__()
        self.queries = nn.Parameter(torch.randn(q, d_out) * 0.02)
        self.kv = nn.Linear(d_vis, d_out)
        self.attn = nn.MultiheadAttention(d_out, n_heads, batch_first=True)
        self.ffn = nn.Sequential(nn.Linear(d_out, d_out), nn.GELU(), nn.Linear(d_out, d_out))
        self.norm = nn.LayerNorm(d_out)

    def forward(self, feat):                                  # (B,N,d_vis)
        B = feat.shape[0]
        kv = self.kv(feat)
        q = self.queries.unsqueeze(0).expand(B, -1, -1)
        out, _ = self.attn(q, kv, kv)
        return self.norm(out + self.ffn(out))                # (B,q,d_out)


class ConnectorClassifier(nn.Module):
    def __init__(self, connector, d_out, n_color=4, n_shape=4):   # n_shape = 4 quadrants (detail)
        super().__init__()
        self.connector = connector
        self.color_head = nn.Linear(d_out, n_color)
        self.shape_head = nn.Linear(d_out, n_shape)

    def forward(self, feat):
        tok = self.connector(feat).mean(1)                   # (B,d_out)
        return self.color_head(tok), self.shape_head(tok)


def train_eval(kind, q, feat_tr, cy_tr, sy_tr, feat_te, cy_te, sy_te,
               d_out=128, steps=400, seed=0):
    torch.manual_seed(seed)
    d_vis = feat_tr.shape[-1]
    conn = MLPPoolConnector(d_vis, d_out, q) if kind == "mlp" else QFormerConnector(d_vis, d_out, q)
    model = ConnectorClassifier(conn, d_out)
    opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    n = feat_tr.shape[0]
    g = torch.Generator().manual_seed(seed)
    for _ in range(steps):
        idx = torch.randint(0, n, (32,), generator=g)
        cl, sl = model(feat_tr[idx])
        loss = F.cross_entropy(cl, cy_tr[idx]) + F.cross_entropy(sl, sy_tr[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        cl, sl = model(feat_te)
        return {"color_acc": (cl.argmax(1) == cy_te).float().mean().item(),
                "shape_acc": (sl.argmax(1) == sy_te).float().mean().item(),
                "n_params": sum(p.numel() for p in conn.parameters())}
