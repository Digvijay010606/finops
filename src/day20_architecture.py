"""Draw the platform architecture diagram. Run: python src/day20_architecture.py"""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(12, 5)); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 5)
boxes = [(.2, 2, "Sources\nbilling CSV / CUR JSON\napp metrics, K8s, S3", "#F2A541"), (2.6, 2, "Ingest\ningest_billing.py\nparse - clean - map", "#7BA7E0"), (5, 2, "Validate\nvalidate.py\nquarantine bad rows", "#7BA7E0"),
         (7.4, 2, "Warehouse\nstar schema (SQLite;\nSnowflake/BQ DDL)", "#2E5BBA"), (9.8, 3.2, "Analytics\nSQL, unit costs,\nrate model, audit", "#6AB187"), (9.8, .8, "Alerting & BI\nanomaly_engine, Streamlit,\nexec PDF", "#6AB187")]
for x, y, t, c in boxes: ax.text(x + .9, y + .5, t, ha="center", va="center", fontsize=8.5, color="white", bbox=dict(boxstyle="round,pad=.6", fc=c))
for x1, y1, x2, y2 in [(1.5, 2.5, 2.3, 2.5), (3.9, 2.5, 4.7, 2.5), (6.3, 2.5, 7.1, 2.5), (8.7, 2.7, 9.5, 3.5), (8.7, 2.3, 9.5, 1.5)]: ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->"))
ax.text(6, 4.6, "Orchestration: Airflow DAG finops_pipeline (daily 02:00)  |  Reconciliation gates every load  |  Terraform + Infracost in CI", ha="center", fontsize=9)
plt.savefig("docs/architecture.png", dpi=130, bbox_inches="tight")
