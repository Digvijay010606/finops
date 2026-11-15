-- DAY 16: asset register + monthly straight-line depreciation / amortisation view
DROP VIEW IF EXISTS vw_monthly_depreciation; DROP TABLE IF EXISTS asset_register;
CREATE TABLE asset_register (asset_id TEXT PRIMARY KEY, asset_name TEXT, category TEXT, purchase_date TEXT, cost REAL, salvage_value REAL, useful_life_months INTEGER);
INSERT INTO asset_register VALUES
 ('SRV-001','Dell R750 compute server #1','Server Hardware','2026-01-15',9500,500,48),('SRV-002','Dell R750 compute server #2','Server Hardware','2026-01-15',9500,500,48),
 ('GPU-001','8x GPU training server','Server Hardware','2026-03-10',72000,6000,36),('NAS-001','All-flash storage array','Storage Hardware','2026-02-01',28000,2000,60),
 ('NET-001','Core switch + firewall','Network Hardware','2026-02-20',14000,1000,60),
 ('SW-001','FinOps platform build (capitalised dev)','Capitalised Software','2026-04-01',45000,0,36),('SW-002','Data pipeline framework (capitalised dev)','Capitalised Software','2026-07-01',30000,0,36);
CREATE VIEW vw_monthly_depreciation AS
WITH RECURSIVE months(m) AS (SELECT '2026-01-01' UNION ALL SELECT date(m,'+1 month') FROM months WHERE m < '2028-12-01')
SELECT strftime('%Y-%m', m.m) AS period, a.asset_id, a.category, ROUND((a.cost - a.salvage_value) / a.useful_life_months, 2) AS depreciation,
       ROUND(a.cost - (a.cost - a.salvage_value) / a.useful_life_months * ((CAST(strftime('%Y',m.m) AS INT)-CAST(strftime('%Y',a.purchase_date) AS INT))*12 + CAST(strftime('%m',m.m) AS INT)-CAST(strftime('%m',a.purchase_date) AS INT) + 1), 2) AS net_book_value
FROM months m JOIN asset_register a ON m.m >= date(a.purchase_date,'start of month')
 AND m.m < date(a.purchase_date,'start of month','+'||a.useful_life_months||' months');
