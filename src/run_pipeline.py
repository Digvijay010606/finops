"""Local runner that mirrors dags/finops_pipeline_dag.py (Airflow is not required). Run: python src/run_pipeline.py"""
import subprocess, sys, time
from pathlib import Path
STEPS = [("ingest_billing", "ingest_billing.py"), ("validate_quality", "validate.py"), ("load_warehouse", "load_warehouse.py"), ("reconcile", "reconcile.py"),
         ("anomaly_alerts", "anomaly_engine.py"), ("unit_economics", "day08_unit_economics.py"), ("optimisation_audit", "day14_audit.py")]
log = []
for name, script in STEPS:
    t = time.time(); r = subprocess.run([sys.executable, f"src/{script}"], capture_output=True, text=True); dt = time.time() - t
    status = "SUCCESS" if r.returncode == 0 else "FAILED"; log.append(f"{status:8s} {name:20s} {dt:6.1f}s"); print(log[-1])
    if r.returncode: print(r.stderr[-500:]); break
Path("reports/pipeline_run.log").write_text("\n".join(log) + "\n")
