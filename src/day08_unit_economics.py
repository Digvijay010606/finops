"""DAY 08: Cloud unit economics. Run: python src/day08_unit_economics.py"""
import sqlite3
import pandas as pd
con = sqlite3.connect("data/processed/warehouse.db")
cost = pd.read_sql("""SELECT d.full_date AS date, SUM(f.unblended_cost) total_cost,
   SUM(CASE WHEN s.cost_category='Compute' THEN f.unblended_cost END) compute_cost
   FROM fact_usage_cost f JOIN dim_date d USING(date_key) JOIN dim_service s USING(service_key) GROUP BY 1""", con)
m = pd.read_csv("data/raw/app_metrics.csv"); m["date"] = m["date"].astype(str).str[:10]; df = cost.merge(m, on="date")
df["cost_per_1k_requests"] = 1000 * df.total_cost / df.api_requests
df["cost_per_active_customer"] = df.total_cost / df.active_customers
df["compute_cost_per_processing_hr"] = df.compute_cost / df.processing_hours
df["month"] = df.date.str[:7]; df.to_csv("reports/unit_economics_daily.csv", index=False)
mo = df.groupby("month").agg(total_cost=("total_cost", "sum"), cost_per_1k_req=("cost_per_1k_requests", "mean"),
      cost_per_customer_day=("cost_per_active_customer", "mean"), compute_per_proc_hr=("compute_cost_per_processing_hr", "mean")).round(4)
mo.to_csv("reports/unit_economics_monthly.csv"); print(mo.to_string())
a, b = mo.iloc[0], mo.iloc[-1]; chg = lambda c: 100 * (b[c] - a[c]) / a[c]
memo = f"""# Executive Memo - Cloud Unit Cost Efficiency
**Period:** Aug-Oct 2026 | **Source:** FinOps warehouse (validated billing) + app telemetry

**Headline:** Cost per 1,000 API requests moved from ${a.cost_per_1k_req:.3f} (Aug) to ${b.cost_per_1k_req:.3f} (Oct), a {chg('cost_per_1k_req'):+.1f}% change,
while cost per active customer per day moved {chg('cost_per_customer_day'):+.1f}% (${a.cost_per_customer_day:.2f} -> ${b.cost_per_customer_day:.2f}).
Compute cost per processing hour moved {chg('compute_per_proc_hr'):+.1f}% (${a.compute_per_proc_hr:.2f} -> ${b.compute_per_proc_hr:.2f}).

**Interpretation:** Unit costs are the signal that matters: absolute spend growth is acceptable only if cost per request / customer stays flat or falls.
September and October include cost spikes (EC2 in prod in September, data transfer in October), which inflate the monthly average and should be treated as incidents, not trend.

**Recommendations:** (1) Track cost per 1k requests as a weekly KPI with a target ceiling. (2) Commit steady-state compute to Savings Plans (Day 11).
(3) Close tagging gaps so unit costs can be attributed per team (Day 9).
"""
open("reports/unit_cost_memo.md", "w").write(memo)
