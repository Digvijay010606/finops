"""DAY 18: Executive FinOps dashboard (Streamlit). Run: pip install streamlit && streamlit run dashboard/app.py"""
import sqlite3
import pandas as pd, streamlit as st
st.set_page_config(page_title="FinOps Executive View", layout="wide")
con = sqlite3.connect("data/processed/warehouse.db")
df = pd.read_sql("""SELECT d.full_date date, d.year_month, ac.account_name account, s.service_code service, s.cost_category category, t.team, f.unblended_cost cost
                    FROM fact_usage_cost f JOIN dim_date d USING(date_key) JOIN dim_account ac USING(account_key) JOIN dim_service s USING(service_key) JOIN dim_tag t USING(tag_key)""", con)
st.sidebar.header("Filters"); accts = st.sidebar.multiselect("Account", sorted(df.account.unique()), default=sorted(df.account.unique()))
cats = st.sidebar.multiselect("Category", sorted(df.category.unique()), default=sorted(df.category.unique())); f = df[df.account.isin(accts) & df.category.isin(cats)]
unit = pd.read_csv("reports/unit_economics_daily.csv"); anomalies = pd.read_csv("reports/anomalies_detected.csv")
c1, c2, c3, c4 = st.columns(4); c1.metric("Total spend (90d)", f"${f.cost.sum():,.0f}"); c2.metric("Avg daily", f"${f.groupby('date').cost.sum().mean():,.0f}")
c3.metric("Cost / 1k requests (latest)", f"${unit.cost_per_1k_requests.iloc[-7:].mean():.2f}"); c4.metric("Untagged team spend", f"{100*f[f.team=='untagged'].cost.sum()/f.cost.sum():.1f}%")
st.subheader("Daily spend"); st.line_chart(f.groupby("date").cost.sum())
l, r = st.columns(2); l.subheader("By service"); l.bar_chart(f.groupby("service").cost.sum().sort_values()); r.subheader("By category"); r.bar_chart(f.groupby("category").cost.sum())
st.subheader("Unit cost per 1k requests"); st.line_chart(unit.set_index("date").cost_per_1k_requests)
st.subheader("Detected anomalies"); st.dataframe(anomalies)
