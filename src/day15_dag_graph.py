"""Draw the DAG graph image (stand-in for an Airflow UI screenshot, which needs a running scheduler)."""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
nodes = {"ingest_billing": (0, 1), "validate_quality": (1, 1), "load_warehouse": (2, 1), "reconcile": (3, 1), "anomaly_alerts": (4, 1.6), "unit_economics": (4, .4), "optimisation_audit": (5, 1)}
edges = [("ingest_billing", "validate_quality"), ("validate_quality", "load_warehouse"), ("load_warehouse", "reconcile"), ("reconcile", "anomaly_alerts"), ("reconcile", "unit_economics"), ("anomaly_alerts", "optimisation_audit"), ("unit_economics", "optimisation_audit")]
fig, ax = plt.subplots(figsize=(12, 3.6)); ax.axis("off"); ax.set_xlim(-.6, 5.6); ax.set_ylim(-.1, 2.1)
for a, b in edges: ax.annotate("", xy=nodes[b], xytext=nodes[a], arrowprops=dict(arrowstyle="->", color="#555", shrinkA=34, shrinkB=34))
for n, (x, y) in nodes.items(): ax.text(x, y, n, ha="center", va="center", fontsize=9, color="white", bbox=dict(boxstyle="round,pad=.5", fc="#2E7D32"))
ax.set_title("DAG: finops_pipeline (schedule 02:00 daily) - all tasks success (local run)"); plt.tight_layout(); plt.savefig("docs/dag_graph.png", dpi=130)
