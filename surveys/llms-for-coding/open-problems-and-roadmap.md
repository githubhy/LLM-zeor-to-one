## 18 Open Problems and Roadmap

<a id="p-18-open-problems-and-roadmap-1"></a><!-- para:18-open-problems-and-roadmap-1 --> The field has gone from autocompleting a line to resolving a real issue in five years, but the frontier is defined by what remains hard. The challenges below are drawn from the recent surveys' explicit future-directions analyses <!-- cite:44 --> [[44]](references.md#ref-44), <!-- cite:45 --> [[45]](references.md#ref-45) and from the gaps surfaced throughout this document.

<!-- sec:18.1 -->
### <a id="sec-18.1"></a>18.1 Repository- and Software-Scale Reliability

<a id="p-181-repository-and-software-scale-reliability-1"></a><!-- para:181-repository-and-software-scale-reliability-1 --> The clearest open problem is reliability at software scale. Models excel at self-contained functions but struggle with repository- and project-level tasks, unseen problems, and long dependency chains — the survey by Jiang et al. names this its first challenge and grounds it in the very datapoints this survey uses: AlphaCode's top-54.3% competition ranking <!-- cite:40 --> [[40]](references.md#ref-40) and SWE-bench's finding that the best model at the time resolved only 1.96% of real issues <!-- cite:38 --> [[38]](references.md#ref-38), <!-- cite:44 --> [[44]](references.md#ref-44). Even the late-2025 frontier band near 80% on SWE-bench Verified (Section 15) carries a contamination asterisk, so true repository-scale reliability — robust over long horizons, across many files, on genuinely novel problems — is unsolved. Weak long-horizon reasoning, complex internal and external dependencies, and finite context windows are the named causes <!-- cite:44 --> [[44]](references.md#ref-44).

<!-- sec:18.2 -->
### <a id="sec-18.2"></a>18.2 Evaluation That Keeps Up

<a id="p-182-evaluation-that-keeps-up-1"></a><!-- para:182-evaluation-that-keeps-up-1 --> Evaluation is itself an open problem, not a solved instrument. Function-level benchmarks are saturated and unrepresentative (the survey calls HumanEval out by name <!-- cite:44 --> [[44]](references.md#ref-44)), static benchmarks are contamination-prone (Section 13), and even the realistic ones are noisy (the 68.3% of SWE-bench instances filtered to build Verified, Section 13). The roadmap item is durable, contamination-resistant, adequately-tested, repository-realistic evaluation that tracks capability faster than it saturates — LiveCodeBench's time-windowing (Section 13) is a template, not a final answer <!-- cite:39 --> [[39]](references.md#ref-39), <!-- cite:44 --> [[44]](references.md#ref-44).

<!-- sec:18.3 -->
### <a id="sec-18.3"></a>18.3 Verification, Security, and Trust

<a id="p-183-verification-security-and-trust-1"></a><!-- para:183-verification-security-and-trust-1 --> Because correctness is the point, integrating *formal* verification into the generation pipeline is a recurring roadmap item — using the LLM to propose code and a verifier to certify it, closing the loop that unit tests only approximate <!-- cite:44 --> [[44]](references.md#ref-44). Alongside it sits security alignment (insecure-code generation is steerable but not solved, Section 16) and the agentic attack surface (prompt injection, Section 16), both of which grow more urgent as agents gain autonomy and permissions. Trust — knowing when to rely on a model's output — is the human-facing version of the same problem <!-- cite:45 --> [[45]](references.md#ref-45).

<!-- sec:18.4 -->
### <a id="sec-18.4"></a>18.4 Architecture, Data, and Efficiency

<a id="p-184-architecture-data-and-efficiency-1"></a><!-- para:184-architecture-data-and-efficiency-1 --> Three systems-level directions recur. **Architecture**: code has structure (syntax trees, control/data flow, compiler intermediate representations) that flat token sequences ignore, and architectures tuned to that structure are an open avenue <!-- cite:44 --> [[44]](references.md#ref-44). **Data**: high-quality and synthetic code data remains the dominant lever (Section 6), and the phi-1 result that data quality reshapes the scaling curve <!-- cite:12 --> [[12]](references.md#ref-12) suggests the frontier of data curation is far from exhausted. **Efficiency**: the inference cost of test-time compute (Section 14) and the carbon footprint of large-scale deployment are explicitly flagged sustainability concerns <!-- cite:44 --> [[44]](references.md#ref-44).

<!-- sec:18.5 -->
### <a id="sec-18.5"></a>18.5 The Software-Engineering Frontier

<a id="p-185-the-software-engineering-frontier-1"></a><!-- para:185-the-software-engineering-frontier-1 --> Finally, the survey by Fan et al. frames the open problems from a software-engineering rather than a model-centric view: deployment and maintenance of LLM-based tools, integration into real development workflows, human-AI collaboration, and the trust and reliability practices that production software demands <!-- cite:45 --> [[45]](references.md#ref-45). This is the frontier where the modality's defining property — that code is executable and its correctness verifiable (Section 2) — must be turned from a benchmark advantage into a dependable engineering discipline. The trajectory of this survey suggests the direction: from generating code, to verifying it, to acting on it autonomously and accountably within real software systems.
