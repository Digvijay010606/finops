"""DAY 06: Data-quality suite. Bad rows go to a quarantine file/table; good rows continue to the warehouse load.
Run: python src/validate.py"""
import json
from pathlib import Path
import pandas as pd

P = Path("data/processed"); df = pd.read_csv(P / "billing_clean.csv", dtype={"account_id": str})
VALID_ACCOUNTS = {"111111111111", "222222222222", "333333333333", "444444444444"}
VALID_REGIONS = {"us-east-1", "us-west-2", "eu-west-1", "ap-south-1"}
reasons = pd.Series("", index=df.index, dtype=object)
def flag(mask, label): reasons.loc[mask & (reasons == "")] = label   # first failing rule wins
flag(df.duplicated("line_item_id", keep="first"), "DUPLICATE_LINE_ITEM")
flag(df.resource_id.isna(), "NULL_RESOURCE_ID")
flag(df.usage_date.isna(), "NULL_DATE")
flag(df.cost.isna(), "NULL_COST")
flag(df.cost < 0, "NEGATIVE_COST")
flag(~df.account_id.isin(VALID_ACCOUNTS), "UNKNOWN_ACCOUNT")
flag(~df.region.isin(VALID_REGIONS), "UNKNOWN_REGION")
bad = reasons != ""
q = df[bad].assign(reason=reasons[bad]); good = df[~bad]
q.to_csv(P / "quarantine.csv", index=False); good.to_csv(P / "billing_valid.csv", index=False)
summary = q.reason.value_counts().to_dict()
sch = json.loads((P / "ingest_stats.json").read_text())
report = ["# Data Quality Report", f"Rows validated: {len(df):,}", f"Passed: {len(good):,}  Quarantined: {len(q):,} ({len(q)/len(df):.2%})", "",
          "| Rule | Rows |", "|---|---|"] + [f"| {k} | {v} |" for k, v in summary.items()] + \
         ["", f"Schema drift columns detected at ingest: {sch['schema_drift_columns']}",
          f"Costs imputed from qty x rate: {sch['cost_imputed_rows']}",
          f"Untagged env/team/owner rows: {int((good.tag_env=='untagged').sum())}/{int((good.tag_team=='untagged').sum())}/{int((good.tag_owner=='untagged').sum())}"]
Path("reports").mkdir(exist_ok=True); Path("reports/data_quality_report.md").write_text("\n".join(report)); print("\n".join(report))
