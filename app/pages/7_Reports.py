import sys
import os
from datetime import datetime, timezone
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_trend_reports  # noqa: E402

st.title(":material/description: Reports")

df = load_trend_reports()
if df.empty:
    st.info("No trend data yet — open Upload first.", icon=":material/upload_file:")
    st.stop()

summary = (
    df.groupby(["disease_code", "location"], as_index=False)["trend_value"]
    .sum()
    .sort_values(["disease_code", "trend_value"], ascending=[True, False])
    .rename(columns={"disease_code": "Disease", "location": "Location", "trend_value": "Case count"})
)

with st.container(border=True):
    st.subheader("Summary report")
    st.dataframe(summary, hide_index=True, width="stretch", alt="Disease trend summary by location")

    csv = summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV report",
        data=csv,
        file_name=f"disease_trend_report_{datetime.now(timezone.utc).date()}.csv",
        mime="text/csv",
        icon=":material/download:",
    )
