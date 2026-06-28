export const meta = {
  name: 'mmllm-evidence',
  description: 'Hardened breadth evidence collection for the multimodal-llms survey (7 Sonnet clusters, file-first ledgers)',
  phases: [
    { title: 'Evidence', detail: '7 evidence-collector clusters, file-first _scratch ledgers' },
    { title: 'Retry', detail: 're-fire dead clusters trimmed (retry<=2)' },
  ],
}

// DRS-HARDEN + citation-integrity preamble shared by every cluster.
const SHARED = `
You are an EVIDENCE COLLECTOR for a multimodal-LLM research survey (learner-register, omni-modal parity).
HARD RULES (DRS-HARDEN, default-on safety net):
- FILE-FIRST DELIVERABLE: your graded output is a markdown ledger file. After EACH question, APPEND your
  findings to that file via Bash heredoc:  cat >> <LEDGER> <<'EOF' ... EOF  (write incrementally — a
  step-capped death must still leave evidence on disk). Your chat return is a 2-line confirmation ONLY.
- NO Glob / no filesystem exploration. Use ONLY the EXACT local PDF paths given below (read them with:
  python3 -c "import fitz; d=fitz.open('PATH'); print(d[i].get_text())"  for specific pages, or grep the
  extracted text). Do NOT read entire large PDFs page-by-page.
- WebSearch is preferred for breadth/numbers; cap full-page WebFetch at <= 2 total.
- CITATION INTEGRITY: never invent a citation, number, or result. Every value (benchmark score, param
  count, objective) must come from a source you actually read; record source + arXiv-id/URL + the exact
  number. If you cannot verify a value, write "UNVERIFIED" — do not guess. Prefer primary sources
  (papers, official model cards) over blogs.
LEDGER ROW FORMAT (markdown), one per finding:
  ### <claim/topic>
  - **value/result**: <exact number or statement>
  - **condition**: <benchmark/split/shots/scale if a metric>
  - **source**: <author-year + arXiv-id or URL> · **tier**: A/B/C · **confidence**: high/med/low
Stop when the questions are answered (aim <= ~6 searches; you have headroom but do not over-search).`

const CLUSTERS = [
  {
    id: 'E1', ledger: 'surveys/multimodal-llms/_scratch/evidence-E1.md',
    title: 'Benchmark & evaluation landscape',
    local: ['download/yue-mmmu-2023.pdf', 'download/li-pope-2023.pdf'],
    qs: `1) MMMU (local yue-mmmu-2023.pdf): what does it measure, how many disciplines/questions, split sizes,
metric, and the human-vs-model gap reported. 2) POPE (local li-pope-2023.pdf): the object-hallucination
probing method (random/popular/adversarial), the metric, and what it revealed. 3) Web: for each of MMBench,
MME, MMStar, DocVQA, ChartQA, TextVQA, AI2D, MathVista, RealWorldQA — one line on what it measures + its
metric + test-set size. 4) Web: the main MLLM-eval pitfalls (contamination, single-image bias, prompt
sensitivity, LLM-judge bias) with a source each.`,
  },
  {
    id: 'E2', ledger: 'surveys/multimodal-llms/_scratch/evidence-E2.md',
    title: 'Quantitative SOTA — open-weight models',
    local: ['download/bai-qwen2.5-vl-2025.pdf','download/wang-qwen2-vl-2024.pdf','download/chen-internvl-2023.pdf','download/deitke-molmo-2024.pdf','download/agrawal-pixtral-2024.pdf','download/dai-nvlm-2024.pdf','download/lu-deepseek-vl-2024.pdf','download/liu-llava-1.5-2023.pdf'],
    qs: `From the local model-card PDFs' RESULT TABLES (and web only to fill gaps), collect MMMU(val),
DocVQA, MathVista, MMBench, and (if present) ChartQA/AI2D scores for: 1) Qwen2.5-VL (72B/7B) and Qwen2-VL;
2) InternVL (and InternVL2/2.5 if findable), Molmo, Pixtral-12B; 3) NVLM, DeepSeek-VL, LLaVA-1.5. Record the
exact number + the benchmark/split + the model scale for each. 4) Note which model claims SOTA on which
benchmark and at what size.`,
  },
  {
    id: 'E3', ledger: 'surveys/multimodal-llms/_scratch/evidence-E3.md',
    title: 'Quantitative SOTA — closed frontier + deployment gap',
    local: [],
    qs: `Web only (these are closed models; tier B/C, weak source tags). 1) GPT-4o and GPT-4V: MMMU, DocVQA,
MathVista numbers from the OpenAI reports/cards (with date). 2) Gemini (1.5 Pro / 2.0) and Claude 3.5 Sonnet
(vision): the same benchmarks where reported. 3) The published-vs-deployed deployment-gap thesis: why
open-weight early-fusion LLaVA-style models dominate practitioner deployment even when a closed model scores
higher — cite the reasoning. Mark every number tier B/C and record the report URL + date; do NOT present any
closed-model number as load-bearing.`,
  },
  {
    id: 'E4', ledger: 'surveys/multimodal-llms/_scratch/evidence-E4.md',
    title: 'Inference & serving — vision-token cost & compression',
    local: ['download/li-blip2-2023.pdf','download/alayrac-flamingo-2022.pdf'],
    qs: `1) The vision-token cost problem: how many tokens a high-res image becomes under common patch
settings (e.g. LLaVA-NeXT AnyRes, Qwen2-VL native res) — web + reasoning. 2) Token-compression / pruning
methods: FastV, LLaVA-PruMerge, ToMe (token merging), and the perceiver-resampler/Q-Former-as-compressor
idea (local blip2/flamingo) — mechanism + reported token-reduction and speedup for each (web). 3) KV-cache /
prefill implications specific to long image+video token sequences (web). Record exact reduction factors and
sources.`,
  },
  {
    id: 'E5', ledger: 'surveys/multimodal-llms/_scratch/evidence-E5.md',
    title: 'Audio / video / omni breadth',
    local: ['download/radford-whisper-2022.pdf','download/chu-qwen-audio-2023.pdf','download/tang-salmonn-2024.pdf','download/rubenstein-audiopalm-2023.pdf','download/lin-video-llava-2023.pdf'],
    qs: `1) Audio encoder front-end: Whisper's mel-spectrogram + encoder (local whisper) and how Qwen-Audio /
SALMONN connect audio to an LLM (SALMONN: window-level Q-Former + LoRA; local). 2) AudioPaLM's
discrete-audio-token approach (local). 3) Video LLMs: frame-sampling + temporal modeling strategies
(Video-LLaVA local + web for the general pattern). 4) Omni / real-time: GPT-4o-style interleaved any-to-any
and full-duplex / streaming speech — what is publicly known (web, tier B/C). Record mechanisms + any numbers
with sources.`,
  },
  {
    id: 'E6', ledger: 'surveys/multimodal-llms/_scratch/evidence-E6.md',
    title: 'Training data & multimodal alignment',
    local: ['download/liu-llava-2023.pdf','download/liu-llava-1.5-2023.pdf'],
    qs: `1) The LLaVA visual-instruction-tuning recipe (local): two-stage (feature-align pretrain then
instruction finetune), the GPT-4-generated instruction data, data volumes. 2) Pretraining data sources for
VLMs: LAION, COYO, MMC4 interleaved, ShareGPT4V — what each is (web). 3) Multimodal alignment / hallucination
mitigation: RLHF-V, RLAIF-V, POVID, mDPO — one line each on the method + claimed effect (web). Record sources
and any quantitative hallucination-reduction numbers.`,
  },
  {
    id: 'E7', ledger: 'surveys/multimodal-llms/_scratch/evidence-E7.md',
    title: 'Catalog-tier models & connector breadth',
    local: ['download/laurencon-idefics2-2024.pdf','download/beyer-paligemma-2024.pdf'],
    qs: `Web (+ local idefics2/paligemma) — for each, ONE line: core idea + the single distinguishing
mechanism + entry-point/fusion/connector type. 1) Fuyu-8B (decoder-only, raw patch tokens, no encoder) and
LLaVA-NeXT (AnyRes tiling). 2) CogVLM (visual expert), MiniGPT-4, mPLUG-Owl. 3) Idefics/Idefics2 (local),
PaliGemma (local), DeepSeek-VL2. 4) Video-LLaMA and one or two video models. These become catalog-tier cards,
so a crisp one-liner + the distinguishing mechanism + a source is enough.`,
  },
]

