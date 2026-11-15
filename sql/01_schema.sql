-- DAY 01: Star schema for cloud usage & billing (SQLite dialect; portable to Postgres/Snowflake with type tweaks)
PRAGMA foreign_keys = ON;
DROP TABLE IF EXISTS fact_usage_cost; DROP TABLE IF EXISTS dim_resource; DROP TABLE IF EXISTS dim_tag;
DROP TABLE IF EXISTS dim_service; DROP TABLE IF EXISTS dim_region; DROP TABLE IF EXISTS dim_account; DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS quarantine_billing;

CREATE TABLE dim_date (date_key INTEGER PRIMARY KEY, full_date TEXT NOT NULL UNIQUE, year INTEGER, month INTEGER,
                       day INTEGER, day_of_week INTEGER, is_weekend INTEGER, year_month TEXT);
CREATE TABLE dim_account (account_key INTEGER PRIMARY KEY, account_id TEXT NOT NULL UNIQUE, account_name TEXT);
CREATE TABLE dim_region  (region_key INTEGER PRIMARY KEY, region_code TEXT NOT NULL UNIQUE, geo TEXT);
CREATE TABLE dim_service (service_key INTEGER PRIMARY KEY, service_code TEXT NOT NULL UNIQUE,
                          cost_category TEXT NOT NULL CHECK (cost_category IN ('Compute','Storage','Networking','Managed Services')));
CREATE TABLE dim_tag     (tag_key INTEGER PRIMARY KEY, env TEXT NOT NULL, team TEXT NOT NULL, owner TEXT NOT NULL,
                          UNIQUE (env, team, owner));
CREATE TABLE dim_resource(resource_key INTEGER PRIMARY KEY, resource_id TEXT NOT NULL UNIQUE, usage_type TEXT, instance_type TEXT);

CREATE TABLE fact_usage_cost (
    line_item_id   TEXT PRIMARY KEY,
    date_key       INTEGER NOT NULL REFERENCES dim_date(date_key),
    account_key    INTEGER NOT NULL REFERENCES dim_account(account_key),
    region_key     INTEGER NOT NULL REFERENCES dim_region(region_key),
    service_key    INTEGER NOT NULL REFERENCES dim_service(service_key),
    resource_key   INTEGER NOT NULL REFERENCES dim_resource(resource_key),
    tag_key        INTEGER NOT NULL REFERENCES dim_tag(tag_key),
    usage_quantity REAL NOT NULL,
    unit_rate      REAL,
    unblended_cost REAL NOT NULL CHECK (unblended_cost >= 0),
    cost_imputed   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE quarantine_billing (line_item_id TEXT, reason TEXT, usage_date TEXT, account_id TEXT, service TEXT,
                                 resource_id TEXT, cost REAL, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP);
