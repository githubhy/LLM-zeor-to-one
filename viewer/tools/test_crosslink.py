"""Tests for crosslink.py.

Covers: tokenization, directional link syntax (make_link), the normalize-with-map
matcher + insertion-point finder, candidate generation (cross-file only +
file-scoped dedup), and a CLI smoke test (extract -> candidates -> check).
"""
import importlib.util
import json
import pytest
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


# -- unit: heading recognition (regression, bug 2026-07-09-13) ---------------

def test_match_heading_accepts_dotted_forms():
    for line, num in [
        ("## 2.1 Title", "2.1"),
        ("### <a id=\"sec-3.7.6\"></a>3.7.6 Quantization", "3.7.6"),
        ("## D.3 Appendix section", "D.3"),
        ("#### A.8.3 Deep section", "A.8.3"),
    ]:
        m = cl.match_heading(line)
        assert m is not None, line
        assert m.group("num") == num


def test_match_heading_accepts_flat_wiki_forms():
    """`## § 1 — …` / `## 1. …` / `## 1 — …` are real wiki headings. Requiring a
    dot made 8 of 14 scoped wikis yield zero sections (bug 2026-07-09-13)."""
    for line, num in [
        ("## § 1 — The scalar-reliability program", "1"),
        ("## 1. DE/EXIT is asymptotic", "1"),
        ("## 1 — Scope: what MI-max means", "1"),
        ("## <a id=\"sec-4\"></a>4 — Self-attention derivation", "4"),
        ("## § 12. Later section", "12"),
    ]:
        m = cl.match_heading(line)
        assert m is not None, line
        assert m.group("num") == num


def test_match_heading_accepts_flat_number_carrying_matching_anchor():
    """`## <a id="sec-17"></a>17 Master matrix` — plain space separator, but the
    anchor is explicit authorial intent (turbo-decoder/evaluation-and-sota.md)."""
    m = cl.match_heading('## <a id="sec-17"></a>17 Master comparison matrix')
    assert m is not None and m.group("num") == "17"
    m = cl.match_heading('### <a id="sec-3-step-2"></a>3 Recombine')
    assert m is not None and m.group("num") == "3"
    # a NON-matching anchor must not license an unmarked flat number
    assert cl.match_heading('## <a id="sec-9"></a>2020 in review') is None


def test_match_heading_rejects_unmarked_prose_numbers():
    """A flat number with no §, no trailing dot and no dash separator is prose."""
    for line in [
        "## 2020 in review",
        "## 5 reasons the decoder stalls",
        "## Setup",
        "## Abstract",
    ]:
        assert cl.match_heading(line) is None, line


def test_sec_anchor_re_accepts_flat_anchor():
    """`#sec-4` is the wiki-target form this module's docstring prescribes."""
    for anchor in ["sec-4", "sec-1", "sec-2.1", "sec-D.3.1", "sec-3-step-2",
                   "sec-D.6-A"]:
        m = cl.SEC_ANCHOR_RE.search(f'<a id="{anchor}"></a>')
        assert m is not None, anchor
        assert m.group(1) == anchor


def test_flat_heading_wiki_is_extracted_and_targetable(tmp_path):
    """End-to-end: a flat-numbered wiki yields sections AND is link-targetable."""
    w = tmp_path / "w.md"
    w.write_text(
        '## <a id="sec-1"></a>§ 1 — Self-attention score operator\n\n'
        'The self-attention gradient descent operator over the tanh domain.\n',
        encoding="utf-8")
    secs = cl.extract_file(str(w))
    assert len(secs) == 1
    assert secs[0]["sec"] == "1"
    assert secs[0]["anchor"] == "sec-1"          # targetable, not just a source


# -- unit: coverage reporting (anti-silence, bug 2026-07-09-13) --------------

def test_parse_paths_flags_empty_and_unanchored(tmp_path):
    empty_f = tmp_path / "empty.md"
    empty_f.write_text("# Title\n\n## Setup\n\nProse with no numbered heading.\n",
                       encoding="utf-8")
    unanch = tmp_path / "unanchored.md"
    unanch.write_text("## 1. Numbered but no anchor\n\nBody text here.\n",
                      encoding="utf-8")
    good = tmp_path / "good.md"
    good.write_text('## <a id="sec-1.1"></a>1.1 Anchored\n\nBody text here.\n',
                    encoding="utf-8")

    sections, empty, unanchored = cl.parse_paths(
        [str(empty_f), str(unanch), str(good)])
    assert [Path(p).name for p in empty] == ["empty.md"]
    assert [Path(p).name for p in unanchored] == ["unanchored.md"]
    assert len(sections) == 2                    # unanchored still a source


# -- unit: directional link syntax ------------------------------------------

def _sec(file, base, corpus, sec, anchor, title="Title"):
    # `path` is identity, `base` is a display name. Never a default: a fixture that
    # omits `path` must fail loudly, not fall back to basename identity (bugs/2026-07-10-18).
    return {"file": file, "path": file, "base": base, "corpus": corpus, "sec": sec,
            "anchor": anchor, "title": title}


def test_make_link_same_survey_target_uses_secxref():
    src = _sec("surveys/x/a.md", "a.md", "survey", "1.1", "sec-1.1")
    dst = _sec("surveys/x/b.md", "b.md", "survey", "2.1", "sec-2.1")
    link, dedup = cl.make_link(src, dst)
    assert link == "<!-- secxref:2.1 -->[§2.1](b.md#sec-2.1)"
    assert dedup == "b.md#sec-2.1"


def test_make_link_cross_survey_target_is_plain_no_glyph_no_secxref():
    """secxref resolves via the SOURCE survey's order.json, so it must never
    cross a survey boundary (bug 2026-07-09-14). Also: no `§` in link text —
    it trips the bare-ref gate."""
    src = _sec("surveys/x/a.md", "a.md", "survey", "1.1", "sec-1.1")
    dst = _sec("surveys/y/b.md", "b.md", "survey", "2.1", "sec-2.1",
               title="MIMO channel estimation")
    link, _ = cl.make_link(src, dst)
    assert "secxref" not in link and "§" not in link
    assert link.startswith("[MIMO channel estimation](")
    assert "../y/b.md#sec-2.1" in link


def test_make_link_single_file_survey_has_no_order_json_so_plain():
    """`surveys/foo.md` has no order.json — a secxref from it cannot resolve."""
    src = _sec("surveys/foo.md", "foo.md", "survey", "1.1", "sec-1.1")
    dst = _sec("surveys/bar.md", "bar.md", "survey", "2.1", "sec-2.1", title="Bar")
    link, _ = cl.make_link(src, dst)
    assert "secxref" not in link and "§" not in link
    # ...and INTO a single-file survey from a dir-survey is equally plain
    src2 = _sec("surveys/x/a.md", "a.md", "survey", "1.1", "sec-1.1")
    link2, _ = cl.make_link(src2, dst)
    assert "secxref" not in link2 and "§" not in link2


