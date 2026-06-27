/* review-workflow.template.js — multi-agent vision review for the markdown
 * viewer's ui-review-loop. Before running: inject review-input.json (an array of
 * {doc × state-group} objects with absolute image paths) at the ROUTES placeholder
 * on the `const ROUTES =` line, then run with the Workflow tool. Returns
 * { reviews, synthesis } — save them to <out>/reviews.json + synthesis.json.
 *
 * REMEMBER (see SKILL.md): the panel output is a list of HYPOTHESES. Verify each
 * blocker/major against code/DOM before trusting it — vision has a high false-alarm
 * rate (lazy-KaTeX-below-fold "broken math", contrast estimates vs. token math,
 * by-design dark-mode code blocks, the service-worker stale cache). The captures
 * already carry the verified DOM state (data-chrome/theme/density) per shot — use it. */
export const meta = {
  name: 'ui-review-loop',
  description: 'Vision review of viewer screenshots across the state matrix (chrome × theme × density × width), then synthesize a verdict',
  phases: [
    { title: 'Review', detail: 'one vision agent per doc × state-group' },
    { title: 'Synthesize', detail: 'consolidate into a verdict + prioritized issues' },
  ],
}

const ROUTES = /*__ROUTES__*/;

// Tailor this to the viewer's design intent; the more concrete, the better the review.
const DESIGN_INTENT = `DESIGN INTENT (judge the screenshots against this):
- A focused, typographic markdown READER. Generous measure, comfortable line-height, restrained chrome.
- Three chrome modes: docs (docked shell + left sidebar + right context pane at wide width),
  reader (immersive, off-canvas drawer), focus (immersive, minimal chrome). data-chrome reflects which.
- Themes light / sepia / dark are all first-class and must be legible (WCAG-AA body text), with
  accents and borders preserved. Code blocks may KEEP their own palette in dark mode — that is by design.
- Math (KaTeX), tables, and code are core content. They must not overflow horizontally or clip.
- Mobile (390px) is first-class: single column, bottom toolbar, no horizontal overflow.
- Wide-desktop layouts: the right context pane (≥1400px docs), split Pane B (≥1440px), and margin
  sidenotes (≥1400px reader) must sit beside the prose without overlapping it or each other.
- Density presets (compact/spacious) tune CHROME line-height only — the prose measure must look the same.
- Be a critical reviewer, not a cheerleader: flag overflow, clipping, contrast failures, broken math,
  cramped mobile, sidenote collisions, misaligned panes, empty states.
- BUT your findings are HYPOTHESES to be verified later — describe precisely what you SEE and where, so
  it can be checked against code/DOM. Do not assert root causes you cannot see. In particular: blank math
  on a tall full-page shot is very likely a lazy-render-below-fold artifact, NOT a real break — say so.`

const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    key: { type: 'string' },
    verdict: { type: 'string', enum: ['excellent', 'good', 'minor-issues', 'major-issues', 'broken'] },
    one_line: { type: 'string' },
    per_state_notes: { type: 'string' },
    highlights: { type: 'array', items: { type: 'string' } },
    issues: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          severity: { type: 'string', enum: ['blocker', 'major', 'minor', 'nit'] },
          state: { type: 'string' },
          description: { type: 'string' },
        },
        required: ['severity', 'state', 'description'],
      },
    },
    legible: { type: 'boolean' },
  },
  required: ['key', 'verdict', 'one_line', 'per_state_notes', 'highlights', 'issues', 'legible'],
}

function reviewPrompt(r) {
  const imgs = r.shots.map((s) => {
    const dom = s.dom ? ` [DOM: chrome=${s.dom.chrome} theme=${s.dom.theme || 'light'} density=${s.dom.density || 'normal'}${s.dom.splitOpen ? ' split-open' : ''}${s.dom.sidenoteBand ? ' sidenotes' : ''}]` : ''
    const bad = (s.seedFails && s.seedFails.length) ? `  ⚠️SEED-MISMATCH: ${s.seedFails.join(', ')}` : ''
    const err = s.error ? `  ⚠️CAPTURE-ERROR: ${s.error}` : ''
    return `- ${s.stateId}${dom}: ${s.img}${bad}${err}`
  }).join('\n')
  return `You are a critical UI/UX reviewer examining ONE document in ONE state group of a markdown viewer.

${DESIGN_INTENT}

DOCUMENT: ${r.doc}  (${r.bytes} bytes)
STATE GROUP: ${r.group} — ${r.groupBlurb}

Use the Read tool to OPEN AND LOOK AT each screenshot (PNGs on disk; Read renders them). Each line lists
the state id, the VERIFIED DOM state (already read off the captured page — trust it for what mode/theme is
active), and the file path:
${imgs}

Compare the states in this group against each other and against the design intent. Be specific and concrete
about what you SEE and WHERE ("the right context pane overlaps the last 30px of the prose column in
three-zone-docs"), not generic praise. If a state looks broken/empty, say so — but if blank math sits at the
BOTTOM of a full-page shot, treat it as a likely lazy-render artifact (note it, don't call it a blocker).
A ⚠️SEED-MISMATCH means the page did not boot into the intended state — that itself is a finding. Return the
structured review.`
}

phase('Review')
const reviews = (await parallel(
  ROUTES.map((r) => () => agent(reviewPrompt(r), { label: `review:${r.key}`, phase: 'Review', schema: REVIEW_SCHEMA }))
)).filter(Boolean)

phase('Synthesize')
const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    overall_verdict: { type: 'string', enum: ['ship-it', 'ship-with-minor-fixes', 'needs-work', 'not-ready'] },
    executive_summary: { type: 'string' },
    top_strengths: { type: 'array', items: { type: 'string' } },
    prioritized_issues: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          severity: { type: 'string', enum: ['blocker', 'major', 'minor', 'nit'] },
          area: { type: 'string' },
          description: { type: 'string' },
          affected_states: { type: 'array', items: { type: 'string' } },
        },
        required: ['severity', 'area', 'description', 'affected_states'],
      },
    },
    dark_mode_assessment: { type: 'string' },
    mobile_assessment: { type: 'string' },
    wide_layout_assessment: { type: 'string' },
    consistency_assessment: { type: 'string' },
    merge_recommendation: { type: 'string' },
  },
  required: ['overall_verdict', 'executive_summary', 'top_strengths', 'prioritized_issues', 'dark_mode_assessment', 'mobile_assessment', 'wide_layout_assessment', 'consistency_assessment', 'merge_recommendation'],
}

const synthesis = await agent(
  `You are the lead reviewer consolidating per-(doc × state-group) reviews of a markdown viewer UI into one verdict.

Per-group reviews (JSON):
${JSON.stringify(reviews, null, 2)}

Produce: overall_verdict + a tight executive_summary; top_strengths (concrete); prioritized_issues
(DEDUPLICATE recurring issues into cross-cutting items — e.g. a contrast problem that recurs across docs is
ONE issue naming the affected states; sort blocker→major→minor→nit; be honest about severity); separate
dark_mode / mobile / wide_layout (right-pane, split, sidenotes) / consistency assessments; and a
merge_recommendation naming any must-fix items. Note: downstream these will be VERIFIED against code/DOM —
flag where you are inferring vs. directly observing, and DEMOTE anything that looks like a lazy-render-below-fold
math artifact.`,
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA }
)

return { reviews, synthesis }
