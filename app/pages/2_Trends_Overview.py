import os
import sys
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_trend_reports  # noqa: E402

st.title("Trends Overview")

df = load_trend_reports()
if df.empty:
    st.warning("No trend data yet — go to the Upload page first.")
    st.stop()

diseases = sorted(df["disease_code"].unique())
selected = st.multiselect("Disease", diseases, default=diseases)
filtered = df[df["disease_code"].isin(selected)]

monthly = filtered.groupby(["period", "disease_code"], as_index=False)["trend_value"].sum()
fig = px.line(
    monthly, x="period", y="trend_value", color="disease_code", markers=True,
    labels={"period": "Month", "trend_value": "Case count", "disease_code": "Disease"},
    title="Case counts over time",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Totals by disease")
totals = filtered.groupby("disease_code", as_index=False)["trend_value"].sum().sort_values("trend_value", ascending=False)
st.dataframe(totals, use_container_width=True)