def test_make_link_wiki_source_to_survey_target_is_plain():
    """A wiki has no order.json either, so it must not emit a secxref."""
    src = _sec("wikis/w.md", "w.md", "wiki", "3", "sec-3")
    dst = _sec("surveys/x/b.md", "b.md", "survey", "2.1", "sec-2.1", title="Decoding")
    link, _ = cl.make_link(src, dst)
    assert "secxref" not in link and "§" not in link
    assert link.startswith("[Decoding](")


def test_survey_dir_of():
    assert cl.survey_dir_of("surveys/llms-for-coding/appendix-d.md") == "surveys/llms-for-coding"
    assert cl.survey_dir_of("surveys/foo.md") is None
    assert cl.survey_dir_of("wikis/w.md") is None


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
    text = "Intro.\n\n1. **Sign product:** XOR of all incoming sign bits.\n2. Next."
    ip = cl.find_insertion_point(text, "XOR of all incoming sign bits")
    assert ip is not None
    # insertion point lands just after "bits", before the period
    assert text[ip - 4:ip] == "bits"
    assert text[ip] == "."


def test_find_insertion_point_missing_returns_none():
    assert cl.find_insertion_point("nothing here", "absent phrase quote") is None


# -- unit: candidate generation ---------------------------------------------

def _section(file, base, corpus, sec, anchor, body, existing=None):
    # `existing` entries are (resolved path, anchor) -- see bugs/2026-07-10-18.
    return {"file": file, "path": file, "base": base, "corpus": corpus, "sec": sec,
            "title": f"{sec} title", "anchor": anchor,
            "tokens": cl.tokenize(body), "snippet": body[:120],
            "existing": existing or []}


# -- bugs/2026-07-09-07: one planner for check and candidates ----------------

def test_check_and_candidates_share_identical_planner_defaults():
    """`check` (the gate) and `candidates` (the pipeline that clears it) built
    their sets with different parameters, so each proposed pairs the other never
    saw. At --severity=error a divergent pair blocked every push and could not be
    cleared -- the operator had to hand-write a pair_key rejection."""
    p = cl.build_parser()
    chk = p.parse_args(["check", "x.md"])
    cnd = p.parse_args(["candidates", "--index", "i.json", "--out", "o.json"])
    for field in ("per_source", "min_score", "max_candidates"):
        assert getattr(chk, field) == getattr(cnd, field), \
            f"{field} diverges: check={getattr(chk, field)} candidates={getattr(cnd, field)}"


def test_gap_config_defaults_are_the_canonical_ones():
    # Pinned on purpose: these two numbers were derived from measurement, not chosen.
    # per_source = 1 dominates 3 at every deployment budget (decisions/2026-07-10-06);
    # min_score = 0.20 minimises tokens per accepted link (decisions/2026-07-10-03).
    # If you change them, change the decision record too -- and note that
    # .githooks/pre-push deliberately passes NO --min-score so this is the only source.
    cfg = cl.GapConfig()
    assert cfg.per_source == cl.DEFAULT_PER_SOURCE == 1
    assert cfg.min_score == cl.DEFAULT_MIN_SCORE == 0.20
    assert cfg.file_scoped is True, "file-scoped dedup is what apply() enforces"


def test_rejecting_a_pair_frees_its_per_source_slot():
    """The ledger filter used to run AFTER the per-source cap, so a rejected pair
    consumed a top-k slot and the next-best target was never surfaced. The gate
    could not converge."""
    shared = "alpha beta gamma delta epsilon "
    src = _extracted("a.md", "1.1", "source", body=shared * 30)
    best = _extracted("b.md", "2.1", "best", body=shared * 30)
    nxt = _extracted("c.md", "3.1", "next", body="alpha beta " * 30)

    cfg = cl.GapConfig(per_source=1, min_score=0.05)
    first, _ = cl.plan_gaps([src, best, nxt], cfg)
    assert first, "fixture must produce a candidate"
    top = first[0]

    cfg2 = cfg._replace(rejected=frozenset({top["pair_key"]}))
    second, _ = cl.plan_gaps([src, best, nxt], cfg2)
    assert second, "rejecting the top pair must surface the next-best target"
    assert second[0]["pair_key"] != top["pair_key"]


def _extracted(base, sec, title, body, anchor=None):
    """Mimic extract_file's record, including tokens = tokenize(title + body)."""
    return {"file": f"surveys/s/{base}", "path": f"surveys/s/{base}",
            "base": base, "corpus": "survey",
            "sec": sec, "title": title, "anchor": anchor or f"sec-{sec}",
            "tokens": cl.tokenize(title + " " + body),
            "snippet": cl.first_paragraph(body),
            "has_prose": bool(cl.first_paragraph(body).strip()),
            "existing": []}


# -- bugs/2026-07-09-11: a prose-less section cannot be a link source ---------

def test_strip_noise_drops_toc_nav():
    """`<div align="right"><a href="#toc">↑ Back to TOC</a></div>` appears under
    nearly every container heading. The generic tag-strip removes the tags and
    leaves the WORDS, so `back` and `toc` entered every container's vector."""
    body = '<div align="right"><a href="#toc">↑ Back to TOC</a></div>\n'
    out = cl._strip_noise(body).lower()
    assert "toc" not in out
    assert "back" not in out


def test_container_section_has_no_prose(tmp_path):
    """A heading immediately followed by its own first subsection has no body."""
    f = tmp_path / "s.md"
    f.write_text(
        '<!-- sec:12 -->\n## <a id="sec-12"></a>12. State of the Art\n'
        '<div align="right"><a href="#toc">↑ Back to TOC</a></div>\n\n'
        '<!-- sec:12.1 -->\n### <a id="sec-12.1"></a>12.1 Detail\n\n'
        'Real prose about gradient descent and the self-attention operator.\n',
        encoding="utf-8")
    secs = {s["sec"]: s for s in cl.extract_file(str(f))}
    assert secs["12"]["has_prose"] is False
    assert secs["12.1"]["has_prose"] is True


def test_prose_less_section_is_never_a_candidate_source():
    """The bug's signature: two surveys' `## 12. State of the Art` sections have
    title-only vectors, so they score cosine 1.000 against each other. 63% of
    >=0.30 candidates had such a source, and `apply` could never place a phrase
    in one -- the judge was paid to reject the tool's own artifacts."""
    a = _extracted("a.md", "12", "State of the Art and Current Practice", body="")
    b = _extracted("b.md", "12", "State of the Art and Current Practice", body="")

    # The fixture must actually reproduce the degenerate pair, or the assertion
    # below would pass vacuously.
    forced = [dict(a, has_prose=True), dict(b, has_prose=True)]
    assert cl.generate_candidates(forced, 3, 0.9, False), \
        "fixture must reproduce the cosine-1.000 pair"

    assert cl.generate_candidates([a, b], 3, 0.9, False) == [], \
        "a section with no prose cannot host a link"


