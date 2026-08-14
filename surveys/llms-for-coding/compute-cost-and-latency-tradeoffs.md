<!-- sec:14 -->
## <a id="sec-14"></a>14 Compute, Cost, and Latency Tradeoffs

<a id="p-14-compute-cost-and-latency-tradeoffs-1"></a><!-- para:14-compute-cost-and-latency-tradeoffs-1 --> **Depth tier:** load-bearing

<a id="p-14-compute-cost-and-latency-tradeoffs-2"></a><!-- para:14-compute-cost-and-latency-tradeoffs-2 --> Every capability claim elsewhere in this survey has a price, and the field almost never reports it. A pilot audit of twelve benchmark papers found that **none of the eight agent-benchmark papers disclosed inference cost in any form** <!-- cite:110 --> [[110]](references.md#ref-110). This section assembles what cost evidence exists, and is explicit about where it does not.

<!-- sec:14.1 -->
### <a id="sec-14.1"></a>14.1 Model Size versus Capability

<a id="p-141-model-size-versus-capability-1"></a><!-- para:141-model-size-versus-capability-1 --> The first-order lever is model size, and the tradeoff is the usual one: a larger model resolves more and costs more per token. What makes code different is that the *deployment mode* changes which end of the curve is correct. Inline autocomplete fires on every keystroke pause and must return in well under a second, so it takes the smallest model that produces usable completions. An agent that runs for minutes on one issue can afford the largest. The open-weight lines matter here because they decouple capability from per-token pricing: a self-hosted model's cost is amortized hardware, not a metered API.

<!-- sec:14.2 -->
### <a id="sec-14.2"></a>14.2 The Cost of Test-Time Compute

<a id="p-142-the-cost-of-test-time-compute-1"></a><!-- para:142-the-cost-of-test-time-compute-1 --> Sampling buys coverage on the schedule derived in <!-- secxref:J.4 -->[§J.4](appendix-j-code-derivations.md#sec-J.4), and pays for it linearly. AlphaCode draws up to a million samples per problem, filters roughly 99% of them against the example tests, and clusters the remainder down to at most 10 submissions — 34.2% of CodeContests validation problems at 10@1M against 21.0% at 10@1k <!-- cite:40 --> [[40]](references.md#ref-40). Three decades of extra sampling buys 13 points, which is the clearest statement in the literature of what inference-time scaling costs at the margin.

<a id="p-142-the-cost-of-test-time-compute-2"></a><!-- para:142-the-cost-of-test-time-compute-2 --> Reasoning models move the same tradeoff inside a single response: a longer chain of thought is more output tokens, billed as such, at higher latency.

<!-- sec:14.3 -->
### <a id="sec-14.3"></a>14.3 What an Agentic Task Actually Costs

<a id="p-143-what-an-agentic-task-actually-costs-1"></a><!-- para:143-what-an-agentic-task-actually-costs-1 --> The Holistic Agent Leaderboard is the exception that makes this subsection possible: a standardized evaluation of 9 models across 9 benchmarks in four domains, **21,730 rollouts**, about **\$40,000** of inference and 2.5 billion logged tokens <!-- cite:102 --> [[102]](references.md#ref-102). It is the only source in this survey's corpus that prices agentic evaluation systematically.

<a id="p-143-what-an-agentic-task-actually-costs-2"></a><!-- para:143-what-an-agentic-task-actually-costs-2 --> **Per-task cost, derived.** The following are *this survey's computation* — run totals divided by task count — from the leaderboard's SWE-bench Verified Mini results, a 50-task random subset, at the leaderboard's per-token prices as of **24 September 2025** <!-- cite:102 --> [[102]](references.md#ref-102):

| Configuration | Run total | Per task | Accuracy |
|---|---|---|---|
| SWE-Agent + Claude Opus 4.1 | \$1,789.67 | **\$35.79** | 54.0% |
| SWE-Agent + o4-mini (low) | \$259.20 | **\$5.18** | **54.0%** |
| SWE-Agent + GPT-5 (medium) | \$162.93 | \$3.26 | 46.0% |
| SWE-Agent + Gemini 2.0 Flash | \$4.72 | \$0.094 | 24.0% |

<a id="p-143-what-an-agentic-task-actually-costs-3"></a><!-- para:143-what-an-agentic-task-actually-costs-3 --> The headline is the first two rows: **identical accuracy at 6.9 times the cost.** That is the practical form of the scaffold-versus-model point from <!-- secxref:12.6 -->[§12.6](agentic-coding-systems.md#sec-12.6) — the expensive configuration is not buying resolution here, and a deployment that reads only the leaderboard column would pay seven times over for nothing.

<a id="p-143-what-an-agentic-task-actually-costs-4"></a><!-- para:143-what-an-agentic-task-actually-costs-4 --> **The frontier is steep and sparse.** Across the nine benchmarks, the most expensive model is on the accuracy-cost Pareto frontier in only **1 of 9** cases, and fewer than a third of tested models are frontier-optimal for any given benchmark — the cheapest model tested is on the frontier in 7 of 9, while one prominent reasoning model is on it in 0 of 9 <!-- cite:102 --> [[102]](references.md#ref-102).

<a id="p-143-what-an-agentic-task-actually-costs-5"></a><!-- para:143-what-an-agentic-task-actually-costs-5 --> **A correction worth stating explicitly.** It is tempting to summarize this as "cost is decoupled from accuracy." That is wrong and the same source contradicts it: token usage correlates *positively* with accuracy on 6 of 9 benchmarks, and the cheapest configurations sit at the bottom of the leaderboards. The defensible claim is narrower — **price is a poor predictor at the top of the range**, where the frontier is sparse and the most expensive option is usually not optimal.

<a id="p-143-what-an-agentic-task-actually-costs-6"></a><!-- para:143-what-an-agentic-task-actually-costs-6 --> **Dollars and tokens disagree.** The leaderboard's own analysis notes that ranking by token usage and ranking by dollar cost produce materially different pictures — one model sits on the token-usage frontier in 3 of 8 benchmarks but the dollar frontier in only 1 of 8 — and that prices move fast enough to invalidate comparisons (one model's price fell 80% after release) <!-- cite:102 --> [[102]](references.md#ref-102). **Every dollar figure above is a 24 September 2025 snapshot.** Token counts are the durable quantity; dollars are a lease on a vendor's current price list.

<a id="p-143-what-an-agentic-task-actually-costs-7"></a><!-- para:143-what-an-agentic-task-actually-costs-7 --> **Scale varies enormously by benchmark.** One benchmark averages about \$13 per full evaluation run; another exceeds \$450, and the leaderboard *declined* to run its most expensive model on it at an estimated \$20,000 <!-- cite:102 --> [[102]](references.md#ref-102). Evaluation cost is now itself a barrier to evaluation, which is part of why independent replication of agentic results is rare (<!-- secxref:12.7 -->[§12.7](agentic-coding-systems.md#sec-12.7)).

<!-- sec:14.4 -->
### <a id="sec-14.4"></a>14.4 How Long Is a Task, and How Long Does It Take?

<a id="p-144-how-long-is-a-task-and-how-long-does-it-take-1"></a><!-- para:144-how-long-is-a-task-and-how-long-does-it-take-1 --> **Task length is now a measured capability axis.** Rather than scoring accuracy on a fixed set, one line of work measures the *length of task* a model completes with 50% reliability, calibrated against human baseliners. On 170 tasks across 12 frontier and 4 near-frontier models with 8 runs per pair, that 50%-reliable horizon has **doubled every 207 days** (95% bootstrapped CI 166–240 days) since 2019, reaching roughly **110 minutes** for the strongest model in the study's early-2025 set, against 2 seconds for GPT-2 <!-- cite:103 --> [[103]](references.md#ref-103).

<a id="p-144-how-long-is-a-task-and-how-long-does-it-take-2"></a><!-- para:144-how-long-is-a-task-and-how-long-does-it-take-2 --> Two qualifications. The 80%-reliability horizon doubles at a similar rate (204 days) but is **four to six times shorter** — the length of task a model can do *reliably* is far below the length it can sometimes do. And the model set is early-2025, so the 110-minute figure is not a statement about the current frontier.

<a id="p-144-how-long-is-a-task-and-how-long-does-it-take-3"></a><!-- para:144-how-long-is-a-task-and-how-long-does-it-take-3 --> **Latency: the evidence does not exist.** The one systematic cost study has timing data and explicitly declines to defend it, because massively parallel evaluation introduces provisioning, network, and server-load variance that swamps the signal, and serial re-runs would take weeks <!-- cite:102 --> [[102]](references.md#ref-102). This survey therefore reports **no wall-clock-per-resolved-task figure** and does not construct one from token counts, which would be a proxy dressed as a measurement. Stating the absence explicitly is the honest option; the parameter is not inapplicable, it is unmeasured.

<!-- sec:14.5 -->
### <a id="sec-14.5"></a>14.5 Latency versus Throughput in Deployment

<a id="p-145-latency-versus-throughput-in-deployment-1"></a><!-- para:145-latency-versus-throughput-in-deployment-1 --> The serving-side levers are covered in <!-- secxref:10 -->[§10](inference-decoding-and-serving.md#sec-10): batching trades per-request latency for aggregate throughput, and prefix caching is the one that matters most for agents, because an agent re-sends a long and mostly-unchanged prompt on every step of its loop. The autocomplete path is latency-bound and favours small models, fill-in-the-middle, and multi-query attention; the agent path is throughput- and cost-bound and favours caching and the largest model whose per-task cost the task justifies.

<a id="p-145-latency-versus-throughput-in-deployment-2"></a><!-- para:145-latency-versus-throughput-in-deployment-2 --> The synthesis for a builder is the first two rows of the table in <!-- secref:14.3 -->[§14.3](#sec-14.3): **measure cost per resolved task, not accuracy**, because at the top of the range they are close to uncorrelated, and the cheaper configuration is often the one on the frontier.
