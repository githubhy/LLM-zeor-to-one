#!/usr/bin/env bash
# Phase-3 source acquisition for the mechanistic-interpretability survey.
# Idempotent: skips files already present. Logs OK/FAIL per source.
# The 2605.29358 "Scaling Monosemanticity" arXiv id was flagged SPURIOUS by the
# evidence pass and is intentionally NOT here (that paper is web-only,
# transformer-circuits.pub). transformer-circuits.pub / distill / blog sources
# are (web)-tagged, not fetched as PDFs.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
OUT=surveys/mechanistic-interpretability/_scratch/fetch-results.txt
FETCH=.claude/skills/source-fetch/oa_fetch.py
: > "$OUT"

# arxiv_id|filename(without .pdf)
MANIFEST='
2209.10652|elhage-toy-models-superposition-2022
2209.11895|olsson-induction-heads-2022
2303.08112|belrose-tuned-lens-2023
2210.13382|li-othello-emergent-world-2022
2309.00941|nanda-emergent-linear-repr-2023
1902.10186|jain-attention-not-explanation-2019
1908.04626|wiegreffe-attention-not-not-explanation-2019
1909.03368|hewitt-probes-control-tasks-2019
1610.01644|alain-linear-classifier-probes-2016
2102.12452|belinkov-probing-classifiers-2022
2202.05262|meng-rome-2022
2211.00593|wang-ioi-2022
2304.05969|goldowsky-dill-path-patching-2023
2310.10348|syed-eap-2023
2309.16042|zhang-activation-patching-best-practices-2023
2404.15255|heimersheim-activation-patching-guide-2024
2403.00745|kramar-atp-star-2024
2304.14997|conmy-acdc-2023
2403.17806|hanna-eap-ig-faithfulness-2024
2303.02536|geiger-das-2023
2305.08809|wu-boundless-das-2023
2301.04709|geiger-causal-abstraction-2025
2309.08600|cunningham-saes-interpretable-features-2023
2404.16014|rajamanoharan-gated-saes-2024
2406.04093|gao-topk-saes-2024
2407.14435|rajamanoharan-jumprelu-saes-2024
2412.06410|bussmann-batchtopk-saes-2024
2503.17547|bussmann-matryoshka-saes-2025
2409.14507|chanin-feature-absorption-2024
2410.14670|engels-dark-matter-saes-2024
2406.11944|dunefsky-transcoders-2024
2501.18823|paulo-transcoders-beat-saes-2025
2308.10248|turner-actadd-2023
2312.06681|rimsky-caa-2024
2310.01405|zou-repe-2023
2406.11717|arditi-refusal-direction-2024
2411.02193|chalnev-sae-ts-2024
2210.07229|meng-memit-2023
2401.07453|gupta-editing-catastrophic-forgetting-2024
2307.12976|cohen-ripple-effects-2023
2301.04213|hase-localization-editing-2023
2301.05217|nanda-grokking-progress-measures-2023
2305.00586|hanna-greater-than-2023
2104.07143|bolukbasi-interpretability-illusion-bert-2021
2307.15771|mcgrath-hydra-effect-2023
2402.15390|rushing-self-repair-2024
2310.04625|mcdougall-copy-suppression-2023
2407.08734|miller-faithfulness-not-robust-2024
2503.09532|karvonen-saebench-2025
2402.17700|huang-ravel-2024
2408.05147|lieberum-gemma-scope-2024
2501.17148|wu-axbench-2025
2502.16681|deepmind-saes-useful-sparse-probing-2025
2506.03093|costa-mp-sae-2025
2401.05566|hubinger-sleeper-agents-2024
2306.03819|belrose-leace-2023
2403.03218|li-wmdp-rmu-2024
2406.07358|vanderweij-sandbagging-2024
'

ok=0; fail=0; skip=0
while IFS='|' read -r id name; do
  [ -z "$id" ] && continue
  path="download/${name}.pdf"
  if [ -f "$path" ]; then echo "SKIP  $id  $path" | tee -a "$OUT"; skip=$((skip+1)); continue; fi
  if python3 "$FETCH" "arxiv:${id}" --download "$path" >>"$OUT" 2>&1 && [ -f "$path" ]; then
    echo "OK    $id  $path" | tee -a "$OUT"; ok=$((ok+1))
  else
    echo "FAIL  $id  $name" | tee -a "$OUT"; fail=$((fail+1))
  fi
done <<< "$MANIFEST"
echo "=== DONE: ok=$ok fail=$fail skip=$skip ===" | tee -a "$OUT"
