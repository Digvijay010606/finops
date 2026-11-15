"""DAY 18: One-page executive PDF view (matplotlib) - spend, unit efficiency, coverage and forecast variance. Run: python src/day18_exec_dashboard.py"""
import json, sqlite3
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
con = sqlite3.connect("data/processed/warehouse.db")
daily = pd.read_sql("SELECT d.full_date date, SUM(f.unblended_cost) cost FROM fact_usage_cost f JOIN dim_date d USING(date_key) GROUP BY 1", con); daily["date"] = pd.to_datetime(daily.date)
cat = pd.read_sql("SELECT s.cost_category c, SUM(f.unblended_cost) v FROM fact_usage_cost f JOIN dim_service s USING(service_key) GROUP BY 1", con)
unit = pd.read_csv("reports/unit_economics_daily.csv"); an = pd.read_csv("reports/anomalies_detected.csv"); aud = json.load(open("reports/audit_summary.json"))
train = daily.iloc[:60]; trend = np.polyfit(np.arange(60), train.cost.clip(upper=train.cost.quantile(.95)), 1); fc = np.polyval(trend, np.arange(60, 90)); act = daily.cost.iloc[60:].values
var_pct = 100 * (act.sum() - fc.sum()) / fc.sum(); total = daily.cost.sum()
fig = plt.figure(figsize=(11.7, 8.3)); fig.suptitle("Cloud FinOps - Executive View (Aug-Oct 2026)", fontsize=16, fontweight="bold", x=.05, ha="left")
kp = [("Total spend (90d)", f"${total:,.0f}"), ("Avg daily spend", f"${daily.cost.mean():,.0f}"), ("Cost / 1k requests (Oct)", f"${unit[unit.month=='2026-10'].cost_per_1k_requests.mean():.2f}"),
      ("Savings identified", f"${aud['total_saving']:,.0f} ({aud['pct']:.0f}%)"), ("SP/RI coverage", "0% (target 70%)"), ("Forecast variance (Oct)", f"{var_pct:+.1f}%")]
for i, (k, v) in enumerate(kp): fig.text(.05 + i * .155, .88, k, fontsize=8, color="#555"); fig.text(.05 + i * .155, .84, v, fontsize=12, fontweight="bold", color="#2E5BBA")
a = fig.add_axes([.06, .45, .55, .3]); a.plot(daily.date, daily.cost, c="#2E5BBA"); a.plot(daily.date.iloc[60:], fc, "--", c="grey", label="forecast"); a.set_title("Daily spend vs forecast (dashed)", fontsize=10); a.legend(fontsize=8)
for d in pd.to_datetime(an.date.unique()): a.axvline(d, c="red", alpha=.25)
b = fig.add_axes([.7, .45, .25, .3]); b.pie(cat.v, labels=cat.c, autopct="%1.0f%%", textprops={"fontsize": 8}); b.set_title("Spend by category", fontsize=10)
c = fig.add_axes([.06, .08, .4, .27]); c.plot(pd.to_datetime(unit.date), unit.cost_per_1k_requests.rolling(7).mean(), c="#2E7D32"); c.set_title("Cost per 1k API requests (7-day avg)", fontsize=10); c.tick_params(axis="x", labelsize=7, rotation=20)
lev = pd.read_csv("reports/audit_levers.csv"); d = fig.add_axes([.62, .08, .33, .27]); d.barh(lev.lever.str.split(" \\(").str[0], lev.annual_saving, color="#2E5BBA"); d.tick_params(labelsize=7); d.set_title("Annual savings by lever ($)", fontsize=10)
fig.text(.05, .01, "Red lines = detected cost anomalies. Coverage figure is a target from the Day 11 model; no commitments exist in the sample data.", fontsize=7, color="#777")
fig.savefig("outputs/executive_dashboard.pdf"); fig.savefig("docs/executive_dashboard.png", dpi=110); print(f"forecast variance {var_pct:+.1f}%")
