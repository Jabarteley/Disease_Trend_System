import os
import sys
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_trend_reports, load_kpis, auth_gate, page_header  # noqa: E402

auth_gate()

page_header(":material/timeline: Trends overview", "Case counts over time, filterable by disease.")

df = load_trend_reports()
if df.empty:
    st.info("No trend data yet — open Upload first.", icon=":material/upload_file:")
    st.stop()

kpis = load_kpis()
with st.container(horizontal=True):
    st.metric("Total records", f"{kpis['total']:,}", border=True)
    for disease, count in sorted(kpis["by_disease"].items(), key=lambda kv: -kv[1]):
        st.metric(disease.title(), f"{count:,}", border=True)

st.divider()

diseases = sorted(df["disease_code"].unique())
selected = st.pills("Disease", diseases, selection_mode="multi", default=diseases)
filtered = df[df["disease_code"].isin(selected)] if selected else df

with st.container(border=True):
    st.subheader("Case counts over time")
    monthly = (
        filtered.groupby(["period", "disease_code"], as_index=False)["trend_value"]
        .sum()
        .pivot(index="period", columns="disease_code", values="trend_value")
        .fillna(0)
    )
    st.line_chart(monthly, alt="Monthly case counts by disease")

with st.container(border=True):
    st.subheader("Totals by disease")
    totals = (
        filtered.groupby("disease_code", as_index=False)["trend_value"]
        .sum()
        .sort_values("trend_value", ascending=False)
        .rename(columns={"disease_code": "Disease", "trend_value": "Total cases"})
    )
    st.dataframe(totals, hide_index=True, width="stretch", alt="Total cases by disease")
