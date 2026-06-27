/* interaction-assemble.cjs — build INTERACTION-README.md from an interact.cjs run.
 * Usage: node .../interaction-assemble.cjs <out-dir>
 * Reads <out>/interactions.json (+ reviews.json, synthesis.json if present).
 * Assertion results are ground truth (behavior); the vision reviews add visual
 * judgement. AFTER running, hand-author the "Verified findings" block for any
 * assertion FAIL you've root-caused (e.g. chrome not persisting across reload). */
const fs = require("fs");
const path = require("path");
const DIR = path.resolve(process.argv[2] || ".");
const rd = (f) => { try { return JSON.parse(fs.readFileSync(path.join(DIR, f), "utf8")); } catch { return null; } };
const scen = rd("interactions.json") || [];
const reviews = rd("reviews.json") || [];
const synth = rd("synthesis.json");
const byId = Object.fromEntries(reviews.map((r) => [r.id, r]));
const SEV = { blocker: "🟥", major: "🟧", minor: "🟨", nit: "⬜" };
const VV = { good: "🟢 good", "minor-issues": "🟡 minor", "major-issues": "🟧 major", broken: "🟥 broken" };

let out = "";
const p = (s = "") => (out += s + "\n");
const totA = scen.flatMap((s) => s.assertions);

p(`# Interaction Review — ${path.basename(DIR)}`);
if (synth) p(`**Verdict:** ${String(synth.overall_verdict).toUpperCase()} · ${scen.length} interactions · assertions ${totA.filter((a) => a.pass).length}/${totA.length} passed`);
else p(`**${scen.length} interactions · assertions ${totA.filter((a) => a.pass).length}/${totA.length} passed** (no synthesis.json yet)`);
p();
p(`> Interaction findings are **assertion-backed** (DOM/a11y checked in a headless browser), with a vision pass on the resulting states. Click a thumbnail for full-res.`);
p();
p(`## ⚠️ Verified findings (hand-author for each assertion FAIL)`);
p(`> Root-cause every failed assertion before reporting it (per the ui-review-loop discipline). The highest-value`);
p(`> failures to scrutinize: chrome NOT persisting across reload (FOUC/hydration), focus NOT returning after a`);
p(`> dismissed settings sheet, focus NOT trapped in the palette, sidenotes overlapping. Replace this block.`);
p();

if (synth) {
  p(`## Summary`);
  p(synth.executive_summary); p();
  p(`**Recently-redesigned surfaces:** ${synth.redesigned_surfaces_ok}`); p();
  p(`**Accessibility:** ${synth.a11y_notes}`); p();
  if (synth.confirmed_issues && synth.confirmed_issues.length) {
    p(`### Confirmed issues`);
    p(`| | Severity | Area | Issue |`); p(`|---|---|---|---|`);
    const rank = { blocker: 0, major: 1, minor: 2, nit: 3 };
    for (const i of [...synth.confirmed_issues].sort((a, b) => rank[a.severity] - rank[b.severity]))
      p(`| ${SEV[i.severity]} | ${i.severity} | ${i.area.replace(/\|/g, "\\|")} | ${i.description.replace(/\n/g, " ").replace(/\|/g, "\\|")} |`);
    p();
  }
}

p(`## Assertion matrix`);
p(`| Interaction | Viewport | Redesigned? | Assertions | Works |`);
p(`|---|---|:---:|:---:|:---:|`);
for (const s of scen) {
  const ok = s.assertions.filter((a) => a.pass).length, tot = s.assertions.length;
  const r = byId[s.id];
  p(`| ${s.label} | ${s.viewport} | ${s.category === "changed" ? "★" : ""} | ${ok}/${tot}${ok < tot ? " ⚠️" : ""} | ${r ? (r.interaction_works ? "✅" : "❌") : (ok === tot ? "✅" : "❌")} |`);
}
p();

p(`---`);
p(`## Per-interaction detail`);
p();
for (const s of scen) {
  const r = byId[s.id] || {};
  p(`### ${s.label}  ${s.category === "changed" ? "★ (redesigned)" : ""}`);
  p(`\`${s.route || "—"}\` · ${s.viewport} · vision: **${VV[r.visual_verdict] || "—"}**${s.error ? ` · ⚠️ driver error: ${s.error}` : ""}`);
  if (s.steps && s.steps.length) p(`\n**Steps:** ${s.steps.join(" → ")}`);
  p();
  p(`**Assertions**`);
  for (const a of s.assertions) p(`- ${a.pass ? "✅" : "❌"} ${a.name} — \`${a.detail}\``);
  p();
  if (s.shots && s.shots.length) {
    p(`| ${s.shots.map((sh) => sh.label).join(" | ")} |`);
    p(`|${s.shots.map(() => ":---:").join("|")}|`);
    p(`| ${s.shots.map((sh) => `[<img src="${sh.file}" width="200">](${sh.file})`).join(" | ")} |`);
    p();
  }
  if (r.notes) p(`**Vision:** ${r.notes}`);
  if (r.issues && r.issues.length) { p(`**Issues:**`); for (const i of r.issues) p(`- ${SEV[i.severity] || ""} *(${i.severity})* ${i.description}`); }
  p(); p();
}
fs.writeFileSync(path.join(DIR, "INTERACTION-README.md"), out);
console.log(`wrote ${path.join(DIR, "INTERACTION-README.md")} — ${scen.length} interactions, ${out.split("\n").length} lines`);