def test_prose_less_section_is_still_a_valid_target():
    """A container is a bad vector and a GOOD target: 'see §8 Frequency Tracking'
    is exactly where a reader wants to land. Kept links and rejected pairs both
    have a median of 7 unique terms on the target side, so only the SOURCE side
    admits a clean rule."""
    src = _extracted("c.md", "3.1", "Frequency tracking loop",
                     body="frequency tracking loop discriminator " * 20)
    tgt = _extracted("t.md", "8", "Frequency Tracking", body="")
    assert tgt["has_prose"] is False

    cands = cl.generate_candidates([src, tgt], 3, 0.05, False)
    assert any(c["target"]["sec"] == "8" for c in cands), \
        "a prose-less section must remain reachable as a link target"


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
    a_linked = dict(a, existing=[("surveys/s/b.md", "sec-2.1")])
    cands2 = cl.generate_candidates([a_linked, b], per_source=3, min_score=0.01,
                                    keep_symmetric=True, file_scoped=True)
    assert ("1.1", "2.1") not in {
        (c["source"]["sec"], c["target"]["sec"]) for c in cands2}


# -- unit: named corpus groups ----------------------------------------------

def test_load_scope_parses_named_groups(tmp_path):
    f = tmp_path / "scope"
    f.write_text(
        "# comment\n"
        "[fec-decoding]\n"
        "surveys/llms-for-coding\n"
        "wikis/a.md\n"
        "\n"
        "[data-channel-rx]\n"
        "surveys/pusch-receiver\n",
        encoding="utf-8")
    g = cl.load_scope(str(f))
    assert list(g) == ["fec-decoding", "data-channel-rx"]      # order preserved
    assert g["fec-decoding"] == ["surveys/llms-for-coding", "wikis/a.md"]
    assert g["data-channel-rx"] == ["surveys/pusch-receiver"]


def test_load_scope_flat_legacy_file_is_one_default_group(tmp_path):
    f = tmp_path / "scope"
    f.write_text("# legacy\nsurveys/llms-for-coding\nwikis/a.md\n", encoding="utf-8")
    g = cl.load_scope(str(f))
    assert g == {"default": ["surveys/llms-for-coding", "wikis/a.md"]}


def test_check_never_proposes_across_groups(tmp_path):
    """The point of groups: two near-identical surveys in DIFFERENT groups must
    never propose a link at each other."""
    for d in ("g1", "g2"):
        p = tmp_path / "surveys" / d
        p.mkdir(parents=True)
        body = ("self-attention gradient descent layer normalization residual stream softmax "
                "rotary embedding key value cache speculative decoding")
        (p / "a.md").write_text(
            f'## <a id="sec-1.1"></a>1.1 Heading A\n\nThe {body}.\n', encoding="utf-8")
        (p / "b.md").write_text(
            f'## <a id="sec-2.1"></a>2.1 Heading B\n\nAlso the {body}.\n', encoding="utf-8")

    scope = tmp_path / "scope"
    scope.write_text("[one]\nsurveys/g1\n\n[two]\nsurveys/g2\n", encoding="utf-8")

    rc, out, err = _run(["check", "--scope-file", "scope", "--min-score", "0.01",
                         "--json"], cwd=tmp_path)
    assert rc == 0
    gaps = json.loads(out)["gaps"]
    assert gaps, "expected within-group gaps"
    for g in gaps:
        sg = g["source"]["file"].replace("\\", "/").split("/")[1]
        tg = g["target"]["file"].replace("\\", "/").split("/")[1]
        assert sg == tg, f"cross-group candidate leaked: {g['source']['file']} -> {g['target']['file']}"
    assert {g["group"] for g in gaps} == {"one", "two"}        # both checked


def test_groups_cmd_lists_and_selects(tmp_path):
    scope = tmp_path / "scope"
    scope.write_text("[alpha]\nsurveys/x\n[beta]\nwikis/y.md\n", encoding="utf-8")
    rc, out, err = _run(["groups", "--scope-file", "scope"], cwd=tmp_path)
    assert rc == 0 and "alpha" in out and "beta" in out
    rc, out, err = _run(["groups", "--scope-file", "scope", "--group", "beta"],
                        cwd=tmp_path)
    assert rc == 0 and out.strip() == "wikis/y.md"
    rc, out, err = _run(["groups", "--scope-file", "scope", "--group", "nope"],
                        cwd=tmp_path)
    assert rc == 2


def test_generate_candidates_dedups_the_reverse_direction():
    """Once a->b is linked, b->a is not a gap — the pair is connected. Without
    this, every applied link is re-reported forever backwards (bug 2026-07-09-15)."""
    shared = "self-attention gradient descent layer normalization residual stream softmax"
    # b.md already links back to a.md#sec-1.1
    a = _section("surveys/s/a.md", "a.md", "survey", "1.1", "sec-1.1", shared)
    b = _section("surveys/s/b.md", "b.md", "survey", "2.1", "sec-2.1", shared,
                 existing=[("surveys/s/a.md", "sec-1.1")])

    cands = cl.generate_candidates([a, b], per_source=3, min_score=0.01,
                                   keep_symmetric=True, file_scoped=True)
    pairs = {(c["source"]["sec"], c["target"]["sec"]) for c in cands}
    assert ("2.1", "1.1") not in pairs      # forward: already linked
    assert ("1.1", "2.1") not in pairs      # reverse: pair already connected


# -- unit: rejection ledger --------------------------------------------------

def test_generate_candidates_honours_rejection_ledger():
    shared = "self-attention gradient descent layer normalization residual stream softmax"
    a = _section("surveys/s/a.md", "a.md", "survey", "1.1", "sec-1.1", shared)
    b = _section("surveys/s/b.md", "b.md", "survey", "2.1", "sec-2.1", shared)

    cands = cl.generate_candidates([a, b], per_source=3, min_score=0.01,
                                   keep_symmetric=True)
    assert cands
    pk = cands[0]["pair_key"]

    suppressed = cl.generate_candidates([a, b], per_source=3, min_score=0.01,
                                        keep_symmetric=True, rejected={pk})
    assert not suppressed          # a judged-rejected pair is not a gap


def test_reject_cmd_is_idempotent_and_only_stores_rejections(tmp_path):
    cands = {"candidates": [
        {"id": "C001", "pair_key": "a.md#1.1|b.md#2.1", "score": 0.4},
        {"id": "C002", "pair_key": "a.md#1.2|b.md#2.2", "score": 0.35},
    ]}
    (tmp_path / "c.json").write_text(json.dumps(cands), encoding="utf-8")
    (tmp_path / "d.json").write_text(json.dumps({"decisions": [
        {"id": "C001", "keep": False, "anchor_phrase": ""},
        {"id": "C002", "keep": True, "anchor_phrase": "x"},
    ]}), encoding="utf-8")

    led = tmp_path / "rej.json"
    for _ in range(2):                       # run twice -> idempotent
        rc, out, err = _run(["reject", "--candidates", "c.json",
                             "--decisions", "d.json", "--out", "rej.json",
                             "--note", "t"], cwd=tmp_path)
        assert rc == 0
    data = json.loads(led.read_text(encoding="utf-8"))["rejected"]
    assert [r["pair_key"] for r in data] == ["a.md#1.1|b.md#2.1"]   # kept one absent
    assert cl.load_rejections(str(led)) == {"a.md#1.1|b.md#2.1"}


