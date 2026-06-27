// Template — Phase 5b end-to-end A/B: drive the FULL target skill original vs proposed on a
// real scoped task, score, TRUST-BUT-VERIFY. Each build agent writes to a WORKTREE or a
// namespaced sandbox and RETURNs a report (gotcha #2). Re-run any gate yourself after (gotcha #3).
export const meta = {
  name: '<target>-e2e-ab',
  description: 'End-to-end A/B of the <target> skill (original vs proposed) on a scoped task',
  phases: [{title:'Build'},{title:'Judge'}],
}
const REPO = '<repo-abs-path>';
const TASK = "<a small, fast, well-specified task the target skill can complete in seconds>";
const SANDBOX = (arm)=>`${REPO}/bench/<target>/runs/<date>-e2e/${arm}`; // namespaced; or use isolation:'worktree'
const BUILD = {type:'object', properties:{arm:{type:'string'}, mode:{type:'string'}, ran:{type:'boolean'},
  produced:{type:'array', items:{type:'string'}}, gate_result:{type:'string'}, notes:{type:'string'}}, required:['arm','mode','ran']};
const prompt = (arm, mode) => `Execute the <target> skill in mode=\`${mode}\` on this scoped task: ${TASK}
Write ONLY inside ${SANDBOX(arm)} (create it). ${mode==='proposed'?'Apply the proposed addenda for your phases.':'Baseline only; read no addenda.'}
Actually RUN the work to produce real artifacts; then run the target skill's gate/validator and report its result.
CRITICAL: confine all writes to your sandbox; do NOT write elsewhere; RETURN the structured report.`;
phase('Build');
const builds = await parallel([
  ()=>agent(prompt('original','original'), {label:'build:original', phase:'Build', agentType:'general-purpose', schema:BUILD}),
  ()=>agent(prompt('proposed','proposed'), {label:'build:proposed', phase:'Build', agentType:'general-purpose', schema:BUILD}),
]);
phase('Judge');
const judge = await agent(`Compare the two produced studies (read both from ${SANDBOX('original')} and ${SANDBOX('proposed')}). Score each on the axes that matter for this skill (0-5 each); note which rigor each has that the other lacks; verdict on whether proposed is more rigorous and WHY. Do NOT write files.`,
  {label:'judge', phase:'Judge', agentType:'general-purpose',
   schema:{type:'object', properties:{original:{type:'object'}, proposed:{type:'object'}, verdict:{type:'string'}}, required:['verdict']}});
// AFTER this returns: the orchestrator re-runs the target validator itself on both arms (trust-but-verify),
// audits for strays outside the sandboxes, and cleans before committing.
return { builds, judge, tokens_spent: budget.spent() };
