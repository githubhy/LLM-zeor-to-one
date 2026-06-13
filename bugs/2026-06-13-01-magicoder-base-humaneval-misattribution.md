---
id: 2026-06-13-01
title: Magicoder §8 base HumanEval figure misattributed (WizardCoder-CL's 48.2 used for Code Llama-Python-7B)
severity: med
status: fixed
date: 2026-06-13
component: surveys/llms-for-coding/instruction-tuning-and-alignment.md (section 8.1)
plan: deep-research-survey "LLMs for coding"
---

## Symptom

section 8.1 (Instruction Tuning) stated: "On Code Llama-Python-7B (48.2% HumanEval pass@1), Magicoder-CL reaches 60.4% ... MagicoderS-CL ... 70.7%." The base figure 48.2% is wrong for Code Llama-Python-7B.

Surfaced by the Phase-5 adversarial citation-audit workflow (`wf_0a879215-105`, verifier `verify:ref-17`), which read Magicoder Table 1 and flagged a `wrong-value`.

## Root cause

The base value was misattributed across rows of Magicoder's Table 1. In that table (Pass@1 on HumanEval(+)), the 7B block lists CODELLAMA-PYTHON-7B = **37.8 (34.1)**, WizardCoder-CL-7B = **48.2 (40.9)**, Magicoder-CL = 60.4 (55.5), MagicoderS-CL = 70.7 (66.5). The figure 48.2 belongs to **WizardCoder-CL-7B**, a different model on an adjacent row; it was lifted as the Code Llama-Python-7B base during evidence collection (cluster C scratch carried "48.2 (40.9)" as the base) and propagated into the survey prose. The dependent figures (Magicoder-CL 60.4, MagicoderS-CL 70.7, MagicoderS-DS 76.8) were all correct — only the base anchor was wrong.

## Fix

Changed "48.2%" → "37.8%" in section 8.1 (commit pending; this repo is not git-initialized). The corrected before→after is 37.8 → 60.4 (OSS-Instruct alone, +22.6) → 70.7 (combined), which *strengthens* rather than alters the section's argument that OSS-Instruct substantially improves the base. Verified the corrected value directly against download/magicoder-2023.pdf Table 1.

## Regression test

none — prose/citation correction, not code. Prevention is the standing citation-audit gate (this bug is the gate working). The corrected number was re-confirmed against the primary PDF locus before landing.

## Refs

- Source: download/magicoder-2023.pdf, Table 1 (7B block).
- Audit: reports/citation-audit-llms-for-coding-2026-06-13.md (ledger row ref 17).
- Conversation log: prompts/2026-06-13-llms-for-coding-survey.md (Conversation 3).
- Severity rationale: wrong-value in a headline comparison metric, but no derivation depends on it and the corrected value does not change the section's conclusion — hence `med`, not `high`.
