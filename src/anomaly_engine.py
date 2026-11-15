"""DAY 12: Cost anomaly detection (rolling median/MAD modified z-score + classic z-score) with webhook alerting.
Set WEBHOOK_URL to POST alerts to Slack/Teams; otherwise alerts are written to reports/alerts.jsonl (dry run).
Run: python src/anomaly_engine.py"""
import json, os, sqlite3, urllib.request
from pathlib import Path
import numpy as np, pandas as pd

WINDOW, Z_THRESHOLD, MIN_DAILY_COST, MIN_DELTA = 14, 3.5, 50.0, 100.0

def detect(series: pd.Series) -> pd.DataFrame:
    base = series.shift(1)                                   # baseline uses only PAST days
    med = base.rolling(WINDOW, min_periods=7).median()
    mad = base.rolling(WINDOW, min_periods=7).apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True).clip(lower=series.mean() * .01)
    mean, std = base.rolling(WINDOW, min_periods=7).mean(), base.rolling(WINDOW, min_periods=7).std()
    out = pd.DataFrame({"cost": series, "baseline": med, "mod_z": 0.6745 * (series - med) / mad, "classic_z": (series - mean) / std})
    out["delta"] = out.cost - out.baseline
    out["is_anomaly"] = (out.mod_z.abs() > Z_THRESHOLD) & (out.cost > MIN_DAILY_COST) & (out.delta > MIN_DELTA)
    return out

def send_alert(a: dict):
    url = os.getenv("WEBHOOK_URL"); payload = {"text": f":rotating_light: Cost anomaly [{a['scope']}] {a['date']}: ${a['cost']:,.0f} vs baseline ${a['baseline']:,.0f} (z={a['mod_z']:.1f})", **a}
    if url:
        req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"}); urllib.request.urlopen(req, timeout=10)
    else:
        with open("reports/alerts.jsonl", "a") as f: f.write(json.dumps(payload) + "\n")

def main():
    Path("reports/alerts.jsonl").unlink(missing_ok=True)
    con = sqlite3.connect("data/processed/warehouse.db")
    df = pd.read_sql("""SELECT d.full_date date, s.service_code, ac.account_name, SUM(f.unblended_cost) cost FROM fact_usage_cost f
        JOIN dim_date d USING(date_key) JOIN dim_service s USING(service_key) JOIN dim_account ac USING(account_key) GROUP BY 1,2,3""", con)
    found = []
    for (svc, acct), g in df.groupby(["service_code", "account_name"]):
        r = detect(g.set_index("date").cost)
        for date, row in r[r.is_anomaly].iterrows():
            found.append(dict(scope=f"{svc}/{acct}", date=date, cost=round(row.cost, 2), baseline=round(row.baseline, 2), mod_z=round(row.mod_z, 1), classic_z=round(row.classic_z, 1), delta=round(row.delta, 2)))
    found = sorted(found, key=lambda a: -a["delta"]); [send_alert(a) for a in found]
    pd.DataFrame(found).to_csv("reports/anomalies_detected.csv", index=False)
    print(f"{len(found)} anomalies flagged"); print(pd.DataFrame(found).head(12).to_string(index=False))

if __name__ == "__main__":
    main()
