export const meta = {
  name: 'drs-skill-ab-end-to-end',
  description: 'End-to-end A/B: run the REAL baseline skill vs the v2 (P1-2+P0-2) skill on one topic, single-blind judge. Credit-free (Workflow budget, no headless CLI).',
  phases: [
    { title: 'Run-skill', detail: 'baseline SKILL.md vs v2 fork, N=3 each, executed end-to-end on the LMS topic' },
    { title: 'Judge', detail: 'single-blind Opus judge scores each survey (scorecard stripped before judging)' },
  ],
}

const COMMON = `You are executing the "deep-research-survey" skill END-TO-END to produce a focused technical mini-survey. Follow ALL phases in order.

SKILL OVERVIEW: Translate the request into a concrete brief, then execute with phased control and a consistent deliverable. Organize fundamentals -> architecture -> method inventory -> tradeoffs -> current practice -> roadmap. Treat omission risk as a quality problem. Say explicitly when a conclusion is inference vs sourced fact.

PHASE 1 SCOPE: Pin down subject, audience, depth, output shape; the output contract is a survey.
PHASE 2 OUTLINE: Build a section outline where every section has a concrete research question (fundamentals; architecture/decomposition; method & variant inventory; governing equations; performance/complexity/cost tradeoffs; SOTA vs practice; open problems).
PHASE 3 EVIDENCE: Collect evidence against the outline; prefer primary sources; every factual claim cites a source. For THIS run, use your own domain knowledge as the evidence base; do NOT call live web search.`

const BASE_45 = `PHASE 4 SYNTHESIS: Write section drafts from the evidence. Distinguish standard practice from SOTA from engineering judgment. For high-stakes surveys, use a UNION merge: generate two or more independent drafts and merge by keeping all unique supported findings. Attribution: sourced facts cited inline; judgment/inferences labeled.
PHASE 5 REPORT: Produce the final deliverable. Short executive summary; traceable claims; end with recommendations, open gaps, next steps; comparison tables where useful.`

const V2_45 = `PHASE 4 SYNTHESIS (memory-guided): Write sections SEQUENTIALLY, not as independent parallel drafts. Maintain a running memory of every symbol/term defined and every equation/result stated. Before writing section k, reuse the established notation and definitions EXACTLY; never redefine a symbol, never restate an equation differently, never contradict a prior section. After each section, update the memory. Order sections by conceptual dependency. Do NOT generate independent drafts and merge them.
PHASE 5 REPORT (with self-evaluation gate): Short executive summary; traceable claims; recommendations and open gaps. MANDATORY SELF-EVALUATION GATE before sign-off: score the draft on Coverage, Structure, Relevance, Synthesis, Critical-Analysis (each 1-5) plus a cross-section consistency check; if any dimension is below 4/5, fix the weakest area and re-score; repeat until all >= 4/5. Emit the final scorecard under a "## Self-evaluation scorecard" heading.`

const RUN = `\n\nTOPIC: the least-mean-squares (LMS) adaptive filter.\nProduce a focused ~5-section survey (roughly 700-1000 words) following ALL phases and gates above. Define every symbol you use and include the key equations. Reuse notation consistently across sections. Output ONLY the final survey in markdown.`

const INSTR = { baseline: COMMON + '\n' + BASE_45 + RUN, v2: COMMON + '\n' + V2_45 + RUN }

const JUDGE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['coverage', 'structure', 'relevance', 'synthesis', 'critical_analysis', 'inconsistency_count', 'note'],
  properties: {
    coverage: { type: 'integer', minimum: 1, maximum: 5 }, structure: { type: 'integer', minimum: 1, maximum: 5 },
    relevance: { type: 'integer', minimum: 1, maximum: 5 }, synthesis: { type: 'integer', minimum: 1, maximum: 5 },
    critical_analysis: { type: 'integer', minimum: 1, maximum: 5 },
    inconsistency_count: { type: 'integer', minimum: 0, description: 'concrete cross-section inconsistencies (symbol/definition/equation/claim that disagrees across sections)' },
    note: { type: 'string' },
  },
}

phase('Run-skill')
const jobs = []
for (const arm of ['baseline', 'v2']) for (let r = 1; r <= 3; r++) jobs.push({ arm, r })
const drafts = (await parallel(jobs.map(j => () =>
  agent(INSTR[j.arm], { label: `run:${j.arm}:r${j.r}`, phase: 'Run-skill', model: 'haiku' })
    .then(text => ({ arm: j.arm, r: j.r, text: text || '' }))))).filter(Boolean)
log(`Generated ${drafts.length} surveys (baseline + v2). Judging single-blind.`)

phase('Judge')
const scored = await parallel(drafts.map(d => () => {
  const blind = (d.text || '').replace(/##\s*Self-evaluation scorecard[\s\S]*$/i, '').trim()  // strip the v2 scorecard so the judge can't tell the arm
  return agent(
    `Strict technical reviewer. Score this mini-survey (you are NOT told how it was produced). Rate Coverage, Structure, Relevance, Synthesis, Critical-Analysis (1-5). Then count concrete CROSS-SECTION inconsistencies (same quantity with different symbols/definitions; one symbol meaning two things; an equation/result stated differently across sections; contradictory claims).\n=== SURVEY ===\n${blind}\n=== END ===`,
    { label: `judge:${d.arm}:r${d.r}`, phase: 'Judge', model: 'opus', schema: JUDGE_SCHEMA })
    .then(s => ({ arm: d.arm, r: d.r, score: s, has_scorecard: /##\s*Self-evaluation scorecard/i.test(d.text), chars: d.text.length }))
}))

return { scored: scored.filter(Boolean) }
