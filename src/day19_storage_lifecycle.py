"""DAY 19: Storage tiering model driven by object-age and access profile. Prices ($/GB-month) are illustrative us-east-1 list prices - verify before use. Run: python src/day19_storage_lifecycle.py"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
PR = dict(std=.023, ia=.0125, gl=.0036, da=.00099); HOT, WARM = .25, .10
b = pd.read_csv("data/raw/s3_buckets.csv"); b["gb"] = b.size_tb * 1024
a0, a30, a90, a365 = 1 - b.pct_age_gt_30d, b.pct_age_gt_30d - b.pct_age_gt_90d, b.pct_age_gt_90d - b.pct_age_gt_365d, b.pct_age_gt_365d
b["pattern"] = pd.cut(b.monthly_get_pct, [-1, WARM, HOT, 9], labels=["cold", "warm", "hot"])
b["cost_now"] = b.gb * PR["std"]
cold = b.gb * (a0 * PR["std"] + a30 * PR["ia"] + a90 * PR["gl"] + a365 * PR["da"])
warm = b.gb * (a0 * PR["std"] + (1 - a0) * PR["ia"]); b["cost_opt"] = cold.where(b.pattern == "cold", warm.where(b.pattern == "warm", b.cost_now))
b["saving"] = b.cost_now - b.cost_opt; b[["bucket", "size_tb", "pattern", "cost_now", "cost_opt", "saving"]].round(2).to_csv("reports/storage_lifecycle_model.csv", index=False)
print(b[["bucket", "size_tb", "pattern", "cost_now", "cost_opt", "saving"]].round(0).to_string(index=False))
print(f"\nMonthly: ${b.cost_now.sum():,.0f} -> ${b.cost_opt.sum():,.0f} | saving ${b.saving.sum():,.0f}/mo (${b.saving.sum()*12:,.0f}/yr, {100*b.saving.sum()/b.cost_now.sum():.1f}%)")
wb = Workbook(); ws = wb.active; ws.title = "Storage Model"; ws.append(["Price Std", PR["std"], "IA", PR["ia"], "Glacier", PR["gl"], "Deep Archive", PR["da"]])
ws.append([]); ws.append(["Bucket", "Size (GB)", "Pattern", "% <=30d", "% 30-90d", "% 90-365d", "% >365d", "Cost now", "Cost optimised", "Saving"])
for i, r in enumerate(b.itertuples(), start=4):
    p0, p1, p2, p3 = a0[r.Index], a30[r.Index], a90[r.Index], a365[r.Index]
    opt = {"cold": f"=B{i}*(D{i}*$B$1+E{i}*$D$1+F{i}*$F$1+G{i}*$H$1)", "warm": f"=B{i}*(D{i}*$B$1+(1-D{i})*$D$1)", "hot": f"=H{i}"}[r.pattern]
    ws.append([r.bucket, round(r.gb, 1), r.pattern, round(p0, 3), round(p1, 3), round(p2, 3), round(p3, 3), f"=B{i}*$B$1", opt, f"=H{i}-I{i}"])
e = len(b) + 3; ws.append(["TOTAL", f"=SUM(B4:B{e})", "", "", "", "", "", f"=SUM(H4:H{e})", f"=SUM(I4:I{e})", f"=SUM(J4:J{e})"])
for c in ws[3]: c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="2E5BBA")
for col in "ABCDEFGHIJ": ws.column_dimensions[col].width = 15
for row in ws.iter_rows(min_row=4): [setattr(c, "number_format", "#,##0") for c in (row[1], row[7], row[8], row[9])]
wb.save("outputs/storage_lifecycle_model.xlsx")
