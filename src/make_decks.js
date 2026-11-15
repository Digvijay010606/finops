// DAY 14 + DAY 21 decks. Run: node src/make_decks.js   (needs pptxgenjs)
const pptxgen = require("pptxgenjs"); const fs = require("fs");
const F = JSON.parse(fs.readFileSync("reports/facts.json")); const money = n => "$" + Math.round(n).toLocaleString("en-US");
const NAVY = "1F2A44", BLUE = "2E5BBA", LIGHT = "F4F7FB", GREY = "5B6577";
function base(pres, title) { const s = pres.addSlide(); s.background = { color: "FFFFFF" };
  s.addText(title, { x: .5, y: .3, w: 9, h: .7, fontSize: 26, bold: true, color: NAVY, fontFace: "Calibri", isTextBox: true }); s.addShape(pres.ShapeType.rect, { x: .5, y: 1.0, w: 1.2, h: .06, fill: { color: BLUE } }); return s; }
function title(pres, t, sub) { const s = pres.addSlide(); s.background = { color: NAVY };
  s.addText(t, { x: .6, y: 1.7, w: 8.8, h: 1.2, fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Calibri", isTextBox: true });
  s.addText(sub, { x: .6, y: 3.1, w: 8.8, h: .8, fontSize: 16, color: "BFD0F0", fontFace: "Calibri", isTextBox: true }); }
function bullets(s, items, o = {}) { s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
  Object.assign({ x: .5, y: 1.3, w: 9, h: 3.8, fontSize: 16, color: "222222", fontFace: "Calibri", valign: "top", isTextBox: true }, o)); }
const tbl = (rows, hdr) => [hdr.map(h => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: BLUE } } })), ...rows.map(r => r.map(c => ({ text: String(c) })))];

