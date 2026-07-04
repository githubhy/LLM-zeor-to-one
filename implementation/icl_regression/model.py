"""Part B — a small TRAINED SOFTMAX regression transformer for in-context linear regression.

Purpose-built causal decoder (plain torch.nn; NOT the token-based tiny_transformer
HookedTransformer, which cannot take continuous (x, y) vectors). Linear read-in for the
interleaved (x, y) token stream (task.interleave), pre-norm softmax attention + GELU-MLP
blocks, linear read-out predicting y at each x-token position. Trained with MSE.

This model supports the BEHAVIORAL claim (H9-B/C/D): its in-context predictions track
least-squares. It does NOT support a mechanistic-GD claim — that is Part A (construction.py),
which is linear attention + constructed weights. Single-head softmax cannot be the exact GD
mechanism (von Oswald §A.9).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .task import make_regression_batch, interleave


@dataclass(frozen=True)
class ICLModelConfig:
    x_dim: int = 8
    d_model: int = 64
    n_layers: int = 4
    n_heads: int = 4
    d_mlp: int = 256
    max_points: int = 40          # k_max; sequence length is 2 * max_points
    seed: int = 0

    def to_dict(self):
        return dataclasses.asdict(self)


class Block(nn.Module):
    """Pre-norm softmax self-attention + GELU MLP (causal)."""

    def __init__(self, d_model: int, n_heads: int, d_mlp: int):
        super().__init__()
        self.n_heads = n_heads
        self.ln1 = nn.LayerNorm(d_model)
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(nn.Linear(d_model, d_mlp), nn.GELU(), nn.Linear(d_mlp, d_model))

    def forward(self, x):
        B, T, D = x.shape
        h = self.ln1(x)
        q, k, v = self.qkv(h).split(D, dim=-1)
        # (B, n_heads, T, d_head)
        q, k, v = (t.view(B, T, self.n_heads, D // self.n_heads).transpose(1, 2) for t in (q, k, v))
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)   # softmax attention
        a = a.transpose(1, 2).reshape(B, T, D)
        x = x + self.proj(a)
        x = x + self.mlp(self.ln2(x))
        return x


class ICLRegressionTransformer(nn.Module):
    def __init__(self, cfg: ICLModelConfig):
        super().__init__()
        self.cfg = cfg
        torch.manual_seed(cfg.seed)
        self.readin = nn.Linear(cfg.x_dim + 1, cfg.d_model)
        self.pos = nn.Parameter(torch.zeros(1, 2 * cfg.max_points, cfg.d_model))
        nn.init.normal_(self.pos, std=0.02)
        self.blocks = nn.ModuleList([Block(cfg.d_model, cfg.n_heads, cfg.d_mlp)
                                     for _ in range(cfg.n_layers)])
        self.ln_f = nn.LayerNorm(cfg.d_model)
        self.readout = nn.Linear(cfg.d_model, 1)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        """tokens (B, T, x_dim+1) -> per-position scalar prediction (B, T)."""
        T = tokens.shape[1]
        h = self.readin(tokens) + self.pos[:, :T]
        for blk in self.blocks:
            h = blk(h)
        return self.readout(self.ln_f(h)).squeeze(-1)


@dataclass(frozen=True)
class ICLTrainConfig:
    steps: int = 4000
    batch: int = 64
    lr: float = 1e-3
    warmup: int = 200
    weight_decay: float = 0.0
    noise_std: float = 0.0
    eval_every: int = 500
    seed: int = 0

    def to_dict(self):
        return dataclasses.asdict(self)


def _make_tokens(rng, batch, k, x_dim, noise_std, device):
    X, y, w = make_regression_batch(rng, batch, k, x_dim, noise_std)
    tok, xpos = interleave(X, y)
    t = torch.as_tensor(tok, dtype=torch.float32, device=device)
    target = torch.as_tensor(y, dtype=torch.float32, device=device)   # (B, k)
    return t, target, xpos


def train(model: ICLRegressionTransformer, tcfg: ICLTrainConfig, device: str = "cpu",
          log=print):
    """AdamW training on in-context linear regression. MSE at x-token positions (predict y_i
    from the preceding pairs). Deterministic given seeds; eval stream offset by 10_000 to avoid
    train/eval collision (tiny_transformer convention). Returns a history dict."""
    cfg = model.cfg
    model.to(device).train()
    torch.manual_seed(tcfg.seed)
    rng = np.random.default_rng(tcfg.seed)
    eval_rng = np.random.default_rng(10_000 + tcfg.seed)
    opt = torch.optim.AdamW(model.parameters(), lr=tcfg.lr, weight_decay=tcfg.weight_decay)

    def lr_at(step):
        return tcfg.lr * (step + 1) / tcfg.warmup if step < tcfg.warmup else tcfg.lr

    hist = {"step": [], "train_mse": [], "eval_mse_last": []}
    for step in range(tcfg.steps + 1):
        for g in opt.param_groups:
            g["lr"] = lr_at(step)
        tok, target, xpos = _make_tokens(rng, tcfg.batch, cfg.max_points, cfg.x_dim,
                                         tcfg.noise_std, device)
        pred = model(tok)[:, xpos]                    # (B, k) predictions at x-token positions
        loss = F.mse_loss(pred, target)
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if step % tcfg.eval_every == 0 or step == tcfg.steps:
            model.eval()
            with torch.no_grad():
                et, ey, exp = _make_tokens(eval_rng, 256, cfg.max_points, cfg.x_dim,
                                           tcfg.noise_std, device)
                ep = model(et)[:, exp]
                eval_mse_last = float(F.mse_loss(ep[:, -1], ey[:, -1]).item())
            model.train()
            hist["step"].append(step)
            hist["train_mse"].append(float(loss.item()))
            hist["eval_mse_last"].append(eval_mse_last)
            log(f"step {step:5d} | train_mse {loss.item():.4f} | eval_mse@k={cfg.max_points} "
                f"{eval_mse_last:.4f}")
    model.eval()
    return hist


@torch.no_grad()
def in_context_predictions(model: ICLRegressionTransformer, X: np.ndarray, y: np.ndarray,
                           device: str = "cpu") -> np.ndarray:
    """Model's running in-context prediction of y_i at each x-token position, for a batch of
    tasks. Returns preds (B, k): preds[:, i] uses examples 0..i-1 plus x_i to predict y_i."""
    tok, xpos = interleave(X, y)
    t = torch.as_tensor(tok, dtype=torch.float32, device=device)
    return model(t)[:, xpos].cpu().numpy()
