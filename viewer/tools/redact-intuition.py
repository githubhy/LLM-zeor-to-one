#!/usr/bin/env python3
"""Phase-8 harness: redact a section's intuition prose so it can be explain-back tested.

The rubric scored this survey's intuition at 100 %, but the metric was *does a
labelled Intuition block exist* — presence, not quality. Three cases were then
found where fluent intuition led a reader to the wrong mechanism. The test that
distinguishes the two is whether the prose lets a competent reader **predict** the
result; so redact the result and ask.

WHAT IS REDACTED, AND WHAT IS DELIBERATELY NOT
    Redacted: display math, inline math, every numeral with its unit, and explicit
    scaling statements ("grows as", "falls as", "proportional to", "∝").

    NOT redacted: the mechanism prose itself. That is the thing under test — if it
    were removed there would be nothing to predict from.

    This boundary cannot be drawn perfectly by a regex, and pretending otherwise
    would be the failure mode. So the tool PRINTS WHAT IT REDACTED and flags any
    residual token that looks like an answer ("exactly", "identically zero",
    "vanishes", "cancels"), because a leaked conclusion turns a passing
    explain-back into evidence of nothing. A human reads the flag list before
    trusting a pass.

WHY THE PREDICTOR SHOULD BE A STRONG MODEL
    Counter-intuitively, the test is *more* meaningful with a capable predictor. A
    weak one fails on good intuition, biasing the harness toward condemning prose
    that is fine. If a strong reader, given only the mechanism, still cannot
    predict the sign — the intuition genuinely does not carry it.

USAGE
    redact-intuition.py <file.md> --section 5.10
    redact-intuition.py <file.md> --section 5.10 --from-git 9ee95ea~1
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Blocks that carry intuition rather than derivation.
# Extraction is KEYWORD-based, not positional. A first version enumerated lead-in
# phrases with bounded character classes, and it silently missed §3.2's
# load-bearing block -- whose lead-in is "**What the gain error does *not*
# produce, because this is the fingerprint §5.1's estimators key on.**", too long
# and too punctuated for any positional pattern. A predictor was handed an
# off-topic paragraph as a result, and flagged it rather than answering from it.
# So: match ANY bold phrase opening a paragraph, then test its text for a keyword.
BOLD_LEAD = re.compile(r"^\s*\*\*(.{3,160}?)\*\*", re.S)
INTUITION_KEYWORDS = (
    "intuition", "insight", "why", "what it shows", "what this shows",
    "what it means", "picture", "mechanism", "the reason", "distinction",
    "consequence", "what survives", "design rule", "the tell", "the trap",
    "does not produce", "does *not* produce", "a real ", "stated honestly",
    "the cost", "the obstruction", "the caveat", "two readings", "so the",
    "counter-intuitive", "read that", "read the",
)
# Blocks that are pure derivation, construction or bookkeeping are excluded even if
# a keyword slips through -- they contain the answer by definition.
EXCLUDE_KEYWORDS = (
    "derivation", "derived", "construction", "setup", "epistemic tag", "configuration",
    "worked example", "basis note", "correction of record", "quantitative prediction",
    # schema slots and figure furniture: structure, not insight, and several state the
    # result outright (a Fragility line names the direction, which IS the answer).
    "schema note", "schema conformance", "how to read it", "limits", "figure",
    "method-in-context", "the method", "the model", "the criterion", "fragility",
    "limiting cases", "in scope", "out of scope", "evidence discipline",
    "evidence status", "state of attack", "candidate next step", "no figure",
    "symbol discipline", "basis declaration", "what was acquired", "row-count gate",
)

# INCLUSIVE extraction (--extract inclusive).
#
# The keyword list above is an OPEN vocabulary -- it must anticipate every way a
# human can phrase an insight -- while the thing it is really trying to keep out is
# CLOSED: prose that contains the answer (a derivation, a schema slot, a stated
# verdict). Enumerating the open set is why extraction missed §3.2's load-bearing
# block (Phase 8) and both of §8.4's, and a survey-wide dump found 313 declined
# bold-leads of which roughly a dozen were plainly load-bearing.
#
# So the inclusive mode inverts the burden: take EVERY bold-lead paragraph except
# those the exclusion list names, plus pure schema slots, which are recognised
# STRUCTURALLY -- a lead of at most three words ending in a period ("Idea.",
# "Complexity.", "Failure modes.", "Question.") is a slot label, not an argument.
#
# The two directions of error are not symmetric, which is what justifies the flip:
# over-inclusion lengthens the artifact, under-inclusion silently deletes the thing
# under test and returns a PASS.
SLOT_RE = re.compile(r"^(?:\([a-z0-9]+\)\s*)?(?:\w+[\s,-]+){0,2}\w+\.?$")


def is_slot_label(lead: str) -> bool:
    return bool(SLOT_RE.match(lead.strip()))


def is_intuition_block(para: str, mode: str = "keyword") -> bool:
    m = BOLD_LEAD.match(para)
    if not m:
        return False
    lead = m.group(1)
    low = lead.lower()
    if any(k in low for k in EXCLUDE_KEYWORDS):
        return False
    if any(k in low for k in INTUITION_KEYWORDS):
        return True
    # Inclusive is a SUPERSET of keyword, never an alternative to it. Written as an
    # alternative first, and it dropped 16 blocks keyword mode had -- including every
    # literal `**Intuition.**`, because a one-word lead is a slot label by the
    # structural rule and the structural rule ran instead of the vocabulary. The
    # harness is named for those blocks. A widening that can narrow is not a widening.
    return mode == "inclusive" and not is_slot_label(lead)


def skipped_leads(body: str, mode: str = "keyword") -> list[str]:
    """Bold-lead paragraphs the keyword filter DECLINED, for the coverage footer.

    The keyword list is a CLOSED VOCABULARY and it will keep missing blocks — it
    already missed §3.2's load-bearing block once (Phase 8) and §8.4's twice more
    (lead-ins "...and it matters which" and "...the part usually missed", neither of
    which contains any listed word). Widening the list is a fix for the instance,
    not for the class.

    So the class fix is to make the miss VISIBLE: print what was declined, and let a
    human decide. Silent under-extraction reads as "this section has thin intuition"
    when it means "the heuristic did not look there", and those are opposite
    conclusions about the survey. Same discipline as crosslink.py's coverage
    warnings: a green result must mean "looked and found nothing", never "did not
    look".
    """
    out: list[str] = []
    for para in body.split("\n\n"):
        clean = MARKER.sub("", para).strip()
        if not clean:
            continue
        m = BOLD_LEAD.match(clean)
        if not m or is_intuition_block(clean, mode):
            continue
        lead = m.group(1).strip()
        why = ("excluded" if any(k in lead.lower() for k in EXCLUDE_KEYWORDS)
               else "slot label" if mode == "inclusive" else "no keyword")
        # The LEAD ITSELF can state the conclusion -- §8.4's is literally "So the
        # symmetry saves a factor $P!$ and does not change the order". Printing it
        # raw would put the answer in the coverage footer, re-creating the exact
        # leak `test_default_artifact_does_not_echo_the_spans_it_redacted` exists to
        # stop, one field over. So the lead is redacted like any other prose.
        safe = LEAK_RE.sub("[V]", NUMERAL.sub("[N]", INLINE_MATH.sub("[M]", lead)))
        out.append(f"[{why}] {safe[:100]}")
    return out


DISPLAY_MATH = re.compile(r"\$\$.*?\$\$", re.S)
INLINE_MATH = re.compile(r"\$[^$\n]+\$")
# a numeral, optionally signed / exponential / with a unit suffix
NUMERAL = re.compile(
    r"[+-]?\b\d+(?:[.,]\d+)?(?:\s*[eE×x]\s*10\^?\{?[+-]?\d+\}?)?"
    r"(?:\s*(?:dB|dBc|dBFS|fs|ps|ns|bits?|LSB|%|GHz|MHz|Hz|samples?|ENOB))?"
)
SCALING = re.compile(
    r"(?:grows?|falls?|scales?|rises?|drops?|varies)\s+(?:as|with|like)\s+\S+|"
    r"proportional to \S+|∝\s*\S+|\bas the (?:square|cube|inverse)[^,.;]{0,40}",
    re.I,
)
# tokens that would hand the reader the answer if they survived redaction
LEAK_RE = re.compile(
    r"\b(?:exactly|identically|vanish(?:es|ing)?|cancels?|zero|null|"
    r"monotonic(?:ally)?|saturat(?:es|ing)|unbounded|diverges?|"
    r"positive|negative|larger|smaller|worse|better|optimistic|pessimistic)\b",
    re.I,
)
MARKER = re.compile(r"<!--[^>]*-->|<a id=\"[^\"]*\"></a>")

# A CROSS-REFERENCE is not a result, and redacting its numerals manufactures a test
# nobody can pass. A link like [SS 7.3](mismatch-shaping.md#sec-7.3) becomes "[NUM]"
# three times over, and the survey-wide sweep produced NINE sections whose extraction
# was almost entirely such tokens. Four predictors independently reported "this probe
# is vacuous; every span is a section index". They were right, and it is the harness's
# fault: a redaction the prose cannot possibly determine is noise that dilutes the
# real spans. So collapse any link into an anchor to one neutral token, BEFORE the
# numeral pass runs.
XREF = re.compile(r"\[[^\]\n]{0,120}\]\([^)\n]*#[^)\n]*\)")

# Whether the block's content CONTINUES into a table or list. Extraction splits on
# blank lines, so a paragraph ending "...the three strategies:" followed by a table
# reaches the predictor as an unfulfilled promise. Two predictors reported exactly
# that as a structural defect in the survey (SS4.4's excitation strategies, SS6.8's
# "two consequences"); both were FALSE ALARMS -- the content is a table and a numbered
# list respectively. A harness that generates false positives costs more than one that
# misses, because every one has to be chased down before it can be dismissed.
CONTINUES = re.compile(r"^\s*(?:\||[-*]\s|\d+\.\s|>)")


def section_body(text: str, sec: str) -> str:
    """Everything between `<!-- sec:N -->` and the next `<!-- sec: -->`."""
    start = text.find(f"<!-- sec:{sec} -->")
    if start < 0:
        raise SystemExit(f"section {sec} not found")
    nxt = re.search(r"\n<!-- sec:[\d.A-Z]+ -->", text[start + 10:])
    return text[start: start + 10 + (nxt.start() if nxt else len(text))]


def redact(body: str, redact_verdicts: bool = False,
           mode: str = "keyword") -> tuple[str, list[str], list[str]]:
    """(redacted intuition prose, what was removed, leak flags).

    `redact_verdicts` additionally blanks the verdict-shaped tokens the leak
    detector flags. Needed whenever the prose STATES its conclusion, which is most
    of the time and is always true of the RED anchor -- the pre-correction §5.10
    text says "corrects the front end **exactly**", so without this the predictor
    reads the answer instead of deriving it, and a pass would prove nothing.
    """
    removed: list[str] = []

    def take(pat: re.Pattern, label: str, s: str) -> str:
        def sub(m: re.Match) -> str:
            removed.append(f"{label}: {m.group(0)[:70]}")
            return f"[{label}]"
        return pat.sub(sub, s)

    blocks = []
    paras = body.split("\n\n")
    for k, para in enumerate(paras):
        clean = MARKER.sub("", para).strip()
        if not clean or not is_intuition_block(clean, mode):
            continue
        nxt = MARKER.sub("", paras[k + 1]).strip() if k + 1 < len(paras) else ""
        tail = ("\n\n[THIS BLOCK CONTINUES INTO A TABLE OR LIST, WITHHELD - its content "
                "is not missing from the survey]" if nxt and CONTINUES.match(nxt) else "")
        clean = XREF.sub("[XREF]", clean)
        clean = take(DISPLAY_MATH, "MATH", clean)
        clean = take(INLINE_MATH, "MATH", clean)
        clean = take(SCALING, "SCALING", clean)
        clean = take(NUMERAL, "NUM", clean)
        if redact_verdicts:
            clean = take(LEAK_RE, "VERDICT", clean)
        blocks.append(clean + tail)

    out = "\n\n".join(blocks)
    leaks = sorted({m.group(0).lower() for m in LEAK_RE.finditer(out)})
    return out, removed, leaks


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-8 intuition redactor.")
    ap.add_argument("file")
    ap.add_argument("--section", required=True)
    ap.add_argument("--from-git", help="read the file at this revision instead of HEAD")
    ap.add_argument("--quiet", action="store_true", help="print only the redacted prose")
    ap.add_argument("--audit", action="store_true",
                    help="print the redacted span CONTENTS. For a human checking "
                         "redaction quality only — never feed an --audit artifact "
                         "to a predictor, it contains the answers.")
    ap.add_argument("--extract", choices=["keyword", "inclusive"], default="keyword",
                    help="keyword: the Phase-8 lead-in vocabulary (reproduces the six "
                         "original artifacts). inclusive: every bold-lead paragraph "
                         "except exclusions and schema slots — under-extraction is the "
                         "dangerous direction, so this is the mode for a sweep.")
    ap.add_argument("--redact-verdicts", action="store_true",
                    help="also blank verdict tokens (exactly / zero / vanishes / ...), "
                         "so a stated conclusion cannot be read off instead of derived")
    args = ap.parse_args()

    if args.from_git:
        rel = str(Path(args.file).resolve().relative_to(REPO))
        text = subprocess.run(["git", "show", f"{args.from_git}:{rel}"], cwd=str(REPO),
                              capture_output=True, text=True).stdout
        if not text:
            raise SystemExit(f"could not read {rel} at {args.from_git}")
    else:
        text = Path(args.file).read_text(encoding="utf-8")

    prose, removed, leaks = redact(section_body(text, args.section),
                                   redact_verdicts=args.redact_verdicts,
                                   mode=args.extract)
    if not prose.strip():
        raise SystemExit(f"no intuition block found in §{args.section}")

    print(prose)
    if args.quiet:
        return 0
    print("\n" + "=" * 62)
    # The span CONTENTS are withheld by default. Printing them defeated the whole
    # exercise: the first version's footer listed "$\\mu^\\star \\propto
    # \\Delta_{acc}^{2/3}$" in plain text under "redacted 40 span(s)", so a
    # predictor asked to derive that exponent could read it off the artifact it was
    # given. Caught by the §8.6 predictor, which flagged it rather than exploiting
    # it. --audit restores the list for a human reviewing the redaction quality.
    from collections import Counter
    kinds = Counter(r.split(":", 1)[0] for r in removed)
    print(f"redacted {len(removed)} span(s): "
          + ", ".join(f"{k}×{n}" for k, n in sorted(kinds.items())))
    if args.audit:
        print("  (--audit) contents, NOT for a blind artifact:")
        for r in removed:
            print(f"  - {r}")
    else:
        print("  contents withheld — pass --audit to inspect them (never into a "
              "predictor's input)")
    if leaks:
        print(f"\nLEAK FLAGS ({len(leaks)}) — a conclusion may have survived redaction, "
              "so a PASS here proves little:")
        print("  " + ", ".join(leaks))
    else:
        print("\nno leak flags: no verdict-shaped token survived redaction")

    # COVERAGE, not silent. A skipped mechanism block is indistinguishable from a
    # section with thin intuition unless the skip is printed.
    skipped = skipped_leads(section_body(text, args.section), mode=args.extract)
    if skipped:
        print(f"\nCOVERAGE: {len(skipped)} bold-lead paragraph(s) NOT extracted — check "
              "none of these is the load-bearing mechanism block:")
        for s in skipped:
            print(f"  {s}")
    else:
        print("\nCOVERAGE: every bold-lead paragraph in this section was extracted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
