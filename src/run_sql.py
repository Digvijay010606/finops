"""Run every '-- Q<n>: name' block of a .sql file against the warehouse and export CSVs. Usage: python src/run_sql.py sql/02_analytics.sql"""
import re, sqlite3, sys
from pathlib import Path
import pandas as pd

sqlfile = Path(sys.argv[1] if len(sys.argv) > 1 else "sql/02_analytics.sql"); out = Path("reports/query_output"); out.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect("data/processed/warehouse.db")
for m in re.finditer(r"-- (Q\d+): (\w+)\n(.*?)(?=\n-- Q\d+:|\Z)", sqlfile.read_text(), re.S):
    qid, name, sql = m.groups(); df = pd.read_sql(sql, con); df.to_csv(out / f"{qid}_{name}.csv", index=False)
    print(f"{qid} {name}: {len(df)} rows"); print(df.head(4).to_string(index=False)); print()
