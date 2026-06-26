"""Tests for crosslink.py.

Covers: tokenization, directional link syntax (make_link), the normalize-with-map
matcher + insertion-point finder, candidate generation (cross-file only +
file-scoped dedup), and a CLI smoke test (extract -> candidates -> check).
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "viewer" / "tools" / "crosslink.py"

spec = importlib.util.spec_from_file_location("crosslink", SCRIPT)
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)


# -- unit: tokenize ----------------------------------------------------------

def test_tokenize_strips_math_and_stopwords_keeps_tech():
    toks = cl.tokenize("The self-attention operation and $\\tanh(x)$ gradient descent.")
    assert "self-attention" in toks
    assert "gradient" in toks and "descent" in toks
    assert "gradient_descent" in toks           # adjacent bigram
    assert "the" not in toks and "and" not in toks
    assert all("tanh" not in t for t in toks)    # math stripped


# -- unit: directional link syntax ------------------------------------------

def _sec(file, base, corpus, sec, anchor, title="Title"):
    return {"file": file, "base": base, "corpus": corpus, "sec": sec,
            "anchor": anchor, "title": title}


def test_make_link_survey_target_uses_secxref():
    src = _sec("surveys/x/a.md", "a.md", "survey", "1.1", "sec-1.1")
    dst = _sec("surveys/x/b.md", "b.md", "survey", "2.1", "sec-2.1")
    link, dedup = cl.make_link(src, dst)
    assert link == "<!-- secxref:2.1 -->[§2.1](b.md#sec-2.1)"
    assert dedup == "b.md#sec-2.1"


def test_make_link_wiki_target_uses_plain_link_no_glyph():
    src = _sec("surveys/x/a.md", "a.md", "survey", "1.1", "sec-1.1")
    dst = _sec("wikis/w.md", "w.md", "wiki", "3", "sec-3", title="Softmax Derivation")
    link, dedup = cl.make_link(src, dst)
    assert link.startswith("[Softmax Derivation](")
    assert "§" not in link
    assert "secxref" not in link
    assert dedup.endswith("wikis/w.md#sec-3")
    assert dedup.startswith("../../")          # relative path from survey dir


# -- unit: normalize-with-map matcher ---------------------------------------

def test_find_insertion_point_through_emphasis():
    text = "Intro.\n\n1. **Attention step:** scale the scores then apply the mask.\n2. Next."
    ip = cl.find_insertion_point(text, "scale the scores then apply the mask")
    assert ip is not None
    # insertion point lands just after "mask", before the period
    assert text[ip - 4:ip] == "mask"
    assert text[ip] == "."


def test_find_insertion_point_missing_returns_none():
    assert cl.find_insertion_point("nothing here", "absent phrase quote") is None


# -- unit: candidate generation ---------------------------------------------

def _section(file, base, corpus, sec, anchor, body, existing=None):
    return {"file": file, "base": base, "corpus": corpus, "sec": sec,
            "title": f"{sec} title", "anchor": anchor,
            "tokens": cl.tokenize(body), "snippet": body[:120],
            "existing": existing or []}


def test_generate_candidates_cross_file_only_and_file_scoped_dedup():
    shared = "self-attention gradient descent layer normalization residual stream softmax"
    a = _section("surveys/s/a.md", "a.md", "survey", "1.1", "sec-1.1", shared)
    b = _section("surveys/s/b.md", "b.md", "survey", "2.1", "sec-2.1", shared)
    # same-file section: must never be a candidate target (cross-file only)
    a2 = _section("surveys/s/a.md", "a.md", "survey", "1.2", "sec-1.2", shared)

    cands = cl.generate_candidates([a, a2, b], per_source=3, min_score=0.01,
                                   keep_symmetric=True)
    pairs = {(c["source"]["sec"], c["target"]["sec"]) for c in cands}
    assert ("1.1", "2.1") in pairs               # cross-file link found
    assert ("1.1", "1.2") not in pairs           # same-file excluded

    # now mark a as already linking b file-wide -> file-scoped dedup drops it
    a_linked = dict(a, existing=[("b.md", "sec-2.1")])
    cands2 = cl.generate_candidates([a_linked, b], per_source=3, min_score=0.01,
                                    keep_symmetric=True, file_scoped=True)
    assert ("1.1", "2.1") not in {
        (c["source"]["sec"], c["target"]["sec"]) for c in cands2}


# -- CLI smoke: extract -> candidates -> check ------------------------------

def _run(args, cwd):
    r = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def test_cli_extract_candidates_check(tmp_path):
    sdir = tmp_path / "surveys" / "s"
    sdir.mkdir(parents=True)
    shared = ("self-attention gradient descent layer normalization residual stream softmax "
              "rotary embedding key value cache speculative decoding")
    (sdir / "a.md").write_text(
        f'## <a id="sec-1.1"></a>1.1 Heading A\n\nThe {shared} appears here.\n',
        encoding="utf-8")
    (sdir / "b.md").write_text(
        f'## <a id="sec-2.1"></a>2.1 Heading B\n\nAlso the {shared} appears.\n',
        encoding="utf-8")

    idx = tmp_path / "idx.json"
    rc, out, err = _run(["extract", "surveys/s", "--out", str(idx)], cwd=tmp_path)
    assert rc == 0 and idx.exists()
    sections = json.loads(idx.read_text(encoding="utf-8"))["sections"]
    assert len(sections) == 2

    cands = tmp_path / "cands.json"
    rc, out, err = _run(["candidates", "--index", str(idx), "--out", str(cands),
                         "--min-score", "0.01"], cwd=tmp_path)
    assert rc == 0
    data = json.loads(cands.read_text(encoding="utf-8"))
    assert data["n_candidates"] >= 1

    # check at error severity with a low block-score must flag the obvious gap
    rc, out, err = _run(["check", "surveys/s", "--severity", "error",
                         "--min-score", "0.01", "--block-score", "0.01"],
                        cwd=tmp_path)
    assert rc == 1                                # blocking gap detected

    # off severity is always silent + exit 0
    rc, out, err = _run(["check", "surveys/s", "--severity", "off"], cwd=tmp_path)
    assert rc == 0
