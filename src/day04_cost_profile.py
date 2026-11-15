"""DAY 04: Profile cost distribution by category / service / usage type. Run: python src/day04_cost_profile.py"""
import sqlite3
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
con = sqlite3.connect("data/processed/warehouse.db")
q = """SELECT s.cost_category, s.service_code, rs.usage_type, f.unblended_cost AS cost FROM fact_usage_cost f
       JOIN dim_service s USING(service_key) JOIN dim_resource rs USING(resource_key)"""
df = pd.read_sql(q, con); tot = df.cost.sum()
cat = df.groupby("cost_category").cost.sum().sort_values(ascending=False)
svc = df.groupby(["cost_category", "service_code"]).cost.agg(["sum", "count"]).reset_index().sort_values("sum", ascending=False)
svc["pct_of_total"] = (100 * svc["sum"] / tot).round(1); svc.to_csv("reports/cost_by_service.csv", index=False)
ut = df[df.service_code == "AmazonEC2"].groupby("usage_type").cost.sum().sort_values(ascending=False).round(2); ut.to_csv("reports/ec2_cost_by_usage_type.csv")
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].pie(cat, labels=cat.index, autopct="%1.0f%%", colors=["#2E5BBA", "#7BA7E0", "#F2A541", "#6AB187"]); ax[0].set_title("Cost by FinOps category")
svc.set_index("service_code")["sum"].sort_values().plot.barh(ax=ax[1], color="#2E5BBA"); ax[1].set_title("Cost by service (90 days, $)"); ax[1].set_ylabel("")
plt.tight_layout(); plt.savefig("docs/cost_distribution.png", dpi=130)
print(f"Total ${tot:,.2f}\n{(100*cat/tot).round(1).to_string()}\n\nTop services:\n{svc.head(5)[['service_code','sum','pct_of_total']].to_string(index=False)}")
