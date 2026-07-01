"""P0-1 determinism-verification gate: same config + seed must give bit-identical output."""
import torch

import sae_frontier as sf
from sae_frontier.config import SAEConfig, SyntheticConfig, TrainConfig
from sae_frontier.utils import tensor_hash


def _run(variant, seed=0):
    data = sf.generate(SyntheticConfig(n_features=48, d_model=12, n_samples=500, seed=seed))
    cfg = SAEConfig(variant=variant, d_model=12, expansion=4, seed=seed, k=6)
    sae = sf.build_sae(cfg)
    out = sf.train_sae(sae, data.x, TrainConfig(steps=150, seed=seed))
    x_hat, _ = sae(data.x)
    return out["final_loss"], tensor_hash(x_hat)


import pytest


@pytest.mark.parametrize("variant", sf.VARIANTS)
def test_training_is_bit_deterministic(variant):
    loss_a, hash_a = _run(variant)
    loss_b, hash_b = _run(variant)
    assert loss_a == loss_b, f"{variant}: non-deterministic loss {loss_a} != {loss_b}"
    assert hash_a == hash_b, f"{variant}: non-deterministic output hash"


@pytest.mark.parametrize("variant", sf.VARIANTS)
def test_init_is_seed_deterministic(variant):
    a = sf.build_sae(SAEConfig(variant=variant, d_model=16, seed=3))
    b = sf.build_sae(SAEConfig(variant=variant, d_model=16, seed=3))
    assert tensor_hash(a.W_dec) == tensor_hash(b.W_dec)
    assert tensor_hash(a.W_enc) == tensor_hash(b.W_enc)
