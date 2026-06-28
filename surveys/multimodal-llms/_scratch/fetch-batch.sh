#!/usr/bin/env bash
# Phase-3 source acquisition for the multimodal-llms survey.
# Fetch each paper by arXiv id (most reliable); resolver title-verifies + content-validates.
# Log per-paper outcome to acquisition.log; titles confirmed afterward against the intended paper.
set -u
cd /Users/claire/GitRepos/llm-zero-to-one
RES=.claude/skills/source-fetch/oa_fetch.py
LOG=surveys/multimodal-llms/_scratch/acquisition.log
: > "$LOG"

# id|filename|intended-title-keywords (for post-hoc verification)
PAPERS='
2103.00020|radford-clip-2021|CLIP Learning Transferable Visual Models Natural Language
2010.11929|dosovitskiy-vit-2020|Image is Worth 16x16 Words Transformers Image Recognition
2303.15343|zhai-siglip-2023|Sigmoid Loss Language Image Pre-Training SigLIP
2204.14198|alayrac-flamingo-2022|Flamingo Visual Language Model Few-Shot Learning
2301.12597|li-blip2-2023|BLIP-2 Bootstrapping Language-Image Pre-training Querying Transformer
2304.08485|liu-llava-2023|Visual Instruction Tuning LLaVA
2310.03744|liu-llava-1.5-2023|Improved Baselines Visual Instruction Tuning LLaVA-1.5
2308.12966|bai-qwen-vl-2023|Qwen-VL Versatile Vision-Language Model
2409.12191|wang-qwen2-vl-2024|Qwen2-VL Enhancing Vision-Language Model Any Resolution
2502.13923|bai-qwen2.5-vl-2025|Qwen2.5-VL Technical Report
2312.14238|chen-internvl-2023|InternVL Scaling up Vision Foundation Models
2405.09818|team-chameleon-2024|Chameleon Mixed-Modal Early-Fusion Foundation Models
2409.18869|wang-emu3-2024|Emu3 Next-Token Prediction is All You Need
2408.11039|zhou-transfusion-2024|Transfusion Predict Next Token Diffuse Images One Multi-Modal Model
2410.13848|wu-janus-2024|Janus Decoupling Visual Encoding Unified Multimodal
2212.04356|radford-whisper-2022|Robust Speech Recognition Large-Scale Weak Supervision Whisper
2311.07919|chu-qwen-audio-2023|Qwen-Audio Advancing Universal Audio Understanding
2310.13289|tang-salmonn-2024|SALMONN Generic Hearing Abilities Large Language Models
2306.12925|rubenstein-audiopalm-2023|AudioPaLM Large Language Model Speak Listen
2311.10122|lin-video-llava-2023|Video-LLaVA Learning United Visual Representation Alignment
1711.00937|vandenoord-vqvae-2017|Neural Discrete Representation Learning VQ-VAE
2012.09841|esser-vqgan-2021|Taming Transformers High-Resolution Image Synthesis VQGAN
2311.16502|yue-mmmu-2023|MMMU Massive Multi-discipline Multimodal Understanding
2305.10355|li-pope-2023|Evaluating Object Hallucination Large Vision-Language Models POPE
2407.07726|beyer-paligemma-2024|PaliGemma Versatile 3B Vision-Language Model
2410.07073|agrawal-pixtral-2024|Pixtral 12B
2409.17146|deitke-molmo-2024|Molmo PixMo Open Weights Open Data State-of-the-Art Multimodal
2403.05525|lu-deepseek-vl-2024|DeepSeek-VL Real-World Vision-Language Understanding
2405.02246|laurencon-idefics2-2024|What Matters Building Vision-Language Models Idefics2
2409.11402|dai-nvlm-2024|NVLM Open Frontier-Class Multimodal LLMs
'

ok=0; fail=0
while IFS='|' read -r id fname title; do
  [ -z "${id:-}" ] && continue
  echo "=== fetching $id -> $fname.pdf ===" >> "$LOG"
  timeout 120 python3 "$RES" "arxiv:$id" --download "download/$fname.pdf" >> "$LOG" 2>&1
  if [ -f "download/$fname.pdf" ] && [ "$(stat -f%z "download/$fname.pdf" 2>/dev/null || echo 0)" -gt 102400 ]; then
    sz=$(stat -f%z "download/$fname.pdf"); echo "OK $fname.pdf ($sz bytes) [intended: $title]" >> "$LOG"; ok=$((ok+1))
  else
    echo "FAIL $fname.pdf (id $id) [intended: $title]" >> "$LOG"; fail=$((fail+1))
  fi
done <<< "$PAPERS"

echo "" >> "$LOG"
echo "DONE: $ok ok, $fail fail" >> "$LOG"
