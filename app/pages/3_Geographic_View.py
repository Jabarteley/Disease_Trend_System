import os
import sys
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_trend_reports  # noqa: E402

st.title("Geographic View")

df = load_trend_reports()
if df.empty:
    st.warning("No trend data yet — go to the Upload page first.")
    st.stop()

diseases = sorted(df["disease_code"].unique())
disease = st.selectbox("Disease", diseases)
filtered = df[df["disease_code"] == disease]

by_location = filtered.groupby("location", as_index=False)["trend_value"].sum().sort_values("trend_value", ascending=False)
fig = px.bar(
    by_location, x="location", y="trend_value",
    labels={"location": "State", "trend_value": "Case count"},
    title=f"{disease.title()} case counts by state",
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(by_location, use_container_width=True)
