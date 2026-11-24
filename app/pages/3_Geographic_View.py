import os
import sys
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_trend_reports  # noqa: E402

st.title(":material/public: Geographic view")

df = load_trend_reports()
if df.empty:
    st.info("No trend data yet — open Upload first.", icon=":material/upload_file:")
    st.stop()

diseases = sorted(df["disease_code"].unique())
disease = st.segmented_control("Disease", diseases, default=diseases[0])
filtered = df[df["disease_code"] == disease] if disease else df.iloc[0:0]

with st.container(border=True):
    st.subheader(f"{(disease or '').title()} case counts by state")
    by_location = (
        filtered.groupby("location", as_index=False)["trend_value"]
        .sum()
        .sort_values("trend_value", ascending=False)
    )
    st.bar_chart(
        by_location, x="location", y="trend_value", horizontal=True,
        x_label="State", y_label="Case count",
        alt=f"{(disease or '').title()} case counts by state",
    )
    st.dataframe(
        by_location.rename(columns={"location": "State", "trend_value": "Case count"}),
        hide_index=True, width="stretch", alt=f"{(disease or '').title()} case counts by state, table form",
    )