phase('Evidence')
async function runCluster(c, trimmed) {
  const note = trimmed ? ' (RETRY-TRIMMED: answer only the FIRST 2 questions; stay under 4 searches.)' : ''
  const localList = c.local.length ? `EXACT local source PDFs (use ONLY these, no Glob):\n${c.local.map(p=>'  '+p).join('\n')}` : 'No local PDFs for this cluster — web sources only.'
  const prompt = `${SHARED}\n\nCLUSTER ${c.id} — ${c.title}.\nLEDGER FILE (create + append after each question): ${c.ledger}\n${localList}\n\nQUESTIONS:\n${c.qs}${note}\n\nFirst run: echo a one-line header into the ledger ( cat > ${c.ledger} <<'EOF' ... EOF ), then answer each question and APPEND. Finish with a 2-line confirmation of how many findings you wrote.`
  return agent(prompt, { label: `ev:${c.id}`, phase: trimmed ? 'Retry' : 'Evidence', agentType: 'evidence-collector', model: 'sonnet' })
}

const first = await parallel(CLUSTERS.map((c) => () => runCluster(c, false).then((r) => ({ c, r }))))

// Empty-return-as-death: a step-capped agent completes with empty text.
const dead = first.filter((x) => !x || !x.r || String(x.r).trim() === '').map((x, i) => x ? x.c : CLUSTERS[i])
const deadClusters = first.map((x, i) => (!x || !x.r || String(x.r).trim() === '') ? CLUSTERS[i] : null).filter(Boolean)

let retried = []
if (deadClusters.length) {
  log(`${deadClusters.length} dead cluster(s) — retrying trimmed: ${deadClusters.map(c=>c.id).join(', ')}`)
  phase('Retry')
  retried = await parallel(deadClusters.map((c) => () => runCluster(c, true).then((r) => ({ c, r }))))
}

const alive = first.filter((x) => x && x.r && String(x.r).trim() !== '').map((x) => x.c.id)
const recovered = retried.filter((x) => x && x.r && String(x.r).trim() !== '').map((x) => x.c.id)
return { alive, recovered, still_dead: deadClusters.map(c=>c.id).filter(id => !recovered.includes(id)) }
