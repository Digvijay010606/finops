"""DAY 05: Index benchmark on a 1.5M-row fact table (before/after). SQLite uses EXPLAIN QUERY PLAN (Postgres equivalent in sql/05_postgres_indexes.sql).
Run: python src/day05_index_benchmark.py"""
import sqlite3, statistics, time
from pathlib import Path
import numpy as np, pandas as pd

DB = Path("data/processed/bench.db"); DB.unlink(missing_ok=True); con = sqlite3.connect(DB); rng = np.random.default_rng(7); N = 1_500_000
dates = pd.date_range("2026-08-01", periods=90).strftime("%Y%m%d").astype(int).values
df = pd.DataFrame({"date_key": rng.choice(dates, N), "account_key": rng.integers(1, 5, N), "service_key": rng.integers(1, 12, N),
                   "resource_key": rng.integers(1, 5001, N), "cost": rng.gamma(2, 5, N).round(4)})
df.to_sql("fact_big", con, index=False)
QUERIES = {"A: one resource, one month": "SELECT SUM(cost) FROM fact_big WHERE resource_key=1234 AND date_key BETWEEN 20260901 AND 20260930",
           "B: service totals, 15-day window": "SELECT service_key, SUM(cost) FROM fact_big WHERE date_key BETWEEN 20261001 AND 20261015 GROUP BY service_key",
           "C: daily trend, account+service": "SELECT date_key, SUM(cost) FROM fact_big WHERE account_key=2 AND service_key=3 GROUP BY date_key"}
def bench():
    out = {}
    for name, q in QUERIES.items():
        plan = " | ".join(r[3] for r in con.execute("EXPLAIN QUERY PLAN " + q)); t = []
        for _ in range(5): s = time.perf_counter(); con.execute(q).fetchall(); t.append((time.perf_counter() - s) * 1000)
        out[name] = (plan, statistics.median(t))
    return out
before = bench()
con.executescript("""CREATE INDEX ix_date ON fact_big(date_key);
CREATE INDEX ix_res_date ON fact_big(resource_key, date_key);
CREATE INDEX ix_acct_svc_date_cost ON fact_big(account_key, service_key, date_key, cost);""")
mid = bench()          # stage 2: plain indexes (query B regresses: non-covering index forces a table lookup per row)
con.executescript("DROP INDEX ix_date; CREATE INDEX ix_date_svc_cost ON fact_big(date_key, service_key, cost);")   # stage 3: covering index
after = bench(); rows = []
for k in QUERIES: rows.append(dict(query=k, before_ms=round(before[k][1], 2), plain_index_ms=round(mid[k][1], 2), after_ms=round(after[k][1], 2), speedup=round(before[k][1] / after[k][1], 1), plan_before=before[k][0], plan_after=after[k][0]))
rep = pd.DataFrame(rows); rep.to_csv("reports/index_benchmark.csv", index=False); print(rep[["query", "before_ms", "plain_index_ms", "after_ms", "speedup"]].to_string(index=False)); print(); print(rep[["query","plan_after"]].to_string(index=False))