// ---------- Mid-term audit ----------
let p = new pptxgen(); p.layout = "LAYOUT_16x9"; p.title = "Cloud Optimization Audit";
title(p, "Cloud Optimization Audit", `Mid-term FinOps review | ${money(F.audit.total_saving)} identified savings (${F.audit.pct}% of run-rate)`);
let s = base(p, "Scope and method");
bullets(s, [`90 days of billing (Aug-Oct 2026), ${F.fact_rows.toLocaleString()} validated line items, 4 accounts, 11 services`, "Pipeline: ingest, validate, quarantine, load to star schema, reconcile (zero data loss)", `Annualised run-rate used as baseline: ${money(F.audit.run_rate)}`, "Levers sized from warehouse data; assumption-based levers are labelled"]);
s = base(p, "Where the money goes"); s.addImage({ path: "docs/cost_distribution.png", x: .5, y: 1.25, w: 9, h: 3.3 });
s.addText("Storage and Compute are 64% of spend; S3 alone is the largest single service.", { x: .5, y: 4.7, w: 9, h: .5, fontSize: 14, color: GREY, isTextBox: true });
s = base(p, "Identified savings by lever"); s.addImage({ path: "docs/audit_levers.png", x: .5, y: 1.2, w: 5.6, h: 2.5 });
s.addTable(tbl(F.levers.map(l => [l.lever.split(" (")[0], money(l.annual_saving), l.pct_of_run_rate + "%"]), ["Lever", "Annual", "% run-rate"]), { x: 6.2, y: 1.2, w: 3.4, fontSize: 9, colW: [1.7, .9, .8] });
s.addText(`Total: ${money(F.audit.total_saving)} per year (${F.audit.pct}%). Target was 15%+.`, { x: .5, y: 4.2, w: 9, h: .5, fontSize: 16, bold: true, color: BLUE, isTextBox: true });
s = base(p, "Recommendations and priorities");
s.addTable(tbl([["1", "Buy 1-yr Compute Savings Plan at ~70% coverage + Spot for non-prod", "Low", money(F.levers[0].annual_saving)], ["2", "Schedule non-prod compute off nights/weekends", "Low", money(F.levers[1].annual_saving)], ["3", "Apply S3 lifecycle policies to cold/warm buckets", "Low", money(F.levers[3].annual_saving)], ["4", "Right-size K8s requests, consolidate nodes", "Medium", money(F.levers[2].annual_saving)], ["5", "Enforce tagging policy, remove orphans", "Medium", money(F.levers[4].annual_saving)]], ["#", "Action", "Effort", "Annual saving"]), { x: .5, y: 1.3, w: 9, fontSize: 12, colW: [.4, 5.6, 1, 2] });
s = base(p, "Risks and assumptions"); bullets(s, ["Discount rates (RI / Savings Plan / Spot) and unit prices are illustrative; confirm against current AWS pricing", "Scheduling and orphan cleanup assume 50% and 30% realisation respectively", "Sample data is synthetic: results demonstrate the method, not a real account", "Savings Plan commitment should follow 2-3 months of stable usage"]);
p.writeFile({ fileName: "outputs/Day14_MidTerm_Audit_Deck.pptx" }).then(() => {
// ---------- Final deck ----------
let q = new pptxgen(); q.layout = "LAYOUT_16x9"; q.title = "Cloud Financial Intelligence Platform";
title(q, "Cloud Financial Intelligence Platform", "Data Engineering and FinOps capstone | 10-minute technical demo");
s = base(q, "Architecture"); s.addImage({ path: "docs/architecture.png", x: .5, y: 1.2, w: 9, h: 3.75 });
s = base(q, "Data model: star schema"); s.addImage({ path: "docs/erd.png", x: 1.7, y: 1.15, w: 6.3, h: 3.95 });
s = base(q, "Pipeline reliability"); const qs = F.quarantine;
bullets(s, [`${F.ingest.rows_csv + F.ingest.rows_json} raw rows from CSV + CUR-style JSON; ${F.fact_rows} loaded; ${Object.values(qs).reduce((a, b) => a + b, 0)} quarantined`, `Quarantine reasons: duplicates ${qs.DUPLICATE_LINE_ITEM}, null resource ${qs.NULL_RESOURCE_ID}, negative cost ${qs.NEGATIVE_COST}`, `${F.ingest.cost_imputed_rows} missing costs recovered from quantity x rate; schema drift column detected`, "7 reconciliation checks (row counts, cost sums, MD5 of IDs): all pass", "Reconcile step gates downstream tasks in the Airflow DAG"]);
s = base(q, "Performance engineering");
s.addTable(tbl(F.index.map(r => [r.query, r.before_ms, r.plain_index_ms, r.after_ms, r.speedup + "x"]), ["Query (1.5M rows)", "Before ms", "Plain idx ms", "Final ms", "Speedup"]), { x: .5, y: 1.3, w: 9, fontSize: 12, colW: [3.4, 1.3, 1.5, 1.3, 1.5] });
s.addText("Lesson: a non-covering index made the wide-range query slower; a covering index fixed it.", { x: .5, y: 3.6, w: 9, h: .6, fontSize: 14, color: BLUE, bold: true, isTextBox: true });
s = base(q, "Anomaly detection"); bullets(s, [`Rolling median/MAD modified z-score (threshold 3.5) over 14-day baselines per service and account`, `${F.anomalies} anomalies flagged: EC2 prod spike 10-12 Sep, data transfer spike 10 Oct`, "Alerts post to a webhook (Slack/Teams) or fall back to a JSONL file", "Unit tests prove detection of spikes without noise false-positives"]);
s = base(q, "Quantified savings"); s.addImage({ path: "docs/audit_levers.png", x: .5, y: 1.2, w: 6, h: 2.7 });
s.addText([{ text: money(F.audit.total_saving), options: { fontSize: 30, bold: true, color: BLUE, breakLine: true } }, { text: `per year, ${F.audit.pct}% of run-rate`, options: { fontSize: 14, color: GREY } }], { x: 6.7, y: 1.7, w: 3, h: 1.4, isTextBox: true });
s = base(q, "Executive dashboard"); s.addImage({ path: "docs/executive_dashboard.png", x: 1.2, y: 1.15, w: 7.2, h: 4.1 });
s = base(q, "Lessons and next steps"); bullets(s, ["Validate before load; quarantine rather than drop", "Index choices need measurement: covering indexes beat plain ones for wide ranges", "Next: real CUR ingestion via S3 + Athena, Snowflake deployment, Infracost in CI, SP purchase tracking"]);
return q.writeFile({ fileName: "outputs/Day21_Final_Presentation.pptx" }); }).then(() => console.log("decks written"));
