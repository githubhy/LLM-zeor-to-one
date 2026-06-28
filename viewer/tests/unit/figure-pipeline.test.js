'use strict';
// Unit tests for the spec-driven pipeline-figure renderer (pure string output,
// no DOM). Mirrors tests/unit/settings-store.test.js (node:test + assert/strict).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const FP = require('../../lib/figure-pipeline.js');

// Demo spec: the scaled dot-product attention pipeline (a canonical LLM figure).
const SPEC = {
  id: 'pipeline-figure',
  title: 'scaled dot-product attention',
  input: { label: 'x', sub: 'tokens' },
  output: { label: 'context' },
  stages: [
    { id: 'qkv', title: 'QKV projection', detail: 'W_Q,W_K,W_V', ref: '§3.3', group: 'A' },
    { id: 'sc',  title: 'Scores', detail: 'QK^T', ref: '§3.4', group: 'A' },
    { id: 'sm',  title: 'Scaled softmax', detail: 'over keys', ref: '§3.2', group: 'B', highlight: true },
    { id: 'wv',  title: 'Weighted sum', detail: 'over V', ref: '§5c', group: 'C' },
    { id: 'op',  title: 'Output projection', detail: 'W_O', ref: '§5d', group: 'C' },
  ],
  edges: ['Q,K,V', 'scores', 'weights', 'heads'],
  groups: {
    A: { label: 'project', color: '#1f77b4' },
    B: { label: 'attend', color: '#ff7f0e' },
    C: { label: 'combine', color: '#2ca02c' },
  },
  defaultStyle: 'colour-academic',
};

test('STYLE_IDS are the five curated ids; image is not a rendered style', () => {
  assert.deepEqual(FP.STYLE_IDS, ['colour-academic', 'monochrome', 'minimal', 'swimlane', 'image']);
  assert.equal(FP.RENDERED_IDS.indexOf('image'), -1);
});

test('colour-academic: linear boxes, highlight, edge labels, group colour', () => {
  const h = FP.render(SPEC, 'colour-academic');
  assert.match(h, /fp-linear fp-colour-academic/);
  assert.match(h, /class="fp-box fp-g-B fp-hot"/);     // softmax box highlighted
  assert.match(h, /Scaled softmax/);
  assert.match(h, /QKV projection/);
  assert.match(h, /Q,K,V/);                            // edge label present
  assert.match(h, /--gc:#1f77b4/);                      // group colour inlined
  assert.match(h, /tokens/);                            // input io
  assert.match(h, /context/);                           // output io
});

test('monochrome and minimal also render the linear scaffold', () => {
  assert.match(FP.render(SPEC, 'monochrome'), /fp-linear fp-monochrome/);
  assert.match(FP.render(SPEC, 'minimal'), /fp-linear fp-minimal/);
});

test('swimlane groups the five stages into three bands', () => {
  const h = FP.render(SPEC, 'swimlane');
  assert.match(h, /fp-swimlane/);
  assert.equal((h.match(/class="fp-band/g) || []).length, 3);
  assert.equal((h.match(/class="fp-scard/g) || []).length, 5);
  assert.match(h, /fp-scard fp-hot/);                   // highlight carries through
});

test('unknown style falls back to the default', () => {
  assert.match(FP.render(SPEC, 'bogus'), /fp-colour-academic/);
});

test('render guards against missing/invalid spec', () => {
  assert.equal(FP.render(null, 'colour-academic'), '');
  assert.equal(FP.render(undefined, 'swimlane'), '');
});

test('spec text is HTML-escaped (no injection)', () => {
  const evil = JSON.parse(JSON.stringify(SPEC));
  evil.stages[0].title = '<img src=x onerror=alert(1)>';
  const h = FP.render(evil, 'colour-academic');
  assert.ok(!h.includes('<img src=x'));
  assert.match(h, /&lt;img src=x/);
});

test('CSS bundle carries the reflow container query', () => {
  assert.match(FP.CSS, /@container \(max-width:900px\)/);
  assert.match(FP.CSS, /\.fp-wrap\{container-type:inline-size/);
});
