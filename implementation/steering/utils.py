"""Shared helpers for the steering study (RIS rule). Re-exports the common env/IO helpers so
this topic dir satisfies the G1 contract without duplicating them."""
from implementation.eap_ig.utils import (  # noqa: F401
    REPO_ROOT, save_json, save_npz, environment, git_commit, set_determinism,
)
