-- DAY 05 (PostgreSQL equivalent). Run EXPLAIN (ANALYZE, BUFFERS) before and after each index.
EXPLAIN (ANALYZE, BUFFERS) SELECT SUM(cost) FROM fact_usage_cost WHERE resource_key = 1234 AND date_key BETWEEN 20260901 AND 20260930;
CREATE INDEX CONCURRENTLY ix_fact_res_date ON fact_usage_cost (resource_key, date_key);          -- composite B-tree: equality col first, range col second
CREATE INDEX CONCURRENTLY ix_fact_acct_svc_date ON fact_usage_cost (account_key, service_key, date_key) INCLUDE (unblended_cost);  -- covering index
-- Partitioning strategy: RANGE by month on date_key (prunes 2 of 3 months for a 1-month query; makes retention = DROP PARTITION)
-- CREATE TABLE fact_usage_cost_p (...) PARTITION BY RANGE (date_key);
-- CREATE TABLE fact_usage_cost_2026_08 PARTITION OF fact_usage_cost_p FOR VALUES FROM (20260801) TO (20260901);
