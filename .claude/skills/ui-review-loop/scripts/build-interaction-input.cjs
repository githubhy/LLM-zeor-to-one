/* build-interaction-input.cjs — emit interaction-review-input.json (absolute shot
 * paths + assertion results) from an interact.cjs run, for the interaction review
 * workflow. Usage: node .../build-interaction-input.cjs <out-dir> > <out>/interaction-review-input.json
 * Absolute paths let the workflow's vision agents Read each PNG directly. */
const fs = require("fs");
const path = require("path");
const OUT = path.resolve(process.argv[2] || ".");
const scen = JSON.parse(fs.readFileSync(path.join(OUT, "interactions.json"), "utf8"));
const rows = scen.map((s) => ({
  id: s.id,
  label: s.label,
  route: s.route,
  viewport: s.viewport,
  category: s.category,
  steps: s.steps || [],
  error: s.error || null,
  assertions: s.assertions || [],
  shots: (s.shots || []).map((sh) => ({ label: sh.label, path: path.join(OUT, sh.file) })),
}));
process.stdout.write(JSON.stringify(rows, null, 2) + "\n");
process.stderr.write(`emitted ${rows.length} interaction scenarios\n`);
