"""DAY 16: Execute depreciation SQL view, export schedule, build Excel model with SLN formulas. Run: python src/day16_depreciation.py"""
import sqlite3
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
con = sqlite3.connect("data/processed/warehouse.db"); con.executescript(open("sql/16_depreciation.sql").read())
sched = pd.read_sql("SELECT * FROM vw_monthly_depreciation ORDER BY period, asset_id", con); sched.to_csv("reports/depreciation_schedule.csv", index=False)
m = pd.read_sql("SELECT period, category, SUM(depreciation) dep FROM vw_monthly_depreciation WHERE period IN ('2026-10','2026-11','2026-12') GROUP BY 1,2", con)
print(m.pivot(index="category", columns="period", values="dep").to_string()); print("Total Nov-2026:", round(m[m.period == "2026-11"].dep.sum(), 2))
reg = pd.read_sql("SELECT * FROM asset_register", con); wb = Workbook(); ws = wb.active; ws.title = "Asset Amortization"
ws.append(["Asset ID", "Name", "Category", "Purchase date", "Cost", "Salvage", "Life (months)", "Monthly depreciation", "Annual depreciation", "Months elapsed to 2026-12", "Accumulated", "Net book value 2026-12"])
for i, r in enumerate(reg.itertuples(), start=2):
    mo = f"=MIN(G{i},(2026-YEAR(D{i}))*12+12-MONTH(D{i})+1)"
    ws.append([r.asset_id, r.asset_name, r.category, pd.Timestamp(r.purchase_date).to_pydatetime(), r.cost, r.salvage_value, r.useful_life_months, f"=SLN(E{i},F{i},G{i})", f"=H{i}*12", mo, f"=H{i}*J{i}", f"=E{i}-K{i}"])
n = len(reg) + 1; ws.append(["TOTAL", "", "", "", f"=SUM(E2:E{n})", f"=SUM(F2:F{n})", "", f"=SUM(H2:H{n})", f"=SUM(I2:I{n})", "", f"=SUM(K2:K{n})", f"=SUM(L2:L{n})"])
for c in ws[1]: c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="2E5BBA")
for col, w in zip("ABCDEFGHIJKL", (10, 42, 22, 14, 12, 11, 12, 20, 18, 22, 14, 22)): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2): row[3].number_format = "yyyy-mm-dd"; [setattr(c, "number_format", "#,##0.00") for c in (row[4], row[5], row[7], row[8], row[10], row[11])]
for c in ws[n + 1]: c.font = Font(bold=True)
wb.save("outputs/asset_amortization_schedule.xlsx")
