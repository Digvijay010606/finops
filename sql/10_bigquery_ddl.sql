-- DAY 10 (BigQuery): partitioned + clustered fact table. Replace `finops` with your dataset.
CREATE TABLE IF NOT EXISTS finops.fact_usage_cost (
  line_item_id STRING NOT NULL, usage_date DATE NOT NULL, account_id STRING, region STRING, service STRING,
  resource_id STRING, env STRING, team STRING, owner STRING, usage_quantity NUMERIC, unblended_cost NUMERIC)
PARTITION BY DATE_TRUNC(usage_date, MONTH)          -- prunes whole months; cheaper scans
CLUSTER BY service, account_id, resource_id         -- co-locates rows for typical filters
OPTIONS (partition_expiration_days = 1095, require_partition_filter = TRUE);
