<!-- sec:15 -->
## <a id="sec-15"></a>15 State of the Art and Practice

<a id="p-15-state-of-the-art-and-practice-1"></a><!-- para:15-state-of-the-art-and-practice-1 --> **Depth tier:** load-bearing

<a id="p-15-state-of-the-art-and-practice-2"></a><!-- para:15-state-of-the-art-and-practice-2 --> This section is a dated snapshot, and it is built from the **official evaluation record** rather than from leaderboard screenshots. Every SWE-bench Verified figure below is computed from the per-submission `results.json` files in the SWE-bench team's own experiments repository <!-- cite:130 --> [[130]](references.md#ref-130), which lists the resolved instance identifiers for each submission. That matters for a reason <!-- secxref:13 -->[§13](evaluation-and-benchmarks.md#sec-13) makes at length: a resolve *rate* is meaningless without its denominator, and at least three denominators circulate in secondary reporting of this benchmark. Every number here is over the same 500 instances, so the rows are comparable to each other.

<a id="p-15-state-of-the-art-and-practice-3"></a><!-- para:15-state-of-the-art-and-practice-3 --> An earlier draft of this survey reported a "frontier band around 80%" as a dated web estimate carrying an explicit caveat that it was not primary-verified. The primary record confirms it — the caveat can now be discharged, and replaced with the actual curve.

<!-- sec:15.1 -->
### <a id="sec-15.1"></a>15.1 The Progression Curve

<a id="p-151-the-progression-curve-1"></a><!-- para:151-the-progression-curve-1 --> Each row is the first submission to set a new best on the official leaderboard, out of 134 submissions with published results.

| Date | Resolved / 500 | Rate |
|---|---|---|
| 2023-10 | 22 | 4.4% |
| 2024-04 | 112 | 22.4% |
| 2024-06 | 192 | 38.4% |
| 2024-08 | 226 | 45.2% |
| 2024-10 | 265 | 53.0% |
| 2024-12 | 311 | 62.2% |
| 2025-03 | 327 | 65.4% |
| 2025-05 | 366 | 73.2% |
| 2025-06 | 376 | 75.2% |
| 2025-09 | 394 | 78.8% |
| **2025-12** | **396** | **79.2%** |

<a id="p-151-the-progression-curve-2"></a><!-- para:151-the-progression-curve-2 --> Two features of this curve matter more than its endpoint.

