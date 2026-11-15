"""DAY 11: Rate-optimisation model (On-Demand vs RI vs Savings Plans vs Spot) + Excel workbook with live formulas.
DISCOUNT RATES ARE ILLUSTRATIVE ASSUMPTIONS - replace with current AWS pricing for your instance families/regions. Run: python src/day11_rate_optimization.py"""
import sqlite3
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
con = sqlite3.connect("data/processed/warehouse.db")
d = pd.read_sql("""SELECT s.service_code, t.env, SUM(f.unblended_cost) c30 FROM fact_usage_cost f JOIN dim_service s USING(service_key) JOIN dim_tag t USING(tag_key)
                   WHERE f.date_key >= 20260930 AND s.service_code IN ('AmazonEC2','AmazonRDS','AmazonEKS','AmazonRedshift') GROUP BY 1,2""", con)
ann = 365 / 30; eligible = d.c30.sum() * ann
nonprod_ec2 = d[(d.service_code == "AmazonEC2") & (d.env.isin(["dev", "staging", "untagged"]))].c30.sum() * ann
A = dict(coverage=.70, ri1=.35, ri3=.55, sp1=.27, sp3=.46, spot=.65, spot_share=.70)
sc = {"On-Demand (baseline)": 0, "1-yr Reserved Instance": A["coverage"] * A["ri1"] * eligible, "3-yr Reserved Instance": A["coverage"] * A["ri3"] * eligible,
      "1-yr Compute Savings Plan": A["coverage"] * A["sp1"] * eligible, "3-yr Compute Savings Plan": A["coverage"] * A["sp3"] * eligible,
      "Spot for non-prod EC2 only": nonprod_ec2 * A["spot_share"] * A["spot"]}
sc["RECOMMENDED: 1-yr SP + Spot (non-prod)"] = sc["1-yr Compute Savings Plan"] + sc["Spot for non-prod EC2 only"]
res = pd.DataFrame({"scenario": list(sc), "annual_savings": [round(v) for v in sc.values()]}); res["pct_of_eligible"] = (100 * res.annual_savings / eligible).round(1)
res.to_csv("reports/rate_optimization.csv", index=False); print(f"Eligible annual run-rate: ${eligible:,.0f} | non-prod EC2: ${nonprod_ec2:,.0f}\n{res.to_string(index=False)}")
wb = Workbook(); a = wb.active; a.title = "Assumptions"; h = Font(bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="2E5BBA")
rows = [("Eligible annual on-demand spend (EC2+RDS+EKS+Redshift, 30d run-rate x 12.17)", round(eligible, 2)), ("Non-prod EC2 annual spend (dev/staging/untagged)", round(nonprod_ec2, 2)),
        ("Commitment coverage of eligible spend", A["coverage"]), ("1-yr RI discount", A["ri1"]), ("3-yr RI discount", A["ri3"]), ("1-yr Savings Plan discount", A["sp1"]),
        ("3-yr Savings Plan discount", A["sp3"]), ("Spot discount", A["spot"]), ("Share of non-prod EC2 that is interruption-tolerant", A["spot_share"])]
a.append(["Assumption (edit blue cells)", "Value"]); [a.append(r) for r in rows]
for c in a[1]: c.font, c.fill = h, fill
for r in range(2, 11): a.cell(r, 2).font = Font(color="0000FF")
a.column_dimensions["A"].width = 78; a.column_dimensions["B"].width = 18
s = wb.create_sheet("Scenarios"); s.append(["Scenario", "Annual savings ($)", "% of eligible spend", "Effective annual cost ($)"])
f = ["0", "=Assumptions!B4*Assumptions!B5*Assumptions!B2", "=Assumptions!B4*Assumptions!B6*Assumptions!B2", "=Assumptions!B4*Assumptions!B7*Assumptions!B2",
     "=Assumptions!B4*Assumptions!B8*Assumptions!B2", "=Assumptions!B3*Assumptions!B10*Assumptions!B9", "=B5+B7"]
for i, (name, formula) in enumerate(zip(sc, f), start=2): s.append([name, formula if formula != "0" else 0, f"=B{i}/Assumptions!$B$2", f"=Assumptions!$B$2-B{i}"])
for c in s[1]: c.font, c.fill = h, fill
for r in range(2, 9): s.cell(r, 2).number_format = s.cell(r, 4).number_format = '#,##0'; s.cell(r, 3).number_format = '0.0%'
s.column_dimensions["A"].width = 42; [setattr(s.column_dimensions[c], "width", 24) for c in "BCD"]
wb.save("outputs/rate_optimization_model.xlsx")
