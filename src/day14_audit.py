"""DAY 14: Consolidated optimisation audit - sizes each savings lever against the annualised run-rate. Run: python src/day14_audit.py
Levers marked (assumption) depend on the stated percentages; adjust to your environment."""
import json, sqlite3
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
con = sqlite3.connect("data/processed/warehouse.db"); ANN = 365 / 30
total30 = con.execute("SELECT SUM(unblended_cost) FROM fact_usage_cost WHERE date_key>=20260930").fetchone()[0]; run_rate = total30 * ANN
nonprod = con.execute("""SELECT SUM(f.unblended_cost) FROM fact_usage_cost f JOIN dim_account a USING(account_key) JOIN dim_service s USING(service_key)
   WHERE f.date_key>=20260930 AND a.account_name IN ('dev-sandbox','staging') AND s.service_code IN ('AmazonEC2','AmazonRDS','AmazonEKS','AmazonRedshift')""").fetchone()[0] * ANN
orph = pd.read_csv("reports/untagged_resources.csv"); orph = orph[orph.owner.isna() & orph.team.isna()].cost_30d.sum() * ANN
rate = pd.read_csv("reports/rate_optimization.csv").set_index("scenario").annual_savings["RECOMMENDED: 1-yr SP + Spot (non-prod)"]
k8s = json.load(open("reports/k8s_summary.json")); stor = pd.read_csv("reports/storage_lifecycle_model.csv").saving.sum() * 12
sched = nonprod * .50 * .90      # stop non-prod nights/weekends (~50% of hours realistic) less 10% overlap with rate savings
levers = {"Savings Plan + Spot (rate)": rate, "Non-prod scheduling (assumption: 50% hrs off)": sched, "K8s right-sizing (pods+nodes)": (k8s["pod_saving_month"] + k8s["node_saving_month"]) * 12,
          "S3 lifecycle tiering": stor, "Orphaned resource cleanup (assumption: 30% removable)": orph * .30}
df = pd.DataFrame({"lever": list(levers), "annual_saving": [round(v) for v in levers.values()]}); df["pct_of_run_rate"] = (100 * df.annual_saving / run_rate).round(1)
tot = df.annual_saving.sum(); df.to_csv("reports/audit_levers.csv", index=False)
summary = dict(run_rate=round(run_rate), total_saving=int(tot), pct=round(100 * tot / run_rate, 1)); json.dump(summary, open("reports/audit_summary.json", "w"))
fig, ax = plt.subplots(figsize=(8, 3.6)); df.set_index("lever").annual_saving.sort_values().plot.barh(ax=ax, color="#2E5BBA"); ax.set_xlabel("Annual saving ($)"); ax.set_ylabel("")
ax.set_title(f"Identified savings \\${tot:,.0f} = {summary['pct']}% of \\${run_rate:,.0f} run-rate"); plt.tight_layout(); plt.savefig("docs/audit_levers.png", dpi=130)
print(df.to_string(index=False)); print(summary)
