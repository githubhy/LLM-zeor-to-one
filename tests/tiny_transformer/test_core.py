"""G1 gate: math-verification tests for the tiny-transformer core.

Run: PYTHONPATH=implementation pytest tests/tiny_transformer -q
"""
import warnings

import numpy as np
import pytest
import torch

warnings.filterwarnings("ignore")
torch.set_num_threads(4)

from tiny_transformer import circuits as C
from tiny_transformer.config import model_config
from tiny_transformer.data import make_induction_batch
from tiny_transformer.model import build_toy, masked_ce
from tiny_transformer.utils import softmax_np, wilson_ci


def _tiny():
    return model_config("induction", n_layers=2, n_heads=2, d_model=16, d_head=8,
                        d_vocab=8, n_ctx=8, seed=0)


# ---------- data: the fixed-offset-shortcut regression (bug 2026-07-02-05) ----------

def test_variable_offset():
    """Repeat offset must vary across sequences (else a 1-layer positional head
    solves induction — bug 2026-07-02-05)."""
    rng = np.random.default_rng(0)
    toks, tgt, ind, ap = make_induction_batch(rng, batch=64, n_ctx=64, d_vocab=32)
    offsets = []
    for b in range(64):
        q = np.flatnonzero(ind[b])
        offsets.append(q[0] - ap[b, q[0]] + 1)  # block length = t - attend + 1
    assert len(set(offsets)) > 5, "induction offset is (near-)constant — shortcut!"


def test_induction_data_property():
    """At each induction query, the target equals the token at attend_pos (what an
    induction head copies)."""
    rng = np.random.default_rng(1)
    toks, tgt, ind, ap = make_induction_batch(rng, batch=32, n_ctx=48, d_vocab=16)
    bb, tt = np.nonzero(ind)
    assert np.all(tgt[bb, tt] == toks[bb, ap[bb, tt]])
    assert np.all(toks[bb, tt] == toks[bb, ap[bb, tt] - 1])  # current == token before match


# ---------- softmax Jacobian (Eq 12) ----------

def test_softmax_jacobian():
    """J = diag(p) - p pᵀ  (Eq 12), checked against finite differences."""
    rng = np.random.default_rng(0)
    z = rng.standard_normal(6)
    p = softmax_np(z)
    J_analytic = np.diag(p) - np.outer(p, p)
    eps = 1e-6
    J_num = np.zeros((6, 6))
    for j in range(6):
        zp = z.copy(); zp[j] += eps
        zm = z.copy(); zm[j] -= eps
        J_num[:, j] = (softmax_np(zp) - softmax_np(zm)) / (2 * eps)
    assert np.max(np.abs(J_analytic - J_num)) < 1e-6


# ---------- circuit / gauge properties (§A.4, §A.8) ----------

def test_qk_rank_cliff():
    """QK circuit M = W_Q W_Kᵀ has rank ≤ d_head (§A.8)."""
    rng = np.random.default_rng(0)
    d, dk = 64, 16
    WQ = rng.standard_normal((d, dk)); WK = rng.standard_normal((d, dk))
    M, s = C.qk_circuit(WQ, WK)
    assert C.effective_rank(s, 0.999) <= dk
    assert np.sum(s > 1e-6 * s.max()) <= dk


def test_gauge_invariance_qk():
    """W_Q → W_Q R, W_K → W_K R⁻ᵀ leaves M = W_Q W_Kᵀ invariant (§A.4)."""
    rng = np.random.default_rng(0)
    d, dk = 32, 8
    WQ = rng.standard_normal((d, dk)); WK = rng.standard_normal((d, dk))
    R = rng.standard_normal((dk, dk))
    Rinv_T = np.linalg.inv(R).T
    M0, _ = C.qk_circuit(WQ, WK)
    M1, _ = C.qk_circuit(WQ @ R, WK @ Rinv_T)
    assert np.max(np.abs(M0 - M1)) < 1e-9


def test_gauge_invariance_ov():
    """W_V → W_V S, W_O → S⁻¹ W_O leaves W_OV = W_V W_O invariant (§A.4)."""
    rng = np.random.default_rng(0)
    d, dk = 32, 8
    WV = rng.standard_normal((d, dk)); WO = rng.standard_normal((dk, d))
    S = rng.standard_normal((dk, dk))
    W0, _ = C.ov_circuit(WV, WO)
    W1, _ = C.ov_circuit(WV @ S, np.linalg.inv(S) @ WO)
    assert np.max(np.abs(W0 - W1)) < 1e-8


# ---------- forward/backward gradient check (H5) ----------

def test_gradient_check_autograd_vs_finitediff():
    """Autograd gradients match central finite differences on the model loss (H5).
    The hand-derived-math reference is the numpy Appendix-C toy (rel-err 1.6e-9);
    this confirms the induction model's forward is differentiated correctly."""
    torch.manual_seed(0)
    model = build_toy(_tiny())
    rng = np.random.default_rng(0)
    toks, tgt, _, _ = make_induction_batch(rng, batch=4, n_ctx=8, d_vocab=8)
    t = torch.as_tensor(toks); y = torch.as_tensor(tgt)

    loss = masked_ce(model(t), y)
    model.zero_grad(); loss.backward()

    named = [(n, p) for n, p in model.named_parameters() if p.grad is not None]
    eps = 1e-3
    rels = []
    rng2 = np.random.default_rng(1)
    for _ in range(25):
        n, p = named[rng2.integers(len(named))]
        idx = tuple(int(rng2.integers(s)) for s in p.shape)
        g_an = float(p.grad[idx])
        with torch.no_grad():
            old = float(p[idx])
            p[idx] = old + eps; lp = float(masked_ce(model(t), y))
            p[idx] = old - eps; lm = float(masked_ce(model(t), y))
            p[idx] = old
        g_num = (lp - lm) / (2 * eps)
        rels.append(abs(g_an - g_num) / (abs(g_an) + abs(g_num) + 1e-8))
    assert np.median(rels) < 1e-2, f"median rel err {np.median(rels):.2e}"
    assert np.max(rels) < 1e-1, f"max rel err {np.max(rels):.2e}"


# ---------- residual-stream decomposition reconstruction (H11) ----------

def test_residual_reconstruction():
    """resid_post = resid_pre + attn_out (+ mlp_out) to float tolerance — the
    additive path-sum of §A.1/§A.20 (H11)."""
    torch.manual_seed(0)
    model = build_toy(_tiny())
    rng = np.random.default_rng(0)
    toks, *_ = make_induction_batch(rng, batch=2, n_ctx=8, d_vocab=8)
    _, cache = model.run_with_cache(torch.as_tensor(toks))
    for l in range(model.cfg.n_layers):
        pre = cache[f"blocks.{l}.hook_resid_pre"]
        post = cache[f"blocks.{l}.hook_resid_post"]
        attn = cache[f"blocks.{l}.hook_attn_out"]
        recon = pre + attn
        if not model.cfg.attn_only:
            recon = recon + cache[f"blocks.{l}.hook_mlp_out"]
        assert torch.max(torch.abs(post - recon)).item() < 1e-4


# ---------- utils sanity ----------

def test_wilson_ci():
    p, lo, hi = wilson_ci(80, 100)
    assert lo < p < hi and 0 <= lo <= hi <= 1