<a id="p-151-the-progression-curve-3"></a><!-- para:151-the-progression-curve-3 --> **It is flattening.** In the six months to June 2025 the frontier moved 62.2% → 75.2%, thirteen points. In the six months after, it moved 75.2% → 79.2%, four points. Whatever else is true, the *rate* of improvement on this benchmark has fallen by roughly a factor of three, which is what a benchmark approaching its ceiling looks like from the outside — and is consistent with the retirement argument in <!-- secxref:13.5 -->[§13.5](evaluation-and-benchmarks.md#sec-13.5). It does not by itself distinguish "models stopped improving" from "the benchmark stopped measuring"; <!-- secref:15.3 -->[§15.3](#sec-15.3) argues the second is the larger part.

<a id="p-151-the-progression-curve-4"></a><!-- para:151-the-progression-curve-4 --> **The official record lags.** The most recent submission carrying published results is dated 2025-12-15, roughly eight months before this survey's own date. Vendors announce figures that never enter this record, and those announcements are the ones secondary trackers repeat. So "the current SOTA" is not a well-defined quantity: there is a slow authoritative record and a fast unverifiable one, and they do not agree.

<!-- sec:15.2 -->
### <a id="sec-15.2"></a>15.2 The Frontier Snapshot, and Two Near-Controlled Comparisons

| Date | System | Resolved / 500 | Rate |
|---|---|---|---|
| 2025-12-15 | LiveSWEAgent + Claude Opus 4.5 | 396 | 79.2% |
| 2025-12-05 | Sonar Foundation Agent + Claude Opus 4.5 | 396 | 79.2% |
| 2025-09-28 | Trae + Doubao Seed Code | 394 | 78.8% |
| 2025-11-27 | OpenHands + Claude Opus 4.5 | 388 | 77.6% |
| 2025-11-20 | LiveSWEAgent + Gemini 3 Pro (preview) | 387 | 77.4% |
| 2025-11-03 | Salesforce SAGE (OpenHands scaffold) | 369 | 73.8% |
| 2025-10-21 | Salesforce SAGE (**bash-only**) | 365 | 73.0% |
| 2025-08-05 | OpenHands + Qwen3-Coder-480B-A35B (open weight) | 348 | 69.6% |
| 2025-09-30 | GLM-4.6 | 341 | 68.2% |
| 2025-08-05 | OpenHands + Qwen3-Coder-30B-A3B (open weight) | 258 | 51.6% |

<a id="p-152-the-frontier-snapshot-and-two-near-controlled-comparisons-1"></a><!-- para:152-the-frontier-snapshot-and-two-near-controlled-comparisons-1 --> The leaderboard is mostly a pile of incomparable `(model × scaffold × date)` triples, but two pairs in it come close to holding one factor fixed, and both are informative.

<a id="p-152-the-frontier-snapshot-and-two-near-controlled-comparisons-2"></a><!-- para:152-the-frontier-snapshot-and-two-near-controlled-comparisons-2 --> **Scaffold held nearly fixed, model varied.** The OpenHands scaffold appears with Claude Opus 4.5 at 77.6% and with the open-weight Qwen3-Coder-480B at 69.6% — an eight-point spread. The comparison is not clean: the submissions are nearly four months apart, and the scaffold itself moved in between. Read it as an upper bound on the open-vs-proprietary gap at fixed scaffolding, not as a measurement of it.

<a id="p-152-the-frontier-snapshot-and-two-near-controlled-comparisons-3"></a><!-- para:152-the-frontier-snapshot-and-two-near-controlled-comparisons-3 --> **Model held nearly fixed, scaffold varied — and this is the striking one.** The same team submitted its SAGE system twice, once on a full OpenHands scaffold (73.8%) and once **bash-only** (73.0%). Eight tenths of a point separates them. The submissions declare `Multiple` for the model, so this is a same-team comparison rather than a strictly controlled one and should not be quoted as an ablation. But it is the closest thing the official record contains to the experiment <!-- secxref:12.2 -->[§12.2](agentic-coding-systems.md#sec-12.2) describes, and it points the same way: **at the 2025 frontier, removing the custom scaffold costs almost nothing.** In 2024 the same removal cost SWE-agent 7.7 points.

<!-- sec:15.3 -->
### <a id="sec-15.3"></a>15.3 What 79.2% Is Not

<a id="p-153-what-792-is-not-1"></a><!-- para:153-what-792-is-not-1 --> The figure is a real, reproducible, primary-sourced measurement, and it is *not* a claim that the frontier resolves four real GitHub issues in five. Three subtractions from <!-- secxref:13.4 -->[§13.4](evaluation-and-benchmarks.md#sec-13.4) apply to it directly.

- <a id="p-153-what-792-is-not-2"></a><!-- para:153-what-792-is-not-2 --> **Solution leakage.** In an audit of resolved instances, 32.67% had the solution stated in the issue text or its comments <!-- cite:105 --> [[105]](references.md#ref-105). Those are reading-comprehension successes, not engineering ones.
- **Weak tests.** A further 31.08% passed on test suites too weak to separate a correct patch from an incomplete one <!-- cite:105 --> [[105]](references.md#ref-105).
- **Flaky instances.** 34 of SWE-bench Lite's 300 problems return inconsistent results for the *same* patch, and in 30 of those the flakiness appears on the dataset's own gold solution <!-- cite:107 --> [[107]](references.md#ref-107).

<a id="p-153-what-792-is-not-3"></a><!-- para:153-what-792-is-not-3 --> The audits were run on earlier systems, so the exact fractions do not transfer to a 2025 submission unchanged. The direction does. When that audit filtered its problematic instances, the measured resolve rate of the system it examined fell from 12.47% to 3.97%, and to 0.55% on issues created after the models' training cutoffs <!-- cite:105 --> [[105]](references.md#ref-105). No comparable filtered re-evaluation of a 2025-frontier system exists in the acquired literature, which is exactly why <!-- secxref:13.6 -->[§13.6](evaluation-and-benchmarks.md#sec-13.6) treats the benchmark portfolio, rather than any single number, as the state of the art in measurement.

<a id="p-153-what-792-is-not-4"></a><!-- para:153-what-792-is-not-4 --> The honest formulation: **79.2% is the state of the art at resolving SWE-bench Verified instances.** The gap between that and "resolving real issues" is not quantified, and the field has not published the experiment that would quantify it.

<!-- sec:15.4 -->
### <a id="sec-15.4"></a>15.4 What Is Actually Deployed, and How to Read a SOTA Claim

<a id="p-154-what-is-actually-deployed-and-how-to-read-a-sota-claim-1"></a><!-- para:154-what-is-actually-deployed-and-how-to-read-a-sota-claim-1 --> Three deployment modes run in production simultaneously: inline autocomplete, chat assistance, and autonomous agents. The consequential shift is the third — coding agents are now the dominant category of deployed agentic AI <!-- cite:52 --> [[52]](references.md#ref-52). On the model side the open-weight lines track the frontier closely enough that many production deployments are open-weight, chosen for cost, latency control, and self-hosting, while the top of the agentic leaderboard is held by proprietary models paired with mature scaffolds — the 69.6%-versus-79.2% spread in <!-- secref:15.2 -->[§15.2](#sec-15.2) is the current shape of that gap on this benchmark. The practical pattern is a portfolio: small fast models for autocomplete, mid-size open or frontier models for chat, the strongest available model for hard agentic work where solve rate justifies cost (<!-- secxref:14 -->[§14](compute-cost-and-latency-tradeoffs.md#sec-14)).

<a id="p-154-what-is-actually-deployed-and-how-to-read-a-sota-claim-2"></a><!-- para:154-what-is-actually-deployed-and-how-to-read-a-sota-claim-2 --> Four rules make a state-of-the-art claim survivable, and this survey follows all four.

1. <a id="p-154-what-is-actually-deployed-and-how-to-read-a-sota-claim-3"></a><!-- para:154-what-is-actually-deployed-and-how-to-read-a-sota-claim-3 --> **A benchmark number is a `(model × scaffold × date)` product.** None of the three can be recovered from the number.
2. **Demand the denominator.** A resolve rate without an instance count is not comparable across evaluators.
3. **Prefer the primary record over the tracker.** The figures above come from the submissions' own result files; secondary trackers reporting materially higher numbers for the same benchmark could not be reproduced across two independent attempts during this survey's evidence round, and are not cited here.
4. **Separate benchmark progress from capability progress.** The function-level classics are saturated and no longer discriminate <!-- cite:44 --> [[44]](references.md#ref-44); SWE-bench Verified is flattening and under documented audit pressure; the contamination-resistant option is the time-windowed construction of LiveCodeBench <!-- cite:39 --> [[39]](references.md#ref-39). Progress is real — 4.4% to 79.2% in twenty-six months on a fixed 500-instance set is not a measurement artifact — but the last few points of it are the least trustworthy, and the field's own answer has been to retire the benchmark rather than to defend them.
