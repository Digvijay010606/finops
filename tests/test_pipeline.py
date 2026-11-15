"""Unit tests for core logic. Run: python -m pytest -q  (or: python tests/test_pipeline.py)"""
import sys; sys.path.insert(0, "src")
import pandas as pd
from ingest_billing import parse_dates
from anomaly_engine import detect

def test_parse_dates_mixed_formats():
    s = pd.Series(["2026-08-05", "05/08/2026", "Aug 05, 2026", "2026-08-05T00:00:00Z"])
    assert parse_dates(s).dt.strftime("%Y-%m-%d").tolist() == ["2026-08-05"] * 4

def test_anomaly_detects_spike_and_ignores_noise():
    s = pd.Series([1000.0 + (i % 3) * 10 for i in range(30)]); s.iloc[25] = 5000.0
    r = detect(s); assert r.is_anomaly.iloc[25] and r.is_anomaly.sum() == 1

def test_reconciliation_report_passes():
    assert "ALL CHECKS PASSED" in open("reports/reconciliation.txt").read()

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("PASS", n)
