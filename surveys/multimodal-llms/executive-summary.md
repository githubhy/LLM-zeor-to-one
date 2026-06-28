<!-- sec:0 -->
## <a id="sec-0"></a>0 Executive summary

<a id="p-0-executive-summary-1"></a><!-- para:0-executive-summary-1 --> **The 60-second verdict.** A multimodal large language model keeps a text-token transformer exactly as it is and lets non-text signals — images, audio, video — enter the same computation, and in the newest systems leave it too. The whole field reduces to one problem (turn a continuous signal into a short sequence of vectors a token model can read, in a geometry it understands) solved along three axes: *where* the signal enters (a pretrained encoder, or raw patches), *how* it fuses with text (concatenated at the input, cross-attended inside a frozen LM, or quantized into the LM's own vocabulary), and *what* is generated (text only, or any modality). Modern open practice has converged to a clear default — **a frozen SigLIP/CLIP vision transformer at native resolution, an MLP projector, early fusion into an instruction-tuned and preference-aligned open LLM, served with token pruning** — and the survey's single most consequential empirical finding is that, on the standard understanding benchmarks, **the open frontier has caught the closed frontier** (Qwen2.5-VL-72B's MMMU $70.2$ versus GPT-4o's $69.1$), while a human-expert ceiling near $88.6\%$ remains far above every model. The one stage where the field has *not* converged is generation: discrete-autoregressive (Chameleon, Emu3) buys clean unification, continuous-diffusion (Transfusion) buys image fidelity, and no design yet pays neither tax.

<a id="p-0-executive-summary-2"></a><!-- para:0-executive-summary-2 --> **Who should read what.** A reader fluent in transformers can skim § <!-- secxref:2 -->[§2](fundamentals.md#sec-2) and start at the architecture design space (§ <!-- secxref:3 -->[§3](architecture-building-blocks.md#sec-3)); a reader wanting the landscape can read the method inventory (§ <!-- secxref:4 -->[§4](method-inventory.md#sec-4)) and the comparison matrix (§ <!-- secxref:10.1 -->[§10.1](comparison-and-tradeoffs.md#sec-10.1)); a practitioner with a requirement should go straight to the decision order (§ <!-- secxref:12.1 -->[§12.1](design-guidance.md#sec-12.1)). The survey is written in a *learner* register — prerequisites are derived from first principles, results are motivated with signal-processing analogies, and worked numerical examples lead.

<a id="p-0-executive-summary-3"></a><!-- para:0-executive-summary-3 --> **Claims → evidence spine.** Each load-bearing claim of the survey, and where it is established:

| Claim | Where |
|---|---|
| Feeding a continuous signal to a discrete-token model is a sampling-and-embedding (front-end) problem | § <!-- secxref:2.1 -->[§2.1](fundamentals.md#sec-2.1) |
| Patch embedding is a learned filterbank; tokens scale as resolution-squared, attention as resolution-to-the-fourth | § <!-- secxref:2.2 -->[§2.2](fundamentals.md#sec-2.2) |
| Contrastive pretraining (CLIP InfoNCE) yields the language-aligned encoder almost every system reuses | § <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) |
| The connector's token count is as consequential as its geometry; resamplers bound it, projectors preserve detail | § <!-- secxref:3.3 -->[§3.3](architecture-building-blocks.md#sec-3.3) |
| Fusion is early-concat vs deep-cross-attention vs native-token; each sits differently on the forgetting curve | § <!-- secxref:3.4 -->[§3.4](architecture-building-blocks.md#sec-3.4) |
| The LLaVA two-stage recipe turns frozen parts into a visual assistant cheaply; data quality is a first-class lever | § <!-- secxref:5.2 -->[§5.2](training-and-alignment.md#sec-5.2) |
| Preference alignment cuts hallucination but must be made to depend on the image (mDPO) | § <!-- secxref:5.3 -->[§5.3](training-and-alignment.md#sec-5.3) |
| Generation splits into discrete-AR vs continuous-diffusion, an unresolved tension | § <!-- secxref:6.4 -->[§6.4](multimodal-generation.md#sec-6.4) |
| Audio and video reuse the same template with different front-ends (the mel spectrogram is patch embedding for sound) | § <!-- secxref:7.1 -->[§7.1](modality-breadth.md#sec-7.1) |
| The visual token count is the dominant serving cost; compression reclaims it at three stack positions | § <!-- secxref:8.1 -->[§8.1](inference-and-serving.md#sec-8.1) |
| Much benchmark signal is text-solvable or contaminated; read every score with the multimodal-gain caveat | § <!-- secxref:9.3 -->[§9.3](evaluation-and-benchmarks.md#sec-9.3) |
| Open models have reached benchmark parity with the closed frontier | § <!-- secxref:11.1 -->[§11.1](state-of-the-art-and-practice.md#sec-11.1) |
| Open early-fusion VLMs dominate self-hosted deployment despite the leaderboard, on cost, privacy, and fine-tunability | § <!-- secxref:11.2 -->[§11.2](state-of-the-art-and-practice.md#sec-11.2) |
| The remaining human-model gap is concentrated in fine-grained grounding and unsettled generation | § <!-- secxref:13.1 -->[§13.1](open-problems-and-roadmap.md#sec-13.1) |

<a id="p-0-executive-summary-4"></a><!-- para:0-executive-summary-4 --> Every external citation traces to a source acquired in `download/` and read; benchmark numbers are reproduced from the primary that reports them, and closed-model figures are flagged as third-party-compiled. The full method inventory, derivations, and reference list follow.
