# Research Brief — Mechanistic Interpretability (north star)

**Survey slug:** `mechanistic-interpretability`
**Branch:** `survey/mechanistic-interpretability`
**Mode:** `proposed` (all P-items + all R-* richness items) · **scale:** `wide` · **audience:** `practitioner` (CONFIRMED 2026-07-01)
**Depth emphasis:** Balanced (headline the foundations + one exemplar per method family; catalog the tail). **Model breadth:** Toy → frontier + vision roots (widest reading of "various models").
**Response mode:** Survey (broad, comparative, source-backed).

## Subject

Mechanistic interpretability (MI): the research program of **reverse-engineering the
internal computations of neural networks — primarily transformer language models — into
human-understandable algorithms ("circuits") and features.** The survey covers the full
method inventory (observational, causal/interventional, and dictionary-learning families),
the mathematical fundamentals they rest on (the residual-stream framework, the linear
representation hypothesis, superposition), worked circuit case studies **across a spread of
models** (toy models → GPT-2 small → Pythia → Gemma 2 → Claude 3), evaluation of
interpretations, current frontier-lab practice, and open problems.

## "Various methods on various models" — how the request is read

- **Various methods** = the full MI toolkit, tiered by R-GOV: probing, logit/tuned lens,
  activation/path/attribution patching, automated circuit discovery (ACDC, EAP), causal
  scrubbing, distributed alignment search (DAS), sparse autoencoders (ReLU/Gated/TopK/
  JumpReLU + transcoders/crosscoders), steering / representation engineering, model editing
  (ROME/MEMIT), automated interpretability, and circuit tracing / attribution graphs.
- **Various models** = the survey deliberately tracks *which model each method was
  demonstrated on and whether it transports across scale/family*: toy/algorithmic models,
  GPT-2 (small/medium), the Pythia suite, GPT-J, Gemma 2 (Gemma Scope), Claude 3 Sonnet
  / 3.5 Haiku, and a bridge back to the vision-model roots (InceptionV1, CLIP). "Does this
  method survive the jump from GPT-2 to a frontier model?" is a recurring cross-cutting
  question, not a separate section.

## Audience & register

- **Reader (CONFIRMED `practitioner`):** Staff-level register — assume working ML/DL math,
  cite or forward-reference prerequisites, one intuition box per load-bearing result, worked
  example FOLLOWS the derivation as a self-checking oracle. Signal-processing analogies are
  kept as *tight one-liners* where they illuminate (matched filter / basis pursuit for SAEs,
  Fourier for the grokking circuit), not as the primary scaffolding.
- Register changes exposition only; every boxed result, worked-oracle number, epistemic
  tag, and load-bearing derivation step is register-invariant.

## Depth (R-GOV tiers)

- **Headline** (full derivation + worked example + figure): the residual-stream framework
  & QK/OV circuits; superposition/toy-models; activation patching; sparse autoencoders
  (the SAE objective + one variant family); induction-head & IOI circuits.
- **Load-bearing** (derivation + intuition + complexity, no full worked example): logit/
  tuned lens, attribution patching, ACDC/EAP, DAS, steering vectors / RepE, ROME, transcoders
  /crosscoders, auto-interp, attribution graphs.
- **Catalog-only** (stated result + applicability + explicit `n/a`): the long tail of
  probing variants, individual SAE micro-variants (BatchTopK, Matryoshka), causal scrubbing
  details, feature-visualization (vision heritage), etc.

## Output contract

Multi-file survey under `surveys/mechanistic-interpretability/`, driven by `order.json`,
single `references.md` (source-tag invariant), heavy derivations in appendices, math-authoring
marker discipline throughout, `/check-survey` green at sign-off, citation-audit before delivery.

## Exclusions (scope boundaries)

- **Not** general XAI / post-hoc attribution (SHAP, LIME, Grad-CAM, integrated gradients)
  except where explicitly contrasted with MI's causal stance.
- **Not** a broad transformer-architecture survey — fundamentals cover only what MI needs
  (residual stream, attention/MLP as read/write ops). Cross-link to any architecture survey.
- **Not** an alignment/safety survey — safety *applications* of MI are covered (a section),
  but RLHF/DPO/red-teaming machinery is out of scope (cross-link).
- Concept-based / prototype interpretability (TCAV, ProtoPNet) mentioned as contrast only.

## Source preferences

Primary sources first: Anthropic transformer-circuits.pub (Elhage, Olah, Bricken, Templeton,
Lindsey), DeepMind (Nanda, Rajamanoharan, Conmy — Gemma Scope, ACDC), OpenAI (Gao TopK SAEs,
Bills auto-interp), EleutherAI (Belrose tuned lens), Redwood (causal scrubbing), Stanford
(Geiger DAS), Bau/Meng (ROME/MEMIT), academic circuit work (Wang IOI, Olsson induction,
Hanna greater-than). Acquire full text via `source-fetch`; cite per citation-integrity rule.

## Governing quality gates (per skill + CLAUDE.md)

R-GOV depth tiers · R-CARD uniform method cards · R-SURVEY artifacts (comparison matrix,
quantitative SOTA table, figures, notation contract, open-problems + RIS handoff, Q&A
appendix) · R-DEPTH per-card depth · R-MATHREV/R-COVER/R-RUBRIC coverage scoring · MAST
per-phase failure checks (P2-5) · citation-integrity + cross-linking + math-authoring
hook-enforced · wide-scale safety-net invariants (checkpoint writes, agent hardening, retry
policy, coverage-gap markers on fallback).
