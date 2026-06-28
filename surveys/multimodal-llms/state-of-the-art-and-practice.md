<!-- sec:11 -->
## <a id="sec-11"></a>11 State of the art and current practice

<a id="p-11-state-of-the-art-and-current-practice-1"></a><!-- para:11-state-of-the-art-and-current-practice-1 --> Two questions close the empirical arc: *what scores best right now*, and *what do practitioners actually deploy* — which turn out to have different answers. This section gives a quantitative SOTA snapshot read against the § <!-- secxref:9.3 -->[§9.3](evaluation-and-benchmarks.md#sec-9.3) caveats, argues the deployment-gap thesis that explains the divergence, and maps the dominant practice at each stage of the stack. Headline depth: these are the survey's "what is true today" claims, and each rests on a number read from a primary source, not a leaderboard screenshot.

<!-- sec:11.1 -->
### <a id="sec-11.1"></a>11.1 A quantitative SOTA snapshot

<a id="p-111-a-quantitative-sota-snapshot-1"></a><!-- para:111-a-quantitative-sota-snapshot-1 --> The table below compiles benchmark accuracies from the comparison table of the Qwen2.5-VL technical report <!-- cite:26 -->[[26]](#ref-26), which is the source actually read for every figure here. All numbers are validation/mini splits under the report's evaluation protocol (chain-of-thought where the benchmark uses it); the closed-model rows (GPT-4o, Claude) are *as compiled by that third party* and may differ from vendor self-reports, and every figure carries the § <!-- secxref:9 -->[§9](evaluation-and-benchmarks.md#sec-9) caveats — finite-split confidence intervals, and the multimodal-gain caution that a slice of any MMMU score is text-only-solvable.

| Model | Access | MMMU (val) | MathVista (mini) | MMStar |
|---|---|---|---|---|
| Qwen2.5-VL-72B | open | 70.2 | 74.8 | 70.8 |
| InternVL2.5-78B | open | 70.1 | 72.3 | 69.5 |
| Qwen2-VL-72B | open | 64.5 | 70.5 | 68.3 |
| Qwen2.5-VL-7B | open | 58.6 | 68.2 | 63.9 |
| GPT-4o (0513) | closed | 69.1 | 63.8 | 64.7 |
| Claude-3.5-Sonnet (0620) | closed | 68.3 | 67.7 | n/r |

<a id="p-111-a-quantitative-sota-snapshot-2"></a><!-- para:111-a-quantitative-sota-snapshot-2 --> The headline reading is the survey's single most consequential empirical claim: **the open frontier has caught the closed frontier on these benchmarks.** Qwen2.5-VL-72B's MMMU $70.2$ edges GPT-4o's $69.1$ and Claude-3.5-Sonnet's $68.3$; on MathVista the open models lead outright ($74.8$ and $72.3$ versus $63.8$); on MMStar the best open model ($70.8$) tops GPT-4o ($64.7$) <!-- cite:26 -->[[26]](#ref-26). The honest qualifications matter — these are one report's compilation, the closed vendors evaluate under their own protocols, and a $1$–$2$-point margin on a validation split is inside the noise § 9.1 warned about — but the *gross* picture is not noise: a year earlier the closed models led comfortably, and open weights have closed that gap. Document and OCR benchmarks tell the same story, with open models reporting the top DocVQA and chart scores in the same report. The MMMU human-expert ceiling of $88.6\%$ (§ <!-- secxref:9.1 -->[§9.1](evaluation-and-benchmarks.md#sec-9.1)) remains far above every row — model and open-versus-closed differences are small next to the gap to human experts. *[reported]* (third-party-compiled benchmark numbers; see § 9 caveats).

<!-- sec:11.2 -->
### <a id="sec-11.2"></a>11.2 The deployment-gap thesis

<a id="p-112-the-deployment-gap-thesis-1"></a><!-- para:112-the-deployment-gap-thesis-1 --> If open and closed models score within a point or two, the *deployment* picture is decided by everything benchmarks do not measure — and there the open early-fusion family wins decisively for self-hosted use. The thesis has three legs. **Parity removes the quality excuse**: when a self-hostable model matches the best API on your task's benchmark (§ 11.1), the residual reasons to pay for a closed API — raw capability — largely evaporate. **Cost and data sovereignty pull the other way**: a self-hosted open-weight model runs at commodity compute cost and keeps sensitive images (medical scans, documents, internal screenshots) entirely on-premises, a hard requirement in regulated settings that no API can meet. **Fine-tunability is the decider**: the LLaVA paradigm (§ <!-- secxref:5.2 -->[§5.2](training-and-alignment.md#sec-5.2)) ships full weights *and* a public training recipe, so a practitioner can fine-tune on their own domain — a capability a closed API structurally cannot offer. The result is a genuine gap between *what tops the leaderboard* and *what is deployed*: the early-fusion, MLP-projector, instruction-tuned open model is the workhorse of self-hosted multimodal AI even where a closed model scores marginally higher. The Molmo line sharpens the point — by investing in open *data* and a careful pipeline it reached near-parity with strong closed models, evidence that the remaining gap is *investment*, not an intrinsic open-versus-closed divide <!-- cite:29 -->[[29]](#ref-29). The closed frontier still leads on the frontier-most capabilities (real-time omni interaction, the longest contexts), but for the bulk of perceive-and-answer workloads the deployment-relevant choice is open. *[reported]* (deployment patterns; the parity claim is the § 11.1 verified anchor).

<!-- sec:11.3 -->
### <a id="sec-11.3"></a>11.3 Dominant practice, stage by stage

<a id="p-113-dominant-practice-stage-by-stage-1"></a><!-- para:113-dominant-practice-stage-by-stage-1 --> Stripped to what is *actually preferred* in modern open systems, the stack has converged to a recognizable default at every stage — the practical distillation of §§ 2–8.

- <a id="p-113-dominant-practice-stage-by-stage-2"></a><!-- para:113-dominant-practice-stage-by-stage-2 --> **Encoder**: a CLIP- or SigLIP-pretrained ViT, frozen, increasingly *native-resolution* rather than fixed-grid (§ <!-- secxref:4.7 -->[§4.7](method-inventory.md#sec-4.7)). SigLIP is a common default for its training economy (§ <!-- secxref:4.3 -->[§4.3](method-inventory.md#sec-4.3)).
- **Connector**: an MLP projector — token-preserving, simple, strong — has displaced the Q-Former as the open default; resamplers persist only where a bounded token budget is the binding constraint (§ <!-- secxref:3.3 -->[§3.3](architecture-building-blocks.md#sec-3.3)).
- **Fusion**: early fusion (concatenate, run one transformer) dominates; deep fusion survives in the frozen-LM and many-image niches (§ <!-- secxref:3.4 -->[§3.4](architecture-building-blocks.md#sec-3.4)).
- **Resolution**: AnyRes tiling or native-resolution patching, to feed document and chart detail without a fixed-grid ceiling (§ <!-- secxref:4.10 -->[§4.10](method-inventory.md#sec-4.10)).
- **Training**: the LLaVA two-stage recipe (align the projector, then instruction-tune the LLM), increasingly followed by a preference-alignment pass (DPO and its multimodal variants) to curb hallucination (§ <!-- secxref:5.2 -->[§5.2](training-and-alignment.md#sec-5.2)–<!-- secxref:5.3 -->[§5.3](training-and-alignment.md#sec-5.3)).
- **Generation**: still genuinely unsettled — discrete-AR (Chameleon/Emu3) for clean unification, diffusion hybrids (Transfusion) for fidelity, with no convergence yet (§ <!-- secxref:6.4 -->[§6.4](multimodal-generation.md#sec-6.4)).
- **Serving**: token reduction is now standard for high-resolution and video workloads — resampling, merging, or attention-based pruning to keep the visual token bill payable (§ <!-- secxref:8.2 -->[§8.2](inference-and-serving.md#sec-8.2)).

<a id="p-113-dominant-practice-stage-by-stage-3"></a><!-- para:113-dominant-practice-stage-by-stage-3 --> The one-sentence summary of current practice: *a frozen SigLIP/CLIP ViT at native resolution, an MLP projector, early fusion into an instruction-tuned and preference-aligned open LLM, served with token pruning* — with generation the sole stage where the field has not yet chosen. The design-guidance and open-problems sections turn this consensus, and its one gap, into procedure and roadmap.
