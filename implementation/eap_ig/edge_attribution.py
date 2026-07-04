"""Edge-level EAP / EAP-IG scorers (Hanna 2024 Eq 1/3).

score(u -> v) = <z'_u - z_u, g_v>  summed over positions, where z'_u - z_u = corrupt - clean
node-output difference (Model.forward_cache) and g_v = dL/d(residual read by dest slot v)
(EdgeModel.forward_grad_edges). EAP uses one gradient (ig_steps=1); EAP-IG integrates the
gradient over m points on the corrupt->clean input-embedding path (activation diff unchanged).

Edge->node consistency (the correctness anchor): because a source's residual contribution is
read by every downstream dest, dL/d z_u = Σ_{v downstream of u} g_v, so
  node_score(u) == Σ_{v downstream of u} edge_score(u -> v).
`node_from_edges` recomputes the node score by summing edges; it must match score_nodes.
"""
from __future__ import annotations

import numpy as np

from .attribution import _dot
from .edges import upstream_sources, dest_slots, source_nodes


def _delta_z(M, batch):
    """z'_u - z_u = corrupt - clean node-output contributions (source nodes)."""
    _, cc = M.forward_cache(batch.clean_ids, batch.attn_mask)
    _, xc = M.forward_cache(batch.corrupt_ids, batch.attn_mask)
    return {u: xc[u] - cc[u] for u in M.names}


def score_edges(M, EM, batch, method: str = "eap", m_ig: int = 5) -> dict[tuple, float]:
    """Return {(u, v): score} over all 32,491 edges."""
    dz = _delta_z(M, batch)
    wte = M.model.transformer.wte
    if method == "eap":
        g = EM.forward_grad_edges(batch.clean_ids, batch.attn_mask, batch.metric,
                                  sign=-1.0, ig_steps=1)
    elif method == "eap_ig":
        g = EM.forward_grad_edges(batch.clean_ids, batch.attn_mask, batch.metric, sign=-1.0,
                                  ig_steps=m_ig, corrupt_embed=wte(batch.corrupt_ids),
                                  clean_embed=wte(batch.clean_ids))
    elif method == "random":
        rng = np.random.default_rng(0)
        L, H = M.n_layer, M.n_head
        return {(u, v): float(rng.standard_normal())
                for v in dest_slots(L, H) for u in upstream_sources(v, L, H)}
    else:
        raise KeyError(method)
    L, H = M.n_layer, M.n_head
    out = {}
    for v in dest_slots(L, H):
        gv = g[v]
        for u in upstream_sources(v, L, H):
            out[(u, v)] = _dot(dz[u], gv, batch.attn_mask)
    return out


def node_from_edges(edge_scores: dict[tuple, float], M) -> dict[str, float]:
    """Recompose node scores by summing all edges OUT of each source (consistency anchor)."""
    acc = {u: 0.0 for u in M.names}
    for (u, v), s in edge_scores.items():
        acc[u] += s
    return acc
