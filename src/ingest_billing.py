"""DAY 03: Ingest + cleanse raw billing logs (CSV export + CUR-style JSON lines) into one tidy dataset.
Run: python src/ingest_billing.py"""
import json
from pathlib import Path
import pandas as pd

RAW, OUT = Path("data/raw"), Path("data/processed"); OUT.mkdir(parents=True, exist_ok=True)
STD_COLS = ["line_item_id", "usage_date", "account_id", "region", "service", "resource_id", "usage_type",
            "usage_quantity", "unit_rate", "cost", "tag_env", "tag_team", "tag_owner"]
JSON_MAP = {"identity/LineItemId": "line_item_id", "lineItem/UsageStartDate": "usage_date", "lineItem/UsageAccountId": "account_id",
            "product/region": "region", "product/servicecode": "service", "lineItem/ResourceId": "resource_id",
            "lineItem/UsageType": "usage_type", "lineItem/UsageAmount": "usage_quantity", "pricing/publicOnDemandRate": "unit_rate",
            "lineItem/UnblendedCost": "cost", "resourceTags/user:env": "tag_env", "resourceTags/user:team": "tag_team",
            "resourceTags/user:owner": "tag_owner"}
DATE_FORMATS = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%d/%m/%Y", "%b %d, %Y"]

def parse_dates(s: pd.Series) -> pd.Series:
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        mask = out.isna()
        out[mask] = pd.to_datetime(s[mask], format=fmt, errors="coerce")
    return out

def load_json(path: Path):
    recs, drift = [], set()
    with open(path) as f:
        for line in f:
            r = json.loads(line); drift |= set(r) - set(JSON_MAP)
            recs.append({JSON_MAP[k]: v for k, v in r.items() if k in JSON_MAP})
    return pd.DataFrame(recs), sorted(drift)

def main():
    csv = pd.read_csv(RAW / "billing_raw.csv", dtype=str); csv["source"] = "csv"
    js, drift = load_json(RAW / "billing_raw.jsonl"); js = js.astype({c: str for c in ("account_id",)}); js["source"] = "json"
    stats = {"rows_csv": len(csv), "rows_json": len(js), "schema_drift_columns": drift}
    df = pd.concat([csv, js.astype(object)], ignore_index=True)[STD_COLS + ["source"]]
    df["usage_date"] = parse_dates(df["usage_date"].astype(str))
    stats["unparseable_dates"] = int(df.usage_date.isna().sum())
    df["region"] = df.region.str.strip().str.lower()
    df["cost"] = pd.to_numeric(df.cost.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
    for c in ("usage_quantity", "unit_rate"): df[c] = pd.to_numeric(df[c], errors="coerce")
    miss = df.cost.isna() & df.usage_quantity.notna() & df.unit_rate.notna()
    df.loc[miss, "cost"] = (df.usage_quantity * df.unit_rate).round(4); df["cost_imputed"] = miss.astype(int)
    stats["cost_imputed_rows"] = int(miss.sum())
    for c in ("tag_env", "tag_team", "tag_owner"): df[c] = df[c].where(df[c].notna() & (df[c] != ""), "untagged")
    df["usage_date"] = df.usage_date.dt.strftime("%Y-%m-%d")
    df.to_csv(OUT / "billing_clean.csv", index=False)
    stats["rows_out"] = len(df); stats["total_cost"] = round(float(df.cost.sum()), 2)
    (OUT / "ingest_stats.json").write_text(json.dumps(stats, indent=2)); print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
