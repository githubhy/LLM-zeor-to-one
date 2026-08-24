#!/usr/bin/env python3
"""Positive control for check-forbidden-phrasing.py — a gate that flags nothing is worthless.

WHY THIS FILE EXISTS. The first draft of the gate MISSED the single most important
phrase in this repo's history — the "bracketing" overclaim from
field-notes/2026-07-05-sionna-xcheck-overclaim-catch.md — because of a gerund and an
intervening numeral between the article and the noun. It was caught only by an ad-hoc
positive control run from a scratch file that was never committed. So the evidence
that the gate works was about to be thrown away, and the next person to touch the
regex could silently re-break the exact catch it exists for.

Every CASE below is a phrasing this repo ACTUALLY SHIPPED and had to retract. They are
regression tests, not hypotheticals.

The NEGATIVE cases matter just as much: a gate people learn to ignore has stopped
gating (cf. todos/2026-07-10-lint-gates-scan-scratch-evidence-ledgers).
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "cfp", Path(__file__).resolve().parents[1] / "check-forbidden-phrasing.py")
cfp = importlib.util.module_from_spec(_spec)
sys.modules["cfp"] = cfp
_spec.loader.exec_module(cfp)


def scan(text: str):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
        p = Path(f.name)
    try:
        return {c for _, c, _, _ in cfp.scan_file(p)}
    finally:
        p.unlink()


class TestHistoricalOverclaims(unittest.TestCase):
    """Each of these was written, shipped, and retracted in this repo."""

    def test_bracketing_the_reference(self):
        # THE one the first draft missed: gerund + "195 ns" between "the" and "reference".
        self.assertIn("PH-BRACKET", scan(
            "The indoor/O2I sweep reaches ~146 ns, bracketing the 195 ns reference."))

    def test_brackets_plain(self):
        self.assertIn("PH-BRACKET", scan("The residual sweep brackets the reference curve."))

    def test_agrees_with_the_reference(self):
        self.assertIn("PH-AGREES", scan(
            "Our sim and Sionna outdoor values agree with the reference (52 vs 40 ns); "
            "the residual is small."))

    def test_qualitative_match(self):
        self.assertIn("PH-QUALITATIVE", scan(
            "The integer BP shows a qualitative match to the Chen 2005 Fig-4 residual."))

    def test_confirms_the_root_cause(self):
        self.assertIn("PH-CONFIRMED", scan(
            "The re-run confirms the root-cause of the calibration gap."))

    def test_closely_matches_the_reference(self):
        self.assertIn("PH-MATCHES", scan(
            "The realized accuracy closely matches the published reference curve; residual small."))

    def test_under_realizes(self):
        # The SECOND catch of the 2026-07-05 adversarial panel, and the one the gate had no
        # pattern for until 2026-08-23 (verified: 0 occurrences of "realiz" in the pre-session
        # tool). "Sionna under-realizes O2I DS" was carried with a flattering-range delta; the
        # honest form the panel substituted is asserted not to fire, below.
        self.assertIn("PH-REALIZES", scan(
            "The port under-realizes accuracy relative to the published reference (61.4 vs 68.0)."))

    def test_over_realizes_and_the_noun_form(self):
        self.assertIn("PH-REALIZES", scan(
            "The generator over-realizes the delay spread against the reference curve."))
        self.assertIn("PH-REALIZES", scan(
            "Our under-realization of the O2I population explains the residual."))

    def test_the_honest_form_the_panel_substituted_does_not_fire(self):
        # A positive control is only half a control: the replacement wording the rule
        # PRESCRIBES must pass, or the gate has no honest form to offer.
        self.assertEqual(set(), scan(
            "The Sionna-vs-ours gap is partly a metric-basis difference; "
            "the reference aligns with our cluster-power basis."))


class TestNoFalsePositives(unittest.TestCase):
    """Idioms that collide with the patterns but are not agreement claims.
    Measured, not guessed: the first corpus run scored ~40% precision."""

    def test_honest_numeric_claim_is_clean(self):
        self.assertEqual(scan(
            "The residual is 8.9 dB at P50, CI [8.1, 9.7], outside the 21-company "
            "envelope; UNCLOSED."), set())

    def test_escape_hatch_exempts(self):
        self.assertEqual(scan(
            "It brackets the reference <!-- phrasing-ok: quoting the rule -->"), set())

    def test_exact_match_scoring_is_not_an_agreement_claim(self):
        """`exact-match` is a core EVAL-SCORING term, not a claim about a reference."""
        self.assertEqual(scan(
            "The exact-match scorer adopted for the residual gap."), set())

    def test_bracketed_reference_is_lint_syntax(self):
        # `[§7.3.2]` — the bare-ref opt-out, not a calibration claim.
        self.assertEqual(scan(
            "Wrap it as a bracketed reference so the bare-ref gap check stays quiet."), set())

    def test_inter_annotator_agreement_is_a_term_of_art(self):
        """`inter-annotator agreement` names a METRIC, not an agreement with a reference."""
        self.assertEqual(scan(
            "The inter-annotator agreement rate, the competing rubrics, and the reference "
            "benchmark gap."), set())

    def test_fenced_code_is_skipped(self):
        self.assertEqual(scan(
            "```\nbrackets the reference residual\n```\n"), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestPrecisionFilters(unittest.TestCase):
    r"""The 2026-08-23 precision pass, and the control on every filter.

    The gate ran on every push reporting **19 findings**, of which a line-by-line triage
    found **15 false**. Its own comment already knew the stakes -- "a gate people learn to
    ignore has stopped gating" -- and it had drifted back there anyway.

    Each filter below removes a MEASURED false class. Each test pairs it with a control
    that the filter does NOT silence a real overclaim, because every one of these is a way
    to make the gate quieter, and quieter is the failure mode.
    """

    # -- already-quantified ---------------------------------------------------------
    def test_a_claim_that_states_its_tolerance_is_the_honest_form(self):
        self.assertEqual(
            scan("UMa coupling loss matches the reference within 1.6 dB median "
                 "(CI <= 0.6 dB), per the calibration residual."), set())

    def test_but_a_number_that_is_the_REFERENCE_VALUE_still_fires(self):
        """THE control that nearly went the other way. 'bracketing the 195 ns reference'
        -- the overclaim this entire gate exists for -- CONTAINS a number and a unit.
        Suppressing on 'a number appears nearby' would have silenced it. The
        discriminator is a TOLERANCE PREPOSITION before the quantity, not the quantity."""
        self.assertIn("PH-BRACKET",
                      scan("The indoor/O2I sweep reaches ~146 ns, bracketing the "
                           "195 ns reference."))

    def test_a_later_sentences_number_does_not_excuse_this_claim(self):
        """The tolerance must be in the sentence carrying the claim. A number two
        sentences on says nothing about it."""
        self.assertIn("PH-MATCHES",
                      scan("The sweep matches the published reference. Separately, the "
                           "residual at the median split is 1.6 points."))

    # -- clause spanning -------------------------------------------------------------
    def test_a_match_that_crosses_a_contrastive_conjunction_is_two_clauses(self):
        self.assertEqual(
            scan("The local file content matches the topic but the reference list "
                 "names a different venue; the residual is unaffected."), set())

    def test_a_contiguous_claim_still_fires(self):
        self.assertIn("PH-MATCHES",
                      scan("The calibrated curve matches the published reference."))

    # -- withdrawn claims ------------------------------------------------------------
    def test_a_struck_through_claim_is_one_the_document_withdrew(self):
        self.assertEqual(
            scan('~~"nor the SV-ratio CDFs as matching the reference"~~ -- withdrawn '
                 'in the 2026-07 residual audit.'), set())

    def test_prose_beside_a_strikethrough_is_still_scanned(self):
        """Blanking the struck span must not blind the rest of the line."""
        self.assertIn("PH-MATCHES",
                      scan("~~old text~~ and the new curve matches the reference."))

    # -- table headers ---------------------------------------------------------------
    def test_a_table_header_labels_a_column_it_does_not_claim(self):
        self.assertEqual(
            scan("| W | modulus | BER | agreement with the float reference |\n"
                 "|---|---|---|---|\n"
                 "| 8 | 251 | 1e-3 | 0.02 dB |\n"), set())

    def test_a_table_BODY_row_making_the_claim_still_fires(self):
        self.assertIn("PH-MATCHES",
                      scan("| W | note |\n|---|---|\n"
                           "| 8 | the fixed-point curve matches the reference |\n"))

    # -- named terms and non-measurement senses --------------------------------------
    def test_named_terms_and_traceability_are_not_agreement_claims(self):
        for line in (
            "Scoring is exact-match against the reference answer; the residual is "
            "an extraction artifact.",
            "ref [54]: a title matching no published work over a real arXiv ID; the "
            "reference is unverifiable.",
            "Several rows look card-backed but are not pinned to a matching revision, "
            "so the reference is unclear.",
            "Judge: stop when the completion matches the gold answer; reference only, "
            "not a capability claim.",
        ):
            self.assertEqual(scan(line), set(), line)

    def test_the_measurement_sense_of_match_still_fires(self):
        self.assertIn("PH-MATCHES",
                      scan("Our residual matches the published reference across the sweep."))

    # -- sentence window across a markdown soft-wrap ---------------------------------
    def test_a_tolerance_stated_on_the_PREVIOUS_line_still_counts(self):
        """Markdown soft-wraps. A line-bounded scan reads a wrapped sentence as if it
        began mid-clause and calls an already-honest claim a violation."""
        self.assertEqual(
            scan("- the `+de` / `+density` equivalence tests (1e-9 to 1e-12; `n_iter`\n"
                 "  EXACT), and the (R,Z) DE-threshold grid matching the reference\n"
                 "  goldens.\n"), set())

    def test_the_walk_back_stops_at_a_blank_line(self):
        """A tolerance in the PREVIOUS PARAGRAPH says nothing about this claim."""
        self.assertIn("PH-MATCHES",
                      scan("The earlier sweep agreed to within 0.01 dB.\n"
                           "\n"
                           "The new curve matches the reference.\n"))

    def test_a_decimal_point_is_not_a_sentence_end(self):
        """rfind('.') lands inside 'TS 38.212' and truncates the tolerance window."""
        self.assertEqual(
            scan("Verified to within 0.02 dB against the TS 38.212 grid, the curve "
                 "matches the reference."), set())

    # -- absolute-tolerance vocabulary -----------------------------------------------
    def test_scientific_notation_and_exactness_are_tolerances(self):
        for line in (
            "The float path matches the reference to 1e-12 across all kernels.",
            "Every kernel matches the Python reference to machine epsilon.",
            "The seeded path is bit-exact, matching the reference logits.",
            "The quantized path matches the reference with every decision EXACT.",
        ):
            self.assertEqual(scan(line), set(), line)

    def test_a_bare_claim_with_no_tolerance_still_fires(self):
        self.assertIn("PH-MATCHES",
                      scan("The quantized path matches the Octave reference."))

    # -- document identifiers are not measurements -----------------------------------
    def test_a_tdoc_or_spec_number_is_a_document_not_a_measurement(self):
        for line in (
            "These are the large-scale values matching R1-165975 -- they are correct "
            "for TR 38.901 V19.3 and differ from the V14 reference.",
            "The margin stack is the one matching R4-2008820, whose reference "
            "performance is the WF value.",
            "Parameters matching TS 38.211 clause 7.4, against the reference chain.",
        ):
            self.assertEqual(scan(line), set(), line)

    def test_a_numeric_claim_NEAR_a_tdoc_id_still_fires(self):
        """The filter must key on the matched span, not on 'a Tdoc appears somewhere'."""
        self.assertIn("PH-MATCHES",
                      scan("Per R1-165975, our fast-fading curve matches the "
                           "calibration reference."))

    # -- the gate's own positive control ---------------------------------------------
    def test_the_overclaim_this_gate_EXISTS_for_is_never_suppressed(self):
        """'bracketing the 195 ns reference' contains a number and a unit. Every
        precision filter above must leave it standing."""
        self.assertIn("PH-BRACKET",
                      scan("The sweep brackets the 195 ns reference across all seeds."))
