"""Correctness oracles (P0-5): every candidate must pass an analytical / reference /
metamorphic check, else G1 fails. These are the anchors a wrong kernel trips on.

- exact_patch (analytical): faith(full circuit)=1, faith(empty circuit)=0 exactly.
- eap_ig    (analytical): EAP-IG at m=1 equals EAP (single interp point = clean gradient).
- eap       (metamorphic): scaling the task metric by c scales the gradient (hence scores) by c.
- random    (reference): a random circuit recovers ~0 normalized faithfulness (floor).
"""
from __future__ import annotations

from .attribution import score_eap, score_eap_ig, score_exact, score_random
from .faithfulness import baselines, faith_curve


def run_oracles(M, batch) -> dict[str, dict]:
    b, bp = baselines(M, batch)
    N = len(M.names)
    out: dict[str, dict] = {}

    # exact_patch — analytical anchor on the intervention itself
    sc_ex = score_exact(M, batch)
    fc = faith_curve(M, batch, sc_ex, [0, N], b, bp)
    full_v, empty_v = fc[N].mean().item(), fc[0].mean().item()
    out["exact_patch"] = {
        "type": "analytical",
        "passed": bool(abs(full_v - 1.0) < 1e-2 and abs(empty_v) < 1e-2),
        "detail": f"faith(full)={full_v:.4f} (=1), faith(empty)={empty_v:.4f} (=0)",
    }

    # eap_ig — analytical tie to eap at m=1
    s_eap = score_eap(M, batch)
    s_ig1 = score_eap_ig(M, batch, m_ig=1)
    md = max(abs(s_eap[u] - s_ig1[u]) for u in M.names)
    out["eap_ig"] = {
        "type": "analytical",
        "passed": bool(md < 1e-4),
        "detail": f"max|eap_ig(m=1) - eap| = {md:.2e} (=0)",
    }

    # eap — metamorphic linearity in the metric scale
    g1, _ = M.forward_grad(batch.clean_ids, batch.attn_mask, batch.metric, sign=-1.0, ig_steps=1)
    g2, _ = M.forward_grad(batch.clean_ids, batch.attn_mask,
                           lambda lg: 2.0 * batch.metric(lg), sign=-1.0, ig_steps=1)
    ref = max(M.names, key=lambda u: g1[u].norm().item())
    ratio = g2[ref].norm().item() / (g1[ref].norm().item() + 1e-12)
    out["eap"] = {
        "type": "metamorphic",
        "passed": bool(abs(ratio - 2.0) < 1e-2),
        "detail": f"grad scaling ratio under 2x metric = {ratio:.4f} (=2.0)",
    }

    # random — reference floor
    s_rand = score_random(M, batch, 0)
    fr = faith_curve(M, batch, s_rand, [40], b, bp)[40].mean().item()
    out["random"] = {
        "type": "reference",
        "passed": bool(abs(fr) < 0.15),
        "detail": f"faith(random circuit, n=40) = {fr:.4f} (~0 floor)",
    }
    return out
