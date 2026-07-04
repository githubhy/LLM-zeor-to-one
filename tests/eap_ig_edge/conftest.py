import os
import pytest

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


@pytest.fixture(scope="session")
def model():
    from implementation.eap_ig.config import ModelConfig
    from implementation.eap_ig.model import Model
    return Model(ModelConfig(name="gpt2", device="cpu", dtype="float32"))


@pytest.fixture(scope="session")
def edge_model(model):
    from implementation.eap_ig.edge_model import EdgeModel
    return EdgeModel(model)


@pytest.fixture(scope="session")
def batch(model):
    from implementation.induction_discovery.task import build_induction
    return build_induction(model.tok, n_examples=5, seed=1, block_len=8).to("cpu")