def test_load_rejections_missing_file_is_empty():
    assert cl.load_rejections("does/not/exist.json") == set()
    assert cl.load_rejections(None) == set()


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


def test_cli_check_refuses_empty_corpus(tmp_path):
    """`check` with no corpus must NOT print a reassuring 'no gaps'."""
    rc, out, err = _run(["check"], cwd=tmp_path)
    assert rc == 2
    assert "no cross-link gaps" not in err
    assert "empty corpus" in err

    # a corpus of only unmatched-heading files is equally not a pass
    sdir = tmp_path / "surveys" / "s"
    sdir.mkdir(parents=True)
    (sdir / "prose.md").write_text("# T\n\n## Setup\n\nNo numbered heading.\n",
                                   encoding="utf-8")
    rc, out, err = _run(["check", "surveys/s"], cwd=tmp_path)
    assert rc == 2
    assert "no cross-link gaps" not in err


def test_cli_extract_warns_and_strict_fails_on_zero_section_file(tmp_path):
    """A scoped file contributing 0 sections must never pass silently."""
    sdir = tmp_path / "surveys" / "s"
    sdir.mkdir(parents=True)
    (sdir / "a.md").write_text(
        '## <a id="sec-1.1"></a>1.1 Heading A\n\nSelf-attention gradient descent.\n',
        encoding="utf-8")
    (sdir / "invisible.md").write_text(
        "# Title\n\n## Setup\n\nNo numbered heading anywhere.\n", encoding="utf-8")

    idx = tmp_path / "idx.json"
    rc, out, err = _run(["extract", "surveys/s", "--out", str(idx)], cwd=tmp_path)
    assert rc == 0
    assert "WARNING: 0 sections" in err and "invisible.md" in err
    assert "1/2 files" in err                     # coverage is visible in the tally

    rc, out, err = _run(["extract", "surveys/s", "--out", str(idx), "--strict"],
                        cwd=tmp_path)
    assert rc == 1                                # strict turns silence into failure


# -- container-vector roll-up (H-2; bugs/2026-07-09-11 target side) -----------

_CONTAINER_A = """# <a id="sec-1"></a>1. Attention Decoding

<!-- sec:1.5 -->
## <a id="sec-1.5"></a>1.5 State of the Art and Current Practice

<!-- sec:1.5.1 -->
### <a id="sec-1.5.1"></a>1.5.1 Layered schedules

Layered attention halves the memory traffic by streaming key/value blocks
sequentially, reusing partial softmax statistics within a single pass.
"""

_CONTAINER_B = """# <a id="sec-2"></a>2. Multimodal Fusion

<!-- sec:2.5 -->
## <a id="sec-2.5"></a>2.5 State of the Art and Current Practice

<!-- sec:2.5.1 -->
### <a id="sec-2.5.1"></a>2.5.1 Hybrid architectures

Hybrid early-late fusion places projection adapters ahead of a reduced set of
cross-attention layers, trading modality alignment depth for compute.
"""


def _two_containers(tmp_path, roll_up):
    (tmp_path / "a.md").write_text(_CONTAINER_A, encoding="utf-8")
    (tmp_path / "b.md").write_text(_CONTAINER_B, encoding="utf-8")
    secs = cl.extract_file(str(tmp_path / "a.md"), roll_up=roll_up) + \
        cl.extract_file(str(tmp_path / "b.md"), roll_up=roll_up)
    vecs, _ = cl.build_vectors(secs)
    by = {(s["base"], s["sec"]): i for i, s in enumerate(secs)}
    return secs, vecs, by


def test_containers_score_cosine_one_without_rollup():
    """Pins the degenerate-vector theorem itself: identical titles, empty bodies.

    Exact in exact arithmetic; the summed dot product of float64 weights lands a
    few ulp short, so compare with a tolerance rather than `== 1.0`.
    """
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        secs, vecs, by = _two_containers(pathlib.Path(d), roll_up=False)
        a, b = by[("a.md", "1.5")], by[("b.md", "2.5")]
        assert secs[a]["tokens"] == secs[b]["tokens"]      # title only, identical
        assert cl.cosine(vecs[a], vecs[b]) == pytest.approx(1.0, abs=1e-12)


def test_rollup_breaks_the_degenerate_band():
    """Same two containers, descendants rolled in: no longer twins."""
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        secs, vecs, by = _two_containers(pathlib.Path(d), roll_up=True)
        a, b = by[("a.md", "1.5")], by[("b.md", "2.5")]
        assert cl.cosine(vecs[a], vecs[b]) < 0.5
        assert "layered" in secs[a]["tokens"]     # child's prose reached the parent
        assert "hybrid" in secs[b]["tokens"]


def test_rollup_leaves_has_prose_and_snippet_alone():
    """A container must stay a bad SOURCE (no anchor phrase) and a good TARGET."""
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        secs, _v, by = _two_containers(pathlib.Path(d), roll_up=True)
        container = secs[by[("a.md", "1.5")]]
        leaf = secs[by[("a.md", "1.5.1")]]
        assert container["has_prose"] is False        # cannot host a link
        assert container["snippet"].strip() == ""
        assert container["anchor"] == "sec-1.5"       # still a link target
        assert leaf["has_prose"] is True


def test_rollup_does_not_inherit_descendant_links():
    """`existing` stays own-body: a parent inheriting child links widens dedup."""
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d)
        (p / "a.md").write_text(
            "# <a id=\"sec-1\"></a>1. Top\n\n"
            "<!-- sec:1.1 -->\n## <a id=\"sec-1.1\"></a>1.1 Container\n\n"
            "<!-- sec:1.1.1 -->\n### <a id=\"sec-1.1.1\"></a>1.1.1 Leaf\n\n"
            "Prose that links to [elsewhere](other.md#sec-9).\n",
            encoding="utf-8")
        secs = cl.extract_file(str(p / "a.md"))
        by = {s["sec"]: s for s in secs}
        want = cl.resolve_target(str(p).replace("\\", "/"), "other.md")
        assert (want, "sec-9") in by["1.1.1"]["existing"]
        assert by["1.1"]["existing"] == []            # parent did NOT inherit it


