// Template — Phase 2 competitive-landscape scan (parameterize FAMILIES + the skill summary).
// One live-web evidence agent per family, pipelined into adversarial verify + a completeness critic.
export const meta = {
  name: '<target>-landscape-scan',
  description: 'Landscape scan for the <target> skill (live web) + adversarial verify + completeness critic',
  phases: [{title:'Evidence'},{title:'Verify'},{title:'Completeness'}],
}
const SKILL_SUMMARY = "<one-paragraph description of what the target skill does>";
const FAMILIES = [
  {id:'F1', title:'<family 1>', q:['<question>','<question>']},
  // ... 5-8 families relevant to the target's domain (e.g. for an LLM/AI skill:
  // survey-gen systems, eval frameworks, citation-grounding, RAG retrievers,
  // quantization schemes, attention variants, decoding methods, benchmark harnesses)
];
const NO_WRITE = "CRITICAL: do NOT write/create/edit any file. Return only the structured result.";
const EVID = {type:'object', properties:{family:{type:'string'},
  systems:{type:'array', items:{type:'object', properties:{name:{type:'string'}, what_it_does:{type:'string'}, key_capability:{type:'string'}, source_url:{type:'string'}}, required:['name','source_url']}},
  practices:{type:'array', items:{type:'string'}}, notes:{type:'string'}}, required:['family','systems']};
const VERIFY = {type:'object', properties:{family:{type:'string'},
  flagged:{type:'array', items:{type:'object', properties:{claim:{type:'string'}, issue:{type:'string'}}, required:['claim','issue']}},
  verdict:{type:'string'}}, required:['flagged']};
phase('Evidence');
const verified = await pipeline(FAMILIES,
  (f)=>agent(`Landscape evidence agent. Skill under comparison: ${SKILL_SUMMARY}\nResearch family "${f.title}": ${f.q.join('; ')}\nWebSearch+WebFetch primary sources, cap ~10 searches. ${NO_WRITE}`,
    {label:`ev:${f.id}`, phase:'Evidence', agentType:'evidence-collector', schema:EVID}),
  (ev,f)=>agent(`Adversarially verify this landscape evidence for "${f.title}" — flag fabricated/misattributed/unsupported claims; be skeptical of version numbers + percentages. ${NO_WRITE}\n${JSON.stringify(ev).slice(0,9000)}`,
    {label:`verify:${f.id}`, phase:'Verify', agentType:'general-purpose', schema:VERIFY}).then(v=>({family:f.id, evidence:ev, verify:v})));
phase('Completeness');
const critic = await agent(`Completeness critic for the <target> landscape. Verified evidence:\n${JSON.stringify(verified.filter(Boolean)).slice(0,16000)}\nList GAPS + the 5-8 most transferable SOTA practices the skill is MISSING (candidate improvements), each mapped to a phase. ${NO_WRITE}`,
  {label:'completeness', phase:'Completeness', agentType:'general-purpose',
   schema:{type:'object', properties:{gaps:{type:'array', items:{type:'string'}}, missing_practices:{type:'array', items:{type:'object', properties:{practice:{type:'string'}, why:{type:'string'}, maps_to_phase:{type:'string'}}, required:['practice','why']}}}, required:['gaps','missing_practices']}});
return { families: verified.filter(Boolean), completeness: critic, tokens_spent: budget.spent() };
