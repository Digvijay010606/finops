"""DAY 10: Local proxy benchmark for partition pruning + clustering (SQLite stands in for Snowflake/BigQuery, which need a cloud account).
Partitioning -> month tables; clustering key -> WITHOUT ROWID table whose primary key physically orders rows. Run: python src/day10_partition_clustering.py"""
import sqlite3, statistics, time
import pandas as pd
con = sqlite3.connect("data/processed/bench.db")
for t in ("fact_noidx", "fact_clustered", "part_2026_08", "part_2026_09", "part_2026_10"): con.execute(f"DROP TABLE IF EXISTS {t}")
con.execute("CREATE TABLE fact_noidx AS SELECT * FROM fact_big")
con.execute("CREATE TABLE fact_clustered (service_key INT, date_key INT, rid INT, account_key INT, resource_key INT, cost REAL, PRIMARY KEY (service_key, date_key, rid)) WITHOUT ROWID")
con.execute("INSERT INTO fact_clustered SELECT service_key, date_key, rowid, account_key, resource_key, cost FROM fact_big ORDER BY 1,2,3")
for ym, lo, hi in (("08", 20260801, 20260831), ("09", 20260901, 20260930), ("10", 20261001, 20261031)):
    con.execute(f"CREATE TABLE part_2026_{ym} AS SELECT * FROM fact_big WHERE date_key BETWEEN {lo} AND {hi}")
con.commit()
def t(sql, n=5):
    r = []
    for _ in range(n): s = time.perf_counter(); con.execute(sql).fetchall(); r.append((time.perf_counter() - s) * 1000)
    return round(statistics.median(r), 2)
rows = [("Partition pruning: Oct 1-15 service totals", t("SELECT service_key,SUM(cost) FROM fact_noidx WHERE date_key BETWEEN 20261001 AND 20261015 GROUP BY 1"),
                                                      t("SELECT service_key,SUM(cost) FROM part_2026_10 WHERE date_key BETWEEN 20261001 AND 20261015 GROUP BY 1")),
        ("Clustering key (service,date): svc=3, Oct", t("SELECT SUM(cost) FROM fact_noidx WHERE service_key=3 AND date_key BETWEEN 20261001 AND 20261031"),
                                                      t("SELECT SUM(cost) FROM fact_clustered WHERE service_key=3 AND date_key BETWEEN 20261001 AND 20261031"))]
df = pd.DataFrame(rows, columns=["scenario", "unoptimised_ms", "optimised_ms"]); df["reduction_pct"] = (100 * (1 - df.optimised_ms / df.unoptimised_ms)).round(1)
df.to_csv("reports/partition_clustering_benchmark.csv", index=False); print(df.to_string(index=False))
