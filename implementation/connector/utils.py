"""Shared helpers for the connector study (RIS G1 contract) — re-exports common env/IO helpers."""
from implementation.eap_ig.utils import (  # noqa: F401
    REPO_ROOT, save_json, save_npz, environment, git_commit, set_determinism,
)
