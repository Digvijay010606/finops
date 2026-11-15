-- DAY 10 (Snowflake): clustering key on date + service; verify with SYSTEM$CLUSTERING_INFORMATION.
CREATE OR REPLACE TABLE finops.public.fact_usage_cost (
  line_item_id STRING NOT NULL, usage_date DATE NOT NULL, account_id STRING, region STRING, service STRING,
  resource_id STRING, env STRING, team STRING, owner STRING, usage_quantity NUMBER(18,4), unblended_cost NUMBER(18,4))
CLUSTER BY (usage_date, service);
SELECT SYSTEM$CLUSTERING_INFORMATION('finops.public.fact_usage_cost', '(usage_date, service)');
