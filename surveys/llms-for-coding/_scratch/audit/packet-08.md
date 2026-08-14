# Citation-audit packet 08

2 source(s), 16 citation marker(s).

## Reference [4]

- **Source PDF:** `download/incoder-2022.pdf`
- **Reference entry:** D. Fried, A. Aghajanyan, J. Lin, S. Wang, et al., "InCoder: A Generative Model for Code Infilling and Synthesi
- **Cited in:** executive-summary, historical-evolution, language-models-from-first-principles, scope-and-the-code-modality
- **Markers:** 8

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-3), [[4]](references.
2. `scope-and-the-code-modality.md:15` — ** Prose is typically consumed left to right, but "code is seldom written in a single left-to-right pass and is instead repeatedly edited and refined" [[4]](references.
3. `scope-and-the-code-modality.md:17` — md#ref-3)) or allow byte-level merges to cross whitespace (InCoder reports a 45% reduction in tokens needed to encode its corpus relative to GPT-2's tokenizer [[4]](references.
4. `scope-and-the-code-modality.md:26` — - **Infilling / fill-in-the-middle** — generating a span given both its left and right context [[4]](references.
5. `scope-and-the-code-modality.md:27` — - **Program repair and editing** — fixing or transforming existing code, which InCoder frames as masking-and-infilling [[4]](references.
6. `language-models-from-first-principles.md:244` — md#ref-3), [[4]](references.
7. `language-models-from-first-principles.md:244` — InCoder instead trains a byte-level BPE tokenizer that allows merges to cross whitespace (excluding newlines), so an idiom like `import numpy as np` can become a single token; this reduces the tokens needed to encode its corpus by 45% relative to GPT-2's tokenizer [[4]](references.
8. `historical-evolution.md:24` — - **InCoder (2022)** was the first large generative code model that could *infill* — generate a span conditioned on both left and right context — via a causal-masking objective, unlocking editing, type inference, and comment generation as zero-shot tasks [[4]](references.

## Reference [7]

- **Source PDF:** `download/the-stack-2022.pdf`
- **Reference entry:** D. Kocetkov, R. Li, L. Ben Allal, J. Li, et al., "The Stack: 3 TB of Permissively Licensed Source Code." 2022.
- **Cited in:** historical-evolution, pretraining-data, safety-security-and-licensing
- **Markers:** 8

### Claims to verify (each is a sentence from the survey that cites this source)

1. `historical-evolution.md:27` — - **StarCoder (2023)** paired an open model with an open, *governed* dataset (The Stack), 15B parameters trained on 1T tokens with 8k context, FIM, and multi-query attention for fast inference [[7]](references.
2. `pretraining-data.md:23` — The Stack (2022) was assembled by collecting active GitHub repository names from the public GHArchive event timeline and pulling their source files [[7]](references.
3. `pretraining-data.md:23` — 1 TB across 30 programming languages — only about 10% of the raw data survives the license filter [[7]](references.
4. `pretraining-data.md:23` — A handful of languages dominate by volume: HTML, JavaScript, Java, and C together account for more than half the permissive dataset [[7]](references.
5. `pretraining-data.md:28` — The Stack's response is permissive-only selection plus a data-governance plan: license detection runs over repositories (via GHArchive metadata where available, and the `go-license-detector`/ScanCode toolkit for the ~97% of repositories lacking repo-level metadata), and developers can request removal of their code through a documented opt-out process [[7]](references.
6. `pretraining-data.md:33` — 7, breaking ties toward higher-starred repositories to preserve context) [[7]](references.
7. `pretraining-data.md:33` — 6% of files are near-duplicates that get removed, and the authors report that "near-deduplicating the data significantly boosts performance across all experiments" [[7]](references.
8. `safety-security-and-licensing.md:21` — The open ecosystem's answer is licensing-by-construction (Section 6): The Stack selects only permissively licensed files and offers a developer opt-out, an explicit attempt to make training data legally defensible rather than litigating after the fact [[7]](references.
