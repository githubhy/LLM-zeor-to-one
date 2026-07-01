import pytest

import sae_frontier as sf


@pytest.mark.parametrize("variant", sf.VARIANTS)
def test_oracle_passes(variant):
    """P0-5: every candidate must pass its correctness oracle before Phase 3."""
    rec = sf.oracle.run_oracle_checks(variant)
    failed = [c for c in rec["checks"] if not c["passed"]]
    assert rec["passed"], f"{variant} oracle FAILED: {failed}"
    assert len(rec["checks"]) >= 3
