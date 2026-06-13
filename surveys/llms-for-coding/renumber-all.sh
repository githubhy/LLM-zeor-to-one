#!/usr/bin/env bash
# Renumber equations in all document files

SCRIPT="../../viewer/tools/renumber-equations.py"

python "$SCRIPT" "executive-summary.md"
python "$SCRIPT" "scope-and-the-code-modality.md"
python "$SCRIPT" "historical-evolution.md"
python "$SCRIPT" "conceptual-and-mathematical-fundamentals.md"
python "$SCRIPT" "the-code-model-pipeline.md"
python "$SCRIPT" "pretraining-data.md"
python "$SCRIPT" "pretraining-objectives-and-scaling.md"
python "$SCRIPT" "instruction-tuning-and-alignment.md"
python "$SCRIPT" "reasoning-and-test-time-compute.md"
python "$SCRIPT" "inference-decoding-and-serving.md"
python "$SCRIPT" "retrieval-and-repository-context.md"
python "$SCRIPT" "agentic-coding-systems.md"
python "$SCRIPT" "evaluation-and-benchmarks.md"
python "$SCRIPT" "compute-cost-and-latency-tradeoffs.md"
python "$SCRIPT" "state-of-the-art-and-practice.md"
python "$SCRIPT" "safety-security-and-licensing.md"
python "$SCRIPT" "design-guidance.md"
python "$SCRIPT" "open-problems-and-roadmap.md"
python "$SCRIPT" "references.md"

echo "Done."