def test_rollup_mints_no_bigram_across_the_seam():
    """Token LISTS are concatenated, not texts -- no parent-last + child-first bigram."""
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d)
        (p / "a.md").write_text(
            "# <a id=\"sec-1\"></a>1. Top\n\n"
            "<!-- sec:1.1 -->\n## <a id=\"sec-1.1\"></a>1.1 Container\n\n"
            "alpha bravo\n\n"
            "<!-- sec:1.1.1 -->\n### <a id=\"sec-1.1.1\"></a>1.1.1 Leaf\n\n"
            "charlie delta\n",
            encoding="utf-8")
        toks = {s["sec"]: s["tokens"] for s in cl.extract_file(str(p / "a.md"))}
        assert "alpha_bravo" in toks["1.1"]
        assert "charlie_delta" in toks["1.1"]         # child's own bigram carried up
        assert "bravo_leaf" not in toks["1.1"]        # seam bigram never minted
        assert "bravo_charlie" not in toks["1.1"]


def test_descendants_of_stops_at_a_sibling():
    heads = [(0, "1", "t", None, 2), (1, "1.1", "t", None, 3),
             (2, "1.1.1", "t", None, 4), (3, "1.2", "t", None, 3),
             (4, "2", "t", None, 2)]
    assert cl.descendants_of(heads, 0) == [1, 2, 3]   # everything under 1
    assert cl.descendants_of(heads, 1) == [2]         # 1.1.1 only, stops at 1.2
    assert cl.descendants_of(heads, 3) == []          # 1.2 is a leaf
    assert cl.descendants_of(heads, 4) == []


# -- link text sanitization (bugs/2026-07-10-14) ------------------------------

def test_link_text_strips_comments_brackets_and_glyph():
    nasty = "CORESET Structure (TS 38.213 <!-- secref:10.1 -->[§10.1](#sec-10.1))"
    t = cl.link_text_of(nasty)
    assert "<!--" not in t and "-->" not in t
    assert "[" not in t and "]" not in t
    assert "§" not in t
    assert t.startswith("CORESET Structure")


def test_make_link_never_emits_a_broken_link_from_a_dirty_title():
    src = _sec("surveys/a.md", "a.md", "survey", "4.2", "sec-4.2")
    dst = _sec("surveys/b.md", "b.md", "survey", "4.2", "sec-4.2",
               title="CORESET Structure (TS 38.213 <!-- secref:10.1 -->[§10.1](#sec-10.1))")
    link, _ = cl.make_link(src, dst)
    # exactly one markdown link, balanced, no comment, no glyph
    assert link.count("[") == 1 and link.count("]") == 1
    assert "<!--" not in link and "§" not in link
    assert link.endswith("(b.md#sec-4.2)")


def test_make_link_drops_a_dangling_open_paren_after_truncation():
    src = _sec("surveys/a.md", "a.md", "survey", "1", "sec-1")
    dst = _sec("surveys/b.md", "b.md", "survey", "2", "sec-2",
               title="One two three four five (six seven eight)")
    link, _ = cl.make_link(src, dst)
    assert not link.split("]")[0].rstrip().endswith("(")


# -- apply idempotency must be exact, not substring (bugs/2026-07-10-15) ------

