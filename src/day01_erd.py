"""DAY 01: Draw the ERD for the star schema. Run: python src/day01_erd.py"""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
T = {"fact_usage_cost": (4.75, 1.3, ["PK line_item_id", "FK date_key", "FK account_key", "FK region_key", "FK service_key", "FK resource_key", "FK tag_key", "usage_quantity", "unit_rate", "unblended_cost", "cost_imputed"]),
     "dim_date": (.3, 4.2, ["PK date_key", "full_date", "year, month, day", "day_of_week", "is_weekend", "year_month"]), "dim_account": (4.75, 5.8, ["PK account_key", "account_id", "account_name"]),
     "dim_region": (9.2, 5.5, ["PK region_key", "region_code", "geo"]), "dim_service": (9.2, 3.4, ["PK service_key", "service_code", "cost_category"]),
     "dim_resource": (.3, 1.5, ["PK resource_key", "resource_id", "usage_type", "instance_type"]), "dim_tag": (9.2, 1.3, ["PK tag_key", "env", "team", "owner"])}
fig, ax = plt.subplots(figsize=(12, 7.5)); ax.axis("off"); ax.set_xlim(0, 12.4); ax.set_ylim(0, 7.4)
ctr = {}
for n, (x, y, cols) in T.items():
    h = .32 * (len(cols) + 1); w = 2.9; fact = n.startswith("fact")
    ax.add_patch(plt.Rectangle((x, y), w, h, fc="#FFF3E0" if fact else "#E8F0FE", ec="#2E5BBA", lw=1.5)); ax.text(x + w / 2, y + h - .16, n, ha="center", va="center", fontweight="bold", fontsize=9)
    for i, c in enumerate(cols): ax.text(x + .1, y + h - .5 - i * .32, c, fontsize=8, family="monospace")
    ctr[n] = (x + w / 2, y + h / 2)
fx, fy, fcols = T["fact_usage_cost"]; fh = .32 * (len(fcols) + 1); W = 2.9
for d, (x, y, cols) in T.items():
    if d == "fact_usage_cost": continue
    h = .32 * (len(cols) + 1); cy = y + h / 2; ty = min(max(cy, fy + .4), fy + fh - .4)
    if d == "dim_account": a, b = (x + W / 2, y), (fx + W / 2, fy + fh)
    elif x < fx: a, b = (x + W, cy), (fx, ty)
    else: a, b = (x, cy), (fx + W, ty)
    ax.annotate("", b, a, arrowprops=dict(arrowstyle="-|>", color="#888", lw=1.2))
ax.set_title("Cloud Usage & Billing - Star Schema (fact_usage_cost at grain: one resource per day)", fontsize=12); plt.savefig("docs/erd.png", dpi=130, bbox_inches="tight")
