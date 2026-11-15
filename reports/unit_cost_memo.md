# Executive Memo - Cloud Unit Cost Efficiency
**Period:** Aug-Oct 2026 | **Source:** FinOps warehouse (validated billing) + app telemetry

**Headline:** Cost per 1,000 API requests moved from $1.429 (Aug) to $1.219 (Oct), a -14.7% change,
while cost per active customer per day moved -9.7% ($1.65 -> $1.49).
Compute cost per processing hour moved +6.2% ($0.90 -> $0.95).

**Interpretation:** Unit costs are the signal that matters: absolute spend growth is acceptable only if cost per request / customer stays flat or falls.
September and October include cost spikes (EC2 in prod in September, data transfer in October), which inflate the monthly average and should be treated as incidents, not trend.

**Recommendations:** (1) Track cost per 1k requests as a weekly KPI with a target ceiling. (2) Commit steady-state compute to Savings Plans (Day 11).
(3) Close tagging gaps so unit costs can be attributed per team (Day 9).
