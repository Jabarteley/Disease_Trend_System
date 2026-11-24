"""
Streamlit entry point. Run with: streamlit run app/Home.py
Additional pages live in app/pages/ and appear automatically in the sidebar.
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from common import load_kpis  # noqa: E402

st.set_page_config(
    page_title="Disease Trend Analysis System",
    page_icon=":material/monitoring:",
    layout="wide",
)

st.title(":material/monitoring: Disease trend analysis system", width="content")
st.caption("Analysis of patient health records for disease trend identification using data mining")

kpis = load_kpis()

if kpis["total"] == 0:
    st.info(
        "No data loaded yet. Open **Upload** in the sidebar, use the bundled hybrid "
        "dataset (or upload your own CSV), and run the pipeline.",
        icon=":material/upload_file:",
    )
else:
    with st.container(horizontal=True):
        st.metric("Total records", f"{kpis['total']:,}", border=True)
        for disease, count in sorted(kpis["by_disease"].items(), key=lambda kv: -kv[1]):
            pct = count / kpis["total"] * 100
            st.metric(disease.title(), f"{count:,}", f"{pct:.1f}% of cohort", border=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader(":material/route: Pipeline")
        st.markdown(
            "1. **Upload** — CSV upload or the bundled hybrid dataset\n"
            "2. **Preprocessing** — cleaning, encoding, derived features\n"
            "3. **Classification** — Random Forest predicts disease category\n"
            "4. **Clustering** — K-Means groups cases by demographic/geographic similarity\n"
            "5. **Dashboard** — trends, clusters, and model performance"
        )
with col2:
    with st.container(border=True):
        st.subheader(":material/explore: Where to go next")
        st.page_link("pages/1_Upload.py", label="Upload data", icon=":material/upload_file:")
        st.page_link("pages/2_Trends_Overview.py", label="Trends overview", icon=":material/timeline:")
        st.page_link("pages/3_Geographic_View.py", label="Geographic view", icon=":material/public:")
        st.page_link("pages/4_Demographic_View.py", label="Demographic view", icon=":material/group:")
        st.page_link("pages/5_Clusters.py", label="Clusters (K-Means)", icon=":material/hub:")
        st.page_link("pages/6_Model_Performance.py", label="Model performance", icon=":material/insights:")
        st.page_link("pages/7_Reports.py", label="Reports", icon=":material/description:")
