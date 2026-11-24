import os
import sys
import streamlit as st
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_clustered_records, clear_cache, ROOT_DIR  # noqa: E402

sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

st.title("Clusters")

if st.button("Run clustering now"):
    import clustering
    with st.spinner("Running K-Means over a range of k, selecting the best by silhouette score..."):
        clustering.run()
    clear_cache()
    st.success("Clustering complete.")

df = load_clustered_records()
if df is None:
    st.warning("No clustering results yet — click “Run clustering now” above.")
    st.stop()

fig = px.scatter(
    df, x="age", y="visit_month", color="cluster", symbol="diagnosis",
    hover_data=["location", "diagnosis"],
    labels={"age": "Age", "visit_month": "Visit month", "cluster": "Cluster"},
    title="Clusters by age and visit month",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Cluster summary")
summary = df.groupby("cluster").agg(
    size=("patient_id", "count"),
    dominant_location=("location", lambda s: s.mode().iat[0]),
    dominant_diagnosis=("diagnosis", lambda s: s.mode().iat[0]),
    mean_age=("age", "mean"),
).round(1)
st.dataframe(summary, use_container_width=True)
st.caption(
    "Interpretation is left to the analyst: a cluster dominated by one location "
    "and one season may indicate a localised, time-bound trend worth investigating."
)
