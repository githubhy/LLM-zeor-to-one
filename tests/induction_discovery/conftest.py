import os
import pytest

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


@pytest.fixture(scope="session")
def model():
    from implementation.eap_ig.config import ModelConfig
    from implementation.eap_ig.model import Model
    return Model(ModelConfig(name="gpt2", device="cpu", dtype="float32"))


@pytest.fixture(scope="session")
def induction_batch(model):
    from implementation.induction_discovery.task import build_induction
    return build_induction(model.tok, n_examples=8, seed=0, block_len=12).to("cpu")


@pytest.fixture(scope="session")
def eager():
    from implementation.induction_discovery.oracle import load_eager
    m, tok = load_eager("gpt2", "cpu", "float32")
    return m, tok
