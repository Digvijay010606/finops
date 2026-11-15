"""Collect headline metrics from all report files into reports/facts.json (single source of truth for decks/PDF/README)."""
import json, sqlite3
import pandas as pd
R = "reports/"; ing = json.load(open("data/processed/ingest_stats.json")); con = sqlite3.connect("data/processed/warehouse.db")
q = pd.read_sql("SELECT reason, COUNT(*) n FROM quarantine_billing GROUP BY 1", con).set_index("reason").n.to_dict()
ib = pd.read_csv(R + "index_benchmark.csv"); pc = pd.read_csv(R + "partition_clustering_benchmark.csv"); an = pd.read_csv(R + "anomalies_detected.csv")
ue = pd.read_csv(R + "unit_economics_monthly.csv"); rate = pd.read_csv(R + "rate_optimization.csv"); k = json.load(open(R + "k8s_summary.json"))
aud = json.load(open(R + "audit_summary.json")); lev = pd.read_csv(R + "audit_levers.csv"); sv = pd.read_csv(R + "cost_by_service.csv")
stor = pd.read_csv(R + "storage_lifecycle_model.csv")
f = dict(ingest=ing, quarantine=q, fact_rows=con.execute("SELECT COUNT(*) FROM fact_usage_cost").fetchone()[0],
         total_cost=round(con.execute("SELECT SUM(unblended_cost) FROM fact_usage_cost").fetchone()[0], 2),
         index=ib[["query", "before_ms", "plain_index_ms", "after_ms", "speedup"]].to_dict("records"), partition=pc.to_dict("records"),
         anomalies=len(an), top_anoms=an.head(4).to_dict("records"), unit=ue.reset_index().to_dict("records"), rate=rate.to_dict("records"),
         k8s=k, audit=aud, levers=lev.to_dict("records"), top_services=sv.head(5)[["service_code", "sum", "pct_of_total"]].to_dict("records"),
         storage_saving_year=round(stor.saving.sum() * 12), untagged=open(R + "reconciliation.txt").read().count("PASS"))
json.dump(f, open(R + "facts.json", "w"), indent=1, default=float); print("facts saved")
