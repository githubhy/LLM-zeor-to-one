/* assemble.cjs — build README.md from a capture+review run of the markdown viewer.
 * Usage: node .../assemble.cjs <out-dir>
 * Reads <out>/manifest.json (+ reviews.json, synthesis.json if present) → <out>/README.md
 * (verdict, panel issue table, per-doc state-matrix gallery). AFTER running, hand-edit
 * the "Verified corrections" block: per SKILL.md, verify every blocker/major against
 * code/DOM and override the panel where it's wrong — that triage IS the product. */
const fs = require("fs");
const path = require("path");
const DIR = path.resolve(process.argv[2] || ".");
const rd = (f, d) => { try { return JSON.parse(fs.readFileSync(path.join(DIR, f), "utf8")); } catch { return d; } };
const manifest = rd("manifest.json", []);
const reviews = rd("reviews.json", []);
const synth = rd("synthesis.json", null);
const byKey = Object.fromEntries(reviews.map((r) => [r.key, r]));

const SEV = { blocker: "🟥", major: "🟧", minor: "🟨", nit: "⬜" };
const VERDICT = { excellent: "🟩 excellent", good: "🟢 good", "minor-issues": "🟡 minor issues", "major-issues": "🟧 major issues", broken: "🟥 broken" };
const GROUP_ORDER = ["core", "theme", "density", "wide", "mobile"];

let out = "";
const p = (s = "") => (out += s + "\n");
const imgCell = (rel) => (rel ? `[<img src="${rel}" width="220">](${rel})` : "—");

const totalShots = manifest.reduce((n, m) => n + Object.keys(m.shots || {}).length, 0);
p(`# UI Review — ${path.basename(DIR)}`);
p(`**Panel verdict:** ${synth ? String(synth.overall_verdict).toUpperCase() : "(no synthesis.json yet)"} · ${manifest.length} docs × state matrix = ${totalShots} captures`);
p();
p(`> Click any thumbnail for the full-resolution screenshot. Each shot's DOM state (chrome/theme/density) is annotated below it.`);
p();
p(`## ⚠️ Verified corrections (edit me)`);
p(`> Per the ui-review-loop discipline, the panel below is a list of **hypotheses**. Verify every`);
p(`> blocker/major against code/DOM (re-measure the layout with \`getBoundingClientRect\`, read the theme`);
p(`> token hex from \`viewer/style.css\` and compute WCAG, \`existsSync\` figure assets, auto-scroll before`);
p(`> calling math "broken") and replace this block with your findings. Common false alarms to rule out:`);
p(`> lazy-KaTeX/mermaid blank-below-fold on tall shots, vision contrast estimates vs. token math,`);
p(`> by-design dark-mode code blocks, and stale service-worker cache (capture with \`?nocache\`).`);
p();

// Surface any settings-seed mismatches up front — a mis-seeded capture means the
// page never booted into the intended state, which is a real finding (or a script bug).
const seedFails = manifest.flatMap((m) => Object.entries(m.shots).map(([id, s]) => ({ doc: m.label, id, fails: s.seedFails || [], err: s.error }))).filter((x) => (x.fails && x.fails.length) || x.err);
if (seedFails.length) {
  p(`### ⚠️ Capture integrity (settings-seed / errors)`);
  p(`| Doc | State | Problem |`);
  p(`|---|---|---|`);
  for (const x of seedFails) p(`| ${x.doc} | ${x.id} | ${x.err ? "ERROR: " + x.err.replace(/\|/g, "\\|") : "seed mismatch: " + x.fails.join(", ")} |`);
  p();
}

if (synth) {
  p(`## Verdict: ${synth.overall_verdict}`);
  p();
  p(synth.executive_summary);
  p();
  p(`### Strengths`);
  for (const s of synth.top_strengths) p(`- ${s}`);
  p();
  p(`### Panel issues (unverified — triage before trusting)`);
  p();
  p(`| | Severity | Area | Issue | States |`);
  p(`|---|---|---|---|---|`);
  const rank = { blocker: 0, major: 1, minor: 2, nit: 3 };
  for (const i of [...synth.prioritized_issues].sort((a, b) => rank[a.severity] - rank[b.severity])) {
    const st = (i.affected_states || []);
    const states = st.length > 6 ? `${st.slice(0, 6).join(", ")} +${st.length - 6}` : st.join(", ");
    p(`| ${SEV[i.severity]} | ${i.severity} | ${i.area.replace(/\|/g, "\\|")} | ${i.description.replace(/\n/g, " ").replace(/\|/g, "\\|")} | ${states || "—"} |`);
  }
  p();
  p(`### Assessments`);
  p(`- **Dark mode:** ${synth.dark_mode_assessment}`);
  p(`- **Mobile:** ${synth.mobile_assessment}`);
  p(`- **Wide layouts (right-pane / split / sidenotes):** ${synth.wide_layout_assessment}`);
  p(`- **Consistency:** ${synth.consistency_assessment}`);
  p();
  p(`### Merge recommendation`);
  p(`> ${String(synth.merge_recommendation).replace(/\n/g, "\n> ")}`);
  p();
}

p(`---`);
p(`## Per-document state-matrix gallery`);
p();
for (const m of manifest) {
  p(`### ${m.label}`);
  p(`\`${m.url}\` · ${m.bytes} bytes`);
  p();
  // Order shots by group, then within group.
  const entries = Object.entries(m.shots);
  entries.sort((a, b) => (GROUP_ORDER.indexOf(a[1].group) - GROUP_ORDER.indexOf(b[1].group)) || a[0].localeCompare(b[0]));
  for (const grp of GROUP_ORDER) {
    const inGrp = entries.filter(([, s]) => s.group === grp);
    if (!inGrp.length) continue;
    const r = byKey[`${m.key}::${grp}`] || {};
    p(`#### ${grp}${r.verdict ? ` · verdict: **${VERDICT[r.verdict] || r.verdict}**` : ""}`);
    if (r.one_line) p(`> ${r.one_line}`);
    p();
    p(`| ${inGrp.map(([id]) => id).join(" | ")} |`);
    p(`|${inGrp.map(() => ":---:").join("|")}|`);
    p(`| ${inGrp.map(([, s]) => imgCell(s.file)).join(" | ")} |`);
    // DOM annotation row
    p(`| ${inGrp.map(([, s]) => s.dom ? `chrome=${s.dom.chrome}<br>theme=${s.dom.theme || "light"}<br>density=${s.dom.density || "normal"}` : "—").join(" | ")} |`);
    p();
    if (r.issues && r.issues.length) { p(`**Issues (unverified)**`); for (const i of r.issues) p(`- ${SEV[i.severity] || ""} *(${i.severity}/${i.state})* ${i.description}`); p(); }
  }
  p();
}
fs.writeFileSync(path.join(DIR, "README.md"), out);
console.log(`wrote ${path.join(DIR, "README.md")} — ${out.split("\n").length} lines, ${manifest.length} docs, ${totalShots} captures`);
