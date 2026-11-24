import os
import sys
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import ROOT_DIR  # noqa: E402

sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

st.title("Model Performance")

st.subheader("Classification (Random Forest)")
if st.button("Train and evaluate classifier"):
    import classification
    with st.spinner("Training and evaluating..."):
        model, test_results = classification.run()
    st.session_state["classifier_results"] = test_results

results = st.session_state.get("classifier_results")
if results:
    cols = st.columns(len(results))
    for col, (k, v) in zip(cols, results.items()):
        col.metric(k, f"{v:.3f}")
else:
    st.caption("Click the button above to train and see metrics here (also printed to the terminal in full, including the per-class report and confusion matrix).")

st.divider()
st.subheader("Clustering (K-Means)")
st.caption(
    "k is selected automatically by comparing Silhouette, Davies-Bouldin, and "
    "Calinski-Harabasz scores across candidate k values — see the Clusters page "
    "to run it and the terminal output for the full comparison table."
)
