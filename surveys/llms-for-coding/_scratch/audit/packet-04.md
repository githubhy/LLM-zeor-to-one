# Citation-audit packet 04

1 source(s), 13 citation marker(s).

## Reference [9]

- **Source PDF:** `download/starcoder2-2024.pdf`
- **Reference entry:** A. Lozhkov, R. Li, L. Ben Allal, F. Cassano, et al., "StarCoder 2 and The Stack v2: The Next Generation." 2024
- **Cited in:** compute-cost-and-latency-tradeoffs, language-models-from-first-principles, pretraining-data, pretraining-objectives-and-scaling, safety-security-and-licensing
- **Markers:** 13

### Claims to verify (each is a sentence from the survey that cites this source)

1. `language-models-from-first-principles.md:175` — 3\mathrm{T}\$ [[9]](references.
2. `pretraining-data.md:23` — 5 TB raw dataset yielding over 900B unique training tokens, four times the first StarCoder corpus [[9]](references.
3. `pretraining-data.md:23` — StarCoder 2's largest 15B model trains on over 913B unique tokens drawn from it [[9]](references.
4. `pretraining-data.md:28` — md#ref-7), [[9]](references.
5. `pretraining-data.md:33` — md#ref-7), [[9]](references.
6. `pretraining-data.md:43` — md#ref-8), [[9]](references.
7. `pretraining-objectives-and-scaling.md:16` — StarCoder and StarCoder 2 use a 49,152-token vocabulary (including FIM sentinels) and report that raising it to 100k "did not improve performance," so they kept it small [[9]](references.
8. `pretraining-objectives-and-scaling.md:21` — StarCoder 2 instead concatenates each repository's files in *random* order, delimited by a file-separator token, treating cross-file learning as a consequence of co-occurrence rather than explicit ordering [[9]](references.
9. `pretraining-objectives-and-scaling.md:21` — md#ref-8), [[9]](references.
10. `pretraining-objectives-and-scaling.md:26` — 3 trillion tokens — far past the token count a compute-optimal law would prescribe — because the goal is inference efficiency, not training efficiency [[9]](references.
11. `compute-cost-and-latency-tradeoffs.md:11` — The second is **deliberate over-training** (Section 7): StarCoder 2 trains small models far past the compute-optimal token count specifically to make *inference* cheap, accepting higher training cost for a smaller, faster deployed model [[9]](references.
12. `safety-security-and-licensing.md:21` — md#ref-8), [[9]](references.
