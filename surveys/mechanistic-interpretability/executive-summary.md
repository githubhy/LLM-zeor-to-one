<!-- sec:0 -->
## <a id="sec-0"></a>0 Executive summary

<a id="p-0-executive-summary-1"></a><!-- para:0-executive-summary-1 --> **The 60-second verdict.** Mechanistic interpretability (MI) is the program of reverse-engineering a
trained network's internal computation into human-understandable **features** (directions in
activation space that stand for concepts) and **circuits** (subgraphs of components that compose
those features into an algorithm). It rests on three empirical pillars established on transformers:
the **residual stream** is a shared linear workspace that every attention head and MLP reads from
and writes to <!-- cite:1 --> [[1]](references.md#ref-1); concepts are represented (largely) as **linear directions** <!-- cite:2 --> [[2]](references.md#ref-2), <!-- cite:4 --> [[4]](references.md#ref-4); and a network
packs more features than it has neurons by placing them in **superposition**, which is why individual
neurons look polysemantic <!-- cite:3 --> [[3]](references.md#ref-3). The field's trajectory is a ladder of abstraction: **hand-found
circuits** (induction heads <!-- cite:80 --> [[80]](references.md#ref-80), the IOI circuit <!-- cite:35 --> [[35]](references.md#ref-35), the fully reverse-engineered
grokking algorithm <!-- cite:55 --> [[55]](references.md#ref-55)) → **causal localization** made scalable (activation, path, and attribution
patching <!-- cite:31 --> [[31]](references.md#ref-31), <!-- cite:36 --> [[36]](references.md#ref-36), <!-- cite:38 --> [[38]](references.md#ref-38); automated discovery, ACDC/EAP <!-- cite:40 --> [[40]](references.md#ref-40), <!-- cite:38 --> [[38]](references.md#ref-38)) → **unsupervised feature extraction**
via sparse autoencoders (SAEs), scaled to a production model with millions of features <!-- cite:7 --> [[7]](references.md#ref-7), <!-- cite:8 --> [[8]](references.md#ref-8) → and,
most recently, **attribution graphs / circuit tracing**, which replace MLPs with cross-layer
transcoders to draw an end-to-end causal graph of a single forward pass in a frontier model <!-- cite:20 --> [[20]](references.md#ref-20), <!-- cite:21 --> [[21]](references.md#ref-21).

<a id="p-0-executive-summary-2"></a><!-- para:0-executive-summary-2 --> The single most consequential development of 2024–2025 is a **reckoning for SAEs**: on downstream tasks (steering, probing) SAE features do **not** beat simple baselines — prompting and difference-in-means directions win — leading a major lab to publicly *deprioritise* SAE research <!-- cite:66 --> [[66]](references.md#ref-66), <!-- cite:67 --> [[67]](references.md#ref-67), while the frontier pivots to transcoders and attribution graphs <!-- cite:18 --> [[18]](references.md#ref-18), <!-- cite:20 --> [[20]](references.md#ref-20). The honest state of the field is therefore two-sided: MI produces genuine, sometimes product-shippable wins (Golden-Gate-Claude feature steering <!-- cite:75 --> [[75]](references.md#ref-75); a linear probe catches "sleeper-agent" defection at over 99% AUROC <!-- cite:71 --> [[71]](references.md#ref-71)), yet it is **not yet** a reliable safety tool and its own leaders estimate a true diagnostic capability is 5–10 years away <!-- cite:76 --> [[76]](references.md#ref-76). And a foundational caution runs through everything: a circuit's headline "faithfulness" number is **not robust** — swapping node- for edge-ablation moves it by more than 50 points on the *same* circuit <!-- cite:62 --> [[62]](references.md#ref-62), and the network's own **self-repair** makes any single-ablation importance estimate a lower bound <!-- cite:59 --> [[59]](references.md#ref-59), <!-- cite:60 --> [[60]](references.md#ref-60).

<a id="p-0-executive-summary-3"></a><!-- para:0-executive-summary-3 --> **Who should read what.** A reader fluent in the transformer-circuits framework can skim the
fundamentals (§ <!-- secxref:2 -->[§2](fundamentals.md#sec-2)) and start at the taxonomy
(§ <!-- secxref:3 -->[§3](methodology-and-taxonomy.md#sec-3)); a reader wanting the landscape should
read the five-part method inventory (§§ <!-- secxref:4 -->[§4](method-inventory-observational.md#sec-4)–<!-- secxref:8 -->[§8](method-inventory-automation.md#sec-8))
and the comparison matrix (§ <!-- secxref:11.1 -->[§11.1](comparison-and-tradeoffs.md#sec-11.1)); a
practitioner with a question in hand should go straight to the decision framework
(§ <!-- secxref:14.1 -->[§14.1](design-guidance.md#sec-14.1)). The survey is written in a
**practitioner** register: standard deep-learning prerequisites are assumed, each load-bearing result
carries one intuition box, and worked numerical examples follow as self-checks.

<a id="p-0-executive-summary-4"></a><!-- para:0-executive-summary-4 --> **Claims → evidence spine.** Each load-bearing claim, and where it is established:

| Claim | Where |
|---|---|
| The residual stream is an additive linear workspace; attention/MLP are read/write ops; "virtual weights" compose across it | § <!-- secxref:2.1 -->[§2.1](fundamentals.md#sec-2.1) |
| Each head factors into an independent QK circuit (where to attend) and OV circuit (what to move) | § <!-- secxref:2.2 -->[§2.2](fundamentals.md#sec-2.2) |
| Features are linear directions; superposition explains polysemantic neurons and motivates dictionary learning | § <!-- secxref:2.4 -->[§2.4](fundamentals.md#sec-2.4) |
| Probing shows a concept is *decodable*, never that it is *used*; causal intervention is the load-bearing step | § <!-- secxref:3.1 -->[§3.1](methodology-and-taxonomy.md#sec-3.1) |
| Activation patching localizes behavior causally; the logit-difference metric and the denoise/noise direction matter | § <!-- secxref:5.1 -->[§5.1](method-inventory-causal.md#sec-5.1) |
| Attribution patching is a first-order approximation that makes patching every site scalable — and where it breaks | § <!-- secxref:5.3 -->[§5.3](method-inventory-causal.md#sec-5.3) |
| The SAE objective (reconstruction + sparsity) recovers monosemantic features; scales to millions on Claude 3 | § <!-- secxref:6.1 -->[§6.1](method-inventory-dictionary.md#sec-6.1) |
| Gated / TopK / JumpReLU each fix L1's shrinkage bias by decoupling the sparsity signal from the magnitude | § <!-- secxref:6.2 -->[§6.2](method-inventory-dictionary.md#sec-6.2) |
| Attribution graphs (cross-layer transcoders + local replacement model) are the current frontier circuit artifact | § <!-- secxref:8.3 -->[§8.3](method-inventory-automation.md#sec-8.3) |
| Refusal, sycophancy, honesty are each mediated by a single steerable direction | § <!-- secxref:7.3 -->[§7.3](method-inventory-steering-editing.md#sec-7.3) |
| Locate-then-edit works, but editing success does not validate the localization (ROME vs. causal tracing) | § <!-- secxref:7.4 -->[§7.4](method-inventory-steering-editing.md#sec-7.4) |
| Faithfulness metrics are not robust to ablation choice; self-repair makes single-ablation an underestimate | § <!-- secxref:10.1 -->[§10.1](evaluation-and-metrics.md#sec-10.1) |
| SAEs lose to simple baselines on downstream tasks; the field is pivoting to transcoders + attribution graphs | § <!-- secxref:12.2 -->[§12.2](state-of-the-art-and-practice.md#sec-12.2) |
| MI has product-level steering/monitoring wins but is not yet a robust, adversarially-safe safety tool | § <!-- secxref:13.1 -->[§13.1](applications.md#sec-13.1) |

<a id="p-0-executive-summary-5"></a><!-- para:0-executive-summary-5 --> Every external citation traces to a source acquired in `download/` (or a web-native publication,
tagged as such) and read; every load-bearing numeric value is reproduced from the primary that
reports it, and search-derived numbers awaiting primary confirmation are flagged at point of use. The
full method inventory, first-principles derivations (Appendices A–E), and reference list follow.
