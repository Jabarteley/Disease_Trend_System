import os
import sys
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_clustered_records, clear_cache, auth_gate, ROOT_DIR  # noqa: E402

auth_gate()

sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

st.title(":material/hub: Clusters")

if st.button("Run clustering now", icon=":material/play_arrow:"):
    import clustering
    try:
        with st.spinner("Running K-Means over a range of k, selecting the best by silhouette score..."):
            clustering.run()
        clear_cache()
        st.success("Clustering complete.", icon=":material/check_circle:")
    except FileNotFoundError:
        st.error(
            "No cleaned dataset found yet. Go to **Upload** first and run "
            "preprocessing → load database → compute trends.",
            icon=":material/error:",
        )
    except Exception as e:
        st.error(f"Clustering failed: {e}", icon=":material/error:")
        with st.expander("Full error details"):
            st.exception(e)

df = load_clustered_records()
if df is None:
    st.info("No clustering results yet — click “Run clustering now” above.", icon=":material/info:")
    st.stop()

with st.container(border=True):
    st.subheader("Clusters by age and visit month")
    st.scatter_chart(
        df, x="age", y="visit_month", color="cluster", size=40,
        x_label="Age", y_label="Visit month",
        alt="Clusters by age and visit month",
    )

with st.container(border=True):
    st.subheader("Cluster summary")
    summary = df.groupby("cluster").agg(
        size=("patient_id", "count"),
        dominant_location=("location", lambda s: s.mode().iat[0]),
        dominant_diagnosis=("diagnosis", lambda s: s.mode().iat[0]),
        mean_age=("age", "mean"),
    ).round(1).rename(columns={
        "size": "Size", "dominant_location": "Dominant location",
        "dominant_diagnosis": "Dominant diagnosis", "mean_age": "Mean age",
    })
    st.dataframe(summary, width="stretch", alt="Cluster summary table")
    st.caption(
        "Interpretation is left to the analyst: a cluster dominated by one location "
        "and one season may indicate a localised, time-bound trend worth investigating."
    )
