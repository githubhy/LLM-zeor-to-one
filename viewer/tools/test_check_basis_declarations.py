"""Tests for the `file_context` / prose-only guard of `check-basis-declarations.py`.

Motivating incident (upstream): a rule guarded by a `file_context` regex tested the
RAW file text, so the guard was satisfied by a markdown link TARGET. Adding one
cross-reference to another document switched the rule on for the whole file and
retroactively flagged three untouched sentences at ERROR severity.

The load-bearing property locked in here is DISCRIMINATION, not cleanliness: a guard
that suppressed everything would pass a silence-only test. So each "silent" case is
paired with a "fires" case differing ONLY in whether the context word appears in
visible prose or in machinery.

DOMAIN NOTE. Upstream this was exercised through a rule whose `file_context` asked
"does this document discuss an interleaved converter array?". THIS repo's REGISTRY is
re-domained to the LLM bases (`N` non-embedding-vs-total, `D` unique-vs-seen tokens,
`B` sequences-vs-tokens, `pass@k`), and **none of those rules declares a
`file_context`** -- the ambiguity is intrinsic to the symbol here, not conditional on
the document's subject. So the guard is DORMANT in this corpus. Rather than invent a
`file_context` rule to have something to test, the file-level cases below are skipped
with that reason, and `prose_only()` -- the actual ported fix -- is tested directly, so
the mechanism stays covered if a `file_context` rule is ever added.
"""
import importlib.util
import pathlib
import subprocess
import sys

import pytest

TOOL = pathlib.Path(__file__).with_name("check-basis-declarations.py")


def _module():
    spec = importlib.util.spec_from_file_location("cbd", TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


#: An ambiguous parameter count, in the form the `N` rule matches: `$N$` in inline
#: math with a `context` word ("parameter"/"scal") on the same line, and no resolver
#: saying whether embeddings are counted.
AMBIGUOUS_USE = "Fitted over $N$ parameters, the scaling exponent settles.\n"

HEAD = "<!-- sec:1 -->\n## <a id=\"sec-1\"></a>1 A scaling-law section\n\n"

HAS_FILE_CONTEXT = any(
    spec.get("file_context") for spec in _module().REGISTRY.values()
)
needs_file_context = pytest.mark.skipif(
    not HAS_FILE_CONTEXT,
    reason="no rule in this repo's REGISTRY declares file_context - the guard is "
           "dormant here; prose_only() is covered directly below",
)


def run(tmp_path, body, name="doc.md"):
    p = tmp_path / name
    p.write_text(HEAD + body, encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOL), "--severity=error", str(p)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.stdout + r.stderr


def fired(out):
    """True iff the N parameter-count rule reported a finding."""
    return "parameter-count-basis" in out


# ------------------------------------------------------------- the rule works
# Without these, "delete the rule" would pass every suppression test below.

def test_an_ambiguous_parameter_count_is_reported(tmp_path):
    """Baseline: `$N$ parameters` with no basis declared must fire."""
    assert fired(run(tmp_path, AMBIGUOUS_USE))


def test_declaring_the_basis_silences_it(tmp_path):
    """The honest form -- naming the basis -- must clear the finding."""
    body = ("Fitted over $N$ non-embedding parameters, the scaling exponent settles.\n")
    assert not fired(run(tmp_path, body))


def test_an_unrelated_symbol_is_silent(tmp_path):
    """Control: no ambiguous basis symbol, no finding."""
    assert not fired(run(tmp_path, "The residual settles quickly.\n"))


# --------------------------------------------------- prose_only(), tested directly
# This is the ported fix. It is exercised here rather than through a rule, because
# no rule in this repo declares a file_context (see the module docstring).

def test_prose_only_strips_a_link_target():
    """The regression: a word appearing only as a link HREF is machinery, not subject."""
    m = _module()
    out = m.prose_only("See [the other section](time-interleaved.md#sec-6.1).\n")
    assert "time-interleaved.md" not in out


def test_prose_only_strips_a_marker_comment():
    """Marker comments are machinery too."""
    m = _module()
    assert "secxref" not in m.prose_only("<!-- secxref:6.1 interleaved -->\n")


def test_prose_only_keeps_visible_link_text():
    """Discrimination: visible link TEXT is prose the reader sees, so it must survive."""
    m = _module()
    out = m.prose_only("See [the interleaved array](other.md#sec-2).\n")
    assert "the interleaved array" in out


def test_prose_only_keeps_plain_prose():
    """A guard that stripped everything would pass the two silence tests above."""
    m = _module()
    body = "This model is a mixture-of-experts transformer.\n"
    assert "mixture-of-experts transformer" in m.prose_only(body)


# ------------------------------------------------- file-level guard (dormant here)

@needs_file_context
def test_link_target_alone_does_not_arm_a_file_context_rule(tmp_path):
    body = AMBIGUOUS_USE + "See [the other section](time-interleaved.md#sec-6.1).\n"
    assert not fired(run(tmp_path, body))


@needs_file_context
def test_prose_context_still_arms_a_file_context_rule(tmp_path):
    body = AMBIGUOUS_USE + "This model is a time-interleaved array.\n"
    assert fired(run(tmp_path, body))
