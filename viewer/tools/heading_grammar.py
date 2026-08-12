"""The corpus's section-number grammar — defined once, here.

Before this module the grammar was hand-copied six times: five inside
`renumber-sections.py` (`HEADING_RE`, `SEC_ANCHOR_RE`, `SEC_MARKER_RE`,
`SECREF_MARKER_RE`, `SECXREF_MARKER_RE`) and a sixth inside `crosslink.py`.
Each copy was free to drift, and **every drift failed by reporting green**:

  * `bugs/2026-07-09-13` — crosslink's copy was dotted-only, so flat-numbered
    wikis contributed ZERO sections. They were absent from the index, not merely
    un-targetable, while `check` printed "no gaps".
  * `bugs/2026-07-09-16` — renumber-sections' copies were dotted-only, so 131
    flat `<!-- secxref:N -->` markers across 39 files were never parsed,
    resolved, or orphan-reported. 35 of them pointed at anchors that do not
    exist: dead links that render as live ones, with `--check` exiting 0.

Two levels, deliberately different:

  ``match_heading`` / ``SECTION_NUM``
      The BROAD form. What may be anchored and what may be a link target. A
      dotted number always counts; a flat number counts only when the line
      MARKS it as a section — a ``§`` glyph, a trailing ``.``, a dash
      separator, or a matching ``sec-N`` anchor already present. Without that
      rule ``## 2020 in review`` would become section 2020.

  ``DOTTED_SECTION_NUM``
      The NARROW form. What ``renumber-sections --init`` promotes from bare
      prose, and what ``validate-refs.py::BARE_SEC_RE`` flags.

`validate-refs.py::BARE_SEC_RE` intentionally does NOT widen to ``SECTION_NUM``.
A bare ``§4`` in prose is ambiguous with an external citation (``[TS 38.211 §4]``),
and the corpus carries 809 such flat mentions across 84 files. That is a
**deliberate exception, not a divergence** — it narrows this module's grammar
rather than redefining it. Any future tool that needs a section number imports
from here; if it needs a narrower one, it imports and narrows, with a comment.
"""

import re

# A section number: flat (`4`, `17`) or dotted (`3.7.6`, `D.7`, `A.8.3`).
SECTION_NUM = r"[A-Za-z]?\d+(?:\.\d+)*|[A-Z]\.\d+(?:\.\d+)*"

# A section number that must contain at least one dot. See the module docstring
# for why the bare-ref gate keeps this narrower form.
DOTTED_SECTION_NUM = r"[A-Za-z]?\d+(?:\.\d+)+|[A-Z]\.\d+(?:\.\d+)*"

# SECTION_NUM carries a top-level `|`. It MUST be wrapped before it is
# concatenated with anything, or the alternation swallows the suffix into only
# its second branch (`secref:3.7.6-step-3` then fails to match). Always use
# `_NUM`, never `SECTION_NUM`, inside a larger pattern.
_NUM = rf"(?:{SECTION_NUM})"

# Optional sub-landmark suffix: `-step-3`, `-lemma-D.6-A`.
_SUB = r"(?:-[\w.\-]+)?"

# An ATX heading. Tolerates a legacy column-0 anchor and the current post-ATX
# anchor (see `.claude/rules/math-authoring.md` and bugs/2026-05-25-02).
#
# The post-ATX group is `*`, not `?`, because a heading may legitimately carry the
# `sec-N` anchor AND a hand-authored semantic anchor:
#     ## <a id="sec-1"></a><a id="estimator"></a>1. The top-k estimator
# With `?` only the first anchor was consumed, the number never matched, and the
# heading was not a heading — so the whole FILE contributed zero sections and was
# absent from the crosslink index while `check` truthfully reported "no gaps" for
# it. Four wikis were invisible this way (rope-scaling, kv-cache-eviction,
# speculative-draft-acceptance, softmax-numerical-stability); the headings look correct
# and carry a valid anchor, so nothing about them reads as broken. Same false-green
# class as bugs/2026-07-09-13, found by the 2026-07-26 harness audit.
_HEADING_RE = re.compile(
    r'^(?:<a\s+id="[^"]*"></a>)?'
    r"(?P<hashes>#{2,6})\s+"
    r'(?:<a\s+id="[^"]*"></a>)*'
    r"(?P<sect>§\s*)?"
    r"(?P<num>" + SECTION_NUM + r")"
    r"(?P<dot>\.)?"
    r"(?P<sep>\s*[—–-]\s+|\s+)"
    r"(?P<title>.*)$"
)

# Group 1 / `anchor` is the FULL anchor id (`sec-3.7.6-step-3`) — that is the
# positional contract `crosslink.py:212` relies on to build `#sec-...` links.
# Group `sec` is the same id without the `sec-` prefix, which is what
# `match_heading` compares against a heading's number.
SEC_ANCHOR_RE = re.compile(rf'<a\s+id="(?P<anchor>sec-(?P<sec>{_NUM}{_SUB}))"></a>')
SEC_MARKER_RE = re.compile(rf"<!--\s*sec:({_NUM}{_SUB})\s*-->")
SECREF_MARKER_RE = re.compile(rf"<!--\s*secref:({_NUM}{_SUB})\s*-->")
SECXREF_MARKER_RE = re.compile(rf"<!--\s*secxref:({_NUM}{_SUB})\s*-->")

# Permissive: matches ANY secxref marker, including ids that are not section
# numbers at all (e.g. the file slug `appendix-derivations`). Used to REPORT
# what the strict pattern cannot consume, instead of skipping it in silence.
ANY_SECXREF_RE = re.compile(r"<!--\s*secxref:(?P<id>[^\s>]+?)\s*-->")

# Permissive anchor matcher. An `<a id="sec-...">` IS a link target, whatever
# its id looks like — the corpus carries hand-authored `sec-A` .. `sec-D` on
# `## Appendix A — …` headings whose visible text starts with a word, not a
# number, so no heading grammar will ever parse them. Resolution must key on
# the anchor, not on the heading; `build_survey_heading_index` uses this.
ANY_SEC_ANCHOR_RE = re.compile(r'<a\s+id="sec-(?P<sec>[^"]+)"></a>')

# Back-compat alias. Callers that only need the raw pattern (not the
# marked-flat rule) may use this; prefer `match_heading`.
HEADING_RE = _HEADING_RE


def match_heading(line):
    """Return the heading match for `line`, or None.

    A dotted number is always a section. A flat number is a section only when
    the line marks it as one:

      * a leading section glyph  -- ``## § 1 Scope``
      * a trailing dot           -- ``## 5. Power-Domain NOMA``
      * a dash separator         -- ``## 3 — Road A``
      * a matching sec-anchor    -- ``## <a id="sec-17"></a>17 Master matrix``

    Otherwise ``## 2020 in review`` would be parsed as section 2020.
    """
    m = _HEADING_RE.match(line)
    if not m:
        return None
    if "." not in m.group("num"):
        marked = m.group("sect") or m.group("dot") or (m.group("sep") or "").strip()
        if not marked:
            am = SEC_ANCHOR_RE.search(line)
            if am:
                aid, num = am.group("sec"), m.group("num")
                marked = aid == num or aid.startswith(num + "-")
        if not marked:
            return None
    return m
