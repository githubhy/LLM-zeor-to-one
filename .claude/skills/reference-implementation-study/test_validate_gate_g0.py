#!/usr/bin/env python3
"""Per-item A/B fixture for the G0 derivation-soundness gate (skill-options RIS-DERIV).

Proves the gate DISCRIMINATES: a sound derivation ledger PASSES, a ledger with a
planted defect (a load-bearing entry missing its independent re-derivation / limit
check / assumptions) FAILS. Mirrors P0-5's "sign-flipped-LLR decoder fails the oracle"
discrimination check.

Runnable two ways:
    python .claude/skills/reference-implementation-study/test_validate_gate_g0.py   # standalone
    python -m pytest .claude/skills/reference-implementation-study/test_validate_gate_g0.py
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ris_validate_gate", _SKILL_DIR / "validate_gate.py")
vg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vg)


def _fails(results: list[tuple[bool, str]]) -> list[str]:
    return [msg for ok, msg in results if not ok]


# A complete, sound ledger: one load-bearing + one catalog candidate.
SOUND = [
    {
        "candidate": "wiener_time",
        "tier": "load-bearing",
        "survey_ref": "data-channel §6.2.2 Eq (44)-(46)",
        "independent_rederivation": "verified",
        "no_missing_step": True,
        "limit_checks": [
            {"limit": "SNR -> inf, 2 pilots", "expect": "linear interp", "derived": "matches"},
            {"limit": "pilot density -> inf", "expect": "MSE -> 0", "derived": "matches"},
        ],
        "assumptions": ["WSSUS", "known R_HH", "Jakes Doppler"],
        "external_values": [
            {"value": "R_HH Bessel-J0 coefficient", "source": "spec: docs/specs/…", "reproduced": True},
        ],
    },
    {
        "candidate": "linear_freq",
        "tier": "catalog",
        "survey_ref": "data-channel §6.1.1",
        "no_missing_step": True,
    },
]


def test_sound_ledger_passes():
    results = vg._check_ledger_entries(copy.deepcopy(SOUND),
                                       modules=["wiener_time", "linear_freq"])
    assert _fails(results) == [], f"sound ledger should pass, got fails: {_fails(results)}"


def test_defective_missing_limit_check_fails():
    bad = copy.deepcopy(SOUND)
    del bad[0]["limit_checks"]          # planted defect on the LOAD-BEARING entry
    fails = _fails(vg._check_ledger_entries(bad, modules=["wiener_time", "linear_freq"]))
    assert any("limit_check" in m for m in fails), f"expected a limit_check failure, got: {fails}"


def test_defective_missing_rederivation_fails():
    bad = copy.deepcopy(SOUND)
    bad[0]["independent_rederivation"] = "todo"   # not 'verified'
    fails = _fails(vg._check_ledger_entries(bad))
    assert any("independent_rederivation" in m for m in fails), f"got: {fails}"


def test_defective_missing_external_values_fails():
    bad = copy.deepcopy(SOUND)
    del bad[0]["external_values"]        # load-bearing entry drops the imported-value attestation
    fails = _fails(vg._check_ledger_entries(bad))
    assert any("external_values" in m for m in fails), f"got: {fails}"


def test_defective_unreproduced_external_value_fails():
    bad = copy.deepcopy(SOUND)
    bad[0]["external_values"] = [        # planted defect: a value NOT reproduced from a source
        {"value": "J-function leading coefficient", "source": "", "reproduced": False},
    ]
    fails = _fails(vg._check_ledger_entries(bad))
    assert any("external_values[0]" in m for m in fails), f"got: {fails}"


def test_empty_external_values_needs_note():
    # a load-bearing derivation that imports NO external constant must say so explicitly
    bad = copy.deepcopy(SOUND)
    bad[0]["external_values"] = []       # no imported values, but no note either
    fails = _fails(vg._check_ledger_entries(bad))
    assert any("external_values_note" in m for m in fails), f"empty list w/o note should fail, got: {fails}"

    ok = copy.deepcopy(SOUND)
    ok[0]["external_values"] = []
    ok[0]["external_values_note"] = "derived entirely from axioms; no imported constants"
    assert _fails(vg._check_ledger_entries(ok)) == [], "empty list + note should PASS"


def test_catalog_entry_ignores_external_values():
    # a catalog entry never needs external_values (tiered — not over-gated)
    results = vg._check_ledger_entries([copy.deepcopy(SOUND[1])])
    assert _fails(results) == [], f"catalog over-gated on external_values: {_fails(results)}"


def test_defective_missing_survey_ref_fails():
    bad = copy.deepcopy(SOUND)
    bad[1].pop("survey_ref")            # catalog entry loses its only ref
    fails = _fails(vg._check_ledger_entries(bad))
    assert any("survey_ref" in m for m in fails), f"got: {fails}"


def test_candidate_without_ledger_entry_fails():
    fails = _fails(vg._check_ledger_entries(copy.deepcopy(SOUND),
                                            modules=["wiener_time", "linear_freq", "kalman_time"]))
    assert any("kalman_time" in m for m in fails), f"expected missing-module fail, got: {fails}"


def test_catalog_entry_needs_only_ref_and_no_missing_step():
    # a catalog entry lacking rederivation/limit/assumptions must still PASS
    results = vg._check_ledger_entries([SOUND[1]])
    assert _fails(results) == [], f"catalog entry over-gated: {_fails(results)}"


def test_gate_g0_end_to_end_sound_passes(tmp_path=None):
    tmp = tmp_path or Path(vg.REPO_ROOT)  # pytest passes tmp_path; standalone uses a real temp
    import tempfile
    if tmp_path is None:
        tmp = Path(tempfile.mkdtemp())
    saved = vg.REPO_ROOT
    try:
        vg.REPO_ROOT = tmp
        art = tmp / "artifacts" / "toy_study"
        art.mkdir(parents=True, exist_ok=True)
        (art / "study-manifest.json").write_text(json.dumps({"derivation_ledger": SOUND}))
        results = vg.gate_g0("toy_study", "toy_topic")
        assert _fails(results) == [], f"end-to-end sound G0 should pass: {_fails(results)}"
    finally:
        vg.REPO_ROOT = saved


def test_gate_g0_missing_ledger_fails(tmp_path=None):
    import tempfile
    tmp = tmp_path or Path(tempfile.mkdtemp())
    saved = vg.REPO_ROOT
    try:
        vg.REPO_ROOT = tmp
        art = tmp / "artifacts" / "toy_study2"
        art.mkdir(parents=True, exist_ok=True)
        (art / "study-manifest.json").write_text(json.dumps({"iterations": []}))  # no ledger
        results = vg.gate_g0("toy_study2", "toy_topic")
        assert _fails(results), "G0 must fail when no derivation ledger is present"
    finally:
        vg.REPO_ROOT = saved


def test_non_candidates_exclude_tooling_but_keep_real_candidates(tmp_path=None):
    """The manifest's derivation_ledger_non_candidates (fnmatch globs) removes tooling
    modules (drivers/figures/probes/diagnostics) from the candidate set, WITHOUT excluding
    a real candidate whose stem shares a prefix (w42_trs_sigma_crossing excluded,
    w42_trs_sigma_derivation kept). Absent key => legacy behaviour (every module a candidate)."""
    import tempfile
    tmp = tmp_path or Path(tempfile.mkdtemp())
    saved = vg.REPO_ROOT
    try:
        vg.REPO_ROOT = tmp
        impl = tmp / "implementation" / "toy_topic"
        impl.mkdir(parents=True, exist_ok=True)
        for stem in ("hst_channel_ref", "w42_trs_sigma_derivation",   # real candidates
                     "w42_trs_sigma_crossing", "w42_hst_figure",       # tooling
                     "w41_basis_probe", "rank2_ce_diagnostic",
                     "utils", "__init__"):
            (impl / f"{stem}.py").write_text("# stub\n")
        art = tmp / "artifacts" / "toy_study"
        art.mkdir(parents=True, exist_ok=True)

        # Without the key: every non-utils module is a candidate (backward-compat).
        (art / "study-manifest.json").write_text(json.dumps({"derivation_ledger": []}))
        assert set(vg._find_candidate_modules("toy_study", "toy_topic")) == {
            "hst_channel_ref", "w42_trs_sigma_derivation", "w42_trs_sigma_crossing",
            "w42_hst_figure", "w41_basis_probe", "rank2_ce_diagnostic",
        }

        # With the key: tooling excluded; the derivation with a shared prefix is KEPT.
        (art / "study-manifest.json").write_text(json.dumps({
            "derivation_ledger": [],
            "derivation_ledger_non_candidates": [
                "*_figure", "*_probe", "*_diagnostic", "w42_trs_sigma_crossing"],
        }))
        assert set(vg._find_candidate_modules("toy_study", "toy_topic")) == {
            "hst_channel_ref", "w42_trs_sigma_derivation"}
    finally:
        vg.REPO_ROOT = saved


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  [+] PASS: {t.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"  [-] FAIL: {t.__name__}: {exc}")
    print(f"\n{passed}/{len(tests)} G0-discrimination checks passed")
    raise SystemExit(0 if passed == len(tests) else 1)
