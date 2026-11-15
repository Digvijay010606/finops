"""DAY 07: Source-to-target row-count + checksum reconciliation. Run: python src/reconcile.py"""
import hashlib, sqlite3
from pathlib import Path
import pandas as pd

P, R = Path("data/processed"), Path("data/raw")
src_rows = len(pd.read_csv(R / "billing_raw.csv", dtype=str)) + sum(1 for _ in open(R / "billing_raw.jsonl"))
clean = pd.read_csv(P / "billing_clean.csv"); valid = pd.read_csv(P / "billing_valid.csv"); quar = pd.read_csv(P / "quarantine.csv")
con = sqlite3.connect(P / "warehouse.db")
fact_n = con.execute("SELECT COUNT(*) FROM fact_usage_cost").fetchone()[0]; q_n = con.execute("SELECT COUNT(*) FROM quarantine_billing").fetchone()[0]
fact_cost = con.execute("SELECT ROUND(SUM(unblended_cost),2) FROM fact_usage_cost").fetchone()[0]
h = lambda ids: hashlib.md5("|".join(sorted(map(str, ids))).encode()).hexdigest()
fact_ids = [r[0] for r in con.execute("SELECT line_item_id FROM fact_usage_cost")]
checks = [("Source rows == cleaned rows", src_rows, len(clean)),
          ("Cleaned rows == valid + quarantined", len(clean), len(valid) + len(quar)),
          ("Valid rows == fact rows in DW", len(valid), fact_n),
          ("Quarantine file == quarantine table", len(quar), q_n),
          ("Valid cost sum == DW cost sum", round(valid.cost.sum(), 2), fact_cost),
          ("Cleaned cost == valid + quarantined cost", round(clean.cost.sum(), 2), round(valid.cost.sum() + quar.cost.fillna(0).sum(), 2)),
          ("MD5(line_item_ids) file vs DW", h(valid.line_item_id), h(fact_ids))]
lines = ["RECONCILIATION REPORT", "-" * 70]; ok = True
for name, a, b in checks:
    p = a == b; ok &= p; lines.append(f"[{'PASS' if p else 'FAIL'}] {name}: {a} vs {b}")
lines += ["-" * 70, "RESULT: " + ("ALL CHECKS PASSED - zero data loss" if ok else "MISMATCH FOUND")]
Path("reports").mkdir(exist_ok=True); Path("reports/reconciliation.txt").write_text("\n".join(lines)); print("\n".join(lines)); raise SystemExit(0 if ok else 1)
