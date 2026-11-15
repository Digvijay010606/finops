@echo off
python src\generate_data.py || goto err
python src\ingest_billing.py || goto err
python src\validate.py || goto err
python src\load_warehouse.py || goto err
python src\reconcile.py || goto err
python src\run_sql.py sql\02_analytics.sql || goto err
python src\day01_erd.py || goto err
python src\day04_cost_profile.py || goto err
python src\day05_index_benchmark.py || goto err
python src\day08_unit_economics.py || goto err
python src\audit_untagged.py || goto err
python src\day10_partition_clustering.py || goto err
python src\day11_rate_optimization.py || goto err
python src\anomaly_engine.py || goto err
python src\day13_k8s_rightsizing.py || goto err
python src\day19_storage_lifecycle.py || goto err
python src\day14_audit.py || goto err
python src\run_pipeline.py || goto err
python src\day16_depreciation.py || goto err
python src\day15_dag_graph.py || goto err
python src\day18_exec_dashboard.py || goto err
python src\day20_architecture.py || goto err
python tests\test_pipeline.py || goto err
python src\collect_facts.py || goto err
echo ALL DONE
goto :eof
:err
echo FAILED - see the message above