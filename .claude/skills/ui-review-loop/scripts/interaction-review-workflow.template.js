/* interaction-review-workflow.template.js — Layer-2 review for the markdown
 * viewer's ui-review-loop. Inject interaction-review-input.json (scenarios with
 * absolute shot paths + assertion results) at the SCENARIOS placeholder, then run
 * with the Workflow tool.
 * (The placeholder is a block-comment marker on the `const SCENARIOS =` line below;
 * don't write that marker token in this header — its closing delimiter would end
 * this comment early.)
 * One agent per scenario judges the VISUAL correctness of the resulting states (the
 * behavioral truth is already in the assertions). Returns { reviews, synthesis }. */
export const meta = {
  name: 'ui-interaction-review',
  description: 'Vision review of viewer interaction states (open palette/sheet/peek/split/drawer) + assertion corroboration',
  phases: [{ title: 'Review' }, { title: 'Synthesize' }],
}

const SCENARIOS = /*__SCENARIOS__*/;

const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'string' },
    interaction_works: { type: 'boolean' },
    visual_verdict: { type: 'string', enum: ['good', 'minor-issues', 'major-issues', 'broken'] },
    notes: { type: 'string' },
    issues: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor', 'nit'] }, description: { type: 'string' } },
        required: ['severity', 'description'],
      },
    },
  },
  required: ['id', 'interaction_works', 'visual_verdict', 'notes', 'issues'],
}

function prompt(s) {
  const shots = s.shots.map((sh) => `- ${sh.label}: ${sh.path}`).join('\n')
  const asserts = s.assertions.map((a) => `- [${a.pass ? 'PASS' : 'FAIL'}] ${a.name} (${a.detail})`).join('\n')
  return `You are reviewing one INTERACTION on a markdown viewer (not a static page). The behavioral truth is
already captured by DOM assertions below — your job is to judge whether the RESULTING VISUAL STATES look
correct and well-designed (the command palette is centered and legible, the settings sheet doesn't clip, the
peek popover is positioned by the cross-ref, the split Pane B reads as a clean second column, the sidenotes
sit in the right whitespace, the drawer is full-height), and to flag any visual/UX problem.

INTERACTION: ${s.label}  (route ${s.route}, ${s.viewport}${s.category === 'changed' ? ', RECENTLY REDESIGNED — scrutinize' : ''})
STEPS: ${s.steps.join(' → ') || '(none)'}
${s.error ? `DRIVER ERROR: ${s.error}` : ''}

DOM ASSERTIONS (already verified in a headless browser — trust these for behavior):
${asserts}

SCREENSHOTS (Read each to see the resulting state):
${shots}

Judge the visual quality of the interaction's resulting states. interaction_works should reflect the
assertions (all pass + states look right = true). Flag concrete visual/UX issues. Return the structured review.`
}

phase('Review')
const reviews = (await parallel(
  SCENARIOS.map((s) => () => agent(prompt(s), { label: `interact:${s.id}`, phase: 'Review', schema: REVIEW_SCHEMA }))
)).filter(Boolean)

phase('Synthesize')
const SYNTH_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    overall_verdict: { type: 'string', enum: ['interactions-solid', 'minor-fixes', 'needs-work', 'broken'] },
    executive_summary: { type: 'string' },
    confirmed_issues: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor', 'nit'] }, area: { type: 'string' }, description: { type: 'string' } },
        required: ['severity', 'area', 'description'],
      },
    },
    redesigned_surfaces_ok: { type: 'string' },
    a11y_notes: { type: 'string' },
  },
  required: ['overall_verdict', 'executive_summary', 'confirmed_issues', 'redesigned_surfaces_ok', 'a11y_notes'],
}
const synthesis = await agent(
  `Consolidate per-interaction reviews of a markdown viewer into a verdict. Pay special attention to the
RECENTLY REDESIGNED surfaces (immersive-toggle, command-palette, settings-sheet, right-pane-segments,
in-situ-peek, split-view, margin-sidenotes) — confirm they work and look right. The most important
assertion-backed checks are: chrome PERSISTS across reload (the FOUC/hydration trap), focus RETURNS after a
dismissed sheet, focus is TRAPPED in the palette, and sidenotes DE-COLLIDE. Any FAILED assertion is a
confirmed bug — fold it in with its root cause. Per-interaction reviews (JSON):
${JSON.stringify(reviews, null, 2)}`,
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA }
)
return { reviews, synthesis }
