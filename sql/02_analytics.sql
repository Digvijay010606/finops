-- DAY 02: 8 analytical queries (window functions, CTEs, aggregation). Each block starts with "-- Q<n>: name".
-- Q1: daily_cost_7d_moving_avg
SELECT d.full_date, ROUND(SUM(f.unblended_cost),2) AS daily_cost,
       ROUND(AVG(SUM(f.unblended_cost)) OVER (ORDER BY d.full_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),2) AS ma_7d
FROM fact_usage_cost f JOIN dim_date d USING(date_key) GROUP BY d.full_date ORDER BY d.full_date;

-- Q2: day_over_day_change_lag
WITH daily AS (SELECT d.full_date, SUM(f.unblended_cost) AS cost FROM fact_usage_cost f JOIN dim_date d USING(date_key) GROUP BY d.full_date)
SELECT full_date, ROUND(cost,2) AS cost, ROUND(LAG(cost) OVER (ORDER BY full_date),2) AS prev_day,
       ROUND(100.0*(cost-LAG(cost) OVER (ORDER BY full_date))/LAG(cost) OVER (ORDER BY full_date),2) AS pct_change
FROM daily ORDER BY ABS(pct_change) DESC NULLS LAST LIMIT 15;

-- Q3: service_rank_per_month
WITH m AS (SELECT d.year_month, s.service_code, s.cost_category, SUM(f.unblended_cost) AS cost
           FROM fact_usage_cost f JOIN dim_date d USING(date_key) JOIN dim_service s USING(service_key) GROUP BY 1,2,3)
SELECT year_month, RANK() OVER (PARTITION BY year_month ORDER BY cost DESC) AS rnk, service_code, cost_category, ROUND(cost,2) AS cost
FROM m ORDER BY year_month, rnk;

-- Q4: top_resources_pareto
WITH r AS (SELECT rs.resource_id, s.service_code, SUM(f.unblended_cost) AS cost FROM fact_usage_cost f
           JOIN dim_resource rs USING(resource_key) JOIN dim_service s USING(service_key) GROUP BY 1,2)
SELECT resource_id, service_code, ROUND(cost,2) AS cost,
       ROUND(100.0*SUM(cost) OVER (ORDER BY cost DESC)/SUM(cost) OVER (),2) AS cumulative_pct
FROM r ORDER BY cost DESC LIMIT 20;

-- Q5: weekly_cost_by_category
SELECT strftime('%Y-W%W', d.full_date) AS week, s.cost_category, ROUND(SUM(f.unblended_cost),2) AS cost,
       ROUND(100.0*SUM(f.unblended_cost)/SUM(SUM(f.unblended_cost)) OVER (PARTITION BY strftime('%Y-W%W', d.full_date)),1) AS pct_of_week
FROM fact_usage_cost f JOIN dim_date d USING(date_key) JOIN dim_service s USING(service_key) GROUP BY 1,2 ORDER BY 1,2;

-- Q6: month_to_date_running_total_per_account
WITH a AS (SELECT d.year_month, d.full_date, ac.account_name, SUM(f.unblended_cost) AS cost
           FROM fact_usage_cost f JOIN dim_date d USING(date_key) JOIN dim_account ac USING(account_key) GROUP BY 1,2,3)
SELECT * FROM (SELECT year_month, full_date, account_name, ROUND(cost,2) AS daily_cost,
       ROUND(SUM(cost) OVER (PARTITION BY account_name, year_month ORDER BY full_date),2) AS mtd_cost FROM a)
WHERE full_date IN ('2026-08-15','2026-08-31','2026-09-15','2026-09-30','2026-10-15','2026-10-29') ORDER BY account_name, full_date;

-- Q7: week_over_week_growth_by_service
WITH w AS (SELECT s.service_code, strftime('%Y-W%W', d.full_date) AS wk, SUM(f.unblended_cost) AS cost
           FROM fact_usage_cost f JOIN dim_date d USING(date_key) JOIN dim_service s USING(service_key) GROUP BY 1,2
           HAVING COUNT(DISTINCT d.full_date) = 7)  -- complete weeks only
SELECT service_code, wk, ROUND(cost,2) AS cost, ROUND(100.0*(cost-LAG(cost) OVER (PARTITION BY service_code ORDER BY wk))/LAG(cost) OVER (PARTITION BY service_code ORDER BY wk),1) AS wow_pct
FROM w ORDER BY wow_pct DESC NULLS LAST LIMIT 15;

-- Q8: resources_with_rising_cost_last14d_vs_prior14d
WITH cur AS (SELECT resource_key, SUM(unblended_cost) c FROM fact_usage_cost WHERE date_key BETWEEN 20261016 AND 20261029 GROUP BY 1),
     prv AS (SELECT resource_key, SUM(unblended_cost) p FROM fact_usage_cost WHERE date_key BETWEEN 20261002 AND 20261015 GROUP BY 1)
SELECT rs.resource_id, ROUND(p,2) AS prior_14d, ROUND(c,2) AS last_14d, ROUND(100.0*(c-p)/p,1) AS growth_pct,
       RANK() OVER (ORDER BY (c-p)/p DESC) AS growth_rank
FROM cur JOIN prv USING(resource_key) JOIN dim_resource rs USING(resource_key) ORDER BY growth_rank LIMIT 10;
