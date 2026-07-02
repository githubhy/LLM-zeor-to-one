"""FastV pruning study invariants (Track B1)."""
import os
import numpy as np
import pytest

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from implementation.fastv.core import flop_reduction, synthetic_dataset, make_image, COLORS


def test_flop_reduction_zero_at_r0():
    assert abs(flop_reduction(K=2, R=0.0, n_img=320, n_total=352)) < 1e-9


def test_flop_reduction_monotone_in_r():
    rs = [flop_reduction(K=2, R=r, n_img=320, n_total=352) for r in (0.1, 0.3, 0.5, 0.7, 0.9)]
    assert all(a < b for a, b in zip(rs, rs[1:]))          # strictly increasing
    assert rs[-1] < 1.0                                    # never fully free


def test_flop_reduction_earlier_K_saves_more():
    # smaller K (prune earlier) => more layers run reduced => more savings
    assert flop_reduction(K=1, R=0.5, n_img=320, n_total=352) > flop_reduction(K=5, R=0.5, n_img=320, n_total=352)


def test_synthetic_dataset_labels_valid():
    ds = synthetic_dataset(n_per=2)
    assert len(ds) == len(COLORS) * 2
    assert all(ex.answer in COLORS for ex in ds)
    assert all(ex.image.size == (224, 224) for ex in ds)


def test_make_image_shapes():
    for shape in ("square", "circle", "triangle"):
        img = make_image("red", shape)
        arr = np.array(img)
        assert arr.shape == (224, 224, 3)
        assert (arr[:, :, 0] > 200).any()                  # red channel present


@pytest.mark.skipif(not os.path.exists(os.path.expanduser(
    "~/.cache/huggingface/hub/models--HuggingFaceTB--SmolVLM-256M-Instruct")),
    reason="SmolVLM weights not cached")
def test_model_answers_red():
    from implementation.fastv.core import FastVModel, Example, make_image
    M = FastVModel(device="cpu")
    ans = M.predict(Example(make_image("red", "circle"), "What color is the shape? Answer in one word.", "red"))
    assert ans.startswith("red")
