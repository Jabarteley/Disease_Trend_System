import os
import sys
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import auth_gate, ROOT_DIR  # noqa: E402

auth_gate()

sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

st.title(":material/insights: Model performance")

with st.container(border=True):
    st.subheader(":material/forest: Classification (Random Forest)")
    if st.button("Train and evaluate classifier", icon=":material/play_arrow:"):
        import classification
        try:
            with st.spinner("Training and evaluating..."):
                model, test_results = classification.run()
            st.session_state["classifier_results"] = test_results
        except FileNotFoundError:
            st.error(
                "No training data found yet. Go to **Upload** first and run "
                "preprocessing → load database → compute trends.",
                icon=":material/error:",
            )
        except Exception as e:
            st.error(f"Training failed: {e}", icon=":material/error:")
            with st.expander("Full error details"):
                st.exception(e)

    results = st.session_state.get("classifier_results")
    if results:
        with st.container(horizontal=True):
            for k, v in results.items():
                st.metric(k.replace("_", " "), f"{v:.3f}", border=True)
    else:
        st.caption(
            "Click the button above to train and see metrics here (the per-class "
            "report and confusion matrix print to the terminal)."
        )

with st.container(border=True):
    st.subheader(":material/hub: Clustering (K-Means)")
    st.caption(
        "k is selected automatically by comparing Silhouette, Davies-Bouldin, and "
        "Calinski-Harabasz scores across candidate k values — see the Clusters page "
        "to run it and the terminal output for the full comparison table."
    )
    st.page_link("app_pages/5_Clusters.py", label="Go to Clusters", icon=":material/arrow_forward:")