def test_apply_does_not_skip_ancestor_anchor_when_descendant_is_linked(tmp_path):
    """`a.md#sec-4` is a SUBSTRING of `a.md#sec-4.2`. A substring test silently
    drops the ancestor link and reports it as already-present."""
    srcf = tmp_path / "s.md"
    srcf.write_text(
        '## <a id="sec-1"></a>1. Source\n\n'
        'Prose citing the deep part [deep](a.md#sec-4.2) already.\n'
        'Ericsson Many Core Architecture is the anchor phrase here.\n',
        encoding="utf-8")
    cands = {"candidates": [{
        "id": "C001", "score": 0.5, "pair_key": "x",
        "source": {"file": str(srcf), "sec": "1", "title": "Source", "snippet": ""},
        "target": {"file": str(tmp_path / "a.md"), "sec": "4", "title": "Arch",
                   "snippet": "", "corpus": "survey"},
        "link_markdown": "[Arch](a.md#sec-4)",
        "dedup_target": "a.md#sec-4",
    }]}
    decs = {"decisions": [{"id": "C001", "keep": True,
                           "anchor_phrase": "Ericsson Many Core Architecture"}]}
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")

    r = subprocess.run([sys.executable, str(SCRIPT), "apply", "--candidates", str(cf),
                        "--decisions", str(df), "--reviewed-by", "test"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    # `apply` reports on STDERR; asserting on stdout alone is vacuously true.
    report = r.stdout + r.stderr
    assert "already-present" not in report, report
    out = srcf.read_text(encoding="utf-8")
    assert "[Arch](a.md#sec-4)" in out           # the ancestor link landed
    assert "[deep](a.md#sec-4.2)" in out         # the descendant link untouched


def test_apply_still_skips_an_exactly_present_target(tmp_path):
    srcf = tmp_path / "s.md"
    srcf.write_text(
        '## <a id="sec-1"></a>1. Source\n\n'
        'Already linked [Arch](a.md#sec-4) here. Anchor phrase lives on.\n',
        encoding="utf-8")
    cands = {"candidates": [{
        "id": "C001", "score": 0.5, "pair_key": "x",
        "source": {"file": str(srcf), "sec": "1", "title": "Source", "snippet": ""},
        "target": {"file": str(tmp_path / "a.md"), "sec": "4", "title": "Arch",
                   "snippet": "", "corpus": "survey"},
        "link_markdown": "[Arch](a.md#sec-4)", "dedup_target": "a.md#sec-4",
    }]}
    decs = {"decisions": [{"id": "C001", "keep": True,
                           "anchor_phrase": "Anchor phrase lives on"}]}
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "apply", "--candidates", str(cf),
                        "--decisions", str(df), "--reviewed-by", "test"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert "already-present" in (r.stdout + r.stderr)


def test_apply_dedups_two_candidates_to_one_target_within_a_run(tmp_path):
    """bugs/2026-07-11-01: two candidates whose sources sit in the SAME file and point
    at the SAME target must not both insert in one run. `existing_targets` is a pre-run
    snapshot, so without seeding it as we plan, both pass and the target is double-linked
    — violating the 'at most once per file' invariant intra-run."""
    srcf = tmp_path / "s.md"
    srcf.write_text(
        '## <a id="sec-1"></a>1. First\n\nFirst section anchor alpha here.\n\n'
        '## <a id="sec-2"></a>2. Second\n\nSecond section anchor beta here.\n',
        encoding="utf-8")
    tgt = str(tmp_path / "a.md")

    def cand(cid, sec):
        return {"id": cid, "score": 0.5, "pair_key": cid,
                "source": {"file": str(srcf), "sec": sec, "title": "S", "snippet": ""},
                "target": {"file": tgt, "sec": "4", "title": "Arch", "snippet": "",
                           "corpus": "survey"},
                "link_markdown": "[Arch](a.md#sec-4)", "dedup_target": "a.md#sec-4"}
    cands = {"candidates": [cand("C001", "1"), cand("C002", "2")]}
    decs = {"decisions": [
        {"id": "C001", "keep": True, "anchor_phrase": "First section anchor alpha"},
        {"id": "C002", "keep": True, "anchor_phrase": "Second section anchor beta"}]}
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), "apply", "--candidates", str(cf),
                        "--decisions", str(df), "--reviewed-by", "test"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr
    body = srcf.read_text(encoding="utf-8")
    assert body.count("[Arch](a.md#sec-4)") == 1, f"target double-linked: {body}"
    assert "already-present" in (r.stdout + r.stderr)


def test_find_insertion_point_refuses_a_mid_word_anchor():
    """bug 2026-07-11-03: a truncated anchor that matches inside a word must not
    yield an insertion point — inserting there splits the token (the mid-URL case
    'refer' -> 'references.md' corrupted a citation). A clean boundary still resolves."""
    text = "keeps only the frequencies with energy here.\n"
    assert cl.find_insertion_point(text, "frequencies wit") is None  # inside 'with'
    assert cl.find_insertion_point(text, "frequencies with energy") is not None


# --- bugs/2026-07-10-18: files are identified by PATH, never by basename -------
#
# Four surveys in the `spatial-sensing` group carry a `fundamentals.md`. Keying identity
# on the basename fused them into one file: cross-file pairs between them were skipped
# as "same-file", `file_existing` merged their outbound links, and `pair_key` collided so
# a ledger rejection suppressed a different pair.

def _twin_surveys(tmp_path, extra_a="", extra_b=""):
    """Two surveys, each with a `fundamentals.md`, sharing enough vocabulary to score."""
    a = tmp_path / "surveys" / "alpha"
    b = tmp_path / "surveys" / "beta"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    body = ("Turbo decoding uses the BCJR recursion over a trellis, with extrinsic "
            "log-likelihood ratios exchanged between constituent decoders. ")
    (a / "fundamentals.md").write_text(
        '## <a id="sec-1.2"></a>1.2 Trellis\n\n' + body + extra_a + "\n", encoding="utf-8")
    (b / "fundamentals.md").write_text(
        '## <a id="sec-1.1"></a>1.1 BCJR\n\n' + body + extra_b + "\n", encoding="utf-8")
    return [str(a / "fundamentals.md"), str(b / "fundamentals.md")]


def _sections(paths):
    secs = []
    for p in paths:
        secs.extend(cl.extract_file(p))
    return secs


def test_same_named_files_in_different_dirs_are_not_the_same_file(tmp_path):
    paths = _twin_surveys(tmp_path)
    secs = _sections(paths)
    assert secs[0]["base"] == secs[1]["base"] == "fundamentals.md"
    assert secs[0]["path"] != secs[1]["path"]
    cands = cl.generate_candidates(secs, per_source=3, min_score=0.0,
                                          keep_symmetric=False)
    # The pair must be PROPOSED. Under basename identity it was skipped as "cross-file only".
    assert len(cands) == 1, f"expected the twin pair to be proposable, got {cands}"


def test_a_link_from_one_twin_does_not_dedup_a_proposal_from_the_other(tmp_path):
    # `alpha/fundamentals.md` already links the target; `beta/fundamentals.md` does not.
    # Under basename identity, file_existing["fundamentals.md"] merged both, so beta's
    # proposal was deduped away by alpha's link.
    a = tmp_path / "surveys" / "alpha"
    b = tmp_path / "surveys" / "beta"
    t = tmp_path / "surveys" / "gamma"
    for d in (a, b, t):
        d.mkdir(parents=True)
    body = ("Turbo decoding uses the BCJR recursion over a trellis with extrinsic "
            "log-likelihood ratios exchanged between constituent decoders. ")
    (t / "target.md").write_text('## <a id="sec-4"></a>4. BCJR derivation\n\n' + body,
                                 encoding="utf-8")
    (a / "fundamentals.md").write_text(
        '## <a id="sec-1.2"></a>1.2 Trellis\n\n' + body +
        "See [BCJR derivation](../gamma/target.md#sec-4).\n", encoding="utf-8")
    (b / "fundamentals.md").write_text(
        '## <a id="sec-1.1"></a>1.1 BCJR\n\n' + body, encoding="utf-8")
    secs = _sections([str(a / "fundamentals.md"), str(b / "fundamentals.md"),
                      str(t / "target.md")])
    cands = cl.generate_candidates(secs, per_source=3, min_score=0.0,
                                          keep_symmetric=True, file_scoped=True)
    beta_to_target = [c for c in cands
                      if c["source"]["file"].endswith("beta/fundamentals.md")
                      and c["target"]["file"].endswith("gamma/target.md")]
    assert beta_to_target, "beta's proposal was deduped by alpha's link (basename fusion)"


def test_pair_keys_of_same_named_files_differ(tmp_path):
    paths = _twin_surveys(tmp_path)
    secs = _sections(paths)
    cands = cl.generate_candidates(secs, per_source=3, min_score=0.0,
                                          keep_symmetric=True)
    keys = {c["pair_key"] for c in cands}
    # Under basename identity both directions collapsed to "fundamentals.md#1.1|fundamentals.md#1.2".
    for k in keys:
        left, right = k.split("|")
        assert left != right, f"pair_key collapses a twin pair onto itself: {k}"
        assert "surveys/alpha" in k and "surveys/beta" in k, k


def test_resolve_target_walks_out_of_the_source_directory():
    assert cl.resolve_target("surveys/a", "../../wikis/foo.md") == "wikis/foo.md"
    assert cl.resolve_target("surveys/a", "b.md") == "surveys/a/b.md"
    assert cl.resolve_target("", "b.md") == "b.md"


def test_resolve_target_leaves_urls_and_absolute_paths_alone():
    # These can never name a corpus section; returning the basename silently fused files.
    assert cl.resolve_target("surveys/a", "https://x.test/y.md") == "https://x.test/y.md"
    assert cl.resolve_target("surveys/a", "/abs/y.md") == "/abs/y.md"


def test_existing_links_record_the_resolved_path(tmp_path):
    d = tmp_path / "surveys" / "alpha"
    d.mkdir(parents=True)
    (d / "s.md").write_text(
        '## <a id="sec-1"></a>1. S\n\nText [x](../../wikis/w.md#sec-2) and [y](#sec-1).\n',
        encoding="utf-8")
    secs = cl.extract_file(str(d / "s.md"))
    ex = dict(secs[0]["existing"])
    resolved = [k for k in ex if k.endswith("wikis/w.md")]
    assert resolved, secs[0]["existing"]           # `../../wikis/w.md` walked out
    assert "w.md" not in ex, "recorded the basename, not the resolved path"
    assert secs[0]["path"] in ex, secs[0]["existing"]   # `#sec-1` -> own path


def test_git_changed_md_yields_paths_not_basenames(monkeypatch):
    # `generate_candidates` filters on src["path"]; a basename can never equal one.
    import subprocess as sp

    class R:
        stdout = "surveys/alpha/fundamentals.md\nsurveys/beta/fundamentals.md\n"

    monkeypatch.setattr(sp, "run", lambda *a, **k: R())
    got = cl.git_changed_md()
    assert got == {"surveys/alpha/fundamentals.md", "surveys/beta/fundamentals.md"}


# --- plan 2026-07-10-crosslink-detector-only: detect, do not auto-apply ---------

def _cand(cid="C001", score=0.38, src_file="surveys/a/x.md", src_sec="1.2",
          dst_file="surveys/b/y.md", dst_sec="1.1", snippet="The reason it holds is clear."):
    return {
        "id": cid, "score": score, "pair_key": f"{src_file}#{src_sec}|{dst_file}#{dst_sec}",
        "source": {"file": src_file, "sec": src_sec, "title": "Source title", "snippet": snippet},
        "target": {"file": dst_file, "sec": dst_sec, "title": "Target title",
                   "snippet": "Target prose.", "corpus": "survey"},
        "link_markdown": f"[Target title]({dst_file}#sec-{dst_sec})",
        "dedup_target": f"{dst_file}#sec-{dst_sec}",
    }


def _cli(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_review_emits_one_block_per_candidate_with_three_unchecked_boxes(tmp_path):
    cands = {"candidates": [_cand("C001"), _cand("C002", src_sec="2.3")]}
    cf, out = tmp_path / "c.json", tmp_path / "review.md"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    r = _cli("review", "--candidates", str(cf), "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    sheet = out.read_text(encoding="utf-8")
    # one machine-readable marker per candidate
    assert sheet.count("<!-- xlink C001 ") == 1
    assert sheet.count("<!-- xlink C002 ") == 1
    # exactly three unchecked boxes per candidate (link / merge / reject)
    assert sheet.count("[ ] link") == 2
    assert sheet.count("[ ] merge") == 2
    assert sheet.count("[ ] reject") == 2


def test_apply_refuses_an_agent_decision_file(tmp_path):
    # An agent-shaped decisions file (no provenance) must be REFUSED, not applied.
    cands = {"candidates": [_cand("C001")]}
    decs = {"decisions": [{"id": "C001", "keep": True, "anchor_phrase": "it holds"}]}
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf), "--decisions", str(df), "--dry-run")
    assert r.returncode == 2, f"expected exit 2, got {r.returncode}: {r.stdout + r.stderr}"
    assert "review" in (r.stdout + r.stderr).lower()


def test_apply_accepts_a_human_reviewed_decision_file(tmp_path):
    # The SAME decisions file, stamped with human provenance, is accepted.
    srcf = tmp_path / "x.md"
    srcf.write_text('## <a id="sec-1.2"></a>1.2 S\n\nThe reason it holds is clear.\n',
                    encoding="utf-8")
    cands = {"candidates": [_cand("C001", src_file=str(srcf))]}
    decs = {"reviewed_by": "alice", "decisions":
            [{"id": "C001", "keep": True, "anchor_phrase": "it holds"}]}
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf), "--decisions", str(df), "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "applied 1/1" in (r.stdout + r.stderr)


