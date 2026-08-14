# Citation-audit packet 03

1 source(s), 13 citation marker(s).

## Reference [1]

- **Source PDF:** `download/chen-codex-evaluating-llms-code-2021.pdf`
- **Reference entry:** M. Chen, J. Tworek, H. Jun, Q. Yuan, et al., "Evaluating Large Language Models Trained on Code." 2021. arXiv:2
- **Cited in:** executive-summary, historical-evolution, language-models-from-first-principles, scope-and-the-code-modality
- **Markers:** 13

### Claims to verify (each is a sentence from the survey that cites this source)

1. `executive-summary.md:8` — md#ref-2) gave way to Codex [[1]](references.
2. `scope-and-the-code-modality.md:11` — Codex operationalizes this by judging a generated program correct if and only if it passes a set of unit tests, and by executing untrusted model output inside a hardened sandbox (a gVisor container) to prevent a malicious or buggy sample from damaging the host [[1]](references.
3. `scope-and-the-code-modality.md:13` — Codex argues that match-based metrics such as exact match and BLEU are fundamentally deficient for code: they "are unable to account for the large and complex space of programs functionally equivalent to a reference solution," and the paper shows empirically that functionally *inequivalent* programs often score *higher* BLEU than equivalent ones [[1]](references.
4. `scope-and-the-code-modality.md:24` — - **Completion** — left-to-right continuation of partial code; the canonical IDE autocomplete setting [[1]](references.
5. `scope-and-the-code-modality.md:25` — - **Natural-language-to-code synthesis** — generating a function from a docstring or specification, as in HumanEval [[1]](references.
6. `scope-and-the-code-modality.md:28` — - **Code translation** — porting between languages, a functional-correctness task Codex cites as motivation [[1]](references.
7. `language-models-from-first-principles.md:244` — md#ref-4), and Codex is a GPT-family model fine-tuned on code [[1]](references.
8. `language-models-from-first-principles.md:261` — Codex instead draws $n \geq k$ samples per problem (the paper uses $n = 200$, $k \leq 100$), counts the number $c \leq n$ that pass, and computes the unbiased estimator [[1]](references.
9. `language-models-from-first-principles.md:268` — It is tempting to instead estimate pass@k as $1-(1-\hat{p})^k$ from an empirical pass@1 of $\hat{p}$, but Codex shows this is biased [[1]](references.
10. `language-models-from-first-principles.md:275` — Functional correctness is "the most convincing" criterion because it is the one human developers use [[1]](references.
11. `historical-evolution.md:16` — OpenAI fine-tuned a GPT-3-family decoder on code collected in May 2020 from 54 million public GitHub repositories — 179 GB of unique Python files under 1 MB, filtered to a final 159 GB [[1]](references.
12. `historical-evolution.md:16` — 2% of problems [[1]](references.
