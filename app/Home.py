"""
Streamlit entry point. Run with: streamlit run app/Home.py
Additional pages live in app/pages/ and appear automatically in the sidebar.
"""
import streamlit as st

st.set_page_config(page_title="Disease Trend Analysis System", layout="wide")

st.title("Disease Trend Analysis System")
st.markdown(
    """
    Analysis of Patient Health Records for Disease Trend Identification using Data Mining.

    Use the sidebar to:
    - **Upload** a patient-records CSV (or use the bundled hybrid dataset)
    - View **Trends Overview**, **Geographic View**, and **Demographic View**
    - Inspect **Clusters** discovered by the clustering model
    - Review **Model Performance** metrics
    - Generate a **Report**
    """
)

st.info(
    "First time running this? Use the Upload page to load the hybrid dataset "
    "(data/raw/patient_records.csv, built by src/dataset_builder.py) into the database."
)