def test_apply_reviewed_by_flag_satisfies_the_guard(tmp_path):
    srcf = tmp_path / "x.md"
    srcf.write_text('## <a id="sec-1.2"></a>1.2 S\n\nThe reason it holds is clear.\n',
                    encoding="utf-8")
    cands = {"candidates": [_cand("C001", src_file=str(srcf))]}
    decs = {"decisions": [{"id": "C001", "keep": True, "anchor_phrase": "it holds"}]}
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf), "--decisions", str(df),
             "--reviewed-by", "bob", "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr


def test_review_roundtrips_through_apply_from_review(tmp_path):
    srcf = tmp_path / "x.md"
    srcf.write_text('## <a id="sec-1.2"></a>1.2 S\n\nThe reason it holds is clear.\n',
                    encoding="utf-8")
    cands = {"candidates": [_cand("C001", src_file=str(srcf))]}
    cf, sheet = tmp_path / "c.json", tmp_path / "review.md"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    assert _cli("review", "--candidates", str(cf), "--out", str(sheet)).returncode == 0
    # human checks the `link` box
    s = sheet.read_text(encoding="utf-8").replace("[ ] link", "[x] link", 1)
    sheet.write_text(s, encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf), "--from-review", str(sheet),
             "--reviewed-by", "carol")
    assert r.returncode == 0, r.stdout + r.stderr
    body = srcf.read_text(encoding="utf-8")
    assert "surveys/b/y.md#sec-1.1" in body and body.count("(") >= 1  # link inserted


def test_apply_from_review_routes_merge_to_its_own_ledger(tmp_path):
    srcf = tmp_path / "x.md"
    srcf.write_text('## <a id="sec-1.2"></a>1.2 S\n\nText.\n', encoding="utf-8")
    cands = {"candidates": [_cand("C001", src_file=str(srcf))]}
    cf, sheet = tmp_path / "c.json", tmp_path / "review.md"
    mledger = tmp_path / "merge.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    _cli("review", "--candidates", str(cf), "--out", str(sheet))
    s = sheet.read_text(encoding="utf-8").replace("[ ] merge", "[x] merge", 1)
    sheet.write_text(s, encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf), "--from-review", str(sheet),
             "--reviewed-by", "dave", "--merge-ledger", str(mledger))
    assert r.returncode == 0, r.stdout + r.stderr
    merged = json.loads(mledger.read_text(encoding="utf-8"))["merge_candidates"]
    assert any(m["pair_key"] == cands["candidates"][0]["pair_key"] for m in merged)
    # a merge is NOT a link: the source file is unchanged
    assert "(" not in srcf.read_text(encoding="utf-8").split("Text.")[1]


def test_apply_provenance_guard_is_structurally_present(tmp_path):
    """Freeze the guard, not just its behaviour (plan Task 4). If a future edit removes
    the human-provenance refusal, TOOL_SWEEPS silently re-opens (bugs/2026-07-10-19).
    A bare --decisions file with no provenance MUST exit 2 — pinned here so the
    behavioural regression is caught even if the source is refactored."""
    cands = {"candidates": [_cand("C001")]}
    decs = [{"id": "C001", "keep": True, "anchor_phrase": "x"}]  # bare list, no reviewed_by
    cf, df = tmp_path / "c.json", tmp_path / "d.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    df.write_text(json.dumps(decs), encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf), "--decisions", str(df), "--dry-run")
    assert r.returncode == 2
    assert "provenance" in (r.stdout + r.stderr).lower()


def test_apply_needs_a_decision_source(tmp_path):
    cands = {"candidates": [_cand("C001")]}
    cf = tmp_path / "c.json"
    cf.write_text(json.dumps(cands), encoding="utf-8")
    r = _cli("apply", "--candidates", str(cf))  # neither --decisions nor --from-review
    assert r.returncode == 2
    assert "from-review" in (r.stdout + r.stderr) or "decisions" in (r.stdout + r.stderr)


# --- judge blinding + prompt as one source of truth (bugs/2026-07-10-16, -06) ---

