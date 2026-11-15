"""Generate a synthetic, deliberately messy AWS-CUR-style dataset (90 days).
Real cloud billing exports are not available offline, so this stands in for them.
Run: python src/generate_data.py"""
import json, random
from pathlib import Path
import numpy as np, pandas as pd

RAW = Path("data/raw"); RAW.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42); random.seed(42)
START, DAYS = pd.Timestamp("2026-08-01"), 90
ACCOUNTS = {"111111111111": "prod", "222222222222": "staging", "333333333333": "data-platform", "444444444444": "dev-sandbox"}
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
SERVICES = {  # service: (count, unit, rate, base daily cost range)
    "AmazonEC2": (80, "Hrs", None, None), "AmazonRDS": (25, "Hrs", 0.17, (6, 30)),
    "AmazonS3": (40, "GB-Mo", 0.023, (2, 40)), "AWSLambda": (40, "Requests-M", 0.20, (0.5, 8)),
    "AmazonEKS": (20, "Hrs", 0.10, (10, 45)), "AmazonCloudFront": (10, "GB", 0.085, (3, 25)),
    "AWSDataTransfer": (15, "GB", 0.09, (2, 30)), "AmazonDynamoDB": (20, "RCU-WCU-M", 0.25, (1, 12)),
    "AmazonRedshift": (5, "Hrs", 0.25, (20, 70)), "AmazonCloudWatch": (15, "GB", 0.50, (0.5, 6)),
    "AmazonEBS": (30, "GB-Mo", 0.08, (1, 15)),
}
EC2_TYPES = {"t3.medium": 0.0416, "m5.large": 0.096, "m5.xlarge": 0.192, "c5.xlarge": 0.17, "r5.large": 0.126}

res = []
for svc, (n, unit, rate, rng_cost) in SERVICES.items():
    for i in range(n):
        acct = random.choices(list(ACCOUNTS), weights=[.45, .15, .25, .15])[0]
        env = {"111111111111": "prod", "222222222222": "staging", "333333333333": "prod", "444444444444": "dev"}[acct]
        if svc == "AmazonEC2":
            itype = random.choice(list(EC2_TYPES)); rate_ = EC2_TYPES[itype]; base = rate_ * 24 * random.uniform(.7, 1)
            usage_type = f"BoxUsage:{itype}"
        else:
            itype = None; rate_ = rate; base = random.uniform(*rng_cost); usage_type = f"{svc}-Usage"
        res.append(dict(resource_id=f"{svc.replace('Amazon','').replace('AWS','').lower()[:8]}-{i:04d}-{random.randrange(16**5):05x}", service=svc, unit=unit,
                        rate=rate_, base=base, account=acct, region=random.choice(REGIONS), usage_type=usage_type,
                        instance_type=itype, env=env, team=random.choice(["platform", "data", "web", "ml"]),
                        owner=random.choice(["asha", "rahul", "meera", "dev", "kiran"]) + "@example.com",
                        trend=random.uniform(-.0003, .0015)))
R = pd.DataFrame(res)
R.loc[R.sample(frac=.15, random_state=1).index, "env"] = None      # governance gaps
R.loc[R.sample(frac=.15, random_state=2).index, "team"] = None
R.loc[R.sample(frac=.12, random_state=3).index, "owner"] = None

rows = []
for d in range(DAYS):
    date = START + pd.Timedelta(days=d); wk = 0.88 if date.dayofweek >= 5 else 1.0
    for r in R.itertuples():
        m = wk * (1 + r.trend * d) * rng.normal(1, .04)
        if r.service == "AmazonEC2" and r.account == "111111111111" and d in (40, 41, 42): m *= 3.1   # injected anomaly
        if r.service == "AWSDataTransfer" and d == 70: m *= 6.5                                       # injected anomaly
        cost = max(r.base * m, .01)
        rows.append(dict(date=date, account=r.account, region=r.region, service=r.service, resource_id=r.resource_id,
                         usage_type=r.usage_type, qty=cost / r.rate, rate=r.rate, cost=cost, env=r.env, team=r.team, owner=r.owner))
df = pd.DataFrame(rows); df["line_item_id"] = [f"li-{i:07d}" for i in range(len(df))]
R.drop(columns=["base", "trend"]).to_csv(RAW / "resource_inventory.csv", index=False)

