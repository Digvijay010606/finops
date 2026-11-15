"""DAY 09: Scan the asset inventory for untagged / orphaned resources and price the exposure. Run: python src/audit_untagged.py"""
import sqlite3
import pandas as pd
REQUIRED = ["env", "team", "owner"]
inv = pd.read_csv("data/raw/resource_inventory.csv")
con = sqlite3.connect("data/processed/warehouse.db")
c30 = pd.read_sql("""SELECT rs.resource_id, SUM(f.unblended_cost) cost_30d FROM fact_usage_cost f JOIN dim_resource rs USING(resource_key)
                     WHERE f.date_key >= 20260930 GROUP BY 1""", con)
inv = inv.merge(c30, on="resource_id", how="left").fillna({"cost_30d": 0})
inv["missing_tags"] = inv[REQUIRED].isna().apply(lambda r: ",".join(c for c in REQUIRED if r[c]), axis=1)
inv["is_untagged"] = inv.missing_tags != ""
inv["is_orphan"] = inv[["team", "owner"]].isna().all(axis=1)            # no team AND no owner: nobody to ask
inv["is_dev_idle_candidate"] = (inv.env.isna() | (inv.env == "dev")) & (inv.service == "AmazonEC2")
inv[inv.is_untagged].sort_values("cost_30d", ascending=False).to_csv("reports/untagged_resources.csv", index=False)
tot = inv.cost_30d.sum(); u = inv[inv.is_untagged].cost_30d.sum(); o = inv[inv.is_orphan].cost_30d.sum()
print(f"Resources: {len(inv)} | untagged: {inv.is_untagged.sum()} ({inv.is_untagged.mean():.0%}) | orphaned: {inv.is_orphan.sum()}")
print(f"Last-30d spend: ${tot:,.0f} | untagged spend: ${u:,.0f} ({u/tot:.1%}) | orphaned spend: ${o:,.0f} ({o/tot:.1%})")
print(inv[inv.is_untagged].groupby("service").size().sort_values(ascending=False).head(5).to_string())
