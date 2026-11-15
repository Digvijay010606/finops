"""DAY 13: Kubernetes request-vs-usage analysis and right-sizing. Unit prices are illustrative assumptions. Run: python src/day13_k8s_rightsizing.py"""
import math
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
CPU_HR, GB_HR, HRS = 0.031, 0.0042, 730; NODE_CPU, NODE_GB, NODE_HR, CURRENT_NODES, TARGET_UTIL = 16, 64, 0.768, 8, 0.80
p = pd.read_csv("data/raw/k8s_pods.csv")
p["cpu_util"] = p.cpu_p95_used / p.cpu_request; p["mem_util"] = p.mem_p95_used_gb / p.mem_request_gb
p["cpu_rec"] = p.cpu_p95_used.mul(1.25).div(.25).apply(math.ceil).mul(.25).clip(lower=.25).clip(upper=p.cpu_request)
p["mem_rec_gb"] = p.mem_p95_used_gb.mul(1.20).div(.5).apply(math.ceil).mul(.5).clip(lower=.5).clip(upper=p.mem_request_gb)
p["monthly_now"] = (p.cpu_request * CPU_HR + p.mem_request_gb * GB_HR) * HRS
p["monthly_rec"] = (p.cpu_rec * CPU_HR + p.mem_rec_gb * GB_HR) * HRS; p["monthly_saving"] = p.monthly_now - p.monthly_rec
p["overprovisioned"] = (p.cpu_util < .40) | (p.mem_util < .40)
p.sort_values("monthly_saving", ascending=False).to_csv("reports/k8s_rightsizing.csv", index=False)
nodes_needed = max(math.ceil(p.cpu_rec.sum() / (NODE_CPU * TARGET_UTIL)), math.ceil(p.mem_rec_gb.sum() / (NODE_GB * TARGET_UTIL)))
node_saving = (CURRENT_NODES - nodes_needed) * NODE_HR * HRS
ns = p.groupby("namespace").agg(pods=("pod", "count"), cpu_req=("cpu_request", "sum"), cpu_rec=("cpu_rec", "sum"), saving=("monthly_saving", "sum")).round(1)
fig, ax = plt.subplots(figsize=(6.5, 4)); ax.scatter(p.cpu_request, p.cpu_p95_used, c="#2E5BBA"); ax.plot([0, 4], [0, 4], "--", c="grey"); ax.set_xlabel("CPU requested (cores)"); ax.set_ylabel("CPU p95 used (cores)")
ax.set_title("Requests vs usage (below dashed line = over-provisioned)"); plt.tight_layout(); plt.savefig("docs/k8s_requests_vs_usage.png", dpi=130)
print(f"Pods {len(p)} | overprovisioned {p.overprovisioned.sum()} | CPU requested {p.cpu_request.sum():.0f} -> {p.cpu_rec.sum():.0f} cores | mem {p.mem_request_gb.sum():.0f} -> {p.mem_rec_gb.sum():.0f} GB")
print(f"Pod-level saving ${p.monthly_saving.sum():,.0f}/mo | nodes {CURRENT_NODES} -> {nodes_needed} (+${node_saving:,.0f}/mo) | annual (nodes) ${node_saving*12:,.0f}\n{ns.to_string()}")
pd.Series(dict(pod_saving_month=p.monthly_saving.sum(), node_saving_month=node_saving, nodes_now=CURRENT_NODES, nodes_needed=nodes_needed, overprov=int(p.overprovisioned.sum()))).to_json("reports/k8s_summary.json")
