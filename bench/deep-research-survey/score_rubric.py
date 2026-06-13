#!/usr/bin/env python3
"""Tier-2 quality scoring: assemble the LLM-as-judge rubric prompt for a survey.

This is the output-quality half superpowers has no equivalent for. The rubric is
the consensus of the survey-generation eval frameworks surfaced in the proposal
(SurveyEval, SurveyBench, SurGE, SGSimEval, SurveyLens, DeepSurvey-Bench): five
content dimensions (1-5) plus citation Recall/Precision/F1.

This script does NOT call a model itself (no API wiring committed). It reads a
survey and prints (a) the assembled judge prompt and (b) the StructuredOutput
JSON schema, ready to feed to a SEPARATE judge model — via the Agent tool, or a
Workflow `agent(prompt, {schema})` stage. Using a *different* model than the one
that wrote the survey is required (avoids the self-preference bias the proposal's
P1-3 calls out).

Usage:
  python3 score_rubric.py surveys/prach-receiver-survey.md            # print prompt+schema
  python3 score_rubric.py surveys/prach-receiver-survey.md --out judge_prompt.txt
"""
import argparse
import json
import sys

DIMENSIONS = {
    "coverage":         "Breadth: are the important methods/variants/architectures all present? Omission is a defect.",
    "structure":        "Logical organization: fundamentals -> architecture -> inventory -> tradeoffs -> SOTA -> roadmap; no gaps or redundancy.",
    "relevance":        "Every section earns its place and answers a real question; no padding.",
    "synthesis":        "Cross-source integration and comparison, not per-source enumeration; tradeoffs made explicit.",
    "critical_analysis":"Depth beyond description: limitations, applicability boundaries, open gaps, engineering judgment.",
}

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [*[f"{d}_score" for d in DIMENSIONS],
                 *[f"{d}_justification" for d in DIMENSIONS],
                 "citation_recall", "citation_precision", "citation_f1",
                 "citation_notes", "overall"],
    "properties": {
        **{f"{d}_score": {"type": "integer", "minimum": 1, "maximum": 5} for d in DIMENSIONS},
        **{f"{d}_justification": {"type": "string"} for d in DIMENSIONS},
        "citation_recall": {"type": "number", "minimum": 0, "maximum": 1,
                            "description": "fraction of load-bearing claims that carry a supporting citation"},
        "citation_precision": {"type": "number", "minimum": 0, "maximum": 1,
                               "description": "fraction of citations that actually support the claim they are attached to"},
        "citation_f1": {"type": "number", "minimum": 0, "maximum": 1},
        "citation_notes": {"type": "string"},
        "overall": {"type": "number", "minimum": 1, "maximum": 5},
    },
}

PROMPT_TEMPLATE = """You are an expert reviewer scoring a technical SURVEY for quality. Be a strict,
calibrated judge. You did NOT write this survey. Score ONLY what is present.

Score each dimension on an integer 1-5 scale (1=poor, 3=adequate, 5=excellent),
with a one-sentence justification grounded in specific evidence from the text:

{dimension_block}

Then assess CITATION quality by sampling load-bearing claims:
  - citation_recall:    of the claims that REQUIRE a source, what fraction carry one?
  - citation_precision: of the citations present, what fraction actually SUPPORT
                        the specific claim they are attached to? (spot-check; a
                        plausible-but-wrong attribution counts against precision)
  - citation_f1:        harmonic mean of the two.
  - citation_notes:     name any unsupported or mis-attributed claims you found.

Finally give an `overall` (1-5). Do NOT reward citation DENSITY for its own sake —
novel synthesis may legitimately have sparse, high-precision citations.

Return ONLY the StructuredOutput object.

================ SURVEY UNDER REVIEW{trunc_note} ================
{survey_text}
================ END SURVEY ================
"""


def main():
    ap = argparse.ArgumentParser(description="Assemble the LLM-judge rubric prompt for a survey.")
    ap.add_argument("survey")
    ap.add_argument("--out", help="write the assembled judge prompt to this file")
    ap.add_argument("--max-chars", type=int, default=120_000,
                    help="truncate very large surveys (judge context budget)")
    ap.add_argument("--schema-only", action="store_true")
    args = ap.parse_args()

    if args.schema_only:
        print(json.dumps(SCHEMA, indent=2))
        return

    text = open(args.survey, encoding="utf-8").read()
    trunc_note = ""
    if len(text) > args.max_chars:
        text = text[:args.max_chars]
        trunc_note = f" (truncated to first {args.max_chars} chars)"

    dim_block = "\n".join(f"  - {d}: {desc}" for d, desc in DIMENSIONS.items())
    prompt = PROMPT_TEMPLATE.format(dimension_block=dim_block, trunc_note=trunc_note, survey_text=text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(prompt)
        sys.stderr.write(f"wrote judge prompt -> {args.out} ({len(prompt)} chars)\n")
    else:
        print(prompt)
    sys.stderr.write("\n--- StructuredOutput schema (feed alongside the prompt) ---\n")
    sys.stderr.write(json.dumps(SCHEMA, indent=2) + "\n")
    sys.stderr.write(
        "\nWire-up: pass `prompt` + `schema` to a judge agent on a DIFFERENT model, e.g.\n"
        "  Workflow:  agent(open('judge_prompt.txt').read(), {schema: <schema>, model: 'haiku'})\n"
        "  Agent tool: subagent_type general-purpose, force StructuredOutput with the schema.\n")


if __name__ == "__main__":
    main()
