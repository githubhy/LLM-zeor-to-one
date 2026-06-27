export const meta = {
  name: 'cap-decompose',
  description: 'Step-level in/out-of-box decomposition of a codebase module, verified against source',
  phases: [
    { title: 'Decompose', detail: 'one agent per subtree fills the procedure→step leaf tree' },
    { title: 'Verify', detail: 'adversarially confirm each present/absent claim against path:line' },
  ],
}

const LEAF_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['unit', 'summary', 'classes', 'moduleLevelAbsent'],
  properties: {
    unit: { type: 'string' },
    summary: { type: 'string' },
    classes: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['name', 'file', 'role', 'procedures', 'classLevelAbsent'],
        properties: {
          name: { type: 'string' },
          file: { type: 'string', description: 'path:lineOfClassDef' },
          role: { type: 'string' },
          procedures: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false,
              required: ['name', 'steps'],
              properties: {
                name: { type: 'string' },
                steps: {
                  type: 'array',
                  description: 'EXHAUSTIVE ordered named operations; a step is the finest unit that could be present/absent/variant — NOT arithmetic primitives.',
                  items: {
                    type: 'object', additionalProperties: false,
                    required: ['step', 'status', 'detail', 'evidence'],
                    properties: {
                      step: { type: 'string' },
                      status: { type: 'string', enum: ['present', 'partial', 'absent'] },
                      detail: { type: 'string' },
                      evidence: { type: 'string', description: 'path:line — required for present/partial' },
                      why: { type: 'string', description: 'for partial/absent: why not (fully) implemented' },
                    },
                  },
                },
              },
            },
          },
          classLevelAbsent: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['what', 'why'], properties: { what: { type: 'string' }, why: { type: 'string' }, evidence: { type: 'string' } } } },
        },
      },
    },
    moduleLevelAbsent: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['what', 'why'], properties: { what: { type: 'string' }, why: { type: 'string' }, evidence: { type: 'string' } } } },
  },
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['checked', 'corrections', 'verdict'],
  properties: {
    checked: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['claim', 'status', 'note'], properties: { claim: { type: 'string' }, status: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] }, note: { type: 'string' } } } },
    corrections: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string' },
  },
}

const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const root = A.root
const moduleName = A.module
const DISC = ` You are decomposing the **${A.module}** module into an EXHAUSTIVE step-level in/out-of-the-box tree. `
  + `For each public class list every PROCEDURE (algorithm it runs) and break it into ordered STEPS — the finest named operation that could independently be present/absent/variant (e.g. for an HTTP client's request: build the URL, merge headers, apply auth, open the connection, stream the body, read the response, follow redirects), NOT arithmetic primitives. `
  + `Set status present/partial/absent, the variant/extent detail, and evidence as path:line (OPEN the file, cite the real function/symbol line). `
  + `Be RUTHLESS about what is NOT in the box (missing algorithms/variants/standard features, unsupported shapes/params, approximations, hardcoded choices) — capture as 'absent' steps, classLevelAbsent, or moduleLevelAbsent, each with WHY (cite asserts/docstrings/NotImplementedError). Read the actual source; cite real line numbers.`

phase('Decompose')
const out = await pipeline(
  A.units,
  (u) => agent(`Decompose the **${u.key}** subtree of ${moduleName} at ${root}.\n${u.prompt}\n${DISC}`,
    { label: `decompose:${u.key}`, phase: 'Decompose', schema: LEAF_SCHEMA, effort: 'high' }),
  (res, u) => {
    if (!res) return null
    const vp = `ADVERSARIALLY verify this step-level decomposition of ${moduleName} subtree "${u.key}".\n${JSON.stringify(res)}\n\n`
      + `Pick the ~6 highest-stakes leaves — every 'absent'/'partial' status and every surprising 'present' variant — and OPEN the cited path:line under ${root} to confirm or refute against the real code. `
      + `Default to refuted/uncertain if the line doesn't support the claim. Flag any MISSED step, wrong status, or wrong line. Give a trustworthiness verdict.`
    return agent(vp, { label: `verify:${u.key}`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'high' })
      .then((v) => ({ unit: u.key, data: res, verification: v }))
  },
)

return { units: out.filter(Boolean) }
