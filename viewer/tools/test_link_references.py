"""Tests for link-references.py.

Focus: the `--init` bare/compound citation rewrite must never fire inside math
or code, and must handle bibliographies of 100+ entries.

Regression for bugs/2026-08-02-link-references-rewrites-math-intervals: a
numeric interval in math (`$\\delta \\in [1,5]$` m) is token-identical to a
compound citation `[1, 5]`, and the unmasked rewrite silently destroyed the
equation while minting two citations no author wrote.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "viewer" / "tools" / "link-references.py"

spec = importlib.util.spec_from_file_location("link_references", SCRIPT)
lr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lr)


BIB = {str(n) for n in range(1, 141)}


def init(lines, bib=BIB):
    """Run the --init rewrite with no references section in scope."""
    return lr.init_cite_markers(lines, None, None, bib, link_target="references.md")


# -- the regression: math intervals are not citations ------------------------

def test_inline_math_interval_is_not_rewritten():
    src = [r"Received power measured against $\delta \in [1,5]$ m at $d = 1$ m."]
    assert init(src) == src


def test_spaced_math_interval_is_not_rewritten():
    src = [r"the destination along a line parameterized by $x \in [40, 100]$ m."]
    assert init(src) == src


def test_unit_interval_is_not_rewritten():
    src = [r"subject to $\beta_{t,n}\in[0,1]$ and $p_{t,n}$ drawn from the codebook."]
    assert init(src) == src


def test_display_math_block_is_not_rewritten():
    src = ["$$", r"\beta_n \in [1,5], \qquad n = 1,\dots,N \tag{3}", "$$"]
    assert init(src) == src


def test_single_line_display_math_is_not_rewritten():
    src = [r"$$f(x) \in [1,5] \tag{4}$$"]
    assert init(src) == src


def test_inline_code_is_not_rewritten():
    src = ["the option `--range [1,5]` selects the sweep."]
    assert init(src) == src


def test_fenced_code_is_not_rewritten():
    src = ["```python", "xs = data[1]", "```"]
    assert init(src) == src


# -- the rewrite still fires where it should ---------------------------------

def test_bare_citation_outside_math_is_rewritten():
    out = init(["as shown in [7]."])
    assert out == ["as shown in <!-- cite:7 -->[[7]](references.md#ref-7)."]


def test_compound_citation_outside_math_is_rewritten():
    out = init(["see [7, 19]."])
    assert "cite:7" in out[0] and "cite:19" in out[0]


def test_citation_on_a_line_that_also_has_math():
    out = init([r"With $\beta \in [0,1]$ the bound of [7] applies."])
    assert r"$\beta \in [0,1]$" in out[0]
    assert "<!-- cite:7 -->[[7]](references.md#ref-7)" in out[0]


def test_unknown_number_is_left_alone():
    out = init(["array index [999] is not a citation."], bib={"7"})
    assert out == ["array index [999] is not a citation."]


# -- 3-digit bibliographies (the cap that hid half the bug) ------------------

def test_three_digit_citation_is_rewritten():
    out = init(["the trial reported in [110]."])
    assert "<!-- cite:110 -->[[110]](references.md#ref-110)" in out[0]


def test_three_digit_reference_entry_is_recognised():
    assert lr.REF_ENTRY.match('[110] Some Author, "A paper," 2023.')
    assert lr.REF_ENTRY.match('[7] Another Author, "A paper," 2019.')


# -- display-state tracking survives an already-marked line ------------------

def test_display_state_tracked_across_marked_lines():
    src = [
        "intro <!-- cite:7 -->[[7]](references.md#ref-7)",
        "$$",
        r"x \in [1,5] \tag{1}",
        "$$",
        "tail [19].",
    ]
    out = init(src)
    assert out[2] == r"x \in [1,5] \tag{1}"      # inside display math, untouched
    assert "cite:19" in out[4]                    # after the block, rewritten
