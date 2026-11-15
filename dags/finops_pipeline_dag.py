"""DAY 15: Daily FinOps pipeline - ingest -> validate -> load -> reconcile -> (anomaly alerts | unit economics) -> audit report.
Deploy by mounting the repo at /opt/finops (or set FINOPS_HOME)."""
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

HOME = os.getenv("FINOPS_HOME", "/opt/finops")
default_args = {"owner": "finops", "retries": 2, "retry_delay": timedelta(minutes=5), "email_on_failure": False}

def py(script): return f"cd {HOME} && python src/{script}"

with DAG("finops_pipeline", default_args=default_args, start_date=datetime(2026, 8, 1), schedule="0 2 * * *",
         catchup=False, max_active_runs=1, tags=["finops"]) as dag:
    ingest = BashOperator(task_id="ingest_billing", bash_command=py("ingest_billing.py"))
    validate = BashOperator(task_id="validate_quality", bash_command=py("validate.py"))     # fails the DAG on unexpected errors; bad rows quarantined
    load = BashOperator(task_id="load_warehouse", bash_command=py("load_warehouse.py"))
    reconcile = BashOperator(task_id="reconcile", bash_command=py("reconcile.py"))          # non-zero exit blocks downstream if checks fail
    anomaly = BashOperator(task_id="anomaly_alerts", bash_command=py("anomaly_engine.py"), env={"WEBHOOK_URL": os.getenv("WEBHOOK_URL", "")}, append_env=True)
    unit = BashOperator(task_id="unit_economics", bash_command=py("day08_unit_economics.py"))
    audit = BashOperator(task_id="optimisation_audit", bash_command=py("day14_audit.py"))
    ingest >> validate >> load >> reconcile >> [anomaly, unit] >> audit
