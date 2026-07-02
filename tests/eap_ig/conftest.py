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
def ioi_batch(model):
    from implementation.eap_ig.config import TaskConfig
    from implementation.eap_ig.tasks import build_task
    return build_task(model.tok, TaskConfig(task="ioi", n_examples=8, seed=0)).to("cpu")
