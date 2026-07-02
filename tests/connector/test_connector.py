"""Connector ablation invariants (Track B2) — model-free (random features)."""
import torch

from implementation.connector.core import (MLPPoolConnector, QFormerConnector,
                                           ConnectorClassifier, gen_dataset, COLORS,
                                           train_eval)


def test_mlp_connector_reduces_to_q_tokens():
    conn = MLPPoolConnector(d_vis=768, d_out=128, q=16)
    out = conn(torch.randn(3, 1024, 768))
    assert out.shape == (3, 16, 128)


def test_qformer_connector_reduces_to_q_tokens():
    conn = QFormerConnector(d_vis=768, d_out=128, q=4)
    out = conn(torch.randn(3, 1024, 768))
    assert out.shape == (3, 4, 128)


def test_classifier_two_heads():
    clf = ConnectorClassifier(MLPPoolConnector(768, 128, 8), d_out=128)
    c, s = clf(torch.randn(5, 1024, 768))
    assert c.shape == (5, 4) and s.shape == (5, 4)     # left-colour + right-colour, both 4-class


def test_gen_dataset_labels():
    imgs, cy, sy = gen_dataset(n_per_combo=2, seed=0)
    assert len(imgs) == len(COLORS) * len(COLORS) * 2      # left x right colour combos
    assert cy.max().item() < len(COLORS) and sy.max().item() < len(COLORS)


def test_train_eval_learns_separable_features():
    """On features where color/shape are linearly encoded, the connector must beat chance."""
    torch.manual_seed(0)
    n, N, d = 96, 64, 768
    cy = torch.randint(0, 4, (n,)); sy = torch.randint(0, 3, (n,))
    def feats(cy, sy):
        f = torch.randn(len(cy), N, d) * 0.1
        f[:, :, :4] += torch.nn.functional.one_hot(cy, 4).unsqueeze(1).float()
        f[:, :, 4:7] += torch.nn.functional.one_hot(sy, 3).unsqueeze(1).float()
        return f
    ftr = feats(cy, sy)
    cyte = torch.randint(0, 4, (n,)); syte = torch.randint(0, 3, (n,))
    fte = feats(cyte, syte)
    r = train_eval("mlp", 8, ftr, cy, sy, fte, cyte, syte, steps=300, seed=0)
    assert r["color_acc"] > 0.5 and r["shape_acc"] > 0.5     # well above chance (0.25 / 0.33)
