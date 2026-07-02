"""Decomposition + intervention invariants — the correctness anchors for the harness."""
import torch


def test_node_count(model):
    assert len(model.names) == 1 + model.n_layer * (model.n_head + 1) == 157


def test_residual_reconstruction(model, ioi_batch):
    """embed + sum(heads + attn_bias + mlp) == pre-ln_f residual (post-ln_f == hidden_states)."""
    with torch.no_grad():
        out = model.model(ioi_batch.clean_ids, attention_mask=ioi_batch.attn_mask,
                          output_hidden_states=True)
    _, contribs = model.forward_cache(ioi_batch.clean_ids, ioi_batch.attn_mask)
    recon = contribs["embed"].clone()
    for l in range(model.n_layer):
        recon = recon + sum(contribs[f"a{l}.h{h}"] for h in range(model.n_head))
        recon = recon + model.blocks[l].attn.c_proj.bias + contribs[f"m{l}"]
    err = (model.model.transformer.ln_f(recon) - out.hidden_states[-1]).abs().max().item()
    assert err < 1e-3, err


def test_patched_identity(model, ioi_batch):
    """all-in-circuit == clean logits; none-in-circuit == corrupt logits."""
    clean = model.model(ioi_batch.clean_ids, attention_mask=ioi_batch.attn_mask).logits
    corrupt = model.model(ioi_batch.corrupt_ids, attention_mask=ioi_batch.attn_mask).logits
    _, cc = model.forward_cache(ioi_batch.corrupt_ids, ioi_batch.attn_mask)
    lg_all = model.patched_logits(ioi_batch.clean_ids, ioi_batch.attn_mask, cc, set(model.names))
    lg_none = model.patched_logits(ioi_batch.clean_ids, ioi_batch.attn_mask, cc, set())
    assert (lg_all - clean).abs().max().item() < 1e-2
    assert (lg_none - corrupt).abs().max().item() < 1e-2


def test_faithfulness_anchors(model, ioi_batch):
    """faith(full)=1, faith(empty)=0 — the analytical oracle."""
    from implementation.eap_ig.faithfulness import baselines, faith_curve
    from implementation.eap_ig.attribution import score_random
    b, bp = baselines(model, ioi_batch)
    fc = faith_curve(model, ioi_batch, score_random(model, ioi_batch), [0, len(model.names)], b, bp)
    assert abs(fc[len(model.names)].mean().item() - 1.0) < 1e-2
    assert abs(fc[0].mean().item()) < 1e-2
