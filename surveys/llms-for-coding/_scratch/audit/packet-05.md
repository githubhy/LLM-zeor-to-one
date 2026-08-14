# Citation-audit packet 05

1 source(s), 10 citation marker(s).

## Reference [5]

- **Source PDF:** `download/fim-bavarian-2022.pdf`
- **Reference entry:** M. Bavarian, H. Jun, N. Tezak, J. Schulman, et al., "Efficient Training of Language Models to Fill in the Midd
- **Cited in:** executive-summary, historical-evolution, inference-decoding-and-serving, language-models-from-first-principles, pretraining-objectives-and-scaling, scope-and-the-code-modality
- **Markers:** 10

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:13` — A simple document transform gives causal models the ability to infill — essential for editing — at no measurable cost to ordinary generation [[5]](references.
2. `scope-and-the-code-modality.md:26` — md#ref-4), [[5]](references.
3. `language-models-from-first-principles.md:249` — Split a document into three pieces and move the middle to the end [[5]](references.
4. `language-models-from-first-principles.md:256` — A **suffix-prefix-middle (SPM)** ordering also exists and is preferred for key-value cache reuse, because appending tokens to the prefix does not invalidate the cached suffix [[5]](references.
5. `language-models-from-first-principles.md:256` — The transform is applied at the character level so completions remain sensible when a prefix ends mid-token, and the best results come from training jointly on PSM and SPM [[5]](references.
6. `language-models-from-first-principles.md:256` — The defining empirical result is "FIM-for-free": training with a 50% FIM rate leaves the left-to-right loss unchanged, so infilling is acquired at no measurable cost to ordinary generation [[5]](references.
7. `historical-evolution.md:25` — , 2022)** showed infilling could be added to any autoregressive model essentially for free, by a simple document transformation (Section 3), making FIM a standard ingredient [[5]](references.
8. `pretraining-objectives-and-scaling.md:11` — The canonical FIM study recommends a 50% FIM rate, character-level spans, and joint training on the prefix-suffix-middle (PSM) and suffix-prefix-middle (SPM) orderings [[5]](references.
9. `inference-decoding-and-serving.md:11` — In the prefix-suffix-middle scheme the model is fed everything up to the middle sentinel and samples until it emits an end-of-text token signaling it has joined prefix to suffix; failure to emit that token signals an unsuccessful join [[5]](references.
10. `inference-decoding-and-serving.md:18` — Caching is the other half: the suffix-prefix-middle FIM ordering exists partly so that appending tokens to the prefix does not invalidate the suffix's cached keys and values [[5]](references.
