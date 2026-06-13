export const meta = {
  name: 'llms-for-coding-citation-audit',
  description: 'Adversarially verify load-bearing numeric/claim citations in the LLMs-for-code survey against acquired source PDFs',
  phases: [{ title: 'Verify', detail: 'one verifier per source PDF, targeted locus reads' }],
}

// Each entry: a source PDF + the exact load-bearing claims the survey attributes to it.
const SOURCES = [
  { ref: 1, file: 'chen-codex-evaluating-llms-code-2021.pdf', claims: [
    'Codex-12B solves 28.8% pass@1 on HumanEval; GPT-3 0%, GPT-J 11.4%',
    'with 100 samples per problem, some sample passes for 70.2% of problems',
    'HumanEval has 164 hand-written problems, average 7.7 unit tests per problem',
    'pass@k unbiased estimator draws n>=k samples; the paper uses n=200, k<=100',
    'training data: 54M GitHub repos, 179GB unique Python files <1MB, filtered to 159GB',
    'untrusted generated code is executed in a gVisor sandbox container' ] },
  { ref: 3, file: 'codegen-2022.pdf', claims: [
    'CodeGen-Mono-16.1B reaches 29.28% HumanEval pass@1',
    'model family sizes are 350M, 2.7B, 6.1B, 16.1B',
    'extends GPT-2 BPE vocab with special tokens for repeated tabs/whitespace' ] },
  { ref: 4, file: 'incoder-2022.pdf', claims: [
    'InCoder-6.7B reaches 15.2% HumanEval pass@1',
    'model sizes are 6.7B and 1.3B',
    'byte-level BPE allowing cross-whitespace merges reduces tokens to encode corpus by 45% vs GPT-2 tokenizer' ] },
  { ref: 5, file: 'fim-bavarian-2022.pdf', claims: [
    'a 50% FIM rate leaves the left-to-right loss unchanged (FIM-for-free)',
    'PSM order concatenates sentinels as <PRE> prefix <SUF> suffix <MID> middle',
    'spans are split at character level; joint PSM+SPM training is best' ] },
  { ref: 6, file: 'code-llama-2023.pdf', claims: [
    'Code Llama-Python-70B reaches 57.3% HumanEval pass@1; Instruct-70B 67.8%',
    'foundation Code Llama 7B/13B/34B/70B HumanEval = 33.5/36.0/48.8/53.0',
    'GPT-4 is listed at 67.0% HumanEval in the same Table 2',
    'trained on 16k-token sequences; long-context extension to 100k tokens',
    'FIM applied with probability 0.9, half PSM and half SPM' ] },
  { ref: 7, file: 'the-stack-2022.pdf', claims: [
    'The Stack is 3.1TB permissively licensed code in 30 languages; all-license >29TB; ~10% kept after permissive filter',
    'near-dedup uses MinHash with 256 permutations + LSH at Jaccard 0.85; 38.6% of permissive files are near-duplicates removed',
    'HTML, JavaScript, Java, and C together exceed 50% of the permissive dataset' ] },
  { ref: 8, file: 'starcoder-2023.pdf', claims: [
    'StarCoderBase trained on 1T tokens; 8k context; uses FIM and Multi-Query Attention',
    'StarCoder fine-tuned StarCoderBase on 35B Python tokens' ] },
  { ref: 9, file: 'starcoder2-2024.pdf', claims: [
    'The Stack v2 raw dataset is 67.5TB, 619 languages, 900B+ unique tokens (4x first StarCoder)',
    'StarCoder2-15B trains on 913B+ unique tokens',
    'vocabulary is 49,152; raising it to 100k did not improve performance',
    'dedup uses 5-grams at Jaccard 0.7; files arranged in random order within a repository; 4k base extended to 16k' ] },
  { ref: 10, file: 'deepseek-coder-2024.pdf', claims: [
    'trained on 2T tokens across 87 languages, 16k context, FIM rate 0.5 PSM at document level',
    'repository concatenation uses a topological sort over a file dependency graph',
    'data mixture is 87% source code, 10% English code-related NL, 3% other NL',
    'vocabulary is 32,000' ] },
  { ref: 11, file: 'qwen25-coder-2024.pdf', claims: [
    'three-stage pipeline: file-level pretrain ~5.2T tokens, repo-level ~300B tokens (128k via YARN), then SFT + DPO',
    'code:text:math mixture ablation finds 70:20:10 best; final dataset 5.2T tokens',
    'vocabulary is 151,646; DPO preferences come from a code sandbox' ] },
  { ref: 12, file: 'phi1-2023.pdf', claims: [
    'phi-1 is 1.3B params, trained 4 days on 8 A100s, ~6B textbook-quality tokens + <1B synthetic GPT-3.5 tokens',
    'phi-1 reaches 50.6% HumanEval and 55.5% MBPP pass@1',
    'a 350M sibling reaches 45% HumanEval',
    'thesis: improving data quality can dramatically change the shape of the scaling laws' ] },
  { ref: 16, file: 'wizardcoder-2023.pdf', claims: [
    'WizardCoder-15B reaches 57.3 HumanEval / 51.8 MBPP; base StarCoder-15B is 33.6 HumanEval',
    'WizardCoder built on Code Llama-34B reaches 71.5 HumanEval / 61.2 MBPP' ] },
  { ref: 17, file: 'magicoder-2023.pdf', claims: [
    'OSS-Instruct uses 80K seed code snippets to generate 75K instruction-response pairs',
    'Code Llama-Python-7B 48.2 -> Magicoder-CL 60.4 -> MagicoderS-CL 70.7 HumanEval pass@1',
    'MagicoderS-DS reaches 76.8 HumanEval on DeepSeek-Coder-Base-6.7B' ] },
  { ref: 19, file: 'coderl-2022.pdf', claims: [
    'CodeRL reward: -1.0 compile error, -0.6 runtime error, -0.3 failed a unit test, +1.0 passed all unit tests',
    'critic predicts one of four outcomes: compile error, runtime error, failed test, passed test',
    'CodeRL rises from ~2% pass@1 to ~20% pass@1000 on APPS' ] },
  { ref: 20, file: 'rlef-2024.pdf', claims: [
    'RLEF 70B: validation improves 37.5 to 40.4, test reaches 41.2 (vs 38.0 with feedback limited to public tests)',
    'new state-of-the-art at both 8B and 70B while reducing samples by an order of magnitude' ] },
  { ref: 23, file: 'self-debugging-2023.pdf', claims: [
    'self-debugging improves Spider by 2-3% overall and up to 9% on hardest problems',
    'on TransCoder and MBPP (with unit tests) it improves accuracy by up to 12%' ] },
  { ref: 24, file: 'reflexion-2023.pdf', claims: [
    'Reflexion reaches 91.0% HumanEval pass@1 vs GPT-4 at 80.1%',
    'architecture is Actor, Evaluator, and Self-Reflection with episodic memory; no weight updates' ] },
  { ref: 25, file: 'deepseek-r1-2025.pdf', claims: [
    'R1-Zero uses GRPO with rule-based accuracy and format rewards, no neural reward model, no SFT cold-start',
    'R1-Zero AIME 2024 rises from 15.6% to 77.9% pass@1; 86.7% with self-consistency cons@16',
    'final DeepSeek-R1: Codeforces 96.3 percentile / 2029 rating; LiveCodeBench 65.9; SWE-bench Verified 49.2' ] },
  { ref: 26, file: 'openai-competitive-programming-2025.pdf', claims: [
    'Codeforces ratings: gpt-4o 808 (11th percentile), o1 1673 (89th), o3 2724 (99.8th)',
    'o3 achieves IOI 2024 gold without hand-crafted test-time strategies; the specialized o1-ioi reached rating 1807' ] },
  { ref: 28, file: 'picard-2021.pdf', claims: [
    'without PICARD ~12% of generated SQL fails with an execution error; with PICARD only ~2% are unusable',
    'PICARD lifts T5-3B to 75.5% exact-set-match dev and 79.3% execution accuracy dev on Spider' ] },
  { ref: 30, file: 'repocoder-2023.pdf', claims: [
    'RepoCoder improves an in-file baseline by over 10% exact match and over 8% edit similarity',
    'it uses an iterative retrieve-generate loop augmenting the query with the previous draft; a sparse Jaccard retriever performs on par with a dense one' ] },
  { ref: 31, file: 'react-2022.pdf', claims: [
    'ReAct beats baselines by 34% absolute on ALFWorld and 10% absolute on WebShop' ] },
  { ref: 32, file: 'swe-agent-2024.pdf', claims: [
    'with GPT-4 Turbo, SWE-agent resolves 12.5% of full SWE-bench and 18.0% of SWE-bench Lite; Claude 3 Opus 10.5%; prior RAG system 3.8%',
    'ablation: replacing the custom editor with the raw shell drops Lite from 18.0% to 10.3%; custom ACI solves 10.7 points more (64% relative)' ] },
  { ref: 33, file: 'autocoderover-2024.pdf', claims: [
    'AutoCodeRover resolves 19% of SWE-bench Lite (57 issues) using GPT-4, with AST-based search and spectrum-based fault localization' ] },
  { ref: 34, file: 'openhands-2024.pdf', claims: [
    'OpenHands CodeActAgent reports a 26% SWE-bench Lite resolve rate with Claude 3.5 Sonnet' ] },
  { ref: 35, file: 'mbpp-austin-2021.pdf', claims: [
    'MBPP has 974 problems with 3 test cases each, plus a 426-problem hand-verified subset',
    'the largest model solves about 59.6% of MBPP in the few-shot setting' ] },
  { ref: 36, file: 'evalplus-2023.pdf', claims: [
    'EvalPlus augments HumanEval tests roughly 80x to build HumanEval+ (same 164 problems)',
    'pass@k drops by up to 19.3% at pass@1 and up to 28.9% at pass@100' ] },
  { ref: 37, file: 'bigcodebench-2024.pdf', claims: [
    'BigCodeBench has 1,140 tasks using 139 libraries across 7 domains, ~5.6 tests/task at 99% average branch coverage',
    'best model GPT-4o reaches about 60% vs 97% human performance' ] },
  { ref: 38, file: 'swe-bench-2023.pdf', claims: [
    'SWE-bench has 2,294 task instances from 12 Python repositories; best model (Claude 2) resolved 1.96%',
    'gold patches average 32.8 edited lines across 1.7 files; mean 3,010 non-test files per instance',
    'SWE-bench Lite is 300 instances' ] },
  { ref: 40, file: 'alphacode-2022.pdf', claims: [
    'AlphaCode reached an average ranking in the top 54.3% of Codeforces participants',
    'CodeContests reduces false-positive rate from 30-60% to about 4% via mutation-generated tests' ] },
  { ref: 41, file: 'asleep-at-keyboard-2021.pdf', claims: [
    '89 scenarios produced 1,689 programs; approximately 40% were vulnerable; 39.33% of top-ranked suggestions' ] },
  { ref: 42, file: 'he-vechev-sven-secure-code-2023.pdf', claims: [
    'on a 2.7B CodeGen model with 59.1% baseline secure rate, SVEN hardening raises it to 92.3% and adversarial mode degrades it to 36.8%; covers 9 CWEs',
    'SVEN uses prefix-tuning (property-specific continuous vectors) with frozen LM weights' ] },
  { ref: 43, file: 'deepseek-coder-v2-2024.pdf', claims: [
    'DeepSeek-Coder-V2 is 236B total / 21B active MoE, with a 16B total / 2.4B active Lite variant; 338 languages; 128k context',
    'reports SWE-bench 12.7 and LiveCodeBench 43.4' ] },
]

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    ref: { type: 'number' },
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          claim: { type: 'string' },
          verdict: { type: 'string', enum: ['correct', 'wrong-value', 'wrong-source', 'fabricated', 'unverifiable'] },
          source_value: { type: 'string', description: 'the actual value/text found in the source for this claim' },
          locator: { type: 'string', description: 'where in the PDF it was found (section/page/figure/table)' },
        },
        required: ['claim', 'verdict', 'source_value', 'locator'],
      },
    },
  },
  required: ['ref', 'verdicts'],
}