is_json = df.account.eq("333333333333")
csv_df, js_df = df[~is_json].copy(), df[is_json].copy()
fmts = ["%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"]
csv_out = pd.DataFrame({
    "line_item_id": csv_df.line_item_id, "usage_date": [d.strftime(random.choices(fmts, [.7, .15, .15])[0]) for d in csv_df.date],
    "account_id": csv_df.account, "region": csv_df.region.where(rng.random(len(csv_df)) > .01, csv_df.region.str.upper()),
    "service": csv_df.service, "resource_id": csv_df.resource_id, "usage_type": csv_df.usage_type,
    "usage_quantity": csv_df.qty.round(4), "unit_rate": csv_df.rate,
    "cost": csv_df.cost.round(4).map(lambda x: f"${x}" if random.random() < .08 else x),
    "tag_env": csv_df.env, "tag_team": csv_df.team, "tag_owner": csv_df.owner})
csv_out.loc[csv_out.sample(frac=.01, random_state=5).index, "cost"] = None            # recoverable via qty*rate
csv_out.loc[csv_out.sample(frac=.004, random_state=6).index, "resource_id"] = None   # unrecoverable
bad = csv_out.sample(n=12, random_state=7).index
csv_out.loc[bad, "cost"] = -abs(csv_out.loc[bad, "usage_quantity"] * 0.1)             # negative cost
csv_out = pd.concat([csv_out, csv_out.sample(n=150, random_state=8)]).sample(frac=1, random_state=9)  # duplicates
csv_out.to_csv(RAW / "billing_raw.csv", index=False)

with open(RAW / "billing_raw.jsonl", "w") as f:
    for i, r in enumerate(js_df.itertuples()):
        rec = {"identity/LineItemId": r.line_item_id, "lineItem/UsageStartDate": r.date.strftime("%Y-%m-%dT00:00:00Z"),
               "lineItem/UsageAccountId": r.account, "product/region": r.region, "product/servicecode": r.service,
               "lineItem/ResourceId": r.resource_id, "lineItem/UsageType": r.usage_type, "lineItem/UsageAmount": round(r.qty, 4),
               "pricing/publicOnDemandRate": r.rate, "lineItem/UnblendedCost": round(r.cost, 4),
               "resourceTags/user:env": r.env, "resourceTags/user:team": r.team, "resourceTags/user:owner": r.owner}
        if i % 700 == 0: rec["lineItem/LegalEntity"] = "Example Corp"   # schema drift
        f.write(json.dumps(rec) + "\n")

dd = pd.date_range(START, periods=DAYS)
pd.DataFrame({"date": dd, "api_requests": (2.2e6 * (1 + np.arange(DAYS) * .004) * np.where(dd.dayofweek >= 5, .8, 1) * rng.normal(1, .05, DAYS)).astype(int),
              "active_customers": (1800 * (1 + np.arange(DAYS) * .003) * rng.normal(1, .02, DAYS)).astype(int),
              "processing_hours": (950 * rng.normal(1, .06, DAYS)).round(1)}).to_csv(RAW / "app_metrics.csv", index=False)
pods = pd.DataFrame({"namespace": random.choices(["checkout", "search", "ml-serving", "etl", "web"], k=60),
                     "pod": [f"pod-{i:03d}" for i in range(60)], "node": [f"node-{random.randint(1,8)}" for _ in range(60)]})
pods["cpu_request"] = rng.choice([.5, 1, 2, 4], 60); pods["cpu_p95_used"] = (pods.cpu_request * rng.uniform(.12, .95, 60)).round(3)
pods["mem_request_gb"] = rng.choice([1, 2, 4, 8, 16], 60); pods["mem_p95_used_gb"] = (pods.mem_request_gb * rng.uniform(.15, .9, 60)).round(2)
pods.to_csv(RAW / "k8s_pods.csv", index=False)
pd.DataFrame({"bucket": [f"bucket-{i:02d}" for i in range(12)], "size_tb": rng.uniform(5, 120, 12).round(1),
              "pct_age_gt_30d": rng.uniform(.3, .9, 12).round(2), "pct_age_gt_90d": rng.uniform(.1, .6, 12).round(2),
              "pct_age_gt_365d": rng.uniform(.02, .3, 12).round(2), "monthly_get_pct": rng.uniform(.001, .3, 12).round(3)}).to_csv(RAW / "s3_buckets.csv", index=False)
print(f"CSV rows={len(csv_out):,} JSONL rows={len(js_df):,} resources={len(R)} true_total_cost=${df.cost.sum():,.2f}")
