"""Load validated data into the star schema (SQLite warehouse). Run: python src/load_warehouse.py"""
import sqlite3
from pathlib import Path
import pandas as pd

P = Path("data/processed"); DB = P / "warehouse.db"
CATEGORY = {"AmazonEC2": "Compute", "AWSLambda": "Compute", "AmazonEKS": "Compute", "AmazonS3": "Storage", "AmazonEBS": "Storage",
            "AmazonCloudFront": "Networking", "AWSDataTransfer": "Networking", "AmazonRDS": "Managed Services",
            "AmazonDynamoDB": "Managed Services", "AmazonRedshift": "Managed Services", "AmazonCloudWatch": "Managed Services"}
ACCT = {"111111111111": "prod", "222222222222": "staging", "333333333333": "data-platform", "444444444444": "dev-sandbox"}
GEO = {"us-east-1": "NA", "us-west-2": "NA", "eu-west-1": "EU", "ap-south-1": "APAC"}

def main():
    DB.unlink(missing_ok=True); con = sqlite3.connect(DB); con.executescript(Path("sql/01_schema.sql").read_text())
    f = pd.read_csv(P / "billing_valid.csv", dtype={"account_id": str})
    d = pd.to_datetime(sorted(f.usage_date.unique()))
    con.executemany("INSERT INTO dim_date VALUES (?,?,?,?,?,?,?,?)", [(int(x.strftime("%Y%m%d")), x.strftime("%Y-%m-%d"), x.year, x.month, x.day, x.dayofweek, int(x.dayofweek >= 5), x.strftime("%Y-%m")) for x in d])
    con.executemany("INSERT INTO dim_account(account_id,account_name) VALUES (?,?)", ACCT.items())
    con.executemany("INSERT INTO dim_region(region_code,geo) VALUES (?,?)", GEO.items())
    con.executemany("INSERT INTO dim_service(service_code,cost_category) VALUES (?,?)", CATEGORY.items())
    tags = f[["tag_env", "tag_team", "tag_owner"]].drop_duplicates(); con.executemany("INSERT INTO dim_tag(env,team,owner) VALUES (?,?,?)", tags.values.tolist())
    res = f[["resource_id", "usage_type"]].drop_duplicates("resource_id"); res["instance_type"] = res.usage_type.str.extract(r"BoxUsage:(.*)")[0]
    con.executemany("INSERT INTO dim_resource(resource_id,usage_type,instance_type) VALUES (?,?,?)", res[["resource_id", "usage_type", "instance_type"]].values.tolist())
    m = lambda t, k, c: dict(con.execute(f"SELECT {c},{k} FROM {t}").fetchall())
    acc, reg, svc, rs = m("dim_account", "account_key", "account_id"), m("dim_region", "region_key", "region_code"), m("dim_service", "service_key", "service_code"), m("dim_resource", "resource_key", "resource_id")
    tg = {(a, b, c): k for k, a, b, c in con.execute("SELECT tag_key,env,team,owner FROM dim_tag")}
    rows = [(r.line_item_id, int(r.usage_date.replace("-", "")), acc[r.account_id], reg[r.region], svc[r.service], rs[r.resource_id],
             tg[(r.tag_env, r.tag_team, r.tag_owner)], r.usage_quantity, r.unit_rate, r.cost, r.cost_imputed) for r in f.itertuples()]
    con.executemany("INSERT INTO fact_usage_cost VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    q = pd.read_csv(P / "quarantine.csv", dtype={"account_id": str})
    con.executemany("INSERT INTO quarantine_billing(line_item_id,reason,usage_date,account_id,service,resource_id,cost) VALUES (?,?,?,?,?,?,?)",
                    q[["line_item_id", "reason", "usage_date", "account_id", "service", "resource_id", "cost"]].where(q.notna(), None).values.tolist())
    con.commit(); print("fact rows:", con.execute("SELECT COUNT(*) FROM fact_usage_cost").fetchone()[0], "| quarantine rows:", con.execute("SELECT COUNT(*) FROM quarantine_billing").fetchone()[0])

if __name__ == "__main__":
    main()