def test_candidates_emit_a_blinded_judge_view(tmp_path):
    """The judge_view must carry ONLY {id, source, target} snippets — never the score
    it exists to be an independent check on (bugs/2026-07-10-17)."""
    w = tmp_path / "surveys" / "s"
    w.mkdir(parents=True)
    body = "Turbo decoding uses the BCJR recursion over a trellis with extrinsic LLRs. "
    (w / "a.md").write_text('## <a id="sec-1"></a>1. A\n\n' + body * 3, encoding="utf-8")
    (w / "b.md").write_text('## <a id="sec-2"></a>2. B\n\n' + body * 3, encoding="utf-8")
    idx, cf = tmp_path / "idx.json", tmp_path / "cands.json"
    assert _cli("extract", str(w / "a.md"), str(w / "b.md"), "--out", str(idx)).returncode == 0
    assert _cli("candidates", "--index", str(idx), "--out", str(cf),
                "--min-score", "0.0").returncode == 0
    out = json.loads(cf.read_text(encoding="utf-8"))
    assert "judge_view" in out and len(out["judge_view"]) == len(out["candidates"])
    blob = json.dumps(out["judge_view"])
    for leak in ("score", "pair_key", "link_markdown", "dedup_target"):
        assert f'"{leak}"' not in blob, f"judge_view leaks {leak}"
    assert set(out["judge_view"][0]["source"]) == {"file", "sec", "title", "snippet"}


def test_assert_judge_view_blind_fires_on_a_leak():
    """Positive control: the guard must reject a view that carries the score."""
    good = [{"id": "C1", "source": {"file": "a", "sec": "1", "title": "t", "snippet": "s"},
             "target": {"file": "b", "sec": "2", "title": "u", "snippet": "v"}}]
    cl.assert_judge_view_blind(good)                     # does not raise
    leaked = [dict(good[0], score=0.9)]
    try:
        cl.assert_judge_view_blind(leaked)
    except AssertionError:
        return
    raise AssertionError("assert_judge_view_blind did not fire on a score leak")


def test_judge_prompt_is_corpus_neutral_by_default():
    r = _cli("judge-prompt")
    assert r.returncode == 0
    assert "LLM inference" not in r.stdout            # bugs/2026-07-10-16: no hardcoded corpus
    assert "technical survey corpus" in r.stdout
    assert "assertion -> derivation" in r.stdout or "derives, grounds, proves" in r.stdout


# --- H-5 scope coverage: non-coverage is loud, not silent ----------------------

def test_coverage_reports_an_ungrouped_unkept_file(tmp_path, monkeypatch):
    root = tmp_path
    (root / "surveys" / "orphan-survey").mkdir(parents=True)
    (root / "surveys" / "orphan-survey" / "ch.md").write_text(
        '## <a id="sec-1"></a>1. X\n\nbody\n', encoding="utf-8")
    (root / "surveys" / "grouped").mkdir(parents=True)
    (root / "surveys" / "grouped" / "ch.md").write_text(
        '## <a id="sec-1"></a>1. Y\n\nbody\n', encoding="utf-8")
    (root / "wikis").mkdir()
    (root / ".claude").mkdir()
    scope = root / ".claude" / "scope"
    scope.write_text("[g]\nsurveys/grouped\n", encoding="utf-8")
    keep = root / ".claude" / "keepout"
    keep.write_text("# none\n", encoding="utf-8")
    monkeypatch.chdir(root)
    r = _cli("coverage", "--scope-file", str(scope), "--keepout", str(keep),
             "--severity", "error")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "orphan-survey" in (r.stdout + r.stderr)
    uncovered_lines = [ln for ln in (r.stdout + r.stderr).splitlines() if "UNCOVERED:" in ln]
    assert not any("grouped" in ln for ln in uncovered_lines)  # grouped file not flagged


def test_coverage_keepout_silences_an_orphan(tmp_path, monkeypatch):
    root = tmp_path
    (root / "surveys" / "archive").mkdir(parents=True)
    (root / "surveys" / "archive" / "old.md").write_text(
        '## <a id="sec-1"></a>1. Z\n\nbody\n', encoding="utf-8")
    (root / "wikis").mkdir()
    (root / ".claude").mkdir()
    scope = root / ".claude" / "scope"; scope.write_text("[g]\nwikis\n", encoding="utf-8")
    keep = root / ".claude" / "keepout"; keep.write_text("surveys/archive/\n", encoding="utf-8")
    monkeypatch.chdir(root)
    r = _cli("coverage", "--scope-file", str(scope), "--keepout", str(keep),
             "--severity", "error")
    assert r.returncode == 0, r.stdout + r.stderr


# -- mdctx insertion-context guard (merged from origin/main) ------------------

def test_insertion_point_is_nudged_out_of_inline_math():
    text = "clamping messages to $[-K, +K]$ — has a qualitative effect\n"
    spans = cl.mdctx.classify(text)
    mask = cl.mdctx.writable_mask(text)
    inside = text.index("$[-K, +K]$") + len("$[-K, +K]")   # just before the closing '$'
    assert not mask[inside], "the pre-fix offset is inside the math span"
    ip = cl.mdctx.advance_to_prose(text, spans, mask, inside)
    out = text[:ip] + " (L)" + text[ip:]
    assert out.startswith("clamping messages to $[-K, +K]$ (L) —"), out
    assert "$[-K, +K] (L)" not in out, "must not land inside the math span"


def test_insertion_is_refused_inside_a_fence_or_comment():
    for text in ("```\nsome code\n```\n", "<!-- some comment -->\n"):
        spans = cl.mdctx.classify(text)
        mask = cl.mdctx.writable_mask(text)
        off = text.index("some")
        assert cl.mdctx.advance_to_prose(text, spans, mask, off) is None


# -- first_paragraph word-boundary fallback (todos/2026-07-11-anchor-suggestion) --

def test_first_paragraph_falls_back_to_word_boundary_not_mid_word():
    """A long paragraph with no sentence break must be cut at a WORD boundary, so the
    anchor suggestion drawn from its tail ends on a complete word (else the
    find_insertion_point mid-word guard skips the sheet-default anchor)."""
    body = "abcde " * 60                       # 360 chars, no '. '; hard cut at 320 = mid-word 'abc'
    s = cl.first_paragraph(body)
    assert s.split()[-1] == "abcde", f"snippet ends mid-word: ...{s[-12:]!r}"
    assert not s.endswith("abc")               # the pre-fix failure mode
    assert cl._anchor_suggestion(s).split()[-1] == "abcde"


def test_first_paragraph_prefers_a_sentence_boundary_past_the_floor():
    """A '. ' boundary past the length floor still wins (unchanged behaviour)."""
    body = ("word " * 30) + "the end. " + ("y " * 100)   # >320 chars; '. ' at ~157 (> 80)
    s = cl.first_paragraph(body)
    assert s.endswith("the end."), s