phase('Verify')

function prompt(s) {
  return `You are a CITATION-AUDIT verifier. Be adversarial: your job is to CATCH drift, not confirm.

SOURCE: download/${s.file}  (this is reference [${s.ref}] in the survey).

The survey "LLMs for Code" attributes the following claims to this source. For EACH claim, verify it against the ACTUAL text of the PDF.

CLAIMS:
${s.claims.map((c, i) => `${i + 1}. ${c}`).join('\n')}

METHOD (locus-targeted — do NOT read the whole PDF):
- Extract text with: pdftotext download/${s.file} - | grep -n -iE 'PATTERN' (try the specific number, e.g. '28.8|70.2|164', and key terms). Or use python+pymupdf (fitz) to pull a page range / search. Read only a tight window around each hit.
- For every cited NUMBER, find it in the source and reproduce the exact value you see. If the survey's number differs from the source, that is wrong-value.
- If the claim is attributed to the wrong work, wrong-source. If it does not exist in the source at all, fabricated. If the PDF is unreadable/unobtainable, unverifiable (NOT a source finding).

For each claim return: verdict (correct | wrong-value | wrong-source | fabricated | unverifiable), the source_value you actually found (the real number/text), and a locator (section/page/table/figure). Default to flagging if a number does not match exactly. Return only the structured object.`
}

const results = await parallel(SOURCES.map(s => () =>
  agent(prompt(s), { schema: SCHEMA, phase: 'Verify', label: `verify:ref-${s.ref}` })
    .then(r => r ? { ...r, file: s.file } : { ref: s.ref, file: s.file, verdicts: [], dead: true })
))

const clean = results.filter(Boolean)
const flagged = []
let total = 0, correct = 0
for (const r of clean) {
  for (const v of (r.verdicts || [])) {
    total++
    if (v.verdict === 'correct') correct++
    else flagged.push({ ref: r.ref, file: r.file, ...v })
  }
}
const dead = clean.filter(r => r.dead).map(r => r.ref)

log(`audited ${total} claims across ${clean.length} sources; ${correct} correct, ${flagged.length} flagged, dead agents: ${dead.length}`)

return { total_claims: total, correct, flagged_count: flagged.length, dead_agents: dead, flagged, all: clean }
